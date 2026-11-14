import json
import urllib.error
import urllib.request
from typing import Any

from config import Config
from logger import get_logger

# Lambda環境での絶対インポート
from models import NotificationResult, ShoppingItem
from opentelemetry import metrics, trace
from opentelemetry.trace import Status, StatusCode

logger = get_logger(__name__)

_tracer = trace.get_tracer("shopping_reminder")
_meter = metrics.get_meter("shopping_reminder")

_notification_counter = _meter.create_counter(
    "shopping_reminder.notifications.sent",
    unit="1",
    description="Number of notifications sent to the notify API",
)


class NotifyAPIError(Exception):
    """通知API に関するエラー"""


class NotifyClient:
    """なんでもお知らせくん API を操作するクライアント"""

    def __init__(self, config: Config) -> None:
        self.config = config
        self.notify_url = f"{config.notify_api_url}/notify"
        logger.info("NotifyClient initialized")
        logger.info(f"Notify URL: {self.notify_url}")

    @_tracer.start_as_current_span("send_notification")
    def send_notification(self, items: list[ShoppingItem]) -> NotificationResult:
        """未チェック項目のリストを通知APIに送信"""
        span = trace.get_current_span()
        span.set_attribute("notify.item_count", len(items))
        if not items:
            logger.info("No unchecked items found - skipping notification")
            return NotificationResult(
                success=True, message="未チェック項目はありません。通知は送信されませんでした。"
            )

        try:
            message = self._format_message(items)
            logger.info(f"Sending notification message: {message}")

            body = {"message": message}
            response_data = self._make_post_request(self.notify_url, body)
            logger.info(f"Notification response: {json.dumps(response_data)}")

            logger.info(f"Notification sent successfully for {len(items)} items")
            _notification_counter.add(1)
            return NotificationResult(
                success=True, message=f"{len(items)}件の未チェック項目について通知を送信しました。"
            )

        except NotifyAPIError as e:
            logger.exception("Failed to send notification")
            # 例外は結果に変えて返すため、span には自分で記録する
            span.record_exception(e)
            span.set_status(Status(StatusCode.ERROR, str(e)))
            return NotificationResult(
                success=False, message="通知の送信に失敗しました。", error=str(e)
            )

    def _format_message(self, items: list[ShoppingItem]) -> str:
        """通知用のメッセージを作成"""
        count = len(items)
        message = f"🛒 {count}件の未チェック項目があります:\n\n"

        for item in items:
            message += f"• {item.name}\n"

        message += "\n買い忘れがないよう確認をお願いします！"
        return message

    def _make_post_request(self, url: str, data: dict[str, Any]) -> dict[str, Any]:
        """通知APIにPOSTリクエストを送信"""
        logger.info(f"Making POST request to: {url}")

        json_data = json.dumps(data, ensure_ascii=False).encode("utf-8")
        logger.info(f"Request data size: {len(json_data)} bytes")

        request = urllib.request.Request(
            url,
            data=json_data,
            headers={
                "x-api-key": self.config.notify_api_key,
                "Content-Type": "application/json",
            },
            method="POST",
        )

        logger.info("Sending request to Notify API...")

        try:
            with urllib.request.urlopen(request) as response:
                response_data = response.read()
                status_code = response.getcode()

                logger.info(f"Response status code: {status_code}")
                logger.info(f"Response data size: {len(response_data)} bytes")

                if status_code == 200:
                    decoded_response = json.loads(response_data.decode("utf-8"))
                    logger.info("Request completed successfully")
                    return decoded_response
                else:
                    error_message = response_data.decode("utf-8")
                    logger.error(f"API request failed with status {status_code}")
                    logger.error(f"Error response: {error_message}")
                    raise NotifyAPIError(
                        f"API request failed with status {status_code}: {error_message}"
                    )

        except urllib.error.HTTPError as e:
            error_message = e.read().decode("utf-8") if e.fp else "Unknown error"
            logger.exception(f"HTTP error occurred: {e.code} - {error_message}")
            raise NotifyAPIError(f"HTTP error {e.code}: {error_message}") from e
        except urllib.error.URLError as e:
            logger.exception(f"URL error occurred: {e.reason}")
            raise NotifyAPIError(f"URL error: {e.reason}") from e
        except json.JSONDecodeError as e:
            logger.exception("JSON decode error occurred")
            raise NotifyAPIError(f"JSON decode error: {e}") from e
