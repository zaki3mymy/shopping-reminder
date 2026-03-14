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
                "NOTIFY_API_KEY": "notify-key-123",
                "NOTIFY_API_URL": "https://example.com/prod",
            },
        ):
            config = Config()
            assert config.notion_api_key == "secret-key-123"
            assert config.notion_database_id == "database-123"
            assert config.notify_api_key == "notify-key-123"
            assert config.notify_api_url == "https://example.com/prod"

    def test_config_creation_missing_api_key(self) -> None:
        with patch.dict(
            os.environ,
            {
                "NOTION_DATABASE_ID": "database-123",
                "NOTIFY_API_KEY": "notify-key-123",
                "NOTIFY_API_URL": "https://example.com/prod",
            },
            clear=True,
        ):
            with pytest.raises(ConfigError) as exc_info:
                Config()
            assert "NOTION_API_KEY" in str(exc_info.value)

    def test_config_creation_missing_database_id(self) -> None:
        with patch.dict(
            os.environ,
            {
                "NOTION_API_KEY": "secret-key-123",
                "NOTIFY_API_KEY": "notify-key-123",
                "NOTIFY_API_URL": "https://example.com/prod",
            },
            clear=True,
        ):
            with pytest.raises(ConfigError) as exc_info:
                Config()
            assert "NOTION_DATABASE_ID" in str(exc_info.value)

    def test_config_creation_missing_notify_api_key(self) -> None:
        with patch.dict(
            os.environ,
            {
                "NOTION_API_KEY": "secret-key-123",
                "NOTION_DATABASE_ID": "database-123",
                "NOTIFY_API_URL": "https://example.com/prod",
            },
            clear=True,
        ):
            with pytest.raises(ConfigError) as exc_info:
                Config()
            assert "NOTIFY_API_KEY" in str(exc_info.value)

    def test_config_creation_missing_notify_api_url(self) -> None:
        with patch.dict(
            os.environ,
            {
                "NOTION_API_KEY": "secret-key-123",
                "NOTION_DATABASE_ID": "database-123",
                "NOTIFY_API_KEY": "notify-key-123",
            },
            clear=True,
        ):
            with pytest.raises(ConfigError) as exc_info:
                Config()
            assert "NOTIFY_API_URL" in str(exc_info.value)

    def test_config_creation_empty_env_vars(self) -> None:
        with patch.dict(
            os.environ,
            {
                "NOTION_API_KEY": "",
                "NOTION_DATABASE_ID": "database-123",
                "NOTIFY_API_KEY": "notify-key-123",
                "NOTIFY_API_URL": "https://example.com/prod",
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
                "NOTIFY_API_KEY": "notify-key-123",
                "NOTIFY_API_URL": "https://example.com/prod",
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
                "NOTIFY_API_KEY": "notify-key-123",
                "NOTIFY_API_URL": "https://example.com/prod",
            },
        ):
            config = Config()
            # 正常に作成されれば例外は発生しない
            assert config is not None

    def test_config_from_dict(self) -> None:
        config_dict = {
            "NOTION_API_KEY": "secret-key-456",
            "NOTION_DATABASE_ID": "database-456",
            "NOTIFY_API_KEY": "notify-key-456",
            "NOTIFY_API_URL": "https://example.com/prod",
        }
        config = Config.from_dict(config_dict)
        assert config.notion_api_key == "secret-key-456"
        assert config.notion_database_id == "database-456"
        assert config.notify_api_key == "notify-key-456"
        assert config.notify_api_url == "https://example.com/prod"

    def test_config_from_dict_missing_key(self) -> None:
        config_dict = {
            "NOTION_DATABASE_ID": "database-456",
            "NOTIFY_API_KEY": "notify-key-456",
            "NOTIFY_API_URL": "https://example.com/prod",
        }
        with pytest.raises(ConfigError) as exc_info:
            Config.from_dict(config_dict)
        assert "NOTION_API_KEY" in str(exc_info.value)

    def test_config_from_dict_with_integer_values(self) -> None:
        """数値が渡された場合の文字列変換テスト"""
        config_dict = {
            "NOTION_API_KEY": 123456,  # 数値
            "NOTION_DATABASE_ID": "database-456",
            "NOTIFY_API_KEY": "notify-key-456",
            "NOTIFY_API_URL": "https://example.com/prod",
        }
        config = Config.from_dict(config_dict)
        assert config.notion_api_key == "123456"  # 文字列に変換される
        assert config.notion_database_id == "database-456"

    def test_config_from_dict_with_whitespace_only_value(self) -> None:
        """空白のみの値の場合のテスト"""
        config_dict = {
            "NOTION_API_KEY": "   ",  # 空白のみ
            "NOTION_DATABASE_ID": "database-456",
            "NOTIFY_API_KEY": "notify-key-456",
            "NOTIFY_API_URL": "https://example.com/prod",
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
                "NOTIFY_API_KEY": "notify-key-123",
                "NOTIFY_API_URL": "https://example.com/prod",
            },
        ):
            config = Config()
            config_str = str(config)
            assert "secret-key-123" not in config_str
            assert "notify-key-123" not in config_str
            assert "*****" in config_str or "hidden" in config_str.lower()
            assert "database-123" in config_str
            assert "https://example.com/prod" in config_str


class TestConfigError:
    def test_config_error_creation(self) -> None:
        error = ConfigError("Test error message")
        assert str(error) == "Test error message"

    def test_config_error_inheritance(self) -> None:
        error = ConfigError("Test error")
        assert isinstance(error, Exception)
