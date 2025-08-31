import boto3
from botocore.exceptions import ClientError, NoCredentialsError, BotoCoreError
from typing import List, Optional

from models import DatabaseConfig
from logger import get_logger

logger = get_logger(__name__)


class DynamoDBError(Exception):
    """DynamoDB操作に関するエラー"""
    pass


def _get_table(table_name: str, region: str = "ap-northeast-1"):
    """DynamoDBテーブルリソースを取得"""
    try:
        dynamodb = boto3.resource("dynamodb", region_name=region)
        return dynamodb.Table(table_name)
    except (NoCredentialsError, BotoCoreError) as e:
        logger.error(f"Failed to get DynamoDB table: {str(e)}")
        raise DynamoDBError(f"Failed to get DynamoDB table: {str(e)}") from e


def get_active_configs(table_name: str, region: str = "ap-northeast-1") -> List[DatabaseConfig]:
    """アクティブなデータベース設定を取得"""
    try:
        logger.info("Querying active database configurations")
        table = _get_table(table_name, region)

        # GSI active_configs_indexを使用してクエリ
        response = table.query(
            IndexName="active_configs_index",
            KeyConditionExpression="is_active = :active",
            ExpressionAttributeValues={":active": True}
        )

        configs = []
        for item in response.get("Items", []):
            config = DatabaseConfig.from_dynamodb_item(item)
            configs.append(config)
            logger.info(f"Retrieved config: {config.config_name} (ID: {config.config_id})")

        logger.info(f"Found {len(configs)} active configurations")
        return configs

    except ClientError as e:
        logger.exception(f"DynamoDB client error: {e.response['Error']['Code']}")
        raise DynamoDBError(f"Failed to get active configs: {str(e)}") from e
    except Exception as e:
        logger.exception(f"Unexpected error getting active configs: {str(e)}")
        raise DynamoDBError(f"Failed to get active configs: {str(e)}") from e


def get_config_by_id(config_id: str, table_name: str, region: str = "ap-northeast-1") -> Optional[DatabaseConfig]:
    """指定IDのデータベース設定を取得"""
    try:
        logger.info(f"Getting configuration by ID: {config_id}")
        table = _get_table(table_name, region)

        response = table.get_item(Key={"config_id": config_id})

        if "Item" not in response:
            logger.info(f"Configuration not found: {config_id}")
            return None

        config = DatabaseConfig.from_dynamodb_item(response["Item"])
        logger.info(f"Retrieved configuration: {config.config_name}")
        return config

    except ClientError as e:
        logger.exception(f"DynamoDB client error: {e.response['Error']['Code']}")
        raise DynamoDBError(f"Failed to get config by ID: {str(e)}") from e
    except Exception as e:
        logger.exception(f"Unexpected error getting config by ID {config_id}: {str(e)}")
        raise DynamoDBError(f"Failed to get config by ID: {str(e)}") from e


def save_config(config: DatabaseConfig, table_name: str, region: str = "ap-northeast-1") -> None:
    """データベース設定を保存"""
    try:
        logger.info(f"Saving configuration: {config.config_name} (ID: {config.config_id})")
        table = _get_table(table_name, region)

        table.put_item(Item=config.to_dynamodb_item())
        logger.info(f"Configuration saved successfully: {config.config_id}")

    except ClientError as e:
        logger.exception(f"DynamoDB client error: {e.response['Error']['Code']}")
        raise DynamoDBError(f"Failed to save config: {str(e)}") from e
    except Exception as e:
        logger.exception(f"Unexpected error saving config {config.config_id}: {str(e)}")
        raise DynamoDBError(f"Failed to save config: {str(e)}") from e


def delete_config(config_id: str, table_name: str, region: str = "ap-northeast-1") -> None:
    """データベース設定を削除"""
    try:
        logger.info(f"Deleting configuration: {config_id}")
        table = _get_table(table_name, region)

        table.delete_item(Key={"config_id": config_id})
        logger.info(f"Configuration deleted successfully: {config_id}")

    except ClientError as e:
        logger.exception(f"DynamoDB client error: {e.response['Error']['Code']}")
        raise DynamoDBError(f"Failed to delete config: {str(e)}") from e
    except Exception as e:
        logger.exception(f"Unexpected error deleting config {config_id}: {str(e)}")
        raise DynamoDBError(f"Failed to delete config: {str(e)}") from e
