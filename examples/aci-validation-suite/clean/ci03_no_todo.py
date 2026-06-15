"""Clean counterpart: no stale TODO/FIXME comments."""


def calculate(x, y):
    if x < 0 or y < 0:
        raise ValueError("negative values not supported")
    return x + y


def validate(data):
    if data is None:
        raise TypeError("data must not be None")
    return bool(data)
