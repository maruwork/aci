# CI-21 fixtures: broad exception swallow and silent sentinel return


def load_config(path):
    try:
        return open(path).read()
    except Exception:
        pass  # CI21_BROAD_EXCEPTION_SWALLOW: swallows without logging or re-raising


def parse_value(raw):
    try:
        return int(raw)
    except Exception:
        return None  # CI21_SILENT_EXCEPTION_RETURN: silently returns None on failure
