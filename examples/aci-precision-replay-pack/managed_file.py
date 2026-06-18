def read_data(path):
    handle = open(path)
    try:
        return handle.read()
    finally:
        handle.close()
