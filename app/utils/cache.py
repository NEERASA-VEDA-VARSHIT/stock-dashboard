import threading
import time
from typing import Any, Optional


class TTLCache:
    def __init__(self, default_ttl_seconds: int = 60):
        self.default_ttl_seconds = default_ttl_seconds
        self._store: dict[str, tuple[float, Any]] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[Any]:
        now = time.time()
        with self._lock:
            item = self._store.get(key)
            if not item:
                return None

            expires_at, value = item
            if expires_at < now:
                self._store.pop(key, None)
                return None

            return value

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl_seconds
        expires_at = time.time() + ttl
        with self._lock:
            self._store[key] = (expires_at, value)

    def invalidate_prefix(self, prefix: str) -> None:
        with self._lock:
            keys = [k for k in self._store if k.startswith(prefix)]
            for key in keys:
                self._store.pop(key, None)

    def invalidate_prefixes(self, prefixes: list[str]) -> None:
        with self._lock:
            keys_to_drop = []
            for key in self._store:
                if any(key.startswith(prefix) for prefix in prefixes):
                    keys_to_drop.append(key)
            for key in keys_to_drop:
                self._store.pop(key, None)

    def clear(self) -> None:
        # Prefer invalidate_prefix/invalidate_prefixes to avoid unnecessary cache loss.
        with self._lock:
            self._store.clear()


api_cache = TTLCache(default_ttl_seconds=120)
