# データベース設計書

## 概要

Issue #22対応のための複数データベース・ページサポート機能のデータベース設計書

## 使用するAWSサービス

### Amazon DynamoDB

**選択理由:**
- サーバーレスアーキテクチャとの親和性
- 自動スケーリング対応
- 使用量ベース課金でコスト効率的
- Lambda関数との低レイテンシ連携
- IAM統合による権限管理

## テーブル設計

### database_configurations テーブル

**概要:** 複数のNotionデータベース・ページの設定を管理

**テーブル構造:**
```
テーブル名: database_configurations
パーティションキー (PK): config_id (String) - UUID
ソートキー (SK): なし (単一アイテムテーブル)
```

**属性 (Attributes):**
- `config_id` (String, PK): 設定の一意識別子 (UUID v4)
- `config_name` (String): 設定の表示名 (例: "買い物リスト", "掃除用品")  
- `notion_database_id` (String): NotionデータベースID
- `notion_page_id` (String): 通知先NotionページID
- `is_active` (Boolean): この設定が有効かどうか
- `description` (String, Optional): 設定の説明

**Global Secondary Index (GSI):**
```
GSI名: active_configs_index
パーティションキー: is_active (Boolean)
ソートキー: config_name (String)

用途: アクティブな設定を名前順で取得
```

## データアクセスパターン

### 主要クエリ
1. **アクティブ設定一覧取得**
   - GSI: `active_configs_index`
   - 条件: `is_active = true`
   - ソート: `config_name`

2. **特定設定詳細取得**
   - テーブル直接検索
   - キー: `config_id`

3. **設定名での検索**
   - GSIスキャン
   - フィルター: `config_name`

## 設計判断の根拠

### PKにconfig_id (UUID) を選択した理由
- **変更可能性**: config_nameの変更がPKに影響しない
- **一意性保証**: UUID使用で重複を確実に回避
- **パーティション分散**: DynamoDBでの負荷分散効果
- **国際化対応**: 日本語設定名でもPK制約を受けない

### 単一テーブル構成
- **シンプルさ**: 複雑な結合操作が不要
- **コスト効率**: テーブル数による課金を最小化  
- **パフォーマンス**: 単一テーブルアクセスで高速

## API制限対策

NotionのAPI制限に対しては、テーブルではなく**アプリケーションレベルでの制御**を採用:
- 各API呼び出し間にsleep()による待機時間を挿入
- リトライ機構の実装
- エラーハンドリングの強化

**理由:** 
- 実行頻度が低い（日1回）
- データベース数も限定的
- 過剰設計を避けてシンプルに保つ

## 使用例

### 設定アイテムの例
```json
{
  "config_id": "550e8400-e29b-41d4-a716-446655440000",
  "config_name": "買い物リスト",
  "notion_database_id": "12345678-1234-1234-1234-123456789abc",
  "notion_page_id": "87654321-4321-4321-4321-cba987654321",
  "is_active": true,
  "description": "日用品の買い物チェックリスト"
}
```

### GSIクエリの例
```python
# アクティブな設定を取得
response = dynamodb.query(
    IndexName='active_configs_index',
    KeyConditionExpression=Key('is_active').eq(True)
)
```

## 今後の拡張性

### 考慮している拡張ポイント
- 設定の優先度管理 (`priority` 属性追加)
- 通知時間の個別設定 (`notification_schedule` 属性)
- 通知方法の多様化 (`notification_type` 属性)

### スケーラビリティ対応
- DynamoDBの自動スケーリングによる負荷対応
- GSIによる効率的なクエリ実行
- パーティション分散によるホットキー回避