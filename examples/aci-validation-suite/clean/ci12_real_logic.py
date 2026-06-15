"""Clean counterpart: class that adds real validation logic — not a pure delegator."""


class DatabaseWrapper:
    def __init__(self, db):
        self._db = db

    def query(self, sql):
        if not sql or not sql.strip():
            raise ValueError("empty query")
        sanitized = sql.strip()
        return self._db.query(sanitized)
