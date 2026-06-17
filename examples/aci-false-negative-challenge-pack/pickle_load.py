import pickle


def restore(blob: bytes):
    return pickle.loads(blob)
