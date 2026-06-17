import yaml


def load_config(raw: str):
    return yaml.safe_load(raw)
