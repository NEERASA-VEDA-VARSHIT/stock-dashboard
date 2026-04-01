from typing import Any


def round_opt(value: float | None, digits: int = 6):
    if value is None:
        return None
    return round(float(value), digits)


def cache_key(*parts: Any) -> str:
    return "v1:" + ":".join(str(p) for p in parts)
