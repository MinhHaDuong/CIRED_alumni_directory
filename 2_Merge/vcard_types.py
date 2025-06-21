# vcard_types.py
from typing import Protocol, Any

class TypedVCard(Protocol):
    fn: Any
    n: Any
    contents: dict[str, list[Any]]

    def add(self, name: str) -> Any: ...
    def serialize(self) -> str: ...
