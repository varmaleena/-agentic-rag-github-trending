resource "aws_lambda_function" "github_ingestion_lambda" {
  package_type                   = "Image"
  image_uri                      = var.ingestion_image
  function_name                  = "agentic-rag-github-ingestion"
  role                           = aws_iam_role.lambda_execution_role.arn
  timeout                        = 300
  memory_size                    = 1024
  reserved_concurrent_executions = 1

  environment {
    variables = {
      QDRANT_URL                = var.qdrant_url
      QDRANT_API_KEY_SECRET_ARN = var.qdrant_api_key_secret_arn
      GITHUB_TOKEN_SECRET_ARN   = var.github_token_secret_arn
      FASTEMBED_CACHE_PATH      = "/tmp/fastembed"
    }
  }
}

resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/agentic-rag-github-ingestion"
  retention_in_days = 7
}

# EventBridge Rule for 15-minute polling schedule
resource "aws_cloudwatch_event_rule" "ingestion_schedule" {
  name                = "agentic-rag-ingestion-15min-trigger"
  description         = "Triggers GitHub trending repo ingestion Lambda every 15 minutes"
  schedule_expression = "rate(15 minutes)"
}

resource "aws_cloudwatch_event_target" "trigger_lambda" {
  rule      = aws_cloudwatch_event_rule.ingestion_schedule.name
  target_id = "IngestionLambdaTarget"
  arn       = aws_lambda_function.github_ingestion_lambda.arn
}

resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.github_ingestion_lambda.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.ingestion_schedule.arn
}
