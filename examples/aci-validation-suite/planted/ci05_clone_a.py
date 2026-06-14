def compute(x, y):
    result = x * y
    result += x
    result -= y
    if result > 0:
        result *= 2
    return result
