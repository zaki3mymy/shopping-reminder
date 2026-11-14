# デプロイメント・運用ガイド

## 🚀 AWSデプロイ

### GitHub Actions によるデプロイ

通常は GitHub Actions の CD（`.github/workflows/cd.yml`）でデプロイする。

| ブランチ | デプロイ先 | Terraform | GitHub の Environment | デプロイ後の確認 |
| --- | --- | --- | --- | --- |
| `develop` | dev 環境（`dev-shopping-reminder`） | `terraform/environments/dev` | `develop` | Lambda を呼び出し、通知の送信まで確認する |
| `main` | 本番環境（`shopping-reminder`） | `terraform/environments/production` | `prod` | Lambda を `{"dry_run": true}` で呼び出す（通知は送信しない） |

dev 環境では EventBridge の定期実行を無効にしており、テスト用の Notion データベースを使う。

### 手動でのデプロイ

#### 前提条件

- AWS CLI設定済み
- Terraform >= 1.2.0 インストール済み
- S3バケット作成済み（tfstateファイル用）

#### デプロイ手順

```bash
# Terraform環境初期化（本番環境）
cd terraform/environments/production
terraform init \
  -backend-config="bucket=<YOUR_BUCKET_NAME>" \
  -backend-config="key=shopping-reminder/terraform.tfstate" \
  -backend-config="region=ap-northeast-1"

# terraform.tfvarsファイルを作成
cat <<EOF > terraform.tfvars
notion_api_key     = "secret_xxxxxxxxxxxx"
notion_database_id = "database-id-here"
notion_page_id     = "page-id-here"
EOF

# デプロイ実行
terraform plan -var-file terraform.tfvars
terraform apply -var-file terraform.tfvars
```

詳細は [terraform/README.md](../terraform/README.md) を参照

#### 必要な設定値

以下の値をterraform.tfvarsファイルに設定してください：

- `notion_api_key`: Notion API キー
- `notion_database_id`: 監視対象のデータベースID
- `notion_page_id`: コメント投稿先のページID

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

### OTel テレメトリ（Grafana Cloud）

Lambda には OTel の Python計装レイヤーと Collectorレイヤー（どちらも [opentelemetry-lambda](https://github.com/open-telemetry/opentelemetry-lambda) のコミュニティ製）をアタッチしている。アプリが送ったトレース・メトリクスを Collector が受け取り、Grafana Cloud に OTLP で送る。

| テレメトリ | バックエンド | 確認方法 |
| --- | --- | --- |
| トレース | Grafana Cloud（Tempo） | Grafana の Explore（データソース: Tempo） |
| メトリクス | Grafana Cloud（Prometheus 互換） | Grafana の Explore（データソース: Prometheus） |

- Collector の設定は `src/shopping_reminder/collector.yaml` にまとめており、デプロイ時に Lambda の zip に含まれる。
- zip には `opentelemetry` パッケージを含めず、Python計装レイヤーが提供する。計装レイヤーは `AWS_LAMBDA_EXEC_WRAPPER=/opt/otel-handler` でハンドラーをラップし、Lambda の呼び出しと `urllib` のリクエスト（Notion API・通知API）の span を作る。
- 環境は、リソース属性 `deployment.environment.name`（と `deployment.environment`）の `dev`・`prod` で区別する。
- コールドスタートのときは、実行環境の初期化が `init <関数名>`（属性 `faas.coldstart=true`）という span になり、そのとき呼ばれた実行と同じトレースに入る（Collector の `telemetryapi` receiver と `coldstart` processor）。
- 計装が付ける属性のうち、URL（`http.url`・`url.full`。Notion のデータベース ID と通知先の API Gateway のホストを含む）、AWS のアカウント ID（`cloud.account.id`）、関数の ARN（`cloud.resource_id`）は、Collector で消してから送る（`attributes/redact`・`resource/redact`）。そのため、urllib のメトリクス（`http.client.duration` など）では Notion と通知API を区別できない。トレースでは親の span（`query_unchecked_items`・`send_notification`）で区別できる。

アプリが作る span とメトリクス：

| 種類 | 名前 | 内容 |
| --- | --- | --- |
| span | `process` | 処理全体。属性 `shopping_reminder.dry_run` |
| span | `query_unchecked_items` | Notion からの未チェック項目の取得。属性 `notion.page_count`・`notion.unchecked_items_count` |
| span | `send_notification` | 通知APIへの送信。属性 `notify.item_count`。失敗したときは span のステータスを ERROR にする |
| メトリクス（counter） | `shopping_reminder.notifications.sent` | 通知を送った回数 |
| メトリクス（histogram） | `shopping_reminder.items.unchecked` | 1回の実行での未チェック項目の数。属性 `dry_run` |

メトリクスは累積値（cumulative）で送る。1日1回の実行でほぼ毎回コールドスタートになり、カウンタは毎回 0 から数え直すため、Grafana では `increase()` ではなく、その日の値（例: `max_over_time(...[1d])`）で見る。本番の CD の dry run の実行も記録されるので、未チェック項目の数は属性 `dry_run` で絞り込む。

#### Grafana Cloud の認証情報

Grafana Cloud に送るための Authorization ヘッダーの値（`Basic <base64(スタックの ID:トークン)>`）は、環境ごとに SSM Parameter Store の SecureString に置かれている前提とする（パラメータはこのリポジトリでは作成・管理しない）。

| 環境 | パラメータ |
| --- | --- |
| dev | `/app/grafana/dev/otlp_auth` |
| prod | `/app/grafana/prod/otlp_auth` |

Collector レイヤーは SSM Parameter Store を読めないため、Terraform がこのパラメータを読み、Lambda の環境変数 `GRAFANA_CLOUD_OTLP_AUTH` に渡す。そのため、**この値は Terraform の state と Lambda の環境変数に残る**。送信先（`GRAFANA_CLOUD_OTLP_ENDPOINT`）は秘密ではないので、モジュールの変数 `grafana_otlp_endpoint` の既定値に書いている。値は、Grafana Cloud のスタックの OTLP の URL に `/otlp` を付けたもの。

パラメータの値が変わったとき（トークンを作り直したときなど）は、このリポジトリでもう一度 apply すると、Lambda の環境変数が新しい値に変わる。

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

## 🔒 セキュリティ考慮事項

- Notion API Keyは環境変数で管理
- AWS IAMロールは最小権限の原則で設定
- git secretsによる認証情報漏洩チェック
- Terraformでsensitive変数を適切に管理
