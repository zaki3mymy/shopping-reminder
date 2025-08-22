import os
import logging
from dataclasses import dataclass
from typing import Dict, Any

# ログ設定
logger = logging.getLogger(__name__)


class ConfigError(Exception):
    """設定に関するエラー"""
    pass


@dataclass
class Config:
    """アプリケーションの設定を管理するクラス"""
    notion_api_key: str
    notion_database_id: str
    notion_page_id: str

    def __init__(self) -> None:
        """環境変数から設定を読み込み"""
        logger.info("Loading configuration from environment variables")

        self.notion_api_key = self._get_required_env_var("NOTION_API_KEY")
        logger.info(f"NOTION_API_KEY loaded (length: {len(self.notion_api_key)} chars)")

        self.notion_database_id = self._get_required_env_var("NOTION_DATABASE_ID")
        logger.info(f"NOTION_DATABASE_ID: {self.notion_database_id}")

        self.notion_page_id = self._get_required_env_var("NOTION_PAGE_ID")
        logger.info(f"NOTION_PAGE_ID: {self.notion_page_id}")

        logger.info("Configuration loaded successfully")

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "Config":
        """辞書から設定を作成"""
        config = cls.__new__(cls)  # __init__を呼ばずにインスタンスを作成

        config.notion_api_key = cls._get_required_dict_value(config_dict, "NOTION_API_KEY")
        config.notion_database_id = cls._get_required_dict_value(config_dict, "NOTION_DATABASE_ID")
        config.notion_page_id = cls._get_required_dict_value(config_dict, "NOTION_PAGE_ID")

        return config

    def _get_required_env_var(self, key: str) -> str:
        """必須の環境変数を取得"""
        logger.info(f"Retrieving environment variable: {key}")
        value = os.environ.get(key)
        if not value or not value.strip():
            logger.exception(f"Environment variable {key} is missing or empty")
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
        return (f"Config("
                f"notion_api_key=***HIDDEN***, "
                f"notion_database_id={self.notion_database_id}, "
                f"notion_page_id={self.notion_page_id})")
