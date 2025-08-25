# Data sources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# CloudWatch Log Group for Lambda
resource "aws_cloudwatch_log_group" "lambda_log_group" {
  name              = "/aws/lambda/${var.lambda_function_name}"
  retention_in_days = var.cloudwatch_log_retention_days

  tags = var.tags
}

# Lambda function
resource "aws_lambda_function" "shopping_reminder" {
  filename      = var.lambda_zip_path
  function_name = var.lambda_function_name
  role          = aws_iam_role.lambda_role.arn
  handler       = "lambda_handler.handler"
  runtime       = "python3.13"
  timeout       = var.lambda_timeout
  memory_size   = var.lambda_memory_size

  source_code_hash = var.lambda_source_code_hash

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

# Lambda permission for EventBridge to invoke
resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.shopping_reminder.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily_reminder.arn
}

# IAM role for Lambda function
resource "aws_iam_role" "lambda_role" {
  name = "${var.lambda_function_name}-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = var.tags
}

# IAM policy for Lambda basic execution
resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role       = aws_iam_role.lambda_role.name
}

# Custom IAM policy for Lambda function
resource "aws_iam_role_policy" "lambda_policy" {
  name = "${var.lambda_function_name}-policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:*"
      }
    ]
  })
}

# Resource Groups
resource "aws_resourcegroups_group" "shopping_reminder" {
  name = var.resource_group_name

  resource_query {
    query = jsonencode({
      ResourceTypeFilters = [
        "AWS::Lambda::Function",
        "AWS::Events::Rule",
        "AWS::Logs::LogGroup"
      ]
      TagFilters = [
        {
          Key    = "Project"
          Values = [var.tags.Project]
        }
      ]
    })
  }

  tags = var.tags
}

# Comprehensive resource group (optional)
resource "aws_resourcegroups_group" "shopping_reminder_all" {
  count = var.create_comprehensive_resource_group ? 1 : 0
  name  = "${var.resource_group_name}-all"

  resource_query {
    query = jsonencode({
      ResourceTypeFilters = ["AWS::AllSupported"]
      TagFilters = [
        {
          Key    = "Project"
          Values = [var.tags.Project]
        }
      ]
    })
  }

  tags = var.tags
}
