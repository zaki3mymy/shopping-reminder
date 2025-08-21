import json
from typing import Dict, Any
from unittest.mock import Mock, patch

from src.shopping_reminder.lambda_handler import handler, ShoppingReminderProcessor
from src.shopping_reminder.models import ShoppingItem, NotificationResult
from src.shopping_reminder.config import Config, ConfigError


class TestShoppingReminderProcessor:
    def setup_method(self) -> None:
        """各テストメソッドの前に実行される"""
        self.config = Config.from_dict({
            "NOTION_API_KEY": "secret_test_key",
            "NOTION_DATABASE_ID": "test_database_id",
            "NOTION_PAGE_ID": "test_page_id"
        })
        self.processor = ShoppingReminderProcessor(self.config)

    def test_processor_initialization(self) -> None:
        assert self.processor.config == self.config
        assert self.processor.notion_client is not None

    @patch("src.shopping_reminder.lambda_handler.NotionClient")
    def test_process_with_unchecked_items(self, mock_notion_client_class: Mock) -> None:
        # モックの設定
        mock_client = Mock()
        mock_notion_client_class.return_value = mock_client

        unchecked_items = [
            ShoppingItem("1", "牛乳", False),
            ShoppingItem("2", "パン", False)
        ]
        mock_client.query_unchecked_items.return_value = unchecked_items
        mock_client.create_comment.return_value = NotificationResult(
            success=True,
            message="2件の未チェック項目について通知を送信しました。"
        )

        processor = ShoppingReminderProcessor(self.config)
        result = processor.process()

        assert result.success is True
        assert "2件の未チェック項目について通知を送信しました" in result.message
        mock_client.query_unchecked_items.assert_called_once()
        mock_client.create_comment.assert_called_once_with(unchecked_items)

    @patch("src.shopping_reminder.lambda_handler.NotionClient")
    def test_process_with_no_unchecked_items(self, mock_notion_client_class: Mock) -> None:
        mock_client = Mock()
        mock_notion_client_class.return_value = mock_client

        mock_client.query_unchecked_items.return_value = []
        mock_client.create_comment.return_value = NotificationResult(
            success=True,
            message="未チェック項目はありません。通知は送信されませんでした。"
        )

        processor = ShoppingReminderProcessor(self.config)
        result = processor.process()

        assert result.success is True
        assert "未チェック項目はありません" in result.message
        mock_client.query_unchecked_items.assert_called_once()
        mock_client.create_comment.assert_called_once_with([])

    @patch("src.shopping_reminder.lambda_handler.NotionClient")
    def test_process_with_query_error(self, mock_notion_client_class: Mock) -> None:
        mock_client = Mock()
        mock_notion_client_class.return_value = mock_client

        mock_client.query_unchecked_items.side_effect = Exception("データベースクエリエラー")

        processor = ShoppingReminderProcessor(self.config)
        result = processor.process()

        assert result.success is False
        assert "処理中にエラーが発生しました" in result.message
        assert "データベースクエリエラー" in result.error

    @patch("src.shopping_reminder.lambda_handler.NotionClient")
    def test_process_with_comment_creation_error(self, mock_notion_client_class: Mock) -> None:
        mock_client = Mock()
        mock_notion_client_class.return_value = mock_client

        unchecked_items = [ShoppingItem("1", "牛乳", False)]
        mock_client.query_unchecked_items.return_value = unchecked_items
        mock_client.create_comment.return_value = NotificationResult(
            success=False,
            message="コメントの作成に失敗しました。",
            error="API key が無効です"
        )

        processor = ShoppingReminderProcessor(self.config)
        result = processor.process()

        assert result.success is False
        assert "コメントの作成に失敗しました" in result.message
        assert "API key が無効です" in result.error


class TestLambdaHandler:
    @patch("src.shopping_reminder.lambda_handler.Config")
    @patch("src.shopping_reminder.lambda_handler.ShoppingReminderProcessor")
    def test_handler_success(self, mock_processor_class: Mock, mock_config_class: Mock) -> None:
        # モックの設定
        mock_config = Mock()
        mock_config_class.return_value = mock_config

        mock_processor = Mock()
        mock_processor_class.return_value = mock_processor
        mock_processor.process.return_value = NotificationResult(
            success=True,
            message="2件の未チェック項目について通知を送信しました。"
        )

        # イベントとコンテキストのダミー
        event: Dict[str, Any] = {}
        context = Mock()

        response = handler(event, context)

        assert response["statusCode"] == 200
        assert response["headers"]["Content-Type"] == "application/json"

        body = json.loads(response["body"])
        assert body["success"] is True
        assert "2件の未チェック項目について通知を送信しました" in body["message"]

        mock_config_class.assert_called_once()
        mock_processor_class.assert_called_once_with(mock_config)
        mock_processor.process.assert_called_once()

    @patch("src.shopping_reminder.lambda_handler.Config")
    def test_handler_config_error(self, mock_config_class: Mock) -> None:
        mock_config_class.side_effect = ConfigError("NOTION_API_KEY is required")

        event: Dict[str, Any] = {}
        context = Mock()

        response = handler(event, context)

        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert body["success"] is False
        assert "設定エラー" in body["message"]
        assert "NOTION_API_KEY is required" in body["error"]

    @patch("src.shopping_reminder.lambda_handler.Config")
    @patch("src.shopping_reminder.lambda_handler.ShoppingReminderProcessor")
    def test_handler_processing_error(
        self,
        mock_processor_class: Mock,
        mock_config_class: Mock
    ) -> None:
        mock_config = Mock()
        mock_config_class.return_value = mock_config

        mock_processor = Mock()
        mock_processor_class.return_value = mock_processor
        mock_processor.process.return_value = NotificationResult(
            success=False,
            message="処理中にエラーが発生しました。",
            error="データベースクエリエラー"
        )

        event: Dict[str, Any] = {}
        context = Mock()

        response = handler(event, context)

        assert response["statusCode"] == 500
        body = json.loads(response["body"])
        assert body["success"] is False
        assert "処理中にエラーが発生しました" in body["message"]
        assert "データベースクエリエラー" in body["error"]

    @patch("src.shopping_reminder.lambda_handler.Config")
    def test_handler_unexpected_error(self, mock_config_class: Mock) -> None:
        mock_config_class.side_effect = Exception("予期しないエラー")

        event: Dict[str, Any] = {}
        context = Mock()

        response = handler(event, context)

        assert response["statusCode"] == 500
        body = json.loads(response["body"])
        assert body["success"] is False
        assert "予期しないエラーが発生しました" in body["message"]
        assert "予期しないエラー" in body["error"]
