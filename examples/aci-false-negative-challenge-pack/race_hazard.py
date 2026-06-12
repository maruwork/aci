# CI-26 fixture: global state mutation
_request_count = 0


def handle_request(data):
    global _request_count
    _request_count += 1
    return {"data": data, "count": _request_count}
