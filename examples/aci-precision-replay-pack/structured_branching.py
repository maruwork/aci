# CI-02 clean: nested but linear control flow


def choose_path(a):
    if a:
        if a > 1:
            if a > 2:
                if a > 3:
                    if a > 4:
                        return a
    return -1
