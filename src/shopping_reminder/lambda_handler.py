import json
from typing import Dict, Any

from config import Config, ConfigError
from notion_client import NotionClient
from models import NotificationResult
from logger import get_logger

logger = get_logger(__name__)


class ShoppingReminderProcessor:
    """買い物リマインダーの処理を行うクラス"""

    def __init__(self, config: Config) -> None:
        self.config = config
        self.notion_client = NotionClient(config)
        logger.info("ShoppingReminderProcessor initialized successfully")

    def process(self) -> NotificationResult:
        """メイン処理を実行（複数データベース対応）"""
        try:
            logger.info("Starting shopping reminder process")
            logger.info(f"Processing {len(self.config.database_configs)} database configurations")

            # 1. すべてのアクティブデータベースから未チェック項目を取得
            logger.info("Querying unchecked items from all active Notion databases")
            all_results = self.notion_client.query_all_unchecked_items()

            total_items = sum(len(items) for _, items in all_results)
            logger.info(f"Found {total_items} total unchecked items across {len(all_results)} databases")

            # データベースごとの詳細をログ出力
            for db_config, items in all_results:
                logger.info(f"{db_config.config_name}: {len(items)} unchecked items")
                for item in items:
                    logger.info(f"  • {item.name} (ID: {item.id})")

            # 2. 各データベースに対応するページにコメントを作成
            logger.info("Creating comment notifications for all databases")
            result = self.notion_client.create_all_comments(all_results)

            if result.success:
                logger.info(f"Process completed successfully: {result.message}")
            else:
                logger.warning(f"Process completed with issues: {result.message}")
                if result.error:
                    logger.error(f"Error details: {result.error}")

            return result

        except Exception as e:
            logger.exception(f"Unexpected error during processing: {str(e)}")
            return NotificationResult(
                success=False, message="処理中にエラーが発生しました。", error=str(e)
            )


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """AWS Lambda のエントリーポイント"""
    logger.info("Lambda handler started")
    logger.info(f"Event: {json.dumps(event) if event else 'No event data'}")
    logger.info(
        f"Request ID: {getattr(context, 'aws_request_id', 'No request ID available') if context else 'No context'}"
    )

    try:
        # 1. 設定の読み込み
        logger.info("Loading configuration")
        config = Config()
        logger.info("Configuration loaded successfully")

        # 2. 処理の実行
        logger.info("Initializing processor")
        processor = ShoppingReminderProcessor(config)
        result = processor.process()

        # 3. レスポンスの作成
        if result.success:
            logger.info("Lambda execution completed successfully")
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(
                    {"success": True, "message": result.message}, ensure_ascii=False
                ),
            }
        else:
            logger.error("Lambda execution completed with errors")
            return {
                "statusCode": 500,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(
                    {"success": False, "message": result.message, "error": result.error},
                    ensure_ascii=False,
                ),
            }

    except ConfigError as e:
        logger.exception(f"Configuration error: {str(e)}")
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(
                {"success": False, "message": "設定エラーが発生しました。", "error": str(e)},
                ensure_ascii=False,
            ),
        }
    except Exception as e:
        logger.exception(f"Unexpected Lambda error: {str(e)}")
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(
                {"success": False, "message": "予期しないエラーが発生しました。", "error": str(e)},
                ensure_ascii=False,
            ),
        }
