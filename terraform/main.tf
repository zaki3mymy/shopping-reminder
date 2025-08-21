provider "aws" {
  region = "ap-northeast-1"
}

# Data source for current AWS account info
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}
