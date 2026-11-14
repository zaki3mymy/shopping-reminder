variable "notion_api_key" {
  description = "Notion API key for accessing the workspace"
  type        = string
  sensitive   = true
}

variable "notion_database_id" {
  description = "ID of the Notion database containing shopping list items"
  type        = string
}

variable "notify_api_key" {
  description = "API key for the notification service"
  type        = string
  sensitive   = true
}

variable "notify_api_url" {
  description = "Base URL of the notification API"
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

variable "schedule_enabled" {
  description = "Whether the EventBridge schedule is enabled (disable it in environments that should not send reminders on a schedule)"
  type        = bool
  default     = true
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

variable "environment" {
  description = "Deployment environment name (dev or prod), set as the OTel resource attribute deployment.environment.name"
  type        = string

  validation {
    condition     = contains(["dev", "prod"], var.environment)
    error_message = "environment must be either \"dev\" or \"prod\"."
  }
}

variable "otel_layer_arns" {
  description = "ARNs of the OpenTelemetry Lambda layers (Python instrumentation + collector)"
  type        = list(string)
  default = [
    # バージョンは https://github.com/open-telemetry/opentelemetry-lambda/releases で確認
    # （layer-python/<version>・layer-collector/<version> のタグ）
    "arn:aws:lambda:ap-northeast-1:184161586896:layer:opentelemetry-python-0_21_0:1",
    "arn:aws:lambda:ap-northeast-1:184161586896:layer:opentelemetry-collector-amd64-0_24_0:1",
  ]
}

variable "grafana_otlp_endpoint" {
  description = "OTLP endpoint of Grafana Cloud (the stack's OTLP URL with /otlp appended). The otlphttp exporter appends /v1/traces and /v1/metrics"
  type        = string
  default     = "https://otlp-gateway-prod-ap-northeast-0.grafana.net/otlp"
}

variable "grafana_otlp_auth_parameter" {
  description = "Name of the SSM parameter that holds the Authorization header value for Grafana Cloud OTLP (managed outside this repository)"
  type        = string
}
