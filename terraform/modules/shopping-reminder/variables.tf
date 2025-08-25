variable "notion_api_key" {
  description = "Notion API key for accessing the workspace"
  type        = string
  sensitive   = true
}

variable "notion_database_id" {
  description = "ID of the Notion database containing shopping list items"
  type        = string
}

variable "notion_page_id" {
  description = "ID of the Notion page where comments will be posted"
  type        = string
}

variable "lambda_function_name" {
  description = "Name of the Lambda function"
  type        = string
  default     = "shopping-reminder"
}

variable "lambda_zip_path" {
  description = "Path to the Lambda deployment zip file"
  type        = string
}

variable "lambda_source_code_hash" {
  description = "Base64 encoded hash of the Lambda zip file"
  type        = string
}

variable "schedule_expression" {
  description = "EventBridge schedule expression for the reminder (JST 17:00 = UTC 08:00)"
  type        = string
  default     = "cron(0 8 * * ? *)"
}

variable "lambda_timeout" {
  description = "Lambda function timeout in seconds"
  type        = number
  default     = 30
}

variable "lambda_memory_size" {
  description = "Lambda function memory size in MB"
  type        = number
  default     = 128
}

variable "cloudwatch_log_retention_days" {
  description = "CloudWatch log retention period in days"
  type        = number
  default     = 14
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default = {
    Project   = "shopping-reminder"
    ManagedBy = "terraform"
  }
}

variable "resource_group_name" {
  description = "Name of the AWS Resource Group"
  type        = string
  default     = "shopping-reminder-resources"
}

variable "create_comprehensive_resource_group" {
  description = "Whether to create a comprehensive resource group that includes all AWS resources"
  type        = bool
  default     = false
}
