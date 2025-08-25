# Lambda deployment package
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = var.source_dir
  output_path = var.output_zip_path
}

# Shopping Reminder module
module "shopping_reminder" {
  source = "../../modules/shopping-reminder"

  # Notion configuration
  notion_api_key     = var.notion_api_key
  notion_database_id = var.notion_database_id
  notion_page_id     = var.notion_page_id

  # Lambda configuration
  lambda_function_name    = var.lambda_function_name
  lambda_zip_path         = data.archive_file.lambda_zip.output_path
  lambda_source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  lambda_timeout          = var.lambda_timeout
  lambda_memory_size      = var.lambda_memory_size

  # EventBridge configuration
  schedule_expression = var.schedule_expression

  # CloudWatch configuration
  cloudwatch_log_retention_days = var.cloudwatch_log_retention_days

  # Resource management
  resource_group_name                 = var.resource_group_name
  create_comprehensive_resource_group = var.create_comprehensive_resource_group

  # Tags
  tags = var.tags
}
