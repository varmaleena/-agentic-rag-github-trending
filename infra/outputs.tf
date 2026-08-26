output "alb_dns_name" {
  description = "Public DNS URL of the Application Load Balancer in front of ECS FastAPI service"
  value       = aws_lb.api_alb.dns_name
}

output "qdrant_instance_private_ip" {
  description = "Private IP address of the Qdrant EC2 vector database instance"
  value       = aws_instance.qdrant_ec2.private_ip
}

output "lambda_function_name" {
  description = "Name of the ingestion Lambda function"
  value       = aws_lambda_function.github_ingestion_lambda.function_name
}
