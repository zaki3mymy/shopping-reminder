output "lambda_function_name" {
  description = "Name of the Lambda function"
  value       = module.shopping_reminder.lambda_function_name
}

output "lambda_function_arn" {
  description = "ARN of the Lambda function"
  value       = module.shopping_reminder.lambda_function_arn
}

output "eventbridge_rule_name" {
  description = "Name of the EventBridge rule"
  value       = module.shopping_reminder.eventbridge_rule_name
}

output "eventbridge_rule_arn" {
  description = "ARN of the EventBridge rule"
  value       = module.shopping_reminder.eventbridge_rule_arn
}

output "schedule_expression" {
  description = "EventBridge schedule expression used"
  value       = module.shopping_reminder.schedule_expression
}

output "cloudwatch_log_group_name" {
  description = "Name of the CloudWatch log group"
  value       = module.shopping_reminder.cloudwatch_log_group_name
}

output "iam_role_arn" {
  description = "ARN of the IAM role used by Lambda"
  value       = module.shopping_reminder.iam_role_arn
}

output "resource_group_name" {
  description = "Name of the main resource group"
  value       = module.shopping_reminder.resource_group_name
}

output "resource_group_arn" {
  description = "ARN of the main resource group"
  value       = module.shopping_reminder.resource_group_arn
}

output "comprehensive_resource_group_name" {
  description = "Name of the comprehensive resource group (if created)"
  value       = module.shopping_reminder.comprehensive_resource_group_name
}

output "comprehensive_resource_group_arn" {
  description = "ARN of the comprehensive resource group (if created)"
  value       = module.shopping_reminder.comprehensive_resource_group_arn
}
