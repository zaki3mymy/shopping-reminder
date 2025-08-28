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

# terraform.tfvarsファイルを作成
cat <<EOF > terraform.tfvars
notion_api_key     = "secret_xxxxxxxxxxxx"
notion_database_id = "database-id-here"
notion_page_id     = "page-id-here"
EOF

# デプロイ実行
terraform plan -var-file terraform.tfvars
terraform apply -var-file terraform.tfvars
```

詳細は [terraform/README.md](../terraform/README.md) を参照

### 必要な設定値

以下の値をterraform.tfvarsファイルに設定してください：

- `notion_api_key`: Notion API キー
- `notion_database_id`: 監視対象のデータベースID
- `notion_page_id`: コメント投稿先のページID

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
