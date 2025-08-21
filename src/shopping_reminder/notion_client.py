import json
import urllib.request
import urllib.parse
from typing import List, Dict, Any

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

    def query_unchecked_items(self) -> List[ShoppingItem]:
        """未チェック項目をデータベースから取得"""
        url = f"{self.base_url}/databases/{self.config.notion_database_id}/query"

        filter_obj = self._build_filter_for_unchecked_items()
        results = []
        start_cursor = None

        while True:
            body = {
                "filter": filter_obj,
                "page_size": 100
            }
            if start_cursor:
                body["start_cursor"] = start_cursor

            response_data = self._make_post_request(url, body)

            # NotionDatabaseItemからShoppingItemに変換
            for item_data in response_data["results"]:
                notion_item = NotionDatabaseItem(
                    id=item_data["id"],
                    properties=item_data["properties"]
                )
                results.append(notion_item.to_shopping_item())

            if not response_data["has_more"]:
                break

            start_cursor = response_data.get("next_cursor")

        return results

    def create_comment(self, items: List[ShoppingItem]) -> NotificationResult:
        """未チェック項目のリストからコメントを作成"""
        if not items:
            return NotificationResult(
                success=True,
                message="未チェック項目はありません。通知は送信されませんでした。"
            )

        try:
            url = f"{self.base_url}/comments"
            message = self._format_comment_message(items)

            body = {
                "parent": {"page_id": self.config.notion_page_id},
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": message}
                    }
                ]
            }

            self._make_post_request(url, body)

            return NotificationResult(
                success=True,
                message=f"{len(items)}件の未チェック項目について通知を送信しました。"
            )

        except NotionAPIError as e:
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
        json_data = json.dumps(data).encode("utf-8")

        request = urllib.request.Request(
            url,
            data=json_data,
            headers={
                "Authorization": f"Bearer {self.config.notion_api_key}",
                "Content-Type": "application/json",
                "Notion-Version": "2022-06-28"
            },
            method="POST"
        )

        try:
            with urllib.request.urlopen(request) as response:
                response_data = response.read()
                status_code = response.getcode()

                if status_code == 200:
                    return json.loads(response_data.decode("utf-8"))
                else:
                    error_message = response_data.decode("utf-8")
                    raise NotionAPIError(f"API request failed with status {status_code}: {error_message}")

        except urllib.error.HTTPError as e:
            error_message = e.read().decode("utf-8") if e.fp else "Unknown error"
            raise NotionAPIError(f"HTTP error {e.code}: {error_message}") from e
        except urllib.error.URLError as e:
            raise NotionAPIError(f"URL error: {e.reason}") from e
        except json.JSONDecodeError as e:
            raise NotionAPIError(f"JSON decode error: {e}") from e
