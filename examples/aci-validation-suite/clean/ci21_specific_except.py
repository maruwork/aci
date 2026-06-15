"""Clean counterpart: specific exception types caught, errors surfaced or logged."""
import json
import urllib.error
import urllib.request


def fetch_data(url):
    try:
        return urllib.request.urlopen(url).read()
    except urllib.error.URLError as exc:
        raise RuntimeError(f"fetch failed: {exc}") from exc


def parse_config(path):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid config at {path}: {exc}") from exc
