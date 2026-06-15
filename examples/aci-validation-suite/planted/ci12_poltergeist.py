"""CI12_POLTERGEIST: wrapper class that only delegates — adds no logic of its own."""


class DatabaseWrapper:
    def __init__(self, db):
        self._db = db

    def query(self, sql):
        return self._db.query(sql)
