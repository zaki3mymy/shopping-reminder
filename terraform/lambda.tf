# CloudWatch Log Group for Lambda
resource "aws_cloudwatch_log_group" "lambda_log_group" {
  name              = "/aws/lambda/${var.lambda_function_name}"
  retention_in_days = var.cloudwatch_log_retention_days

  tags = var.tags
}

# Lambda function
resource "aws_lambda_function" "shopping_reminder" {
  filename      = data.archive_file.lambda_zip.output_path
  function_name = var.lambda_function_name
  role          = aws_iam_role.lambda_role.arn
  handler       = "lambda_handler.handler"
  runtime       = "python3.13"
  timeout       = var.lambda_timeout
  memory_size   = var.lambda_memory_size

  source_code_hash = data.archive_file.lambda_zip.output_base64sha256

  environment {
    variables = {
      NOTION_API_KEY     = var.notion_api_key
      NOTION_DATABASE_ID = var.notion_database_id
      NOTION_PAGE_ID     = var.notion_page_id
    }
  }

  depends_on = [
    aws_iam_role_policy_attachment.lambda_basic_execution,
    aws_cloudwatch_log_group.lambda_log_group,
  ]

  tags = var.tags
}

# Lambda permission for EventBridge to invoke
resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.shopping_reminder.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily_reminder.arn
}
