from __future__ import annotations

import json
from typing import Any


class DuplicateMemberError(ValueError):
    def __init__(self, member: str):
        super().__init__(f"duplicate object member: {member}")
        self.member = member


def strict_json_loads(text: str) -> Any:
    def object_from_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in pairs:
            if key in value:
                raise DuplicateMemberError(key)
            value[key] = item
        return value

    return json.loads(text, object_pairs_hook=object_from_pairs)
