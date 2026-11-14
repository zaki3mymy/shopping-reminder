import json
from typing import Any

from config import Config, ConfigError
from logger import get_logger
from models import NotificationResult
from notify_client import NotifyClient
from notion_client import NotionClient
from opentelemetry import metrics, trace
from opentelemetry.trace import Status, StatusCode

logger = get_logger(__name__)

_tracer = trace.get_tracer("shopping_reminder")
_meter = metrics.get_meter("shopping_reminder")

_unchecked_items_histogram = _meter.create_histogram(
    "shopping_reminder.items.unchecked",
    unit="1",
    description="Number of unchecked items in the shopping list per run",
)


class ShoppingReminderProcessor:
    """買い物リマインダーの処理を行うクラス"""

    def __init__(self, config: Config) -> None:
        self.config = config
        self.notion_client = NotionClient(config)
        self.notify_client = NotifyClient(config)
        logger.info("ShoppingReminderProcessor initialized successfully")

    @_tracer.start_as_current_span("process")
    def process(self, dry_run: bool = False) -> NotificationResult:
        """メイン処理を実行

        dry_run が True のときは、Notion から未チェック項目を取得するところまで実行し、
        通知は送信しない（デプロイ後の動作確認用）
        """
        span = trace.get_current_span()
        span.set_attribute("shopping_reminder.dry_run", dry_run)
        try:
            logger.info(f"Starting shopping reminder process (dry_run={dry_run})")

            # 1. 未チェック項目を取得
            logger.info("Querying unchecked items from Notion database")
            unchecked_items = self.notion_client.query_unchecked_items()
            logger.info(f"Found {len(unchecked_items)} unchecked items")
            _unchecked_items_histogram.record(len(unchecked_items), {"dry_run": dry_run})

            for item in unchecked_items:
                logger.info(f"Unchecked item: {item.name} (ID: {item.id})")

            if dry_run:
                logger.info("Dry run - skipping notification")
                return NotificationResult(
                    success=True,
                    message=(
                        f"dry run: {len(unchecked_items)}件の未チェック項目があります。"
                        "通知は送信していません。"
                    ),
                )

            # 2. 通知を送信（未チェック項目がない場合も含む）
            logger.info("Sending notification")
            result = self.notify_client.send_notification(unchecked_items)

            if result.success:
                logger.info(f"Process completed successfully: {result.message}")
            else:
                logger.warning(f"Process completed with issues: {result.message}")
                if result.error:
                    logger.error(f"Error details: {result.error}")

            return result

        except Exception as e:
            logger.exception("Unexpected error during processing")
            # 例外は結果に変えて返すため、span には自分で記録する
            span.record_exception(e)
            span.set_status(Status(StatusCode.ERROR, str(e)))
            return NotificationResult(
                success=False, message="処理中にエラーが発生しました。", error=str(e)
            )


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
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
        # {"dry_run": true} で呼ばれたときは通知を送信しない（デプロイ後の動作確認用）。
        # EventBridge からの定期実行のイベントには dry_run がないので、通常どおり通知する
        dry_run = isinstance(event, dict) and event.get("dry_run") is True

        processor = ShoppingReminderProcessor(config)
        result = processor.process(dry_run=dry_run)

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
        logger.exception("Configuration error")
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(
                {"success": False, "message": "設定エラーが発生しました。", "error": str(e)},
                ensure_ascii=False,
            ),
        }
    except Exception as e:
        logger.exception("Unexpected Lambda error")
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(
                {"success": False, "message": "予期しないエラーが発生しました。", "error": str(e)},
                ensure_ascii=False,
            ),
        }
