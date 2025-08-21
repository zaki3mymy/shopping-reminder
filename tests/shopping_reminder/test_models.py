from typing import Dict, Any
import pytest

from src.shopping_reminder.models import ShoppingItem, NotionDatabaseItem, NotificationResult


class TestShoppingItem:
    def test_shopping_item_creation(self) -> None:
        item = ShoppingItem(id="123", name="牛乳", checked=False)
        assert item.id == "123"
        assert item.name == "牛乳"
        assert item.checked is False

    def test_shopping_item_creation_with_checked_true(self) -> None:
        item = ShoppingItem(id="456", name="パン", checked=True)
        assert item.id == "456"
        assert item.name == "パン"
        assert item.checked is True

    def test_shopping_item_equality(self) -> None:
        item1 = ShoppingItem(id="123", name="牛乳", checked=False)
        item2 = ShoppingItem(id="123", name="牛乳", checked=False)
        assert item1 == item2

    def test_shopping_item_inequality(self) -> None:
        item1 = ShoppingItem(id="123", name="牛乳", checked=False)
        item2 = ShoppingItem(id="456", name="パン", checked=True)
        assert item1 != item2

    def test_shopping_item_equality_with_non_shopping_item(self) -> None:
        """異なる型のオブジェクトとの比較テスト（行13をカバー）"""
        item = ShoppingItem(id="123", name="牛乳", checked=False)

        # 文字列との比較
        assert item.__eq__("not a shopping item") == NotImplemented

        # 数値との比較
        assert item.__eq__(123) == NotImplemented

        # 辞書との比較
        assert item.__eq__({"id": "123", "name": "牛乳"}) == NotImplemented

        # Noneとの比較
        assert item.__eq__(None) == NotImplemented


class TestNotionDatabaseItem:
    def test_notion_database_item_creation(self) -> None:
        properties = {
            "名前": {"title": [{"text": {"content": "牛乳"}}]},
            "完了": {"checkbox": False}
        }
        item = NotionDatabaseItem(id="123", properties=properties)
        assert item.id == "123"
        assert item.properties == properties

    def test_to_shopping_item_unchecked(self) -> None:
        properties = {
            "名前": {"title": [{"text": {"content": "牛乳"}}]},
            "完了": {"checkbox": False}
        }
        notion_item = NotionDatabaseItem(id="123", properties=properties)
        shopping_item = notion_item.to_shopping_item()

        assert shopping_item.id == "123"
        assert shopping_item.name == "牛乳"
        assert shopping_item.checked is False

    def test_to_shopping_item_checked(self) -> None:
        properties = {
            "名前": {"title": [{"text": {"content": "パン"}}]},
            "完了": {"checkbox": True}
        }
        notion_item = NotionDatabaseItem(id="456", properties=properties)
        shopping_item = notion_item.to_shopping_item()

        assert shopping_item.id == "456"
        assert shopping_item.name == "パン"
        assert shopping_item.checked is True

    def test_to_shopping_item_empty_title(self) -> None:
        properties = {
            "名前": {"title": []},
            "完了": {"checkbox": False}
        }
        notion_item = NotionDatabaseItem(id="789", properties=properties)
        shopping_item = notion_item.to_shopping_item()

        assert shopping_item.id == "789"
        assert shopping_item.name == ""
        assert shopping_item.checked is False

    def test_to_shopping_item_missing_properties(self) -> None:
        properties: Dict[str, Any] = {}
        notion_item = NotionDatabaseItem(id="999", properties=properties)

        with pytest.raises(KeyError):
            notion_item.to_shopping_item()


class TestNotificationResult:
    def test_notification_result_success(self) -> None:
        result = NotificationResult(success=True, message="通知を送信しました")
        assert result.success is True
        assert result.message == "通知を送信しました"
        assert result.error is None

    def test_notification_result_failure(self) -> None:
        result = NotificationResult(
            success=False,
            message="通知の送信に失敗しました",
            error="API key が無効です"
        )
        assert result.success is False
        assert result.message == "通知の送信に失敗しました"
        assert result.error == "API key が無効です"

    def test_notification_result_default_values(self) -> None:
        result = NotificationResult(success=True, message="成功")
        assert result.success is True
        assert result.message == "成功"
        assert result.error is None
