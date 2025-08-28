# デプロイメント・運用ガイド

## 🚀 AWSデプロイ

### 前提条件

- AWS CLI設定済み
- Terraform >= 1.2.0 インストール済み
- S3バケット作成済み（tfstateファイル用）

### デプロイ手順

```bash
# Terraform環境初期化（本番環境）
cd terraform/environments/production
terraform init \
  -backend-config="bucket=<YOUR_BUCKET_NAME>" \
  -backend-config="key=shopping-reminder/terraform.tfstate" \
  -backend-config="region=ap-northeast-1"

# 設定ファイル terraform.tfvars を作成
terraform plan
terraform apply
```

詳細は [terraform/README.md](../terraform/README.md) を参照

### 必要な環境変数

以下の環境変数を設定してください：

```bash
export NOTION_API_KEY="secret_xxxxxxxxxxxx"
export NOTION_DATABASE_ID="database-id-here"
export NOTION_PAGE_ID="page-id-here"
```

## 🔍 運用・監視

### CloudWatch Logs

Lambdaの実行ログは以下で確認：

```bash
# リアルタイム監視
aws logs tail /aws/lambda/shopping-reminder --follow

# エラーログの抽出
aws logs filter-log-events \
  --log-group-name /aws/lambda/shopping-reminder \
  --filter-pattern "ERROR"
```

### Lambda動作確認

```bash
# Lambda実行テスト
aws lambda invoke \
  --function-name shopping-reminder \
  --payload '{}' \
  response.json

# 実行結果確認
cat response.json
```

## 🐛 トラブルシューティング

### よくある問題

1. **Notion API エラー**
   - API Keyの有効性確認
   - データベース・ページのアクセス権限確認

2. **Lambda 実行エラー**
   - CloudWatch Logsでエラー詳細確認
   - Lambda設定の確認（タイムアウト、メモリ等）

3. **テスト失敗**
   - 必要な環境変数のE2Eテスト用設定
   - Notion API接続確認

## 🔒 セキュリティ考慮事項

- Notion API Keyは環境変数で管理
- AWS IAMロールは最小権限の原則で設定
- git secretsによる認証情報漏洩チェック
- Terraformでsensitive変数を適切に管理
