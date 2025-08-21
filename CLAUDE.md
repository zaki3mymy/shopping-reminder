# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクト概要

毎日17時にNotionの「日用品　買い物リスト」データベースをチェックし、未チェック項目があればコメントで通知するAWS Lambdaアプリケーション。

## 開発コマンド

### パッケージ管理

- `uv sync --dev` - 開発依存関係を含めて全依存関係をインストール
- `uv add <package>` - 新しい依存関係を追加
- `uv add --dev <package>` - 開発依存関係を追加

### コード品質

- `uv run ruff check` - コードのリント実行（行長100文字、ダブルクォート）
- `uv run ruff check --fix` - リント問題の自動修正
- `uv run ruff format` - コードフォーマット
- `uv run mypy` - 型チェック実行（未型付け定義もチェック）

### テスト実行

- `uv run pytest` - 全テストを実行
- `uv run pytest tests/shopping-reminder/test_specific.py` - 特定テストファイルを実行
- `uv run pytest -k "test_name"` - パターンマッチするテストを実行
- `uv run pytest tests/shopping-reminder/test_e2e.py` - E2Eテストを実行
- カバレッジレポートは自動でterm、XML、HTML形式で生成される

### pre-commitフック

- `uv run pre-commit install --install-hooks` - pre-commitフックをインストール
- `uv run pre-commit run --all-files` - 全ファイルに対してフックを手動実行
- フックにはリント、型チェック、末尾空白除去、AWS認証情報チェックが含まれる
- 単体テストはpre-merge-commitステージで実行される

## プロジェクト構造

- `src/shopping-reminder/` - メインアプリケーションコード
  - `lambda_handler.py` - Lambda関数のエントリーポイント
  - `notion_client.py` - Notion API操作クライアント
  - `models.py` - データモデル定義
  - `config.py` - 設定管理
- `tests/shopping-reminder/` - テストファイル
  - `test_e2e.py` - エンドツーエンドテスト
  - `fixtures/` - テスト用データ
- `terraform/` - AWSインフラ設定（Googleベストプラクティス準拠）
- Python パスは `src/` ディレクトリを含むよう設定済み
- Python 3.13+ を使用（.python-versionで指定）

## コードスタイル

- 行長: 100文字
- クォートスタイル: ダブルクォート
- インデント: スペース4文字
- importソート: ruffでfirst-partyパッケージを考慮して設定

## テスト設定

- pytestでカバレッジ有効化（デフォルト）
- src/ ディレクトリのブランチカバレッジレポート生成
- tests/ ディレクトリからテスト自動検出
- E2Eテスト用の環境変数: `NOTION_API_KEY_TEST`, `NOTION_DATABASE_ID_TEST`, `NOTION_PAGE_ID_TEST`

## 技術仕様

- **言語**: Python 3.13+、標準ライブラリのみ使用
- **AWSサービス**: Lambda、EventBridge（日本時間17時実行）
- **外部API**: Notion API（データベースクエリ、コメント作成）
- **開発手法**: TDD（テスト駆動開発）
- **カバレッジ**: 100%を目標

## 開発ワークフロー

1. 機能ブランチ作成: `git switch -c feature-x` または `git switch -c fix-x`
2. 開発環境構築: `uv sync --dev && uv run pre-commit install --install-hooks`
3. TDDサイクル: Red → Green → Refactor
4. 段階的コミット（細かい単位で実装・コミット）
5. 品質チェック: ruff、mypy、pytestが全て通ることを確認

## Markdownリント

Markdownファイル作成・編集時は以下を実行：
`npx -y markdownlint-cli2 --fix <filepath>`

## Terraform

- Googleベストプラクティスに準拠した構造
- `terraform fmt`, `terraform validate`, `terraform plan` で検証
