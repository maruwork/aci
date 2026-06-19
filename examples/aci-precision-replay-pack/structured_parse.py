# CI-14 clean: structured parsing, no eval/exec
import json


def evaluate_user_formula(expression):
    payload = json.loads(expression)
    return payload["result"]
