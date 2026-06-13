from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from .security import sha256_json


class AuditLog:
    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []
        self.previous_hash = "0" * 64

    def append(self, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        event = {
            "event_id": f"AUD-{len(self.events) + 1:05d}",
            "event_type": event_type,
            "timestamp": datetime.now(UTC).isoformat(),
            "payload": payload,
            "previous_hash": self.previous_hash,
        }
        event["event_hash"] = sha256_json(event)
        self.previous_hash = event["event_hash"]
        self.events.append(event)
        return event
