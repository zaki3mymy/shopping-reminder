# GitHub Workflow Guide

このドキュメントでは、Claude CodeとGitHubを組み合わせたプロジェクト開発のワークフローについて説明します。

## 概要

Claude CodeとGitHub CLIを活用することで、Issue管理からプルリクエスト作成・レビュー対応まで、効率的な開発フローを実現できます。

## 基本ワークフロー

### 1. Issue確認・選択

```bash
# オープンなIssueを一覧表示
gh issue list --state open

# 特定のIssueの詳細を確認
gh issue view <issue_number>
```

**実例**：
```bash
$ gh issue list --state open
1  OPEN  terraformのモジュール構成を整理する   2025-08-23T16:52:14Z

$ gh issue view 1
title: terraformのモジュール構成を整理する
author: zaki3mymy
assignees: zaki3mymy
...
```

### 2. 作業ブランチ作成

Issue対応用のフィーチャーブランチを作成：

```bash
git switch -c feature/<issue-description>
# 例: git switch -c feature/terraform-module-restructure
```

### 3. 実装・コミット

- **Todo管理**: Claude Codeの`TodoWrite`ツールでタスクを追跡
- **品質保証**: pre-commitフックによる自動チェック
- **段階的コミット**: 機能単位での細かいコミット

**コミットメッセージ例**：
```
Refactor terraform configuration to use modules

- Restructure terraform files following best practices
- Create modules/shopping-reminder/ for reusable infrastructure components
- Add environments/production/ for environment-specific configurations

This addresses Issue #1 for better terraform module organization.

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

### 4. プルリクエスト作成

```bash
# ブランチをプッシュ
git push -u origin feature/<branch-name>

# プルリクエスト作成
gh pr create --title "<title>" --body "<body>"
```

**プルリクエスト本文テンプレート**：
```markdown
## Summary
- 変更内容の概要
- 実装した機能や修正内容

## Test plan
- [x] pre-commitフックが通る
- [x] 全テストが成功
- [x] 機能が正しく動作する

Issue #<number>を解決します。

🤖 Generated with [Claude Code](https://claude.ai/code)
```

## レビュー対応フロー

### 1. レビューコメント取得

```bash
gh api \
  repos/{owner}/{repo}/pulls/{pull_number}/comments \
  --paginate \
  --jq '.[] | {id: .id, user: .user.login, path: .path, position: .position, body: .body}'
```

### 2. コメント対応・修正

各レビューコメントに対して：
1. 指摘内容を確認
2. 修正実装
3. コミット作成（1つのコメントにつき1コミット推奨）

### 3. レビューコメント返信

修正完了後、コミットハッシュを含めて返信：

```bash
gh api repos/{owner}/{repo}/pulls/{pr_number}/comments/{comment_id}/replies \
  -X POST \
  -f body="修正完了しました。

<修正内容の説明>
コミット: <commit_hash>"
```

## 実際の作業例

### Issue #1対応の流れ

1. **Issue確認**
   ```bash
   gh issue list --state open
   gh issue view 1  # "terraformのモジュール構成を整理する"
   ```

2. **ブランチ作成・実装**
   ```bash
   git switch -c feature/terraform-module-restructure
   # Terraformファイルのリファクタリング実装
   ```

3. **プルリクエスト作成**
   ```bash
   git push -u origin feature/terraform-module-restructure
   gh pr create --title "Refactor terraform configuration to use modules" --body "..."
   ```

4. **レビュー対応**
   - コメント1: `.claude/settings.local.json`を`.gitignore`に追加
   - コメント2: `terraform/README.md`から不要な変数を削除

   それぞれ個別にコミット・返信

5. **マージ完了**

## ベストプラクティス

### コミット管理
- **原子性**: 1コミット1つの変更
- **メッセージ**: 明確で詳細な説明
- **Claude Code署名**: 自動生成であることを明示

### レビュー対応
- **迅速対応**: コメント受信後速やかに対応
- **明確な返信**: コミットハッシュ付きで修正完了を報告
- **段階的修正**: 1コメント1コミットで対応状況を明確化

### 品質保証
- **pre-commit**: 自動品質チェック
- **テスト**: 全テストの実行確認
- **ドキュメント**: 変更に応じたドキュメント更新

## GitHub CLI便利コマンド

```bash
# Issue操作
gh issue list                    # Issue一覧
gh issue view <number>           # Issue詳細
gh issue create                  # Issue作成

# PR操作
gh pr list                       # PR一覧
gh pr view <number>              # PR詳細
gh pr create                     # PR作成
gh pr merge <number>             # PRマージ

# API呼び出し
gh api repos/{owner}/{repo}/pulls/{pr}/comments    # レビューコメント取得
gh api repos/{owner}/{repo}/pulls/comments/{id}/replies -X POST -f body="..."  # 返信
```

## Claude Code特有の機能

### TodoWriteツール
プロジェクトの進捗管理に活用：
```
1. GitHub Issueを確認 ✅
2. 対応するIssueを選択 ✅
3. 作業用ブランチを作成 ✅
4. Issue対応の実装 ✅
5. テスト実行と品質チェック ✅
6. プルリクエストの作成 ✅
```

### 自動品質チェック
- ruff (linting)
- mypy (type checking)
- pytest (testing)
- pre-commit hooks

### セキュリティ
- 機密情報の自動検出・除外
- `.gitignore`の適切な管理
- sensitive変数の保護

## まとめ

このワークフローにより：
- **効率的**: Issue→ブランチ→PR→マージの流れが自動化
- **高品質**: pre-commitとテストによる品質保証
- **透明性**: 全過程がGitHub上で追跡可能
- **協働**: レビュー・コメント機能による効果的なコラボレーション

Claude CodeとGitHubを組み合わせることで、プロ品質の開発プロセスを維持しながら、迅速な開発が可能になります。
