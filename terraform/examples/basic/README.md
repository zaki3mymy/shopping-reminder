# Basic Shopping Reminder Example

この例では基本的な日用品チェッカーのデプロイ方法を示します。

## 使用方法

1. `terraform.tfvars`ファイルを作成：

```hcl
notion_api_key     = "your_notion_api_key"
notion_database_id = "your_database_id"
notion_page_id     = "your_page_id"
```

2. Terraformを実行：

```bash
terraform init
terraform plan
terraform apply
```

3. 作成されたリソースを確認：

```bash
terraform output
```

## 注意事項

- この例では Lambda パッケージが `../../../dist/lambda_function.zip` に存在することを前提としています
- 実際の使用前に、Notion APIキーとリソースIDが正しく設定されていることを確認してください
