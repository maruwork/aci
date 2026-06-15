"""Clean counterpart: same logic extracted into helpers — shallow nesting, low complexity."""


def _is_valid_item(item):
    return item and 0 < item < 100


def _apply_flags(item, flags, state):
    if flags and state.get("active"):
        return item
    return None


def process_request(items, config, mode, flags, state):
    if not config or mode != "a":
        return None
    for item in items:
        result = _apply_flags(item, flags, state) if _is_valid_item(item) else None
        if result is not None:
            return result
    return None
