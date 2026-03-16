import json
import urllib.error
from typing import List
from unittest.mock import Mock, patch

from src.shopping_reminder.notify_client import NotifyClient, NotifyAPIError
from src.shopping_reminder.models import ShoppingItem
from src.shopping_reminder.config import Config


class TestNotifyClient:
    def setup_method(self) -> None:
        """各テストメソッドの前に実行される"""
        self.config = Config.from_dict(
            {
                "NOTION_API_KEY": "secret_test_key",
                "NOTION_DATABASE_ID": "test_database_id",
                "NOTIFY_API_KEY": "test_notify_key",
                "NOTIFY_API_URL": "https://example.com/prod",
            }
        )
        self.client = NotifyClient(self.config)

    def test_notify_client_initialization(self) -> None:
        assert self.client.config == self.config
        assert self.client.notify_url == "https://example.com/prod/notify"

    @patch("urllib.request.urlopen")
    def test_send_notification_success(self, mock_urlopen: Mock) -> None:
        mock_response_data = {"message": "Successfully sent 1 message(s)"}

        mock_response = Mock()
        mock_response.read.return_value = json.dumps(mock_response_data).encode("utf-8")
        mock_response.getcode.return_value = 200
        mock_urlopen.return_value.__enter__.return_value = mock_response

        items = [ShoppingItem("1", "牛乳", False), ShoppingItem("2", "パン", False)]
        result = self.client.send_notification(items)

        assert result.success is True
        assert "2件の未チェック項目について通知を送信しました" in result.message
        assert result.error is None
        mock_urlopen.assert_called_once()

    @patch("urllib.request.urlopen")
    def test_send_notification_empty_items(self, mock_urlopen: Mock) -> None:
        items: List[ShoppingItem] = []
        result = self.client.send_notification(items)

        assert result.success is True
        assert "未チェック項目はありません" in result.message
        assert result.error is None
        # APIが呼ばれないことを確認
        mock_urlopen.assert_not_called()

    @patch("urllib.request.urlopen")
    def test_send_notification_api_error(self, mock_urlopen: Mock) -> None:
        mock_response = Mock()
        mock_response.getcode.return_value = 400
        mock_response.read.return_value = b'{"message": "No message or messages key found"}'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        items = [ShoppingItem("1", "牛乳", False)]
        result = self.client.send_notification(items)

        assert result.success is False
        assert "通知の送信に失敗しました" in result.message
        assert "400" in result.error

    @patch("urllib.request.urlopen")
    def test_send_notification_http_error(self, mock_urlopen: Mock) -> None:
        http_error = urllib.error.HTTPError(
            url="https://example.com/prod/notify",
            code=500,
            msg="Internal Server Error",
            hdrs={},
            fp=None,
        )
        mock_urlopen.side_effect = http_error

        items = [ShoppingItem("1", "牛乳", False)]
        result = self.client.send_notification(items)

        assert result.success is False
        assert "通知の送信に失敗しました" in result.message
        assert "HTTP error 500" in result.error

    @patch("urllib.request.urlopen")
    def test_send_notification_url_error(self, mock_urlopen: Mock) -> None:
        url_error = urllib.error.URLError("Connection refused")
        mock_urlopen.side_effect = url_error

        items = [ShoppingItem("1", "牛乳", False)]
        result = self.client.send_notification(items)

        assert result.success is False
        assert "通知の送信に失敗しました" in result.message
        assert "URL error" in result.error

    @patch("urllib.request.urlopen")
    def test_send_notification_json_decode_error(self, mock_urlopen: Mock) -> None:
        mock_response = Mock()
        mock_response.read.return_value = b"invalid json{"
        mock_response.getcode.return_value = 200
        mock_urlopen.return_value.__enter__.return_value = mock_response

        items = [ShoppingItem("1", "牛乳", False)]
        result = self.client.send_notification(items)

        assert result.success is False
        assert "通知の送信に失敗しました" in result.message
        assert "JSON decode error" in result.error

    def test_format_message_single_item(self) -> None:
        items = [ShoppingItem("1", "牛乳", False)]
        message = self.client._format_message(items)

        assert "1件の未チェック項目があります" in message
        assert "• 牛乳" in message
        assert "確認をお願いします" in message

    def test_format_message_multiple_items(self) -> None:
        items = [
            ShoppingItem("1", "牛乳", False),
            ShoppingItem("2", "パン", False),
            ShoppingItem("3", "卵", False),
        ]
        message = self.client._format_message(items)

        assert "3件の未チェック項目があります" in message
        assert "• 牛乳" in message
        assert "• パン" in message
        assert "• 卵" in message

    @patch("urllib.request.urlopen")
    def test_request_uses_api_key_header(self, mock_urlopen: Mock) -> None:
        """x-api-key ヘッダーが正しく設定されることを確認"""
        mock_response_data = {"message": "Successfully sent 1 message(s)"}
        mock_response = Mock()
        mock_response.read.return_value = json.dumps(mock_response_data).encode("utf-8")
        mock_response.getcode.return_value = 200
        mock_urlopen.return_value.__enter__.return_value = mock_response

        items = [ShoppingItem("1", "牛乳", False)]
        self.client.send_notification(items)

        call_args = mock_urlopen.call_args
        request = call_args[0][0]
        assert request.get_header("X-api-key") == "test_notify_key"


class TestNotifyAPIError:
    def test_notify_api_error_creation(self) -> None:
        error = NotifyAPIError("Test error message")
        assert str(error) == "Test error message"

    def test_notify_api_error_inheritance(self) -> None:
        error = NotifyAPIError("Test error")
        assert isinstance(error, Exception)
