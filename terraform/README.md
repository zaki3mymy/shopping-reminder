# Terraform Infrastructure

このディレクトリには、Shopping Reminder アプリケーション用のTerraformインフラストラクチャコードが含まれています。

## 構成

```
terraform/
├── modules/
│   └── shopping-reminder/    # メインアプリケーションモジュール
│       ├── main.tf          # リソース定義
│       ├── variables.tf     # 変数定義
│       └── outputs.tf       # 出力値定義
├── environments/
│   └── production/          # 本番環境設定
│       ├── main.tf          # モジュール使用
│       ├── variables.tf     # 環境変数定義
│       ├── outputs.tf       # 出力値
│       ├── providers.tf     # プロバイダー設定
│       ├── versions.tf      # Terraform/プロバイダーバージョン
│       └── terraform.tfvars # 環境固有の値
└── README.md               # このファイル
```

## 概要

以下のAWSリソースを作成します：

- **AWS Lambda**: 日用品チェッカーアプリケーション
- **EventBridge**: 毎日17:00（JST）にLambdaを実行するスケジュール
- **CloudWatch Logs**: Lambda実行ログの保存
- **IAM Role**: Lambda実行に必要な最小限の権限
- **Resource Groups**: AWS リソースの管理・監視を簡素化

## デプロイメント

### 本番環境

```bash
cd environments/production

# 初期化
terraform init \
  -backend-config="bucket=<YOUR_BUCKET_NAME>" \
  -backend-config="key=shopping-reminder/terraform.tfstate" \
  -backend-config="region=ap-northeast-1"

# プランニング
terraform plan

# デプロイ
terraform apply
```

### terraform.tfvars の設定

`environments/production/terraform.tfvars` に以下の値を設定してください：

```hcl
notion_api_key     = "secret_xxxxxxxxxxxx"
notion_database_id = "database-id-here"
notion_page_id     = "page-id-here"
```

## デプロイ後の確認

```bash
# 作成されたリソースの確認
terraform output

# Lambda実行テスト
aws lambda invoke --function-name shopping-reminder response.json

# リソースグループの確認
aws resource-groups list-groups
aws resource-groups get-group --group-name shopping-reminder-resources
```

## モジュール

### shopping-reminder モジュール

メインアプリケーションのAWSリソースを管理するモジュールです：

- **Lambda関数**: メインアプリケーション実行
- **EventBridge**: 日次スケジュール実行
- **IAMロール**: Lambda実行権限
- **CloudWatchロググループ**: ログ記録
- **リソースグループ**: リソース管理

#### 主要変数

- `notion_api_key`: Notion API キー (sensitive)
- `notion_database_id`: 監視対象データベースID
- `notion_page_id`: コメント投稿先ページID
- `lambda_function_name`: Lambda関数名
- `schedule_expression`: 実行スケジュール (デフォルト: JST 17:00)

#### 出力値

- `lambda_function_arn`: Lambda関数ARN
- `eventbridge_rule_arn`: EventBridge ルールARN
- `cloudwatch_log_group_name`: CloudWatchロググループ名

詳細は各モジュールの `variables.tf` と `outputs.tf` を参照してください。

<!-- BEGIN_TF_DOCS -->


## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | >= 1.2.0 |
| <a name="requirement_aws"></a> [aws](#requirement\_aws) | ~> 5.92 |

## Providers

| Name | Version |
|------|---------|
| <a name="provider_aws"></a> [aws](#provider\_aws) | ~> 5.92 |

## Modules

No modules.

## Resources

| Name | Type |
|------|------|
| [aws_cloudwatch_event_rule.daily_reminder](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_event_rule) | resource |
| [aws_cloudwatch_event_target.lambda_target](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_event_target) | resource |
| [aws_cloudwatch_log_group.lambda_log_group](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_log_group) | resource |
| [aws_iam_role.lambda_role](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role) | resource |
| [aws_iam_role_policy.lambda_policy](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role_policy) | resource |
| [aws_iam_role_policy_attachment.lambda_basic_execution](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role_policy_attachment) | resource |
| [aws_lambda_function.shopping_reminder](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_function) | resource |
| [aws_lambda_permission.allow_eventbridge](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_permission) | resource |
| [aws_resourcegroups_group.shopping_reminder](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/resourcegroups_group) | resource |
| [aws_resourcegroups_group.shopping_reminder_all](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/resourcegroups_group) | resource |
| [aws_caller_identity.current](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/caller_identity) | data source |
| [aws_region.current](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/region) | data source |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_cloudwatch_log_retention_days"></a> [cloudwatch\_log\_retention\_days](#input\_cloudwatch\_log\_retention\_days) | CloudWatch log retention period in days | `number` | `14` | no |
| <a name="input_create_comprehensive_resource_group"></a> [create\_comprehensive\_resource\_group](#input\_create\_comprehensive\_resource\_group) | Whether to create a comprehensive resource group that includes all AWS resources | `bool` | `false` | no |
| <a name="input_lambda_function_name"></a> [lambda\_function\_name](#input\_lambda\_function\_name) | Name of the Lambda function | `string` | `"shopping-reminder"` | no |
| <a name="input_lambda_memory_size"></a> [lambda\_memory\_size](#input\_lambda\_memory\_size) | Lambda function memory size in MB | `number` | `128` | no |
| <a name="input_lambda_source_code_hash"></a> [lambda\_source\_code\_hash](#input\_lambda\_source\_code\_hash) | Base64 encoded hash of the Lambda zip file | `string` | n/a | yes |
| <a name="input_lambda_timeout"></a> [lambda\_timeout](#input\_lambda\_timeout) | Lambda function timeout in seconds | `number` | `30` | no |
| <a name="input_lambda_zip_path"></a> [lambda\_zip\_path](#input\_lambda\_zip\_path) | Path to the Lambda deployment zip file | `string` | n/a | yes |
| <a name="input_notion_api_key"></a> [notion\_api\_key](#input\_notion\_api\_key) | Notion API key for accessing the workspace | `string` | n/a | yes |
| <a name="input_notion_database_id"></a> [notion\_database\_id](#input\_notion\_database\_id) | ID of the Notion database containing shopping list items | `string` | n/a | yes |
| <a name="input_notion_page_id"></a> [notion\_page\_id](#input\_notion\_page\_id) | ID of the Notion page where comments will be posted | `string` | n/a | yes |
| <a name="input_resource_group_name"></a> [resource\_group\_name](#input\_resource\_group\_name) | Name of the AWS Resource Group | `string` | `"shopping-reminder-resources"` | no |
| <a name="input_schedule_expression"></a> [schedule\_expression](#input\_schedule\_expression) | EventBridge schedule expression for the reminder (JST 17:00 = UTC 08:00) | `string` | `"cron(0 8 * * ? *)"` | no |
| <a name="input_tags"></a> [tags](#input\_tags) | Tags to apply to all resources | `map(string)` | <pre>{<br/>  "ManagedBy": "terraform",<br/>  "Project": "shopping-reminder"<br/>}</pre> | no |

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

## セキュリティ考慮事項

- Notion API キーは`sensitive = true`で保護されています
- IAM ロールは最小権限の原則に従い、必要な権限のみを付与
- CloudWatch Logsのみアクセス可能

## AWS Resource Groups について

このTerraform設定では、作成されたAWSリソースを効率的に管理するためにResource Groupsを使用します。

### 作成されるリソースグループ

1. **メインリソースグループ** (`shopping-reminder-resources`)
   - Lambda、EventBridge、CloudWatch Logsを含む
   - プロジェクトタグでフィルタリング
   - 注意: IAMロールはResource Groupsでサポートされていないため除外

2. **包括的リソースグループ** (`shopping-reminder-resources-all`) - オプション
   - プロジェクトに関連する全てのAWSリソースを含む
   - `create_comprehensive_resource_group = true` で有効化

### リソースグループの利点

- **一元管理**: 関連リソースをグループ化して管理
- **監視の簡素化**: CloudWatchでグループ単位での監視
- **コスト分析**: 請求情報をプロジェクト単位で分析
- **権限管理**: リソースグループに対する一括操作

### 使用方法

```bash
# リソースグループ一覧表示
aws resource-groups list-groups

# 特定グループの詳細確認
aws resource-groups get-group --group-name shopping-reminder-resources

# グループ内のリソース一覧
aws resource-groups list-group-resources --group-name shopping-reminder-resources

# AWS コンソールでの確認
# https://console.aws.amazon.com/resource-groups/
```

## トラブルシューティング

### Lambda実行エラー

CloudWatch Logsでエラーを確認：

```bash
aws logs tail /aws/lambda/shopping-reminder --follow
```

### 権限エラー

IAMロールの権限を確認し、必要に応じて追加：

```bash
aws iam get-role --role-name shopping-reminder-role
```

### リソースグループが空の場合

タグが正しく設定されているか確認：

```bash
# リソースのタグ確認
aws lambda get-function --function-name shopping-reminder --query 'Tags'
```

## リソース削除

```bash
terraform destroy
```

## ベストプラクティス準拠

このTerraform設定はGoogleのベストプラクティスに準拠しています：

- 型指定された変数とデフォルト値
- 明確な説明文
- 適切なファイル分割
- タグ付けの一貫性
- アウトプットの提供
- S3バックエンドによるステート管理
- バージョン固定されたプロバイダー

## 開発ワークフロー

pre-commitフックが設定されており、以下が自動実行されます：

- Terraformファイルの自動フォーマット (`terraform fmt`)
- Terraformファイルの構文検証 (`terraform validate`)
- AWS認証情報の漏洩チェック
- Pythonコードのlintとtype check
- 単体テストの実行（pre-merge-commit時）
