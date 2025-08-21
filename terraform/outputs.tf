output "lambda_function_name" {
  description = "Name of the Lambda function"
  value       = aws_lambda_function.shopping_reminder.function_name
}

output "lambda_function_arn" {
  description = "ARN of the Lambda function"
  value       = aws_lambda_function.shopping_reminder.arn
}

output "eventbridge_rule_name" {
  description = "Name of the EventBridge rule"
  value       = aws_cloudwatch_event_rule.daily_reminder.name
}

output "eventbridge_rule_arn" {
  description = "ARN of the EventBridge rule"
  value       = aws_cloudwatch_event_rule.daily_reminder.arn
}

output "schedule_expression" {
  description = "EventBridge schedule expression used"
  value       = aws_cloudwatch_event_rule.daily_reminder.schedule_expression
}

output "cloudwatch_log_group_name" {
  description = "Name of the CloudWatch log group"
  value       = aws_cloudwatch_log_group.lambda_log_group.name
}

output "iam_role_arn" {
  description = "ARN of the IAM role used by Lambda"
  value       = aws_iam_role.lambda_role.arn
}

# Resource Groups outputs
output "resource_group_name" {
  description = "Name of the main resource group"
  value       = aws_resourcegroups_group.shopping_reminder.name
}

output "resource_group_arn" {
  description = "ARN of the main resource group"
  value       = aws_resourcegroups_group.shopping_reminder.arn
}

output "comprehensive_resource_group_name" {
  description = "Name of the comprehensive resource group (if created)"
  value       = var.create_comprehensive_resource_group ? aws_resourcegroups_group.shopping_reminder_all[0].name : null
}

output "comprehensive_resource_group_arn" {
  description = "ARN of the comprehensive resource group (if created)"
  value       = var.create_comprehensive_resource_group ? aws_resourcegroups_group.shopping_reminder_all[0].arn : null
}
