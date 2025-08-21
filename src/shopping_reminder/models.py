from dataclasses import dataclass
from typing import Dict, Any, Optional


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
