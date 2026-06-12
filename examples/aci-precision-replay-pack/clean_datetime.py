# CI-25 clean: timezone-aware datetime (not matched by nondeterminism detector)
from datetime import datetime, timezone


def get_timestamp() -> datetime:
    return datetime.now(timezone.utc)


def get_seed(base: int) -> int:
    return base * 31 + 17
