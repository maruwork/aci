"""CI02_SPAGHETTI_CODE: nesting depth >= 5 AND cyclomatic complexity >= 8."""


def process_request(items, config, mode, flags, state):
    if config:
        if mode == "a":
            for item in items:
                if item:
                    if item > 0:
                        if item < 100:
                            if flags:
                                if state.get("active"):
                                    return item
    return None
