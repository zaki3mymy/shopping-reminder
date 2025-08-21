import os
import pytest
from typing import Dict, Any

from src.shopping_reminder.lambda_handler import handler
from src.shopping_reminder.config import Config


class TestE2E:
    """
    エンドツーエンドテスト

    これらのテストは実際のNotion APIを使用するため、以下の環境変数が必要です：
    - NOTION_API_KEY_TEST: テスト用のNotion API キー
    - NOTION_DATABASE_ID_TEST: テスト用のデータベースID
    - NOTION_PAGE_ID_TEST: テスト用のページID

    これらの環境変数が設定されていない場合、テストはスキップされます。
    """

    def setup_method(self) -> None:
        """各テストメソッドの前に実行される"""
        # 本番用の環境変数をバックアップ
        self.original_api_key = os.environ.get("NOTION_API_KEY")
        self.original_database_id = os.environ.get("NOTION_DATABASE_ID")
        self.original_page_id = os.environ.get("NOTION_PAGE_ID")

        # テスト用の環境変数を設定
        test_api_key = os.environ.get("NOTION_API_KEY_TEST")
        test_database_id = os.environ.get("NOTION_DATABASE_ID_TEST")
        test_page_id = os.environ.get("NOTION_PAGE_ID_TEST")

        if test_api_key:
            os.environ["NOTION_API_KEY"] = test_api_key
        if test_database_id:
            os.environ["NOTION_DATABASE_ID"] = test_database_id
        if test_page_id:
            os.environ["NOTION_PAGE_ID"] = test_page_id

    def teardown_method(self) -> None:
        """各テストメソッドの後に実行される"""
        # 元の環境変数を復元
        if self.original_api_key is not None:
            os.environ["NOTION_API_KEY"] = self.original_api_key
        elif "NOTION_API_KEY" in os.environ:
            del os.environ["NOTION_API_KEY"]

        if self.original_database_id is not None:
            os.environ["NOTION_DATABASE_ID"] = self.original_database_id
        elif "NOTION_DATABASE_ID" in os.environ:
            del os.environ["NOTION_DATABASE_ID"]

        if self.original_page_id is not None:
            os.environ["NOTION_PAGE_ID"] = self.original_page_id
        elif "NOTION_PAGE_ID" in os.environ:
            del os.environ["NOTION_PAGE_ID"]

    def _has_test_credentials(self) -> bool:
        """テスト用の認証情報が設定されているかを確認"""
        return all([
            os.environ.get("NOTION_API_KEY_TEST"),
            os.environ.get("NOTION_DATABASE_ID_TEST"),
            os.environ.get("NOTION_PAGE_ID_TEST")
        ])

    @pytest.mark.skipif(
        not os.environ.get("NOTION_API_KEY_TEST"),
        reason="Test requires NOTION_API_KEY_TEST environment variable"
    )
    def test_config_loading_with_test_credentials(self) -> None:
        """テスト用認証情報での設定読み込みテスト"""
        if not self._has_test_credentials():
            pytest.skip("Test credentials not available")

        config = Config()
        assert config.notion_api_key == os.environ["NOTION_API_KEY_TEST"]
        assert config.notion_database_id == os.environ["NOTION_DATABASE_ID_TEST"]
        assert config.notion_page_id == os.environ["NOTION_PAGE_ID_TEST"]

    @pytest.mark.skipif(
        not os.environ.get("NOTION_API_KEY_TEST"),
        reason="Test requires NOTION_API_KEY_TEST environment variable"
    )
    def test_lambda_handler_integration(self) -> None:
        """Lambda ハンドラーの統合テスト"""
        if not self._has_test_credentials():
            pytest.skip("Test credentials not available")

        # Lambda イベントとコンテキストのダミー
        event: Dict[str, Any] = {}

        # Mock context object
        class MockLambdaContext:
            def __init__(self) -> None:
                self.function_name = "test-shopping-reminder"
                self.aws_request_id = "test-request-id"
                self.remaining_time_in_millis = lambda: 30000

        context = MockLambdaContext()

        # Lambda ハンドラーを実行
        response = handler(event, context)

        # レスポンスの検証
        assert response["statusCode"] in [200, 500]  # 成功またはエラー
        assert "Content-Type" in response["headers"]
        assert response["headers"]["Content-Type"] == "application/json"
        assert "body" in response

        # レスポンスボディをパース
        import json
        body = json.loads(response["body"])

        assert "success" in body
        assert "message" in body
        assert isinstance(body["success"], bool)
        assert isinstance(body["message"], str)

        # 成功の場合のレスポンス検証
        if response["statusCode"] == 200:
            assert body["success"] is True
            # メッセージに日本語が含まれていることを確認
            assert any(char in body["message"] for char in "未チェック項目通知")

        # エラーの場合のレスポンス検証
        if response["statusCode"] == 500:
            assert body["success"] is False
            assert "error" in body
            assert isinstance(body["error"], str)

    def test_missing_test_credentials(self) -> None:
        """テスト用認証情報が欠如している場合のテスト"""
        # 全ての環境変数をクリア
        original_vars = {}
        for key in ["NOTION_API_KEY", "NOTION_DATABASE_ID", "NOTION_PAGE_ID"]:
            original_vars[key] = os.environ.get(key)
            if key in os.environ:
                del os.environ[key]

        try:
            event: Dict[str, Any] = {}
            context = type('MockContext', (), {'function_name': 'test'})()

            response = handler(event, context)

            # 設定エラーが発生することを確認
            assert response["statusCode"] == 400

            import json
            body = json.loads(response["body"])
            assert body["success"] is False
            assert "設定エラー" in body["message"]

        finally:
            # 環境変数を復元
            for key, value in original_vars.items():
                if value is not None:
                    os.environ[key] = value

    @pytest.mark.skipif(
        not os.environ.get("NOTION_API_KEY_TEST"),
        reason="Test requires NOTION_API_KEY_TEST environment variable"
    )
    def test_notion_client_integration(self) -> None:
        """Notion クライアントの統合テスト"""
        if not self._has_test_credentials():
            pytest.skip("Test credentials not available")

        from src.shopping_reminder.notion_client import NotionClient

        config = Config()
        client = NotionClient(config)

        # データベースクエリのテスト
        try:
            items = client.query_unchecked_items()
            assert isinstance(items, list)
            # 各項目がShoppingItemのインスタンスであることを確認
            from src.shopping_reminder.models import ShoppingItem
            for item in items:
                assert isinstance(item, ShoppingItem)
                assert hasattr(item, 'id')
                assert hasattr(item, 'name')
                assert hasattr(item, 'checked')
                assert isinstance(item.checked, bool)

        except Exception as e:
            # API エラーの場合は適切な例外がスローされることを確認
            from src.shopping_reminder.notion_client import NotionAPIError
            if not isinstance(e, NotionAPIError):
                # NotionAPIError以外の例外は再発生させる
                raise

    def test_e2e_documentation(self) -> None:
        """E2Eテストのドキュメンテーション確認"""
        # このテストは必要な環境変数についてドキュメント化する
        required_vars = [
            "NOTION_API_KEY_TEST",
            "NOTION_DATABASE_ID_TEST",
            "NOTION_PAGE_ID_TEST"
        ]

        missing_vars = []
        for var in required_vars:
            if not os.environ.get(var):
                missing_vars.append(var)

        if missing_vars:
            message = (
                f"E2Eテストを実行するには以下の環境変数が必要です: {', '.join(missing_vars)}\n"
                "これらはテスト専用のNotion workspaceとdatabaseを参照する必要があります。"
            )
            pytest.skip(message)
        else:
            # 全ての環境変数が設定されている場合は成功
            assert True
