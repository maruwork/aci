def tally(a, b):
    total = a * b
    total += a
    total -= b
    if total > 0:
        total *= 2
    return total
