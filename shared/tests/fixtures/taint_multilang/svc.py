# Source -> sink taint flow fixture (intentionally vulnerable; not runtime code).
# Untrusted request input reaches eval(). A single-pattern matcher only sees
# eval(code); a taint engine proves `code` originates from request.args (the
# untrusted source). Used by test_semgrep_lane_detects_multilang_taint_flow.
from flask import request


def handler():
    user_input = request.args.get("expr")
    code = user_input
    return eval(code)  # deliberate taint sink for the fixture (not runtime code)
