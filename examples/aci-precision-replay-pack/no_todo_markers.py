# CI-03 clean: resolved work with no stale marker comments


def calculate_total(items):
    return sum(items)


def normalize_name(raw):
    if raw is None:
        raise TypeError("raw must not be None")
    return raw.strip().title()
