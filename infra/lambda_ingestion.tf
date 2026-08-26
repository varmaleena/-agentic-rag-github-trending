resource "aws_lambda_function" "github_ingestion_lambda" {
  filename         = "ingestion.zip" # Packaged Lambda ZIP artifact
  function_name    = "agentic-rag-github-ingestion"
  role             = aws_iam_role.lambda_execution_role.arn
  handler          = "lambda_handler.lambda_handler"
  runtime          = "python3.11"
  timeout          = 300
  memory_size      = 512

  environment {
    variables = {
      AWS_REGION      = var.aws_region
      QDRANT_HOST     = aws_instance.qdrant_ec2.private_ip
      QDRANT_PORT     = "6333"
      GITHUB_TOKEN    = ""
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
