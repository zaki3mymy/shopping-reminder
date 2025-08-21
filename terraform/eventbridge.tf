# EventBridge rule for daily reminder
resource "aws_cloudwatch_event_rule" "daily_reminder" {
  name                = "${var.lambda_function_name}-schedule"
  description         = "Trigger shopping reminder daily at 17:00 JST (08:00 UTC)"
  schedule_expression = var.schedule_expression

  tags = var.tags
}

# EventBridge target pointing to Lambda function
resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.daily_reminder.name
  target_id = "ShoppingReminderLambdaTarget"
  arn       = aws_lambda_function.shopping_reminder.arn
}
