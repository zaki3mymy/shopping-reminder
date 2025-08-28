# 📝 Shopping Reminder

毎日17時（JST）にNotionの「日用品 買い物リスト」データベースをチェックし、未チェック項目があればコメントで通知するAWS Lambdaアプリケーション。

## 🚀 概要

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

## 🛠️ クイックスタート

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

```bash
export NOTION_API_KEY="secret_xxxxxxxxxxxx"
export NOTION_DATABASE_ID="database-id-here"
export NOTION_PAGE_ID="page-id-here"
```

### 3. 動作確認

```bash
# テスト実行
uv run pytest

# Lambdaハンドラーのテスト
uv run python -c "
from src.shopping_reminder.lambda_handler import handler
result = handler({}, None)
print(result)
"
```

## 📁 プロジェクト構造

```text
shopping-reminder/
├── src/shopping_reminder/    # メインアプリケーション
├── tests/shopping_reminder/  # テストコード
├── terraform/               # AWS インフラ設定
├── docs/                    # 詳細ドキュメント
├── pyproject.toml
├── .pre-commit-config.yaml
└── CLAUDE.md               # 開発ガイドライン
```

## 📋 要件

- **Python 3.13+** （.python-versionで指定）
- **AWS Lambda** 実行環境
- **Terraform >= 1.2.0**
- **uv** パッケージマネージャー

### Notion設定

監視対象のNotionデータベースには以下のプロパティが必要：

- `名前` (title): アイテム名
- `完了` (checkbox): チェック状態

## 📚 詳細ドキュメント

- [開発ガイド](docs/DEVELOPMENT.md) - テスト、コード品質、コントリビューション
- [デプロイメント・運用ガイド](docs/DEPLOYMENT.md) - AWSデプロイ、監視、トラブルシューティング

## 📄 ライセンス

このプロジェクトはMITライセンスの下で公開されています。
