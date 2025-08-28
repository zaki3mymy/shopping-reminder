# 開発ガイド

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

# E2Eテスト（環境変数必須）
uv run pytest tests/shopping_reminder/test_e2e.py -v

# Lambdaハンドラーの動作確認
uv run python -c "
from src.shopping_reminder.lambda_handler import handler
result = handler({}, None)
print(result)
"
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

## 🤝 コントリビューション

1. フィーチャーブランチ作成
2. 変更内容の実装
3. テストの追加・実行
4. pre-commitフックの通過確認
5. プルリクエストの作成

詳細な開発ガイドラインは [CLAUDE.md](../CLAUDE.md) を参照してください。
