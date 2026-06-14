from datetime import datetime, timezone

def stamp():
    return datetime.now(timezone.utc)
