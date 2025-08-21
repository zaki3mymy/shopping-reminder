import json
from typing import Dict, Any

from .config import Config, ConfigError
from .notion_client import NotionClient
from .models import NotificationResult


class ShoppingReminderProcessor:
    """買い物リマインダーの処理を行うクラス"""

    def __init__(self, config: Config) -> None:
        self.config = config
        self.notion_client = NotionClient(config)

    def process(self) -> NotificationResult:
        """メイン処理を実行"""
        try:
            # 1. 未チェック項目を取得
            unchecked_items = self.notion_client.query_unchecked_items()

            # 2. コメントを作成（未チェック項目がない場合も含む）
            result = self.notion_client.create_comment(unchecked_items)

            return result

        except Exception as e:
            return NotificationResult(
                success=False,
                message="処理中にエラーが発生しました。",
                error=str(e)
            )


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """AWS Lambda のエントリーポイント"""
    try:
        # 1. 設定の読み込み
        config = Config()

        # 2. 処理の実行
        processor = ShoppingReminderProcessor(config)
        result = processor.process()

        # 3. レスポンスの作成
        if result.success:
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({
                    "success": True,
                    "message": result.message
                }, ensure_ascii=False)
            }
        else:
            return {
                "statusCode": 500,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({
                    "success": False,
                    "message": result.message,
                    "error": result.error
                }, ensure_ascii=False)
            }

    except ConfigError as e:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "success": False,
                "message": "設定エラーが発生しました。",
                "error": str(e)
            }, ensure_ascii=False)
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "success": False,
                "message": "予期しないエラーが発生しました。",
                "error": str(e)
            }, ensure_ascii=False)
        }
