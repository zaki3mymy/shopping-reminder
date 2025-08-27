# GitHub Actions Workflows

このディレクトリにはShopping Reminderプロジェクトのための CI/CDワークフローが含まれています。

## ワークフロー概要

### CI (Continuous Integration) - `ci.yml`

**トリガー**:
- `main`ブランチへのpush
- `main`ブランチへのプルリクエスト

**ジョブ**:
1. **lint-and-format**: ruffによるコードリント・フォーマットチェック
2. **type-check**: mypyによる型チェック
3. **test**: pytestによるテスト実行（カバレッジレポートをGitHub artifactsに保存）
4. **terraform-validate**: Terraformファイルの検証

**所要時間**: 約3-5分

### CD (Continuous Deployment) - `cd.yml`

**トリガー**:
- `main`ブランチへのpush（自動デプロイ）
- 手動実行（workflow_dispatch）

**ジョブ**:
1. **deploy**: AWSへの自動デプロイ
   - テスト実行
   - Terraformによるインフラ構築・更新
   - Lambda関数のデプロイメント検証

**所要時間**: 約5-10分

## 必要なSecrets設定

GitHub リポジトリの Settings > Secrets and variables > Actions で以下を設定：

### AWS認証
- `AWS_ROLE_ARN`: OIDC認証用のAWS IAMロールARN

### Terraform
- `TERRAFORM_STATE_BUCKET`: Terraformステートファイル保存用S3バケット名

### Notion API
- `NOTION_API_KEY`: Notion APIキー
- `NOTION_DATABASE_ID`: 監視対象NotionデータベースID
- `NOTION_PAGE_ID`: コメント投稿先NotionページID


## Environment設定

GitHub リポジトリの Settings > Environments で `production` environment を作成し、必要に応じて保護ルール（レビュー必須等）を設定。

## ローカル開発での活用

CIで実行されるチェックをローカルで事前確認：

```bash
# リント・フォーマットチェック
uv run ruff check
uv run ruff format --check

# 型チェック
uv run mypy src/

# テスト実行
uv run pytest --cov-report=term

# Terraform検証
terraform fmt -check -recursive terraform/
cd terraform/environments/production
terraform init -backend=false
terraform validate
```

## 品質ゲート

**CI通過条件**:
- 全てのlintチェックが通る
- 型チェックエラーがない
- 全てのテストが成功
- Terraformファイルが有効

**CD実行条件**:
- CIが成功
- テストが全て成功
- AWSクレデンシャルが有効

## トラブルシューティング

### CIが失敗する場合
1. Actions タブでログを確認
2. 該当するチェックをローカルで再現
3. 修正・コミット・プッシュで再実行

### CDが失敗する場合
1. AWS認証情報を確認
2. Terraformステートバケットのアクセス権限を確認
3. Notion APIキーの有効性を確認

### デバッグ用コマンド

```bash
# GitHub CLI でワークフロー状況確認
gh workflow list
gh run list --workflow=ci.yml
gh run view <run-id>

# AWS CLIでデプロイ状況確認
aws lambda get-function --function-name shopping-reminder
aws logs tail /aws/lambda/shopping-reminder --follow
```

## セキュリティ考慮事項

- 全てのAPIキー・認証情報はSecretsで管理
- Environment保護により本番デプロイを制限
- 最小権限の原則でIAMロールを設定
- Terraformステートファイルは暗号化されたS3バケットで管理

## バッジ設定

README.mdに以下のバッジを追加可能：

```markdown
[![CI](https://github.com/zaki3mymy/shopping-reminder/workflows/CI/badge.svg)](https://github.com/zaki3mymy/shopping-reminder/actions)
```

## カバレッジレポートの確認

テスト実行後、カバレッジレポートはGitHub ActionsのArtifactsに保存されます：

1. GitHub Actions > CI実行結果 > Artifacts
2. `coverage-report` をダウンロード
3. `index.html` をブラウザで開いて詳細な カバレッジ情報を確認
