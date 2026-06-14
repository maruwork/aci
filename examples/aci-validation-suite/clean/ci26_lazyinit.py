_cache = None

def get_cache():
    global _cache
    if _cache is None:
        _cache = {}
    return _cache
