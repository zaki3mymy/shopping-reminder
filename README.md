# 📝 Shopping Reminder

毎日17時（JST）にNotionの「日用品 買い物リスト」データベースをチェックし、未チェック項目があればコメントで通知するAWS Lambdaアプリケーション。

## 🚀 概要

このアプリケーションの動作フロー：

- **監視**: Notionデータベースの未チェック項目を取得
- **スケジュール**: EventBridgeが毎日17:00（JST）に実行
- **通知**: 未チェック項目があればNotionページにコメントで通知
- **ログ出力**: AWS Lambdaで処理結果を記録

## 🏗️ システム構成

```text
EventBridge (Schedule) → AWS Lambda → Notion API
                           ↓
                    CloudWatch Logs
```

## 🛠️ セットアップ

### 1. 環境構築

```bash
# リポジトリをクローン
git clone <repository-url>
cd shopping-reminder

# Python依存関係をインストール（uv使用）
uv sync --dev

# pre-commitフックをインストール
uv run pre-commit install --install-hooks
```

### 2. 環境変数設定

以下の環境変数を設定してください：

```bash
export NOTION_API_KEY="secret_xxxxxxxxxxxx"
export NOTION_DATABASE_ID="database-id-here"
export NOTION_PAGE_ID="page-id-here"
```

### 3. テスト実行

```bash
# 全テストを実行
uv run pytest

# カバレッジ付きテスト
uv run pytest --cov src --cov-branch --cov-report term-missing

# E2Eテスト（環境変数必須）
uv run pytest tests/shopping_reminder/test_e2e.py -v

# Lambdaハンドラーの動作確認
uv run python -c "
from src.shopping_reminder.lambda_handler import handler
result = handler({}, None)
print(result)
"
```

### 4. AWSデプロイ

```bash
# Terraform環境初期化（本番環境）
cd terraform/environments/production
terraform init \
  -backend-config="bucket=<YOUR_BUCKET_NAME>" \
  -backend-config="key=shopping-reminder/production/terraform.tfstate" \
  -backend-config="region=ap-northeast-1"

# 設定ファイル terraform.tfvars を作成
terraform plan
terraform apply
```

詳細は [terraform/README.md](terraform/README.md) を参照

## 📁 プロジェクト構造

```text
shopping-reminder/
├── src/shopping_reminder/          # メインアプリケーション
│   ├── models.py                   # データモデル
│   ├── config.py                   # 設定管理
│   ├── logger.py                   # ロギング機能
│   ├── notion_client.py           # Notion API クライアント
│   └── lambda_handler.py          # Lambda エントリーポイント
├── tests/shopping_reminder/        # テストコード
│   ├── test_models.py             # モデルテスト
│   ├── test_config.py             # 設定テスト
│   ├── test_notion_client.py      # API クライアントテスト
│   ├── test_lambda_handler.py     # Lambda テスト
│   └── test_e2e.py               # E2Eテスト
├── terraform/                     # AWS インフラ設定
│   ├── modules/
│   │   └── shopping-reminder/     # 再利用可能なモジュール
│   │       ├── main.tf            # Lambda・EventBridge・IAM設定
│   │       ├── variables.tf       # 変数定義
│   │       └── outputs.tf         # 出力値定義
│   ├── environments/
│   │   └── production/            # 本番環境設定
│   │       ├── main.tf            # メイン設定（モジュール使用）
│   │       ├── variables.tf       # 環境固有変数
│   │       ├── outputs.tf         # 出力値定義
│   │       ├── providers.tf       # プロバイダー設定
│   │       └── versions.tf        # バージョン制約
│   ├── examples/
│   │   └── basic/                 # 基本利用例
│   └── versions.tf                # 共通バージョン制約
├── pyproject.toml                 # Python プロジェクト設定
├── .pre-commit-config.yaml        # pre-commitフック
└── CLAUDE.md                      # 開発ガイドライン
```

## 🧪 テスト

### テスト方針

- **TDD（Test-Driven Development）** によるアプローチ
- **100%テストカバレッジ** を目標
- **単体テスト**: モジュール単位のテスト
- **E2Eテスト**: 実際のNotion APIを使用した統合テスト

### テスト実行

```bash
# 全テスト実行
uv run pytest

# 特定のテストファイルを実行
uv run pytest tests/shopping_reminder/test_models.py -v

# カバレッジレポート生成
uv run pytest --cov src --cov-branch --cov-report html
```

### テストカバレッジ

現在のテストカバレッジ: **100%** (157/157行、22/22分岐)

## ⚙️ 開発ワークフロー

### コード品質

pre-commitフックにより以下が自動実行されます：

- **基本チェック**: 行末空白の削除、改行の統一
- **Pythonコード**: ruff（linter）とmypy（型チェック）
- **Terraformコード**: フォーマットと構文チェック
- **機密情報チェック**: AWS認証情報の漏洩防止
- **テスト実行**: 単体テスト実行（pre-merge-commitステージ）

### 開発コマンド

```bash
# 開発環境セットアップ
uv sync --dev
uv run pre-commit install --install-hooks

# コード品質チェック
uv run ruff check src/
uv run mypy src/

# フォーマット
uv run ruff format src/
terraform fmt -recursive terraform/

# テスト実行
uv run pytest --cov src --cov-branch --cov-report term-missing

# pre-commit 手動実行
uv run pre-commit run --all-files
```

## 📋 要件

### システム要件

- **Python 3.13+** （.python-versionで指定）
- **AWS Lambda** 実行環境
- **Terraform >= 1.2.0**
- **uv** パッケージマネージャー

### Notion設定

- **Notion API Key** （Integration作成）
- **データベースID** （監視対象のデータベース）
- **ページID** （コメント投稿先のページ）

#### データベース構造

監視対象のNotionデータベースには以下のプロパティが必要：

- `名前` (title): アイテム名
- `完了` (checkbox): チェック状態

## 🔒 セキュリティ考慮事項

- Notion API Keyは環境変数で管理
- AWS IAMロールは最小権限の原則で設定
- git secretsによる認証情報漏洩チェック
- Terraformでsensitive変数を適切に管理

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

## 📄 ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 🤝 コントリビューション

1. フィーチャーブランチ作成
2. 変更内容の実装
3. テストの追加・実行
4. pre-commitフックの通過確認
5. プルリクエストの作成

詳細な開発ガイドラインは [CLAUDE.md](CLAUDE.md) を参照してください。
