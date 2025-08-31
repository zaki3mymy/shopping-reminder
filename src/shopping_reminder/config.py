import os
from dataclasses import dataclass
from typing import Dict, Any, List, Optional

# Lambda環境での絶対インポート
from logger import get_logger
from models import DatabaseConfig
from dynamodb_client import get_active_configs, DynamoDBError  # type: ignore

logger = get_logger(__name__)


class ConfigError(Exception):
    """設定に関するエラー"""

    pass


@dataclass
class Config:
    """アプリケーションの設定を管理するクラス"""

    notion_api_key: str
    database_configs: List[DatabaseConfig]
    dynamodb_table_name: Optional[str] = None
    dynamodb_region: str = "ap-northeast-1"

    def __init__(self) -> None:
        """環境変数から設定を読み込み"""
        logger.info("Loading configuration from environment variables")

        self.notion_api_key = self._get_required_env_var("NOTION_API_KEY")
        logger.info(f"NOTION_API_KEY loaded (length: {len(self.notion_api_key)} chars)")

        # DynamoDBテーブル名（オプション）
        self.dynamodb_table_name = os.environ.get("DYNAMODB_TABLE_NAME")
        if self.dynamodb_table_name:
            logger.info(f"DYNAMODB_TABLE_NAME: {self.dynamodb_table_name}")

        # DynamoDBリージョン（デフォルトあり）
        self.dynamodb_region = os.environ.get("DYNAMODB_REGION", "ap-northeast-1")
        logger.info(f"DYNAMODB_REGION: {self.dynamodb_region}")

        # データベース設定を取得
        self.database_configs = self._load_database_configs()
        logger.info(f"Loaded {len(self.database_configs)} database configurations")

        logger.info("Configuration loaded successfully")

    def _load_database_configs(self) -> List[DatabaseConfig]:
        """データベース設定を取得（DynamoDBまたは環境変数から）"""
        if self.dynamodb_table_name:
            # DynamoDBから設定を取得
            return self._load_from_dynamodb()
        else:
            # 環境変数から単一設定を取得（後方互換性）
            return self._load_from_env_vars()

    def _load_from_dynamodb(self) -> List[DatabaseConfig]:
        """DynamoDBからアクティブな設定を取得"""
        try:
            logger.info("Loading database configurations from DynamoDB")
            configs = get_active_configs(self.dynamodb_table_name, self.dynamodb_region)  # type: ignore

            if not configs:
                logger.warning("No active database configurations found in DynamoDB")
                raise ConfigError("No active database configurations found in DynamoDB")

            for config in configs:
                logger.info(f"Loaded config: {config.config_name} (ID: {config.config_id})")

            return configs

        except DynamoDBError as e:
            logger.exception(f"Failed to load configurations from DynamoDB: {str(e)}")
            raise ConfigError(f"Failed to load configurations from DynamoDB: {str(e)}") from e

    def _load_from_env_vars(self) -> List[DatabaseConfig]:
        """環境変数から単一設定を取得（後方互換性のため）"""
        logger.info("Loading single database configuration from environment variables")

        try:
            notion_database_id = self._get_required_env_var("NOTION_DATABASE_ID")
            notion_page_id = self._get_required_env_var("NOTION_PAGE_ID")

            logger.info(f"NOTION_DATABASE_ID: {notion_database_id}")
            logger.info(f"NOTION_PAGE_ID: {notion_page_id}")

            # 単一設定をDatabaseConfigとして作成
            config = DatabaseConfig.create_new(
                config_name="Default Configuration",
                notion_database_id=notion_database_id,
                notion_page_id=notion_page_id,
                description="Legacy single configuration from environment variables"
            )

            return [config]

        except ConfigError:
            # 環境変数も設定されていない場合
            logger.error("Neither DynamoDB table name nor legacy environment variables are configured")
            raise ConfigError(
                "Configuration not found. Set DYNAMODB_TABLE_NAME for multi-config support, "
                "or NOTION_DATABASE_ID and NOTION_PAGE_ID for legacy single-config mode."
            )

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "Config":
        """辞書から設定を作成（テスト用）"""
        config = cls.__new__(cls)  # __init__を呼ばずにインスタンスを作成

        config.notion_api_key = cls._get_required_dict_value(config_dict, "NOTION_API_KEY")

        # DynamoDB設定
        config.dynamodb_table_name = config_dict.get("DYNAMODB_TABLE_NAME")
        config.dynamodb_region = config_dict.get("DYNAMODB_REGION", "ap-northeast-1")

        # 後方互換性のため単一設定も対応
        if "NOTION_DATABASE_ID" in config_dict and "NOTION_PAGE_ID" in config_dict:
            notion_database_id = cls._get_required_dict_value(config_dict, "NOTION_DATABASE_ID")
            notion_page_id = cls._get_required_dict_value(config_dict, "NOTION_PAGE_ID")

            database_config = DatabaseConfig.create_new(
                config_name="Test Configuration",
                notion_database_id=notion_database_id,
                notion_page_id=notion_page_id,
                description="Test configuration from dictionary"
            )
            config.database_configs = [database_config]
        else:
            config.database_configs = []

        return config

    def _get_required_env_var(self, key: str) -> str:
        """必須の環境変数を取得"""
        logger.info(f"Retrieving environment variable: {key}")
        value = os.environ.get(key)
        if not value or not value.strip():
            logger.error(f"Environment variable {key} is missing or empty")
            raise ConfigError(f"Environment variable {key} is required and cannot be empty")
        logger.info(f"Environment variable {key} retrieved successfully")
        return value.strip()

    @staticmethod
    def _get_required_dict_value(config_dict: Dict[str, Any], key: str) -> str:
        """必須の辞書の値を取得"""
        if key not in config_dict:
            raise ConfigError(f"Configuration key {key} is required")
        value = config_dict[key]
        if not value or not str(value).strip():
            raise ConfigError(f"Configuration key {key} is required and cannot be empty")
        return str(value).strip()

    def __str__(self) -> str:
        """設定の文字列表現（API keyは隠す）"""
        config_names = [config.config_name for config in self.database_configs]
        return (
            f"Config("
            f"notion_api_key=***HIDDEN***, "
            f"database_configs={len(self.database_configs)} configs: {config_names}, "
            f"dynamodb_table_name={self.dynamodb_table_name}, "
            f"dynamodb_region={self.dynamodb_region})"
        )
