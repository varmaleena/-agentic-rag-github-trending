variable "aws_region" {
  description = "AWS region for infrastructure deployment"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Deployment environment name"
  type        = string
  default     = "dev"
}

variable "bedrock_model_id" {
  description = "Bedrock model ID or inference profile ID"
  type        = string
  default     = "us.amazon.nova-lite-v1:0"
}

variable "backend_image" {
  type = string
}

variable "ingestion_image" {
  type = string
}

variable "acm_certificate_arn" {
  type = string
}

variable "qdrant_url" {
  type = string
  validation {
    condition     = startswith(var.qdrant_url, "https://")
    error_message = "Qdrant must be reachable over HTTPS."
  }
}

variable "qdrant_api_key_secret_arn" {
  type = string
}

variable "github_token_secret_arn" {
  type = string
}

variable "history_database_url_secret_arn" {
  type = string
}
