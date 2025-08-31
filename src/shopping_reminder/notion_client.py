import json
import urllib.request
import urllib.parse
import time
from typing import List, Dict, Any, Tuple

# Lambda環境での絶対インポート
from models import ShoppingItem, NotionDatabaseItem, NotificationResult, DatabaseConfig
from config import Config
from logger import get_logger

logger = get_logger(__name__)


class NotionAPIError(Exception):
    """Notion API に関するエラー"""

    pass


class NotionClient:
    """Notion API を操作するクライアント（複数データベース対応）"""

    def __init__(self, config: Config) -> None:
        self.config = config
        self.base_url = "https://api.notion.com/v1"
        logger.info("NotionClient initialized")
        logger.info(f"Managing {len(config.database_configs)} database configurations")

    def query_all_unchecked_items(self) -> List[Tuple[DatabaseConfig, List[ShoppingItem]]]:
        """すべてのアクティブデータベースから未チェック項目を取得"""
        all_results: List[Tuple[DatabaseConfig, List[ShoppingItem]]] = []

        for config in self.config.database_configs:
            logger.info(f"Querying database: {config.config_name} (ID: {config.config_id})")

            # API制限対策：リクエスト間隔を制御
            if len(all_results) > 0:  # 最初のリクエスト以外は待機
                logger.info("Waiting 1 second to respect Notion API rate limits")
                time.sleep(1)

            try:
                items = self._query_unchecked_items_for_database(config)
                all_results.append((config, items))
                logger.info(f"Found {len(items)} unchecked items in {config.config_name}")

            except NotionAPIError as e:
                logger.error(f"Failed to query database {config.config_name}: {str(e)}")
                # 一つのデータベースが失敗しても他を続行
                all_results.append((config, []))
                continue

        total_items = sum(len(items) for _, items in all_results)
        logger.info(f"Query completed for all databases. Total unchecked items: {total_items}")
        return all_results

    def _query_unchecked_items_for_database(self, db_config: DatabaseConfig) -> List[ShoppingItem]:
        """指定されたデータベースから未チェック項目を取得"""
        url = f"{self.base_url}/databases/{db_config.notion_database_id}/query"
        logger.info(f"Querying Notion database: {url}")

        filter_obj = self._build_filter_for_unchecked_items()
        logger.info(f"Filter object: {json.dumps(filter_obj)}")

        results = []
        start_cursor = None
        page_count = 0

        while True:
            page_count += 1
            body = {"filter": filter_obj, "page_size": 100}
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
                    id=item_data["id"], properties=item_data["properties"]
                )
                shopping_item = notion_item.to_shopping_item()
                results.append(shopping_item)
                logger.info(
                    f"Processed item: {shopping_item.name} (ID: {shopping_item.id}, Checked: {shopping_item.checked})"
                )

            if not response_data["has_more"]:
                break

            start_cursor = response_data.get("next_cursor")
            logger.info(f"Moving to next page with cursor: {start_cursor}")

        logger.info(f"Database query completed. Items found: {len(results)}")
        return results

    def create_all_comments(self, all_results: List[Tuple[DatabaseConfig, List[ShoppingItem]]]) -> NotificationResult:
        """すべてのデータベース結果に対してコメントを作成"""
        total_items = 0
        successful_notifications = 0
        failed_notifications = 0
        error_messages = []

        for db_config, items in all_results:
            if not items:
                logger.info(f"No unchecked items for {db_config.config_name} - skipping")
                continue

            total_items += len(items)

            # API制限対策：コメント作成間隔を制御
            if successful_notifications > 0:  # 最初のコメント以外は待機
                logger.info("Waiting 1 second before creating next comment")
                time.sleep(1)

            try:
                result = self._create_comment_for_database(db_config, items)
                if result.success:
                    successful_notifications += 1
                    logger.info(f"Successfully notified for {db_config.config_name}")
                else:
                    failed_notifications += 1
                    error_messages.append(f"{db_config.config_name}: {result.error}")
                    logger.error(f"Failed to notify for {db_config.config_name}: {result.error}")

            except Exception as e:
                failed_notifications += 1
                error_msg = str(e)
                error_messages.append(f"{db_config.config_name}: {error_msg}")
                logger.exception(f"Unexpected error creating comment for {db_config.config_name}: {error_msg}")

        # 結果をまとめて返す
        if total_items == 0:
            return NotificationResult(
                success=True,
                message="すべてのデータベースで未チェック項目はありません。通知は送信されませんでした。"
            )
        elif failed_notifications == 0:
            return NotificationResult(
                success=True,
                message=f"{successful_notifications}個のデータベースで計{total_items}件の未チェック項目について通知を送信しました。"
            )
        elif successful_notifications > 0:
            return NotificationResult(
                success=True,
                message=f"{successful_notifications}個のデータベースで通知成功、{failed_notifications}個で失敗しました。",
                error="; ".join(error_messages)
            )
        else:
            return NotificationResult(
                success=False,
                message="すべてのデータベースで通知の作成に失敗しました。",
                error="; ".join(error_messages)
            )

    def _create_comment_for_database(self, db_config: DatabaseConfig, items: List[ShoppingItem]) -> NotificationResult:
        """指定されたデータベースの未チェック項目についてコメントを作成"""
        try:
            url = f"{self.base_url}/comments"
            logger.info(f"Creating comment for {db_config.config_name} at: {url}")

            message = self._format_comment_message_for_database(db_config, items)
            logger.info(f"Comment message: {message}")

            body = {
                "parent": {"page_id": db_config.notion_page_id},
                "rich_text": [{"type": "text", "text": {"content": message}}],
            }

            logger.info(f"Comment request body: {json.dumps(body)}")
            response_data = self._make_post_request(url, body)
            logger.info(f"Comment creation response: {json.dumps(response_data)}")

            logger.info(f"Comment created successfully for {db_config.config_name} with {len(items)} items")
            return NotificationResult(
                success=True,
                message=f"{db_config.config_name}: {len(items)}件の未チェック項目について通知を送信しました。"
            )

        except NotionAPIError as e:
            logger.exception(f"Failed to create comment for {db_config.config_name}: {str(e)}")
            return NotificationResult(
                success=False,
                message=f"{db_config.config_name}のコメント作成に失敗しました。",
                error=str(e)
            )

    def _build_filter_for_unchecked_items(self) -> Dict[str, Any]:
        """未チェック項目を取得するためのフィルターを構築"""
        return {"property": "完了", "checkbox": {"equals": False}}

    def _format_comment_message_for_database(self, db_config: DatabaseConfig, items: List[ShoppingItem]) -> str:
        """データベース固有のコメント用メッセージを作成"""
        count = len(items)
        message = f"🛒 [{db_config.config_name}] {count}件の未チェック項目があります:\n\n"

        for item in items:
            message += f"• {item.name}\n"

        message += "\n買い忘れがないよう確認をお願いします！"
        return message

    def _format_comment_message(self, items: List[ShoppingItem]) -> str:
        """コメント用のメッセージを作成（後方互換性のため残す）"""
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
                "Authorization": f"Bearer {self.config.notion_api_key}",
                "Content-Type": "application/json",
                "Notion-Version": "2022-06-28",
            },
            method="POST",
        )

        # ログ出力時のみAPIキーをマスク
        headers_for_log = dict(request.headers)
        headers_for_log["Authorization"] = f"Bearer {self.config.notion_api_key[:10]}..."
        logger.info(f"Request headers: {headers_for_log}")

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
                    raise NotionAPIError(
                        f"API request failed with status {status_code}: {error_message}"
                    )

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
