terraform {
  required_version = ">= 1.5"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }
}

variable "project_id" {
  type = string
}

variable "region" {
  type = string
}

variable "backend_image" {
  type = string
}

variable "gemini_model" {
  type = string
}

variable "qdrant_url" {
  type = string
  validation {
    condition     = startswith(var.qdrant_url, "https://")
    error_message = "Qdrant must be reachable over HTTPS."
  }
}

variable "qdrant_api_key_secret" {
  type = string
}

variable "history_database_url_secret" {
  type = string
}

provider "google" {
  project = var.project_id
  region  = var.region
}

resource "google_project_service" "apis" {
  for_each           = toset(["aiplatform.googleapis.com", "run.googleapis.com", "secretmanager.googleapis.com"])
  service            = each.value
  disable_on_destroy = false
}

resource "google_service_account" "backend" {
  account_id = "agentic-rag-backend"
}

resource "google_project_iam_member" "vertex" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.backend.email}"
}

resource "google_secret_manager_secret_iam_member" "backend" {
  for_each   = toset([var.qdrant_api_key_secret, var.history_database_url_secret])
  secret_id  = each.value
  role       = "roles/secretmanager.secretAccessor"
  member     = "serviceAccount:${google_service_account.backend.email}"
  depends_on = [google_project_service.apis]
}

resource "google_cloud_run_v2_service" "backend" {
  name     = "agentic-rag"
  location = var.region

  template {
    service_account = google_service_account.backend.email
    timeout         = "900s"

    containers {
      image = var.backend_image

      ports {
        container_port = 8000
      }

      resources {
        limits = { cpu = "2", memory = "2Gi" }
      }

      dynamic "env" {
        for_each = {
          LLM_PROVIDER          = "vertex"
          GOOGLE_CLOUD_PROJECT  = var.project_id
          GOOGLE_CLOUD_LOCATION = "global"
          GEMINI_MODEL          = var.gemini_model
          QDRANT_URL            = var.qdrant_url
        }
        content {
          name  = env.key
          value = env.value
        }
      }

      dynamic "env" {
        for_each = {
          QDRANT_API_KEY       = var.qdrant_api_key_secret
          HISTORY_DATABASE_URL = var.history_database_url_secret
        }
        content {
          name = env.key
          value_source {
            secret_key_ref {
              secret  = env.value
              version = "latest"
            }
          }
        }
      }
    }
  }

  depends_on = [
    google_project_service.apis,
    google_project_iam_member.vertex,
    google_secret_manager_secret_iam_member.backend,
  ]
}

output "backend_url" {
  value = google_cloud_run_v2_service.backend.uri
}
