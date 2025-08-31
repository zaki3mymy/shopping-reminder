from dataclasses import dataclass
from typing import Dict, Any, Optional
import uuid


@dataclass
class DatabaseConfig:
    """データベース設定を管理するモデル"""
    config_id: str
    config_name: str
    notion_database_id: str
    notion_page_id: str
    is_active: bool
    description: Optional[str] = None

    @classmethod
    def create_new(
        cls,
        config_name: str,
        notion_database_id: str,
        notion_page_id: str,
        is_active: bool = True,
        description: Optional[str] = None,
    ) -> "DatabaseConfig":
        """新しいデータベース設定を作成"""
        return cls(
            config_id=str(uuid.uuid4()),
            config_name=config_name,
            notion_database_id=notion_database_id,
            notion_page_id=notion_page_id,
            is_active=is_active,
            description=description,
        )

    def to_dynamodb_item(self) -> Dict[str, Any]:
        """DynamoDB用のアイテム形式に変換"""
        item = {
            "config_id": self.config_id,
            "config_name": self.config_name,
            "notion_database_id": self.notion_database_id,
            "notion_page_id": self.notion_page_id,
            "is_active": self.is_active,
        }
        if self.description:
            item["description"] = self.description
        return item

    @classmethod
    def from_dynamodb_item(cls, item: Dict[str, Any]) -> "DatabaseConfig":
        """DynamoDBアイテムから DatabaseConfig を作成"""
        return cls(
            config_id=item["config_id"],
            config_name=item["config_name"],
            notion_database_id=item["notion_database_id"],
            notion_page_id=item["notion_page_id"],
            is_active=item["is_active"],
            description=item.get("description"),
        )


@dataclass
class ShoppingItem:
    id: str
    name: str
    checked: bool

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ShoppingItem):
            return NotImplemented
        return self.id == other.id and self.name == other.name and self.checked == other.checked


@dataclass
class NotionDatabaseItem:
    id: str
    properties: Dict[str, Any]

    def to_shopping_item(self) -> ShoppingItem:
        name_property = self.properties["名前"]
        title_array = name_property["title"]
        name = title_array[0]["text"]["content"] if title_array else ""

        checked = self.properties["完了"]["checkbox"]

        return ShoppingItem(id=self.id, name=name, checked=checked)


@dataclass
class NotificationResult:
    success: bool
    message: str
    error: Optional[str] = None
