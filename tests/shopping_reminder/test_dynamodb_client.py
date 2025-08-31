import uuid
from unittest.mock import Mock, patch
from botocore.exceptions import ClientError
import pytest

from src.shopping_reminder.dynamodb_client import (
    get_active_configs,
    get_config_by_id,
    save_config,
    delete_config,
    DynamoDBError,
    _get_table
)
from src.shopping_reminder.models import DatabaseConfig


class TestDynamoDBClient:
    """DynamoDB操作関数のテスト"""

    @patch("src.shopping_reminder.dynamodb_client.boto3.resource")
    def test_get_table_success(self, mock_boto3_resource: Mock) -> None:
        """テーブル取得の成功テスト"""
        mock_dynamodb = Mock()
        mock_table = Mock()
        mock_dynamodb.Table.return_value = mock_table
        mock_boto3_resource.return_value = mock_dynamodb

        result = _get_table("test-table", "us-east-1")

        assert result == mock_table
        mock_boto3_resource.assert_called_once_with("dynamodb", region_name="us-east-1")
        mock_dynamodb.Table.assert_called_once_with("test-table")

    @patch("src.shopping_reminder.dynamodb_client.boto3.resource")
    def test_get_table_error(self, mock_boto3_resource: Mock) -> None:
        """テーブル取得のエラーテスト"""
        from botocore.exceptions import BotoCoreError

        mock_boto3_resource.side_effect = BotoCoreError()

        with pytest.raises(DynamoDBError, match="Failed to get DynamoDB table"):
            _get_table("test-table")

    @patch("src.shopping_reminder.dynamodb_client._get_table")
    def test_get_active_configs_success(self, mock_get_table: Mock) -> None:
        """アクティブ設定取得の成功テスト"""
        # モックテーブルの設定
        mock_table = Mock()
        mock_table.query.return_value = {
            "Items": [
                {
                    "config_id": "test-id-1",
                    "config_name": "買い物リスト",
                    "notion_database_id": "db-123",
                    "notion_page_id": "page-123",
                    "is_active": True
                },
                {
                    "config_id": "test-id-2",
                    "config_name": "掃除用品",
                    "notion_database_id": "db-456",
                    "notion_page_id": "page-456",
                    "is_active": True,
                    "description": "掃除用品チェックリスト"
                }
            ]
        }
        mock_get_table.return_value = mock_table

        # テスト実行
        configs = get_active_configs("test-table")

        # 検証
        assert len(configs) == 2
        assert configs[0].config_id == "test-id-1"
        assert configs[0].config_name == "買い物リスト"
        assert configs[0].notion_database_id == "db-123"
        assert configs[0].notion_page_id == "page-123"
        assert configs[0].is_active is True
        assert configs[0].description is None

        assert configs[1].config_id == "test-id-2"
        assert configs[1].config_name == "掃除用品"
        assert configs[1].description == "掃除用品チェックリスト"

        # モックの呼び出し確認
        mock_get_table.assert_called_once_with("test-table", "ap-northeast-1")
        mock_table.query.assert_called_once_with(
            IndexName="active_configs_index",
            KeyConditionExpression="is_active = :active",
            ExpressionAttributeValues={":active": True}
        )

    @patch("src.shopping_reminder.dynamodb_client._get_table")
    def test_get_active_configs_empty(self, mock_get_table: Mock) -> None:
        """アクティブ設定が空の場合のテスト"""
        mock_table = Mock()
        mock_table.query.return_value = {"Items": []}
        mock_get_table.return_value = mock_table

        configs = get_active_configs("test-table")

        assert len(configs) == 0

    @patch("src.shopping_reminder.dynamodb_client._get_table")
    def test_get_active_configs_client_error(self, mock_get_table: Mock) -> None:
        """アクティブ設定取得のClientErrorテスト"""
        mock_table = Mock()
        mock_table.query.side_effect = ClientError(
            error_response={"Error": {"Code": "ValidationException"}},
            operation_name="Query"
        )
        mock_get_table.return_value = mock_table

        with pytest.raises(DynamoDBError, match="Failed to get active configs"):
            get_active_configs("test-table")

    @patch("src.shopping_reminder.dynamodb_client._get_table")
    def test_get_config_by_id_found(self, mock_get_table: Mock) -> None:
        """ID指定での設定取得（見つかった場合）"""
        test_id = str(uuid.uuid4())
        mock_table = Mock()
        mock_table.get_item.return_value = {
            "Item": {
                "config_id": test_id,
                "config_name": "テスト設定",
                "notion_database_id": "db-test",
                "notion_page_id": "page-test",
                "is_active": True
            }
        }
        mock_get_table.return_value = mock_table

        config = get_config_by_id(test_id, "test-table")

        assert config is not None
        assert config.config_id == test_id
        assert config.config_name == "テスト設定"
        mock_table.get_item.assert_called_once_with(Key={"config_id": test_id})

    @patch("src.shopping_reminder.dynamodb_client._get_table")
    def test_get_config_by_id_not_found(self, mock_get_table: Mock) -> None:
        """ID指定での設定取得（見つからない場合）"""
        mock_table = Mock()
        mock_table.get_item.return_value = {}
        mock_get_table.return_value = mock_table

        config = get_config_by_id("non-existent-id", "test-table")

        assert config is None

    @patch("src.shopping_reminder.dynamodb_client._get_table")
    def test_save_config_success(self, mock_get_table: Mock) -> None:
        """設定保存の成功テスト"""
        mock_table = Mock()
        mock_get_table.return_value = mock_table

        config = DatabaseConfig.create_new(
            config_name="新しい設定",
            notion_database_id="db-new",
            notion_page_id="page-new",
            description="新しいテスト設定"
        )

        # エラーが発生しないことを確認
        save_config(config, "test-table")

        mock_table.put_item.assert_called_once_with(Item=config.to_dynamodb_item())

    @patch("src.shopping_reminder.dynamodb_client._get_table")
    def test_save_config_client_error(self, mock_get_table: Mock) -> None:
        """設定保存のClientErrorテスト"""
        mock_table = Mock()
        mock_table.put_item.side_effect = ClientError(
            error_response={"Error": {"Code": "ValidationException"}},
            operation_name="PutItem"
        )
        mock_get_table.return_value = mock_table

        config = DatabaseConfig.create_new(
            config_name="新しい設定",
            notion_database_id="db-new",
            notion_page_id="page-new"
        )

        with pytest.raises(DynamoDBError, match="Failed to save config"):
            save_config(config, "test-table")

    @patch("src.shopping_reminder.dynamodb_client._get_table")
    def test_delete_config_success(self, mock_get_table: Mock) -> None:
        """設定削除の成功テスト"""
        mock_table = Mock()
        mock_get_table.return_value = mock_table

        test_id = str(uuid.uuid4())

        # エラーが発生しないことを確認
        delete_config(test_id, "test-table")

        mock_table.delete_item.assert_called_once_with(Key={"config_id": test_id})

    @patch("src.shopping_reminder.dynamodb_client._get_table")
    def test_delete_config_client_error(self, mock_get_table: Mock) -> None:
        """設定削除のClientErrorテスト"""
        mock_table = Mock()
        mock_table.delete_item.side_effect = ClientError(
            error_response={"Error": {"Code": "ResourceNotFoundException"}},
            operation_name="DeleteItem"
        )
        mock_get_table.return_value = mock_table

        test_id = str(uuid.uuid4())

        with pytest.raises(DynamoDBError, match="Failed to delete config"):
            delete_config(test_id, "test-table")

    def test_get_active_configs_with_custom_region(self) -> None:
        """カスタムリージョンでのテスト"""
        with patch("src.shopping_reminder.dynamodb_client._get_table") as mock_get_table:
            mock_table = Mock()
            mock_table.query.return_value = {"Items": []}
            mock_get_table.return_value = mock_table

            get_active_configs("test-table", "eu-west-1")

            mock_get_table.assert_called_once_with("test-table", "eu-west-1")
