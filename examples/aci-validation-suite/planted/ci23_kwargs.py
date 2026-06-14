def build(**kwargs):
    host = kwargs["host"]
    port = kwargs["port"]
    return f"{host}:{port}"
