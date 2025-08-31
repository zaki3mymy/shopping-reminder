# Production Environment

Shopping Reminder アプリケーションの本番環境デプロイメント設定です。

## デプロイメント手順

### 1. 事前準備

#### S3バックエンドの設定

Terraformの状態管理用S3バケットを作成してください：

```bash
# S3バケット作成（バケット名は一意である必要があります）
aws s3 mb s3://your-terraform-state-bucket --region ap-northeast-1

# バージョニング有効化
aws s3api put-bucket-versioning \
  --bucket your-terraform-state-bucket \
  --versioning-configuration Status=Enabled

# 暗号化有効化
aws s3api put-bucket-encryption \
  --bucket your-terraform-state-bucket \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "AES256"
      }
    }]
  }'
```

#### Lambda デプロイパッケージの準備

```bash
# プロジェクトルートで実行
cd ../../../
python -m zipfile -c dist/lambda_function.zip src/shopping_reminder/*
```

### 2. 環境固有設定

#### terraform.tfvars の作成

`terraform.tfvars`ファイルを作成し、以下の値を設定してください：

```hcl
# Notion API設定
notion_api_key     = "secret_xxxxxxxxxxxx"  # NotionのIntegrationから取得
notion_database_id = "your-database-id"     # ショッピングリストデータベースのID
notion_page_id     = "your-page-id"         # コメント投稿先ページのID

# Lambda設定
lambda_function_name = "shopping-reminder"
lambda_zip_path     = "../../dist/lambda_function.zip"
lambda_source_code_hash = filebase64sha256("../../dist/lambda_function.zip")

# スケジュール設定（デフォルト：JST 17:00）
schedule_expression = "cron(0 8 * * ? *)"  # UTC 08:00 = JST 17:00

# リソースタグ
tags = {
  Environment = "production"
  ManagedBy   = "terraform"
  Project     = "shopping-reminder"
}
```

### 3. デプロイ実行

```bash
cd terraform/environments/production

# Terraform初期化
terraform init \
  -backend-config="bucket=your-terraform-state-bucket" \
  -backend-config="key=shopping-reminder/production.tfstate" \
  -backend-config="region=ap-northeast-1"

# プラン確認
terraform plan

# デプロイ実行
terraform apply
```

## 設定値の取得方法

### Notion API Key

