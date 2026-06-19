# CI-02 fixture: deep nesting plus branching complexity


def choose_path(a, items):
    if a:
        if a > 1:
            if a > 2:
                for item in items:
                    if item and a:
                        if item > 3 or items:
                            return item
                        elif item > 4:
                            return 0
    return -1
