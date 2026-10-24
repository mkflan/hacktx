"""Bounded in-memory TTL cache for validated LLM responses.

Keys hash the actual content (user record, preferences, idea/project, resource bank, prompt
version, model and mode), so a profile change invalidates by content without any database
revision column. Lost on restart; two identical simultaneous requests may both call the LLM.
"""

import copy
import hashlib
import json
import threading
import time
from collections import OrderedDict
from collections.abc import Callable
from typing import Any


def content_key(**parts: Any) -> str:
    canonical = json.dumps(parts, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class TTLCache:
    def __init__(
        self,
        max_entries: int = 100,
        ttl_seconds: float = 900.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._max = max_entries
        self._ttl = ttl_seconds
        self._clock = clock
        self._items: OrderedDict[str, tuple[float, Any]] = OrderedDict()
        self._lock = threading.Lock()

    def get(self, key: str) -> Any | None:
        with self._lock:
            item = self._items.get(key)
            if item is None:
                return None
            expires_at, value = item
            if self._clock() >= expires_at:
                del self._items[key]
                return None
            self._items.move_to_end(key)
            return copy.deepcopy(value)

    def set(self, key: str, value: Any) -> None:
        if self._max <= 0:
            return
        with self._lock:
            self._items[key] = (self._clock() + self._ttl, copy.deepcopy(value))
            self._items.move_to_end(key)
            while len(self._items) > self._max:
                self._items.popitem(last=False)

    def __len__(self) -> int:
        return len(self._items)
