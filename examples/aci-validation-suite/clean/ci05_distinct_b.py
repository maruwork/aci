def describe(items):
    out = []
    for it in items:
        out.append(str(it))
    return ", ".join(out)
