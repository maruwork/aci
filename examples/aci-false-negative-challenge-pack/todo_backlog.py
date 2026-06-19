# CI-03 fixture: unresolved TODO/FIXME markers


def calculate_total(items):
    # TODO: handle discounted bundles
    return sum(items)


def normalize_name(raw):
    # FIXME: this still breaks on None
    return raw.strip().title()
