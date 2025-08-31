# Terraform Infrastructure

このディレクトリには、Shopping Reminder アプリケーション用のTerraformインフラストラクチャコードが含まれています。

## 構成

```
terraform/
├── modules/
│   └── shopping-reminder/    # メインアプリケーションモジュール
│       ├── main.tf          # リソース定義
│       ├── variables.tf     # 変数定義
│       ├── outputs.tf       # 出力値定義
│       └── README.md        # モジュール詳細ドキュメント
├── environments/
│   └── production/          # 本番環境設定
│       ├── main.tf          # モジュール使用
│       ├── variables.tf     # 環境変数定義
│       ├── outputs.tf       # 出力値
│       ├── providers.tf     # プロバイダー設定
│       ├── versions.tf      # Terraform/プロバイダーバージョン
│       ├── terraform.tfvars # 環境固有の値
│       └── README.md        # 環境別デプロイ手順
└── README.md               # このファイル（概要）
```

## 概要

以下のAWSリソースを作成します：

- **AWS Lambda**: 日用品チェッカーアプリケーション
- **EventBridge**: 毎日17:00（JST）にLambdaを実行するスケジュール
- **CloudWatch Logs**: Lambda実行ログの保存
- **IAM Role**: Lambda実行に必要な最小限の権限
- **Resource Groups**: AWS リソースの管理・監視を簡素化

## ドキュメント

各コンポーネントの詳細なドキュメントは以下を参照してください：

- **[モジュール詳細](./modules/shopping-reminder/README.md)**: リソース仕様、変数、出力値
- **[本番環境デプロイ](./environments/production/README.md)**: デプロイ手順、設定方法

## ドキュメント生成

各コンポーネントのドキュメントはterraform-docsで自動生成されます：

```bash
# モジュール詳細ドキュメント生成
terraform-docs --config=terraform/modules/shopping-reminder/.terraform-docs.yml terraform/modules/shopping-reminder/

# 本番環境ドキュメント生成
terraform-docs --config=terraform/environments/production/.terraform-docs.yml terraform/environments/production/
```

## セキュリティ考慮事項

- Notion API キーは`sensitive = true`で保護されています
- IAM ロールは最小権限の原則に従い、必要な権限のみを付与
- CloudWatch Logsのみアクセス可能

## AWS Resource Groups について

このTerraform設定では、作成されたAWSリソースを効率的に管理するためにResource Groupsを使用します。

### 作成されるリソースグループ

1. **メインリソースグループ** (`shopping-reminder-resources`)
   - Lambda、EventBridge、CloudWatch Logsを含む
   - プロジェクトタグでフィルタリング
   - 注意: IAMロールはResource Groupsでサポートされていないため除外

2. **包括的リソースグループ** (`shopping-reminder-resources-all`) - オプション
   - プロジェクトに関連する全てのAWSリソースを含む
   - `create_comprehensive_resource_group = true` で有効化

### リソースグループの利点

- **一元管理**: 関連リソースをグループ化して管理
- **監視の簡素化**: CloudWatchでグループ単位での監視
- **コスト分析**: 請求情報をプロジェクト単位で分析
- **権限管理**: リソースグループに対する一括操作

### 使用方法

```bash
# リソースグループ一覧表示
aws resource-groups list-groups

# 特定グループの詳細確認
aws resource-groups get-group --group-name shopping-reminder-resources

# グループ内のリソース一覧
aws resource-groups list-group-resources --group-name shopping-reminder-resources

# AWS コンソールでの確認
# https://console.aws.amazon.com/resource-groups/
```

## トラブルシューティング

### Lambda実行エラー

CloudWatch Logsでエラーを確認：

```bash
aws logs tail /aws/lambda/shopping-reminder --follow
```

### 権限エラー

IAMロールの権限を確認し、必要に応じて追加：

```bash
aws iam get-role --role-name shopping-reminder-role
```

### リソースグループが空の場合

タグが正しく設定されているか確認：

```bash
# リソースのタグ確認
aws lambda get-function --function-name shopping-reminder --query 'Tags'
```

## リソース削除

```bash
terraform destroy
```

## ベストプラクティス準拠

このTerraform設定はGoogleのベストプラクティスに準拠しています：

- 型指定された変数とデフォルト値
- 明確な説明文
- 適切なファイル分割
- タグ付けの一貫性
- アウトプットの提供
- S3バックエンドによるステート管理
- バージョン固定されたプロバイダー

## 開発ワークフロー

pre-commitフックが設定されており、以下が自動実行されます：

- Terraformファイルの自動フォーマット (`terraform fmt`)
- Terraformファイルの構文検証 (`terraform validate`)
- AWS認証情報の漏洩チェック
- Pythonコードのlintとtype check
- 単体テストの実行（pre-merge-commit時）
