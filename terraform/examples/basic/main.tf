module "shopping_reminder" {
  source = "../../"

  notion_api_key     = var.notion_api_key
  notion_database_id = var.notion_database_id
  notion_page_id     = var.notion_page_id

  lambda_function_name = "shopping-reminder-example"

  tags = {
    Project     = "shopping-reminder"
    Environment = "example"
    ManagedBy   = "terraform"
  }
}
