# デプロイメント・運用ガイド

## 🚀 AWSデプロイ

### GitHub Actions によるデプロイ

通常は GitHub Actions の CD（`.github/workflows/cd.yml`）でデプロイする。

| ブランチ | デプロイ先 | Terraform | GitHub の Environment | デプロイ後の確認 |
| --- | --- | --- | --- | --- |
| `develop` | dev 環境（`dev-shopping-reminder`） | `terraform/environments/dev` | `develop` | Lambda を `{"dry_run": true}` で呼び出す |
| `main` | 本番環境（`shopping-reminder`） | `terraform/environments/production` | `prod` | Lambda を `{"dry_run": true}` で呼び出す |

`{"dry_run": true}` で呼び出すと、Notion から未チェック項目を読み、通知API に `"dry_run": true` を付けて送る。dry run なので、通知は送信されない。未チェック項目がないときは、通知API を呼ばない。

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

Lambda には OTel の Python計装レイヤーと Collectorレイヤー（どちらも [opentelemetry-lambda](https://github.com/open-telemetry/opentelemetry-lambda) のコミュニティ製）をアタッチしている。アプリが送ったトレース・メトリクス・ログを Collector が受け取り、Grafana Cloud に OTLP で送る。

Lambda のランタイムの Python は、コミュニティの Python計装レイヤーを作った Python（今は 3.14）と同じバージョンにしている。違うとレイヤーの `.pyc` が使われず、コールドスタートのたびにコンパイルし直すので遅くなる。レイヤーを上げるときは、そのタグの `python/src/otel/Dockerfile` の Python のバージョンも確認する。

| テレメトリ | バックエンド | 確認方法 |
| --- | --- | --- |
| トレース | Grafana Cloud（Tempo） | Grafana の Explore（データソース: Tempo） |
| メトリクス | Grafana Cloud（Prometheus 互換） | Grafana の Explore（データソース: Prometheus） |
| ログ | Grafana Cloud（Loki） | Grafana の Explore（データソース: Loki）。`{service_name="shopping-reminder"}` で絞り込む |

- Collector の設定は `src/shopping_reminder/collector.yaml` にまとめており、デプロイ時に Lambda の zip に含まれる。
- zip には `opentelemetry` パッケージを含めず、Python計装レイヤーが提供する。計装レイヤーは `AWS_LAMBDA_EXEC_WRAPPER=/opt/otel-handler` でハンドラーをラップし、Lambda の呼び出しの span を作る。`urllib` のリクエスト（Notion API・通知API）の span と、`logging` のログの送信は、自前の計装のレイヤーが行う（下記）。
- 環境は、リソース属性 `deployment.environment.name`（と `deployment.environment`）の `dev`・`prod` で区別する。
- コールドスタートのときは、実行環境の初期化が `init <関数名>`（属性 `faas.coldstart=true`）という span になり、そのとき呼ばれた実行と同じトレースに入る（Collector の `telemetryapi` receiver と `coldstart` processor）。
- 計装が付ける属性のうち、URL（`http.url`・`url.full`。Notion のデータベース ID と通知先の API Gateway のホストを含む）、AWS のアカウント ID（`cloud.account.id`）、関数の ARN（`cloud.resource_id`）は、Collector で消してから送る（`attributes/redact`・`resource/redact`）。そのため、urllib のメトリクス（`http.client.duration` など）では Notion と通知API を区別できない。トレースでは親の span（`query_unchecked_items`・`send_notification`）で区別できる。
- ログは、アプリの `logging` のログを `opentelemetry-instrumentation-logging`（自前の計装のレイヤー）が OTel のログにして送る。この計装はルートロガーにハンドラーを付けるので、アプリのロガー（`logger.py` の `get_logger`）は自分ではハンドラーを持たず、ルートロガーに任せる。CloudWatch Logs には、Lambda のランタイムのハンドラーが今までどおり出す。ログにはそのときの span の `trace_id`・`span_id` が付くので、Grafana でトレースとログを行き来できる。
- Lambda の計装は、実行の終わりにトレースとメトリクスしか flush しない。ログは SDK がまとめて送るので、そのままでは応答を返したあとに実行環境が凍結され、次の呼び出しまで送られない（実行環境が止まると失われる）ことがある。そのため、`handler` の最後（例外のときも）でログを flush している（`lambda_handler.py` の `flush_logs`）。
- ログの本文には、トレースやメトリクスでは消している値が入る。Collector で次の値を `***` に置き換えてから送る（`transform/redact_log_body`）。CloudWatch Logs には元のまま出る。
  - ARN の中の AWS のアカウント ID と、EventBridge のイベントの `"account"`（`Event: ...` のログ）
  - 通知先の API Gateway のホスト（`Notify URL: ...` など）
  - Notion のデータベース ID（Lambda の環境変数 `NOTION_DATABASE_ID` と同じ文字列。Notion の URL のログにも入る）
  - Notion の API キー（`Request headers: ...` のログの `Bearer <値>` と、`ntn_`・`secret_` で始まるトークン）
- ほかはそのまま送るので、未チェック項目の名前と ID（`Unchecked item: ...`）も含まれる。

アプリが作る span とメトリクス：

| 種類 | 名前 | 内容 |
| --- | --- | --- |
| span | `process` | 処理全体。属性 `shopping_reminder.dry_run` |
| span | `query_unchecked_items` | Notion からの未チェック項目の取得。属性 `notion.page_count`・`notion.unchecked_items_count` |
| span | `send_notification` | 通知APIへの送信。属性 `notify.item_count`。失敗したときは span のステータスを ERROR にする |
| メトリクス（counter） | `shopping_reminder.notifications.sent` | 通知を送った回数 |
| メトリクス（histogram） | `shopping_reminder.items.unchecked` | 1回の実行での未チェック項目の数。属性 `dry_run` |

メトリクスは累積値（cumulative）で送る。1日1回の実行でほぼ毎回コールドスタートになり、カウンタは毎回 0 から数え直すため、Grafana では `increase()` ではなく、その日の値（例: `max_over_time(...[1d])`）で見る。本番の CD の dry run の実行も記録されるので、未チェック項目の数は属性 `dry_run` で絞り込む。

#### 自前の計装のレイヤー

コミュニティの Python計装レイヤーには、次の計装が入っていない。そのため、これらを入れたレイヤーを自前で作り、コミュニティのレイヤーに重ねている（`terraform/modules/shopping-reminder/main.tf` の `aws_lambda_layer_version.otel_instrumentations`）。

| 計装 | 無いと |
| --- | --- |
| `opentelemetry-instrumentation-urllib` | Notion API と通知API の呼び出しの span が出ず、通知API（nandemo-oshirase）へのリクエストに `traceparent` も付かないので、nandemo-oshirase と1つのトレースにならない |
| `opentelemetry-instrumentation-logging` | `logging` のログが OTel のログとして送られない |

- zip は `scripts/build-otel-instrumentations-layer.py` で作る（CI の terraform-plan と CD で、Terraform の前に実行する）。依存するパッケージはコミュニティのレイヤーにあるので、これらの計装だけを `--no-deps` で入れる。計装を足すときは、スクリプトの `PACKAGES` と `pyproject.toml` の両方に足す。同じバージョンなら zip のハッシュは変わらないので、レイヤーは作り直されない。
- バージョンは `uv.lock` のものを使う。`pyproject.toml` の OTel の依存は、本番と同じもの（コミュニティの Python計装レイヤーの `opentelemetry-distro`・`opentelemetry-exporter-otlp-proto-http`・`opentelemetry-instrumentation-aws-lambda` と、自前のレイヤーの `opentelemetry-instrumentation-urllib`・`opentelemetry-instrumentation-logging`）を、レイヤー（タグの `requirements.txt`）と同じバージョンに `==` で固定している（ローカルと本番のバージョンをそろえるため）。コードが使うのは `opentelemetry-api` だけで、zip には依存を含めない。Dependabot では OTel のパッケージを上げない（`.github/dependabot.yml` の `ignore`）。
- コミュニティのレイヤーの新しいバージョンは、`.github/workflows/update-otel-lambda-layers.yml` が見つけて、`terraform/modules/shopping-reminder/main.tf` の ARN と `pyproject.toml`・`uv.lock` の OTel の依存を一緒に上げる PR を develop に作る。opentelemetry-lambda のリリースは feed-release-invoke-workflow の `repository_dispatch`（`otel-lambda-release`）で知り、取りこぼしに備えて週1回の `schedule` でも確認する。

#### Grafana Cloud の認証情報

Grafana Cloud に送るための Authorization ヘッダーの値（`Basic <base64(スタックの ID:トークン)>`）は、環境ごとに SSM Parameter Store の SecureString に置かれている前提とする（パラメータはこのリポジトリでは作成・管理しない）。

| 環境 | パラメータ |
| --- | --- |
| dev | `/app/grafana/dev/otlp_auth` |
| prod | `/app/grafana/prod/otlp_auth` |

トークン（Access Policy）には、`traces:write`・`metrics:write`・`logs:write` の権限が要る。`logs:write` が無いと、ログの送信だけが 401/403 で失敗する。

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
