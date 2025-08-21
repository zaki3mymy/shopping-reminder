# Shopping Reminder Infrastructure

このディレクトリにはAWS Lambdaで動作する日用品チェッカーのTerraform設定が含まれています。

## 概要

以下のAWSリソースを作成します：

- **AWS Lambda**: 日用品チェッカーアプリケーション
- **EventBridge**: 毎日17:00（JST）にLambdaを実行するスケジュール
- **CloudWatch Logs**: Lambda実行ログの保存
- **IAM Role**: Lambda実行に必要な最小限の権限
- **Resource Groups**: AWS リソースの管理・監視を簡素化

## 前提条件

- AWS CLI が設定済み
- Terraform >= 1.2.0 がインストール済み
- S3バケット（Terraformステート保存用）が作成済み
- Lambda デプロイメントパッケージ `../dist/lambda_function.zip` が作成済み

## 使用方法

### 1. Lambdaパッケージの作成

```bash
# プロジェクトルートディレクトリで実行
mkdir -p dist

# shopping_reminder パッケージの内容をzipのトップレベルに配置
cd src/shopping_reminder
zip -r ../../dist/lambda_function.zip .
cd ../..

# 確認（zipのトップレベルに.pyファイルが配置されていることを確認）
unzip -l dist/lambda_function.zip
```

### 2. Terraform変数の設定

`terraform.tfvars` ファイルを作成し、必要な変数を設定：

```hcl
notion_api_key     = "secret_api_key_here"
notion_database_id = "your_database_id_here"
notion_page_id     = "your_page_id_here"
```

### 3. Terraformの実行

```bash
# 初期化（S3バックエンド設定）
terraform init \
  -backend-config="bucket=<YOUR_BUCKET_NAME>" \
  -backend-config="key=shopping-reminder/terraform.tfstate" \
  -backend-config="region=ap-northeast-1"

# 計画の確認
terraform plan

# リソースの作成
terraform apply
```

### 4. デプロイ後の確認

```bash
# 作成されたリソースの確認
terraform output

# Lambda実行テスト
aws lambda invoke --function-name shopping-reminder response.json

# リソースグループの確認
aws resource-groups list-groups
aws resource-groups get-group --group-name shopping-reminder-resources
```

## 変数一覧

| 変数名 | 説明 | デフォルト値 | 必須 |
|--------|------|-------------|------|
| `notion_api_key` | Notion API キー | - | Yes |
| `notion_database_id` | NotionデータベースID | - | Yes |
| `notion_page_id` | NotionページID | - | Yes |
| `lambda_function_name` | Lambda関数名 | `shopping-reminder` | No |
| `schedule_expression` | 実行スケジュール | `cron(0 8 * * ? *)` | No |
| `lambda_timeout` | タイムアウト（秒） | `30` | No |
| `lambda_memory_size` | メモリサイズ（MB） | `128` | No |
| `cloudwatch_log_retention_days` | ログ保持期間（日） | `14` | No |
| `resource_group_name` | リソースグループ名 | `shopping-reminder-resources` | No |
| `environment` | 環境名 | `production` | No |
| `create_comprehensive_resource_group` | 包括的リソースグループの作成 | `false` | No |

## セキュリティ考慮事項

- Notion API キーは`sensitive = true`で保護されています
- IAM ロールは最小権限の原則に従い、必要な権限のみを付与
- CloudWatch Logsのみアクセス可能

## AWS Resource Groups について

このTerraform設定では、作成されたAWSリソースを効率的に管理するためにResource Groupsを使用します。

### 作成されるリソースグループ

1. **メインリソースグループ** (`shopping-reminder-resources`)
   - Lambda、EventBridge、CloudWatch Logs、IAMロールを含む
   - プロジェクトタグでフィルタリング

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
