# CI-26 clean: encapsulated state in a class, no global mutation


class RequestCounter:
    def __init__(self) -> None:
        self._count = 0

    def handle(self, data: dict) -> dict:
        self._count += 1
        return {"data": data, "count": self._count}
