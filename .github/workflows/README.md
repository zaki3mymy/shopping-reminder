# GitHub Actions Workflows

このディレクトリにはShopping Reminderプロジェクトのための CI/CDワークフローが含まれています。

ブランチは `develop`（開発用、デフォルトブランチ）と `main`（リリース用）に分かれています。開発用の PR は develop にスカッシュマージし、develop から main へのリリース PR はマージコミットでマージします。

## ワークフロー概要

### CI (Continuous Integration) - `ci.yml`

**トリガー**:
- `develop` / `main` へのプルリクエスト
- CD（`cd.yml`）からの呼び出し

**ジョブ**:
1. **lint-and-format**: ruffによるコードリント・フォーマットチェック
2. **type-check**: mypyによる型チェック
3. **test**: pytestによるテスト実行（カバレッジレポートをGitHub artifactsに保存）
4. **terraform-validate**: Terraformファイルの検証
5. **terraform-plan**: PR の向き先の環境（develop: dev、main: 本番）に対する plan（PR のときだけ）

### CD (Continuous Deployment) - `cd.yml`

**トリガー**:
- `develop` / `main` へのpush（自動デプロイ）
- 手動実行（workflow_dispatch）

**ジョブ**:
1. **ci**: `ci.yml` を呼び出す
2. **deploy**: AWSへの自動デプロイ（develop: dev 環境、main: 本番環境）
   - Terraformによるインフラ構築・更新
   - Lambda関数の動作確認（dev は通常どおり、本番は `{"dry_run": true}` で通知を送らない）
3. **tag**: 本番（main）のデプロイが成功したら、次のバージョンのタグを打つ（[zaki3mymy/actions](https://github.com/zaki3mymy/actions) の `next-tag.yml`）
4. **release**: タグから GitHub リリースを作る（zaki3mymy/actions の `create-release.yml`）

### リリース - `release.yml`

`v*.*.*` のタグを手で push したときに、GitHub リリースを作ります（zaki3mymy/actions の `create-release.yml`）。CD がタグを打ったときは `GITHUB_TOKEN` で push するので、このワークフローは動きません（CD の `release` ジョブが作ります）。

### PR のタイトルからラベルを付ける - `label-pr-by-title.yml`

PR のタイトル（Conventional Commits）から、種類に応じたラベルを付けます（zaki3mymy/actions の `label-pr-by-title.yml`）。タイトルの形が違うときは失敗します。

| タイトル | ラベル |
|---|---|
| `feat!:` など `!` 付き | `breaking`（メジャーを上げる） |
| `feat:` | `feat`（マイナーを上げる） |
| `fix:` | `fix` |
| `release:` | `skip-release-notes`（リリースノートに載せない） |

## リリース（タグと GitHub リリース）

- 本番にデプロイしたものに、SemVer のタグ（`vX.Y.Z`）を打ち、GitHub リリースを作ります。
- 次のバージョンは、前のタグからの PR のラベルで決めます（`breaking`: メジャー、`feat`: マイナー、それ以外: パッチ）。
- リリースノートは GitHub の自動生成で、PR のラベルごとの見出しに振り分けます（`.github/release.yml`）。
- develop から main へのリリース PR は `release: ...` のタイトルにします。

## 必要なSecrets設定

Secrets と Environment（`develop` / `prod`）は、[zaki3mymy/github](https://github.com/zaki3mymy/github) の Terraform で管理しています。CD と CI の terraform-plan は、ジョブの `environment` で次の Secrets を参照します。

- `AWS_ROLE_ARN`: OIDC認証用のAWS IAMロールARN
- `TERRAFORM_STATE_BUCKET`: Terraformステートファイル保存用S3バケット名
- `NOTION_API_KEY`: Notion APIキー
- `NOTION_DATABASE_ID`: 監視対象NotionデータベースID
- `NOTIFY_API_KEY`: なんでもお知らせくん API のキー
- `NOTIFY_API_URL`: なんでもお知らせくん API のベースURL

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
