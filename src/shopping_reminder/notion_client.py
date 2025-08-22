import json
import logging
import urllib.request
import urllib.parse
from typing import List, Dict, Any

# ログ設定
logger = logging.getLogger(__name__)

try:
    # Lambda環境での絶対インポート
    from models import ShoppingItem, NotionDatabaseItem, NotificationResult  # type: ignore
    from config import Config  # type: ignore
except ImportError:
    # 開発環境での相対インポート
    from .models import ShoppingItem, NotionDatabaseItem, NotificationResult
    from .config import Config


class NotionAPIError(Exception):
    """Notion API に関するエラー"""
    pass


class NotionClient:
    """Notion API を操作するクライアント"""

    def __init__(self, config: Config) -> None:
        self.config = config
        self.base_url = "https://api.notion.com/v1"
        logger.info("NotionClient initialized")
        logger.info(f"Database ID: {config.notion_database_id}")
        logger.info(f"Page ID: {config.notion_page_id}")

    def query_unchecked_items(self) -> List[ShoppingItem]:
        """未チェック項目をデータベースから取得"""
        url = f"{self.base_url}/databases/{self.config.notion_database_id}/query"
        logger.info(f"Querying Notion database: {url}")

        filter_obj = self._build_filter_for_unchecked_items()
        logger.info(f"Filter object: {json.dumps(filter_obj)}")

        results = []
        start_cursor = None
        page_count = 0

        while True:
            page_count += 1
            body = {
                "filter": filter_obj,
                "page_size": 100
            }
            if start_cursor:
                body["start_cursor"] = start_cursor

            logger.info(f"Sending request for page {page_count}")
            logger.info(f"Request body: {json.dumps(body)}")

            response_data = self._make_post_request(url, body)

            logger.info(f"Response received for page {page_count}")
            logger.info(f"Response contains {len(response_data.get('results', []))} items")

            # NotionDatabaseItemからShoppingItemに変換
            for item_data in response_data["results"]:
                notion_item = NotionDatabaseItem(
                    id=item_data["id"],
                    properties=item_data["properties"]
                )
                shopping_item = notion_item.to_shopping_item()
                results.append(shopping_item)
                logger.info(f"Processed item: {shopping_item.name} (ID: {shopping_item.id}, Checked: {shopping_item.checked})")

            if not response_data["has_more"]:
                break

            start_cursor = response_data.get("next_cursor")
            logger.info(f"Moving to next page with cursor: {start_cursor}")

        logger.info(f"Query completed. Total items found: {len(results)}")
        return results

    def create_comment(self, items: List[ShoppingItem]) -> NotificationResult:
        """未チェック項目のリストからコメントを作成"""
        if not items:
            logger.info("No unchecked items found - skipping comment creation")
            return NotificationResult(
                success=True,
                message="未チェック項目はありません。通知は送信されませんでした。"
            )

        try:
            url = f"{self.base_url}/comments"
            logger.info(f"Creating comment at: {url}")

            message = self._format_comment_message(items)
            logger.info(f"Comment message: {message}")

            body = {
                "parent": {"page_id": self.config.notion_page_id},
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": message}
                    }
                ]
            }

            logger.info(f"Comment request body: {json.dumps(body)}")
            response_data = self._make_post_request(url, body)
            logger.info(f"Comment creation response: {json.dumps(response_data)}")

            logger.info(f"Comment created successfully for {len(items)} items")
            return NotificationResult(
                success=True,
                message=f"{len(items)}件の未チェック項目について通知を送信しました。"
            )

        except NotionAPIError as e:
            logger.exception(f"Failed to create comment: {str(e)}")
            return NotificationResult(
                success=False,
                message="コメントの作成に失敗しました。",
                error=str(e)
            )

    def _build_filter_for_unchecked_items(self) -> Dict[str, Any]:
        """未チェック項目を取得するためのフィルターを構築"""
        return {
            "property": "完了",
            "checkbox": {"equals": False}
        }

    def _format_comment_message(self, items: List[ShoppingItem]) -> str:
        """コメント用のメッセージを作成"""
        count = len(items)
        message = f"🛒 {count}件の未チェック項目があります:\n\n"

        for item in items:
            message += f"• {item.name}\n"

        message += "\n買い忘れがないよう確認をお願いします！"
        return message

    def _make_post_request(self, url: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Notion APIにPOSTリクエストを送信"""
        logger.info(f"Making POST request to: {url}")

        json_data = json.dumps(data).encode("utf-8")
        logger.info(f"Request data size: {len(json_data)} bytes")

        request = urllib.request.Request(
            url,
            data=json_data,
            headers={
                "Authorization": f"Bearer {self.config.notion_api_key[:10]}...",  # マスクして表示
                "Content-Type": "application/json",
                "Notion-Version": "2022-06-28"
            },
            method="POST"
        )

        logger.info(f"Request headers: {dict(request.headers)}")

        try:
            logger.info("Sending request to Notion API...")
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
                    raise NotionAPIError(f"API request failed with status {status_code}: {error_message}")

        except urllib.error.HTTPError as e:
            error_message = e.read().decode("utf-8") if e.fp else "Unknown error"
            logger.exception(f"HTTP error occurred: {e.code} - {error_message}")
            raise NotionAPIError(f"HTTP error {e.code}: {error_message}") from e
        except urllib.error.URLError as e:
            logger.exception(f"URL error occurred: {e.reason}")
            raise NotionAPIError(f"URL error: {e.reason}") from e
        except json.JSONDecodeError as e:
            logger.exception(f"JSON decode error occurred: {e}")
            raise NotionAPIError(f"JSON decode error: {e}") from e