1. [Notion Developers](https://www.notion.so/my-integrations) にアクセス
2. 「New integration」で新しい統合を作成
3. 生成された「Internal Integration Token」をコピー

### Database ID

1. Notion でショッピングリストデータベースを開く
2. URLから32文字のIDを取得: `https://notion.so/{database_id}?v=...`
3. ハイフンを除いた32文字がDatabase ID

### Page ID

1. コメントを投稿したいNotionページを開く
2. URLから32文字のIDを取得: `https://notion.so/{page_id}`
3. ハイフンを除いた32文字がPage ID

## デプロイ後の確認

### リソースの確認

```bash
# 作成されたリソースの出力値確認
terraform output

# Lambda関数の確認
aws lambda get-function --function-name shopping-reminder

# EventBridgeルールの確認
aws events describe-rule --name shopping-reminder-daily
```

### 動作テスト

```bash
# Lambda関数の手動実行
aws lambda invoke \
  --function-name shopping-reminder \
  --payload '{}' \
  response.json

# レスポンス確認
cat response.json

# CloudWatchログの確認
aws logs tail /aws/lambda/shopping-reminder --follow
```

### リソースグループでの管理

```bash
# プロジェクトリソース一覧
aws resource-groups list-group-resources --group-name shopping-reminder-resources

# AWS コンソールでの確認
# https://console.aws.amazon.com/resource-groups/
```

## メンテナンス

### ログの確認

```bash
# 最新のログを表示
aws logs tail /aws/lambda/shopping-reminder --follow

# エラーログのみフィルタリング
aws logs filter-log-events \
  --log-group-name /aws/lambda/shopping-reminder \
  --filter-pattern "ERROR"
```

### コードの更新

```bash
# 新しいLambdaパッケージを作成
cd ../../../
python -m zipfile -c dist/lambda_function.zip src/shopping_reminder/*

# terraform.tfvarsのハッシュ値を更新
lambda_source_code_hash = filebase64sha256("../../dist/lambda_function.zip")

# デプロイ実行
cd terraform/environments/production
terraform apply
```

### 実行スケジュールの変更

`terraform.tfvars`の`schedule_expression`を変更してください：

```hcl
# 毎日JST 18:00に変更する場合
schedule_expression = "cron(0 9 * * ? *)"  # UTC 09:00 = JST 18:00

# 平日のみJST 17:00に変更する場合
schedule_expression = "cron(0 8 ? * MON-FRI *)"
```

## トラブルシューティング

### よくある問題

1. **Lambda関数が実行されない**
   - EventBridgeルールが有効か確認
   - IAMロールの権限を確認

2. **Notion API エラー**
   - API Keyが正しいか確認
   - データベース/ページIDが正しいか確認
   - Notionの統合権限が設定されているか確認

3. **デプロイエラー**
   - S3バックエンドのアクセス権限を確認
   - AWSクレデンシャルが設定されているか確認

### ログレベル設定

開発時のデバッグ用に、Lambdaの環境変数でログレベルを設定できます：

```hcl
# main.tf内のLambda関数設定で追加
environment {
  variables = {
    LOG_LEVEL = "DEBUG"  # INFO, DEBUG, ERROR
  }
}
```

## セキュリティ考慮事項

- Notion API Keyは`sensitive = true`でマークされ、ログに出力されません
- IAMロールは最小権限の原則に従い、必要な権限のみ付与
- S3バックエンドは暗号化とバージョニングを有効化
- CloudWatch Logsは14日間の保持期間を設定

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
| <a name="input_lambda_function_name"></a> [lambda\_function\_name](#input\_lambda\_function\_name) | Name of the Lambda function | `string` | `"shopping-reminder"` | no |
| <a name="input_lambda_memory_size"></a> [lambda\_memory\_size](#input\_lambda\_memory\_size) | Lambda function memory size in MB | `number` | `128` | no |
| <a name="input_lambda_timeout"></a> [lambda\_timeout](#input\_lambda\_timeout) | Lambda function timeout in seconds | `number` | `30` | no |
| <a name="input_notion_api_key"></a> [notion\_api\_key](#input\_notion\_api\_key) | Notion API key for accessing the workspace | `string` | n/a | yes |
| <a name="input_notion_database_id"></a> [notion\_database\_id](#input\_notion\_database\_id) | ID of the Notion database containing shopping list items | `string` | n/a | yes |
| <a name="input_notion_page_id"></a> [notion\_page\_id](#input\_notion\_page\_id) | ID of the Notion page where comments will be posted | `string` | n/a | yes |
| <a name="input_output_zip_path"></a> [output\_zip\_path](#input\_output\_zip\_path) | Path where the Lambda deployment zip file will be created | `string` | `"../../../dist/lambda_function.zip"` | no |
| <a name="input_resource_group_name"></a> [resource\_group\_name](#input\_resource\_group\_name) | Name of the AWS Resource Group | `string` | `"shopping-reminder-resources"` | no |
| <a name="input_schedule_expression"></a> [schedule\_expression](#input\_schedule\_expression) | EventBridge schedule expression for the reminder (JST 17:00 = UTC 08:00) | `string` | `"cron(0 8 * * ? *)"` | no |
| <a name="input_source_dir"></a> [source\_dir](#input\_source\_dir) | Path to the source directory containing Lambda function code | `string` | `"../../../src/shopping_reminder"` | no |
| <a name="input_tags"></a> [tags](#input\_tags) | Tags to apply to all resources | `map(string)` | <pre>{<br/>  "Environment": "production",<br/>  "ManagedBy": "terraform",<br/>  "Project": "shopping-reminder"<br/>}</pre> | no |

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
