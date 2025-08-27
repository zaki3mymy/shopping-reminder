import os
import pytest
from unittest.mock import patch

from src.shopping_reminder.config import Config, ConfigError


class TestConfig:
    def test_config_creation_with_env_vars(self) -> None:
        with patch.dict(
            os.environ,
            {
                "NOTION_API_KEY": "secret-key-123",
                "NOTION_DATABASE_ID": "database-123",
                "NOTION_PAGE_ID": "page-123",
            },
        ):
            config = Config()
            assert config.notion_api_key == "secret-key-123"
            assert config.notion_database_id == "database-123"
            assert config.notion_page_id == "page-123"

    def test_config_creation_missing_api_key(self) -> None:
        with patch.dict(
            os.environ,
            {"NOTION_DATABASE_ID": "database-123", "NOTION_PAGE_ID": "page-123"},
            clear=True,
        ):
            with pytest.raises(ConfigError) as exc_info:
                Config()
            assert "NOTION_API_KEY" in str(exc_info.value)

    def test_config_creation_missing_database_id(self) -> None:
        with patch.dict(
            os.environ,
            {"NOTION_API_KEY": "secret-key-123", "NOTION_PAGE_ID": "page-123"},
            clear=True,
        ):
            with pytest.raises(ConfigError) as exc_info:
                Config()
            assert "NOTION_DATABASE_ID" in str(exc_info.value)

    def test_config_creation_missing_page_id(self) -> None:
        with patch.dict(
            os.environ,
            {"NOTION_API_KEY": "secret-key-123", "NOTION_DATABASE_ID": "database-123"},
            clear=True,
        ):
            with pytest.raises(ConfigError) as exc_info:
                Config()
            assert "NOTION_PAGE_ID" in str(exc_info.value)

    def test_config_creation_empty_env_vars(self) -> None:
        with patch.dict(
            os.environ,
            {
                "NOTION_API_KEY": "",
                "NOTION_DATABASE_ID": "database-123",
                "NOTION_PAGE_ID": "page-123",
            },
        ):
            with pytest.raises(ConfigError) as exc_info:
                Config()
            assert "NOTION_API_KEY" in str(exc_info.value)

    def test_config_creation_whitespace_env_vars(self) -> None:
        with patch.dict(
            os.environ,
            {
                "NOTION_API_KEY": "  ",
                "NOTION_DATABASE_ID": "database-123",
                "NOTION_PAGE_ID": "page-123",
            },
        ):
            with pytest.raises(ConfigError) as exc_info:
                Config()
            assert "NOTION_API_KEY" in str(exc_info.value)

    def test_config_validation_all_required_fields_present(self) -> None:
        with patch.dict(
            os.environ,
            {
                "NOTION_API_KEY": "secret-key-123",
                "NOTION_DATABASE_ID": "database-123",
                "NOTION_PAGE_ID": "page-123",
            },
        ):
            config = Config()
            # 正常に作成されれば例外は発生しない
            assert config is not None

    def test_config_from_dict(self) -> None:
        config_dict = {
            "NOTION_API_KEY": "secret-key-456",
            "NOTION_DATABASE_ID": "database-456",
            "NOTION_PAGE_ID": "page-456",
        }
        config = Config.from_dict(config_dict)
        assert config.notion_api_key == "secret-key-456"
        assert config.notion_database_id == "database-456"
        assert config.notion_page_id == "page-456"

    def test_config_from_dict_missing_key(self) -> None:
        config_dict = {"NOTION_DATABASE_ID": "database-456", "NOTION_PAGE_ID": "page-456"}
        with pytest.raises(ConfigError) as exc_info:
            Config.from_dict(config_dict)
        assert "NOTION_API_KEY" in str(exc_info.value)

    def test_config_from_dict_with_integer_values(self) -> None:
        """数値が渡された場合の文字列変換テスト（行50をカバー）"""
        config_dict = {
            "NOTION_API_KEY": 123456,  # 数値
            "NOTION_DATABASE_ID": "database-456",
            "NOTION_PAGE_ID": "page-456",
        }
        config = Config.from_dict(config_dict)
        assert config.notion_api_key == "123456"  # 文字列に変換される
        assert config.notion_database_id == "database-456"
        assert config.notion_page_id == "page-456"

    def test_config_from_dict_with_whitespace_only_value(self) -> None:
        """空白のみの値の場合のテスト（行49をカバー）"""
        config_dict = {
            "NOTION_API_KEY": "   ",  # 空白のみ
            "NOTION_DATABASE_ID": "database-456",
            "NOTION_PAGE_ID": "page-456",
        }
        with pytest.raises(ConfigError) as exc_info:
            Config.from_dict(config_dict)
        assert "NOTION_API_KEY" in str(exc_info.value)
        assert "cannot be empty" in str(exc_info.value)

    def test_config_str_representation_hides_sensitive_data(self) -> None:
        with patch.dict(
            os.environ,
            {
                "NOTION_API_KEY": "secret-key-123",
                "NOTION_DATABASE_ID": "database-123",
                "NOTION_PAGE_ID": "page-123",
            },
        ):
            config = Config()
            config_str = str(config)
            assert "secret-key-123" not in config_str
            assert "*****" in config_str or "hidden" in config_str.lower()
            assert "database-123" in config_str
            assert "page-123" in config_str


class TestConfigError:
    def test_config_error_creation(self) -> None:
        error = ConfigError("Test error message")
        assert str(error) == "Test error message"

    def test_config_error_inheritance(self) -> None:
        error = ConfigError("Test error")
        assert isinstance(error, Exception)
