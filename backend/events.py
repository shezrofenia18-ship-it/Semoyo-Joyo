"""Realtime notifications (SSE) — in-process broadcaster for admin/owner panels."""
import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("mbg.events")


class Broadcaster:
    def __init__(self) -> None:
        self._subscribers: set[asyncio.Queue] = set()

    def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=100)
        self._subscribers.add(q)
        return q

    def unsubscribe(self, q: asyncio.Queue) -> None:
        self._subscribers.discard(q)

    def publish(self, event_type: str, data: dict[str, Any]) -> None:
        payload = {"type": event_type, "data": data, "at": datetime.now(timezone.utc).isoformat()}
        for q in list(self._subscribers):
            try:
                q.put_nowait(payload)
            except asyncio.QueueFull:
                logger.warning("SSE subscriber queue full, dropping event")

    @property
    def subscriber_count(self) -> int:
        return len(self._subscribers)


broadcaster = Broadcaster()


def sse_format(payload: dict[str, Any]) -> str:
    return f"event: {payload['type']}\ndata: {json.dumps(payload, default=str)}\n\n"
