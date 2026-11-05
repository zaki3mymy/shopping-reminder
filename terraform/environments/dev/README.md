# Dev Environment

Shopping Reminder アプリケーションの dev 環境の設定です。`develop` ブランチへの push で、CD（`.github/workflows/cd.yml`）がデプロイします。

本番環境（[production](../production/README.md)）との違い:

- Lambda 関数などのリソース名に `dev-` を付ける（`dev-shopping-reminder`）
- EventBridge の定期実行は無効にする（`schedule_enabled = false`）
- テスト用の Notion データベースを使う（GitHub の Environment `develop` の Secrets で設定する）
- Terraform の state は `shopping-reminder/dev/terraform.tfstate` に置く

## デプロイ

```bash
cd terraform/environments/dev

terraform init \
  -backend-config="bucket=your-terraform-state-bucket" \
  -backend-config="key=shopping-reminder/dev/terraform.tfstate" \
  -backend-config="region=ap-northeast-1"

terraform plan
terraform apply
```

## 動作確認

```bash
aws lambda invoke \
  --function-name dev-shopping-reminder \
  --payload '{}' \
  --cli-binary-format raw-in-base64-out \
  response.json
cat response.json
```

<!-- BEGIN_TF_DOCS -->


## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | >= 1.2.0 |
| <a name="requirement_archive"></a> [archive](#requirement\_archive) | ~> 2.7 |
| <a name="requirement_aws"></a> [aws](#requirement\_aws) | ~> 5.92 |

## Providers

| Name | Version |
|------|---------|
| <a name="provider_archive"></a> [archive](#provider\_archive) | 2.7.1 |

## Modules

| Name | Source | Version |
|------|--------|---------|
| <a name="module_shopping_reminder"></a> [shopping\_reminder](#module\_shopping\_reminder) | ../../modules/shopping-reminder | n/a |

## Resources

| Name | Type |
|------|------|
| [archive_file.lambda_zip](https://registry.terraform.io/providers/hashicorp/archive/latest/docs/data-sources/file) | data source |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_cloudwatch_log_retention_days"></a> [cloudwatch\_log\_retention\_days](#input\_cloudwatch\_log\_retention\_days) | CloudWatch log retention period in days | `number` | `14` | no |
| <a name="input_create_comprehensive_resource_group"></a> [create\_comprehensive\_resource\_group](#input\_create\_comprehensive\_resource\_group) | Whether to create a comprehensive resource group that includes all AWS resources | `bool` | `false` | no |
| <a name="input_lambda_function_name"></a> [lambda\_function\_name](#input\_lambda\_function\_name) | Name of the Lambda function | `string` | `"dev-shopping-reminder"` | no |
| <a name="input_lambda_memory_size"></a> [lambda\_memory\_size](#input\_lambda\_memory\_size) | Lambda function memory size in MB | `number` | `128` | no |
| <a name="input_lambda_timeout"></a> [lambda\_timeout](#input\_lambda\_timeout) | Lambda function timeout in seconds | `number` | `30` | no |
| <a name="input_notify_api_key"></a> [notify\_api\_key](#input\_notify\_api\_key) | API key for the notification service | `string` | n/a | yes |
| <a name="input_notify_api_url"></a> [notify\_api\_url](#input\_notify\_api\_url) | Base URL of the notification API | `string` | n/a | yes |
| <a name="input_notion_api_key"></a> [notion\_api\_key](#input\_notion\_api\_key) | Notion API key for accessing the workspace | `string` | n/a | yes |
| <a name="input_notion_database_id"></a> [notion\_database\_id](#input\_notion\_database\_id) | ID of the Notion database containing shopping list items | `string` | n/a | yes |
| <a name="input_output_zip_path"></a> [output\_zip\_path](#input\_output\_zip\_path) | Path where the Lambda deployment zip file will be created | `string` | `"../../../dist/lambda_function.zip"` | no |
| <a name="input_resource_group_name"></a> [resource\_group\_name](#input\_resource\_group\_name) | Name of the AWS Resource Group | `string` | `"dev-shopping-reminder-resources"` | no |
| <a name="input_schedule_expression"></a> [schedule\_expression](#input\_schedule\_expression) | EventBridge schedule expression for the reminder (JST 17:00 = UTC 08:00) | `string` | `"cron(0 8 * * ? *)"` | no |
| <a name="input_source_dir"></a> [source\_dir](#input\_source\_dir) | Path to the source directory containing Lambda function code | `string` | `"../../../src/shopping_reminder"` | no |
| <a name="input_tags"></a> [tags](#input\_tags) | Tags to apply to all resources | `map(string)` | <pre>{<br/>  "Environment": "dev",<br/>  "ManagedBy": "terraform",<br/>  "Project": "shopping-reminder-dev"<br/>}</pre> | no |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_cloudwatch_log_group_name"></a> [cloudwatch\_log\_group\_name](#output\_cloudwatch\_log\_group\_name) | Name of the CloudWatch log group |
| <a name="output_comprehensive_resource_group_arn"></a> [comprehensive\_resource\_group\_arn](#output\_comprehensive\_resource\_group\_arn) | ARN of the comprehensive resource group (if created) |
| <a name="output_comprehensive_resource_group_name"></a> [comprehensive\_resource\_group\_name](#output\_comprehensive\_resource\_group\_name) | Name of the comprehensive resource group (if created) |
| <a name="output_eventbridge_rule_arn"></a> [eventbridge\_rule\_arn](#output\_eventbridge\_rule\_arn) | ARN of the EventBridge rule |
| <a name="output_eventbridge_rule_name"></a> [eventbridge\_rule\_name](#output\_eventbridge\_rule\_name) | Name of the EventBridge rule |
| <a name="output_iam_role_arn"></a> [iam\_role\_arn](#output\_iam\_role\_arn) | ARN of the IAM role used by Lambda |
| <a name="output_lambda_function_arn"></a> [lambda\_function\_arn](#output\_lambda\_function\_arn) | ARN of the Lambda function |
| <a name="output_lambda_function_name"></a> [lambda\_function\_name](#output\_lambda\_function\_name) | Name of the Lambda function |
| <a name="output_resource_group_arn"></a> [resource\_group\_arn](#output\_resource\_group\_arn) | ARN of the main resource group |
| <a name="output_resource_group_name"></a> [resource\_group\_name](#output\_resource\_group\_name) | Name of the main resource group |
| <a name="output_schedule_expression"></a> [schedule\_expression](#output\_schedule\_expression) | EventBridge schedule expression used |

<!-- END_TF_DOCS -->
