# CI-21 clean: narrow exception types and proper error propagation


def load_config(path: str) -> str:
    try:
        with open(path) as f:
            return f.read()
    except FileNotFoundError:
        raise


def parse_value(raw: str) -> int:
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError(f"Cannot parse {raw!r} as int") from exc
