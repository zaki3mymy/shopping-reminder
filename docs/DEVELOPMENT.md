# 開発ガイド

## 開発環境

開発に使うツールは [flake.nix](../flake.nix) で管理する。

| ツール | 用途 |
| --- | --- |
| uv | Python と依存関係の管理 |
| pre-commit | コミット前のチェック。開発環境に入ると、フックが自動で入る（flake.nix の `shellHook`） |
| git-secrets | 認証情報のコミットのチェック（pre-commit） |
| tflint | Terraform の lint（pre-commit） |
| terraform-docs | Terraform のドキュメントの生成（pre-commit） |
| nodejs | Markdown の lint（`npx -y markdownlint-cli2`） |

次のものは flake に入れていないので、別に入れる。

- Python：uv が `.python-version` を見て入れる（CI の `setup-uv` と同じ）。ruff などの Python のツールは uv.lock で管理し、`uv run` で使う
- terraform：unfree で cache.nixos.org にビルド済みのものがなく、flake.lock を更新するたびにソースからのビルド（数分）がかかるため。CI では `hashicorp/setup-terraform` で入れる

[direnv](https://direnv.net/) を使うと、このディレクトリに入ったときに自動でツールが PATH に入る（[.envrc](../.envrc)）。direnv を使わないときは `nix develop` を実行する。

```shell
direnv allow   # または nix develop
```

- ツールのバージョンは、flake.lock の nixpkgs のコミット（`rev`）で決まる。nixpkgs のコミットを進めると、すべてのツールがまとめて新しくなる。
  - 更新は Dependabot が週に1回 PR を作る。手で上げるときは `nix flake update` を実行する。
  - 実際のバージョンは `nix develop -c uv --version` や `nix eval --inputs-from . --raw nixpkgs#uv.version` で確かめられる。
- uv のバージョンは `pyproject.toml` の `[tool.uv] required-version` の範囲のものを使う（CI も同じ範囲の uv を使う）。nixpkgs を進めて uv が範囲から外れたら、`required-version` と CI の uv を合わせて上げる。

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

# E2Eテスト（テスト用環境変数必須）
# 以下の環境変数が必要（本番用とは別のテスト用環境）：
# - NOTION_API_KEY_TEST: テスト用のNotion API キー
# - NOTION_DATABASE_ID_TEST: テスト用のデータベースID
# - NOTION_PAGE_ID_TEST: テスト用のページID
uv run pytest tests/shopping_reminder/test_e2e.py -v

# Lambdaハンドラーの動作確認
uv run python -c "
from src.shopping_reminder.lambda_handler import handler
result = handler({}, None)
print(result)
"
```

### テストカバレッジ

プロジェクトでは100%テストカバレッジを目標としています。

## ⚙️ 開発ワークフロー

### コード品質

pre-commitフックにより以下が自動実行されます：

- **基本チェック**: 行末空白の削除、改行の統一
- **Pythonコード**: ruff（linter）とmypy（型チェック）
- **Terraformコード**: フォーマットと構文チェック
- **機密情報チェック**: AWS認証情報の漏洩防止
- **テスト実行**: 単体テスト実行（マージのタイミングで実行）

### 開発コマンド

```bash
# 開発環境セットアップ（pre-commit のフックは開発環境に入ったときに自動で入る）
uv sync --dev

# コード品質チェック
uv run ruff check src/
uv run mypy src/

# フォーマット
uv run ruff format src/
terraform fmt -recursive terraform/

# テスト実行
uv run pytest --cov src --cov-branch --cov-report term-missing

# pre-commit 手動実行
pre-commit run --all-files
```

## 🤝 コントリビューション

1. フィーチャーブランチ作成
2. 変更内容の実装
3. テストの追加・実行
4. pre-commitフックの通過確認
5. プルリクエストの作成
6. レビュー完了後、マージ（管理者のみ）

詳細な開発ガイドラインは [CLAUDE.md](../CLAUDE.md) を参照してください。
