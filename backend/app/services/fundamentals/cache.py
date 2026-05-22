"""Simple in-memory TTL cache for the fundamentals provider layer.

Module-level singletons because the router constructs a new provider
instance per `get_provider()` call (the LLM provider pattern we
mirror does the same), so per-instance caching would have zero hit
rate. Module-level keeps the cache alive across requests within a
process.

Trade-off: per-process. Railway can scale horizontally; in that case
each instance caches independently. Acceptable for an operator-facing
tool. Swap to Redis if we ever scale past one backend instance under
real load.

No external dependency — `time.monotonic()` is monotonic across the
process so we don't have to worry about wall-clock jumps.
"""
from __future__ import annotations

import time
from threading import Lock
from typing import Any


class TTLCache:
    """Thread-safe TTL cache with a single TTL applied to all entries."""

    def __init__(self, ttl_seconds: float) -> None:
        self._store: dict[str, tuple[float, Any]] = {}
        self._ttl = ttl_seconds
        self._lock = Lock()

    def get(self, key: str) -> Any | None:
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            expires_at, value = entry
            if time.monotonic() > expires_at:
                # Lazy eviction — fine for this volume.
                del self._store[key]
                return None
            return value

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            self._store[key] = (time.monotonic() + self._ttl, value)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._store)


# Module-level singletons keyed by purpose. TTL choices:
#   - Fundamentals: 6h — financials don't change intraday; even on
#     earnings day, a 6h stale read is acceptable for a research tool.
#   - Peers list: 24h — sector membership rarely changes.
#   - Peer quotes: 5 minutes — close enough to "live" for a research
#     workspace without burning the free-tier rate budget on every
#     page load.
FUNDAMENTALS_CACHE = TTLCache(ttl_seconds=6 * 3600)
PEERS_LIST_CACHE = TTLCache(ttl_seconds=24 * 3600)
PEER_QUOTE_CACHE = TTLCache(ttl_seconds=5 * 60)
