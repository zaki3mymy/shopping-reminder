import json
from unittest.mock import Mock, patch
import pytest

from src.shopping_reminder.notion_client import NotionClient, NotionAPIError
from src.shopping_reminder.config import Config


class TestNotionClient:
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
        self.client = NotionClient(self.config)

    def test_notion_client_initialization(self) -> None:
        assert self.client.config == self.config

    @patch("urllib.request.urlopen")
    def test_query_unchecked_items_success(self, mock_urlopen: Mock) -> None:
        # モックレスポンスのデータ
        mock_response_data = {
            "results": [
                {
                    "id": "item1",
                    "properties": {
                        "名前": {"title": [{"text": {"content": "牛乳"}}]},
                        "完了": {"checkbox": False},
                    },
                },
                {
                    "id": "item2",
                    "properties": {
                        "名前": {"title": [{"text": {"content": "パン"}}]},
                        "完了": {"checkbox": False},
                    },
                },
            ],
            "has_more": False,
        }

        mock_response = Mock()
        mock_response.read.return_value = json.dumps(mock_response_data).encode("utf-8")
        mock_response.getcode.return_value = 200
        mock_urlopen.return_value.__enter__.return_value = mock_response

        items = self.client.query_unchecked_items()

        assert len(items) == 2
        assert items[0].id == "item1"
        assert items[0].name == "牛乳"
        assert items[0].checked is False
        assert items[1].id == "item2"
        assert items[1].name == "パン"
        assert items[1].checked is False

    @patch("urllib.request.urlopen")
    def test_query_unchecked_items_empty_results(self, mock_urlopen: Mock) -> None:
        mock_response_data = {"results": [], "has_more": False}

        mock_response = Mock()
        mock_response.read.return_value = json.dumps(mock_response_data).encode("utf-8")
        mock_response.getcode.return_value = 200
        mock_urlopen.return_value.__enter__.return_value = mock_response

        items = self.client.query_unchecked_items()
        assert len(items) == 0

    @patch("urllib.request.urlopen")
    def test_query_unchecked_items_pagination(self, mock_urlopen: Mock) -> None:
        # 最初のページ
        first_page = {
            "results": [
                {
                    "id": "item1",
                    "properties": {
                        "名前": {"title": [{"text": {"content": "牛乳"}}]},
                        "完了": {"checkbox": False},
                    },
                }
            ],
            "has_more": True,
            "next_cursor": "cursor123",
        }

        # 2番目のページ
        second_page = {
            "results": [
                {
                    "id": "item2",
                    "properties": {
                        "名前": {"title": [{"text": {"content": "パン"}}]},
                        "完了": {"checkbox": False},
                    },
                }
            ],
            "has_more": False,
        }

        # モックの設定：複数のレスポンスを順番に返す
        mock_response1 = Mock()
        mock_response1.read.return_value = json.dumps(first_page).encode("utf-8")
        mock_response1.getcode.return_value = 200

        mock_response2 = Mock()
        mock_response2.read.return_value = json.dumps(second_page).encode("utf-8")
        mock_response2.getcode.return_value = 200

        mock_urlopen.return_value.__enter__.side_effect = [mock_response1, mock_response2]

        items = self.client.query_unchecked_items()

        assert len(items) == 2
        assert items[0].name == "牛乳"
        assert items[1].name == "パン"

    @patch("urllib.request.urlopen")
    def test_query_unchecked_items_api_error(self, mock_urlopen: Mock) -> None:
        mock_response = Mock()
        mock_response.getcode.return_value = 401
        mock_response.read.return_value = b'{"message": "Unauthorized"}'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        with pytest.raises(NotionAPIError) as exc_info:
            self.client.query_unchecked_items()

        assert "401" in str(exc_info.value)
        assert "Unauthorized" in str(exc_info.value)

    @patch("urllib.request.urlopen")
    def test_http_error_without_fp(self, mock_urlopen: Mock) -> None:
        """HTTPError で e.fp が None の場合のテスト（行136-137をカバー）"""
        import urllib.error

        # HTTPErrorのモックを作成し、fpをNoneに設定
        http_error = urllib.error.HTTPError(
            url="https://test.com", code=500, msg="Internal Server Error", hdrs={}, fp=None
        )
        mock_urlopen.side_effect = http_error

        with pytest.raises(NotionAPIError) as exc_info:
            self.client.query_unchecked_items()

        assert "HTTP error 500" in str(exc_info.value)

    @patch("urllib.request.urlopen")
    def test_url_error(self, mock_urlopen: Mock) -> None:
        """URLError の場合のテスト"""
        import urllib.error

        url_error = urllib.error.URLError("Connection refused")
        mock_urlopen.side_effect = url_error

        with pytest.raises(NotionAPIError) as exc_info:
            self.client.query_unchecked_items()

        assert "URL error" in str(exc_info.value)
        assert "Connection refused" in str(exc_info.value)

    @patch("urllib.request.urlopen")
    def test_json_decode_error(self, mock_urlopen: Mock) -> None:
        """JSONDecodeError の場合のテスト"""
        mock_response = Mock()
        mock_response.read.return_value = b"invalid json{"
        mock_response.getcode.return_value = 200
        mock_urlopen.return_value.__enter__.return_value = mock_response

        with pytest.raises(NotionAPIError) as exc_info:
            self.client.query_unchecked_items()

        assert "JSON decode error" in str(exc_info.value)

    def test_build_filter_for_unchecked_items(self) -> None:
        filter_obj = self.client._build_filter_for_unchecked_items()

        expected_filter = {"property": "完了", "checkbox": {"equals": False}}
        assert filter_obj == expected_filter


class TestNotionAPIError:
    def test_notion_api_error_creation(self) -> None:
        error = NotionAPIError("Test error message")
        assert str(error) == "Test error message"

    def test_notion_api_error_inheritance(self) -> None:
        error = NotionAPIError("Test error")
        assert isinstance(error, Exception)
