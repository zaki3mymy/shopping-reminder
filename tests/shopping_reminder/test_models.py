from typing import Dict, Any
import pytest

from src.shopping_reminder.models import ShoppingItem, NotionDatabaseItem, NotificationResult, DatabaseConfig


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
            "完了": {"checkbox": False},
        }
        item = NotionDatabaseItem(id="123", properties=properties)
        assert item.id == "123"
        assert item.properties == properties

    def test_to_shopping_item_unchecked(self) -> None:
        properties = {
            "名前": {"title": [{"text": {"content": "牛乳"}}]},
            "完了": {"checkbox": False},
        }
        notion_item = NotionDatabaseItem(id="123", properties=properties)
        shopping_item = notion_item.to_shopping_item()

        assert shopping_item.id == "123"
        assert shopping_item.name == "牛乳"
        assert shopping_item.checked is False

    def test_to_shopping_item_checked(self) -> None:
        properties = {
            "名前": {"title": [{"text": {"content": "パン"}}]},
            "完了": {"checkbox": True},
        }
        notion_item = NotionDatabaseItem(id="456", properties=properties)
        shopping_item = notion_item.to_shopping_item()

        assert shopping_item.id == "456"
        assert shopping_item.name == "パン"
        assert shopping_item.checked is True

    def test_to_shopping_item_empty_title(self) -> None:
        properties = {"名前": {"title": []}, "完了": {"checkbox": False}}
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
            success=False, message="通知の送信に失敗しました", error="API key が無効です"
        )
        assert result.success is False
        assert result.message == "通知の送信に失敗しました"
        assert result.error == "API key が無効です"

    def test_notification_result_default_values(self) -> None:
        result = NotificationResult(success=True, message="成功")
        assert result.success is True
        assert result.message == "成功"
        assert result.error is None


class TestDatabaseConfig:
    def test_database_config_creation(self) -> None:
        """DatabaseConfig の作成テスト"""
        config = DatabaseConfig(
            config_id="test-id-123",
            config_name="テスト設定",
            notion_database_id="db-123",
            notion_page_id="page-123",
            is_active=True,
            description="テスト用の設定です"
        )

        assert config.config_id == "test-id-123"
        assert config.config_name == "テスト設定"
        assert config.notion_database_id == "db-123"
        assert config.notion_page_id == "page-123"
        assert config.is_active is True
        assert config.description == "テスト用の設定です"

    def test_database_config_create_new(self) -> None:
        """DatabaseConfig.create_new のテスト"""
        config = DatabaseConfig.create_new(
            config_name="新しい設定",
            notion_database_id="db-new",
            notion_page_id="page-new",
            is_active=False,
            description="新しいテスト設定"
        )

        # UUIDが生成されているか確認
        assert config.config_id is not None
        assert len(config.config_id) == 36  # UUID4の標準的な長さ
        assert config.config_name == "新しい設定"
        assert config.notion_database_id == "db-new"
        assert config.notion_page_id == "page-new"
        assert config.is_active is False
        assert config.description == "新しいテスト設定"

    def test_database_config_create_new_defaults(self) -> None:
        """DatabaseConfig.create_new のデフォルト値テスト"""
        config = DatabaseConfig.create_new(
            config_name="デフォルト設定",
            notion_database_id="db-default",
            notion_page_id="page-default"
        )

        assert config.is_active is True  # デフォルトでTrue
        assert config.description is None  # デフォルトでNone

    def test_to_dynamodb_item(self) -> None:
        """to_dynamodb_item のテスト"""
        config = DatabaseConfig(
            config_id="test-id-456",
            config_name="DynamoDB テスト",
            notion_database_id="db-456",
            notion_page_id="page-456",
            is_active=True,
            description="DynamoDB変換テスト"
        )

        item = config.to_dynamodb_item()

        expected = {
            "config_id": "test-id-456",
            "config_name": "DynamoDB テスト",
            "notion_database_id": "db-456",
            "notion_page_id": "page-456",
            "is_active": True,
            "description": "DynamoDB変換テスト"
        }
        assert item == expected

    def test_to_dynamodb_item_without_description(self) -> None:
        """to_dynamodb_item の description なしテスト"""
        config = DatabaseConfig(
            config_id="test-id-789",
            config_name="説明なし設定",
            notion_database_id="db-789",
            notion_page_id="page-789",
            is_active=False
        )

        item = config.to_dynamodb_item()

        expected = {
            "config_id": "test-id-789",
            "config_name": "説明なし設定",
            "notion_database_id": "db-789",
            "notion_page_id": "page-789",
            "is_active": False
        }
        assert item == expected
        assert "description" not in item

    def test_from_dynamodb_item(self) -> None:
        """from_dynamodb_item のテスト"""
        item = {
            "config_id": "from-db-123",
            "config_name": "データベースから",
            "notion_database_id": "db-from",
            "notion_page_id": "page-from",
            "is_active": True,
            "description": "データベースからの復元"
        }

        config = DatabaseConfig.from_dynamodb_item(item)

        assert config.config_id == "from-db-123"
        assert config.config_name == "データベースから"
        assert config.notion_database_id == "db-from"
        assert config.notion_page_id == "page-from"
        assert config.is_active is True
        assert config.description == "データベースからの復元"

    def test_from_dynamodb_item_without_description(self) -> None:
        """from_dynamodb_item の description なしテスト"""
        item = {
            "config_id": "from-db-456",
            "config_name": "説明なしデータベース設定",
            "notion_database_id": "db-no-desc",
            "notion_page_id": "page-no-desc",
            "is_active": False
        }

        config = DatabaseConfig.from_dynamodb_item(item)

        assert config.config_id == "from-db-456"
        assert config.config_name == "説明なしデータベース設定"
        assert config.description is None
