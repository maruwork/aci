"""CI21_BROAD_EXCEPTION_SWALLOW / CI21_SILENT_EXCEPTION_RETURN."""


def fetch_data(url):
    try:
        import urllib.request
        return urllib.request.urlopen(url).read()
    except Exception:
        pass


def parse_config(path):
    try:
        import json
        with open(path) as f:
            return json.load(f)
    except Exception:
        return None
