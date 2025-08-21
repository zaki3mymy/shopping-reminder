# AWS Resource Groups for Shopping Reminder Application

resource "aws_resourcegroups_group" "shopping_reminder" {
  name        = var.resource_group_name
  description = "Resources for Shopping Reminder application"

  resource_query {
    query = jsonencode({
      ResourceTypeFilters = [
        "AWS::Lambda::Function",
        "AWS::Events::Rule",
        "AWS::Logs::LogGroup",
        "AWS::IAM::Role"
      ],
      TagFilters = [
        {
          Key    = "Project"
          Values = ["shopping-reminder"]
        }
      ]
    })
  }

  tags = {
    Name        = var.resource_group_name
    Project     = "shopping-reminder"
    Environment = var.environment
  }
}

# Optional: Resource group for all resources (tag-based)
resource "aws_resourcegroups_group" "shopping_reminder_all" {
  count       = var.create_comprehensive_resource_group ? 1 : 0
  name        = "${var.resource_group_name}-all"
  description = "All resources related to Shopping Reminder application"

  resource_query {
    query = jsonencode({
      ResourceTypeFilters = ["AWS::AllSupported"],
      TagFilters = [
        {
          Key    = "Project"
          Values = ["shopping-reminder"]
        }
      ]
    })
  }

  tags = {
    Name        = "${var.resource_group_name}-all"
    Project     = "shopping-reminder"
    Environment = var.environment
  }
}
