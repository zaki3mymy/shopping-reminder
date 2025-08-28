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

## GitHub開発ワークフロー

### Issue対応フロー

1. `gh issue list --state open` - オープンなIssueを確認
2. `gh issue view <number>` - Issue詳細を確認・選択
3. `git switch main && git pull origin main` - 最新のmainブランチに切り替え
4. `git switch -c feature/<description>` - 作業用ブランチ作成（mainブランチから必ず作成）
5. TodoWriteツールでタスク管理・進捗追跡
6. 実装・テスト・品質チェック（ruff、mypy、pytest全て通すこと）
7. 段階的コミット（機能単位での細かいコミット）
8. `git push -u origin <branch>` でプッシュ
9. `gh pr create --title "..." --body "..."` でプルリクエスト作成

### プルリクエストタイトル規則

[Conventional Commits](https://www.conventionalcommits.org/ja/v1.0.0/)に従う：

```
<type>[optional scope]: <description>

例:
feat: terraformのモジュール構成を整理
fix: Notion API接続エラーを修正
docs: README更新とワークフロー追加
refactor: lambda handler構造を改善
test: E2Eテストケースを追加
chore: 依存関係を更新
```

**主要なtype**:

- `feat`: 新機能
- `fix`: バグ修正
- `docs`: ドキュメント変更
- `style`: コードスタイル変更（動作に影響しない）
- `refactor`: リファクタリング
- `test`: テスト追加・修正
- `chore`: ビルド・補助ツール変更

### プルリクエスト本文テンプレート

```markdown
## Summary
- 変更内容の概要・実装した機能

## Test plan
- [x] pre-commitフックが全て通る
- [x] 全テストが成功
- [x] 機能が正しく動作

Issue #<number>を解決します。

🤖 Generated with [Claude Code](https://claude.ai/code)
```

### レビュー対応フロー

1. `get-review-threads.sh <owner> <repo> <pull_number>` - レビューコメントスレッドを取得
2. 各コメント個別に修正実装（1コメント1コミット厳守）
3. `gh api repos/{owner}/{repo}/pulls/{pr}/comments/{comment_id}/replies -X POST -f body="修正完了しました。\n\n<修正内容>\nコミット: <hash>"` - 返信でコミットハッシュ含めて報告

#### レビューコメント取得方法

**専用スクリプト使用（推奨）**:
```bash
get-review-threads.sh zaki3mymy shopping-reminder 5
```
- 未解決のレビュースレッドのみを表示
- `databaseId`フィールドでコメント返信に必要なIDを取得
- 構造化されたJSON形式で出力

**従来のAPI呼び出し**:
```bash
gh api repos/{owner}/{repo}/pulls/{pr}/comments --paginate --jq '.[] | {id: .id, user: .user.login, path: .path, body: .body}'
```
- 全コメントを表示（解決済みを含む）
- 返信コメントも混在するため絞り込みが必要

### コミットメッセージ形式

```
<Type>: <Summary>

- 変更内容の詳細
- 実装・修正内容

<Issue言及がある場合>
This addresses Issue #<number> for <description>.

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

### 品質保証要件

- pre-commitフック全通過必須
- テストカバレッジ維持（目標100%）
- リント・型チェックエラーなし
- レビューコメント対応完了まで確実に実施
