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

variable "qdrant_instance_type" {
  description = "EC2 instance size for self-hosted Qdrant vector database"
  type        = string
  default     = "t3.small"
}

variable "bedrock_model_id" {
  description = "AWS Bedrock Claude model ID"
  type        = string
  default     = "anthropic.claude-3-haiku-20240307-v1:0"
}
