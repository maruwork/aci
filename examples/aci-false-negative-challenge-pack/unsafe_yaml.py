import yaml


def load_config(raw: str):
    return yaml.load(raw)
