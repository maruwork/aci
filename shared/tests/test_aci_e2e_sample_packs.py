"""E2E sample pack tests (MGEF-T39-restore).

Two example packs validate end-to-end detection accuracy:
- aci-false-negative-challenge-pack: realistic planted examples that should fire
- aci-precision-replay-pack: realistic clean counterparts that should stay quiet
"""
from __future__ import annotations

from pathlib import Path

from aci.aci_signal_collection import scan_signals

_EXAMPLES = Path(__file__).parent.parent.parent / "examples"
_FN_PACK = _EXAMPLES / "aci-false-negative-challenge-pack"
_PR_PACK = _EXAMPLES / "aci-precision-replay-pack"


def _signals(pack: Path) -> set[str]:
    return scan_signals(pack)


# ── False-negative challenge pack ─────────────────────────────────────────

def test_fn_pack_detects_parameter_cluster() -> None:
    assert "CI18_PARAMETER_CLUSTER" in _signals(_FN_PACK)


def test_fn_pack_detects_scattered_constant() -> None:
    assert "CI20_SCATTERED_CONSTANT" in _signals(_FN_PACK)


def test_fn_pack_detects_broad_exception_swallow() -> None:
    assert "CI21_BROAD_EXCEPTION_SWALLOW" in _signals(_FN_PACK)


def test_fn_pack_detects_silent_exception_return() -> None:
    assert "CI21_SILENT_EXCEPTION_RETURN" in _signals(_FN_PACK)


def test_fn_pack_detects_environment_drift() -> None:
    assert "CI25_ENVIRONMENT_DRIFT" in _signals(_FN_PACK)


def test_fn_pack_detects_race_hazard() -> None:
    assert "CI26_RACE_HAZARD" in _signals(_FN_PACK)


def test_fn_pack_detects_unsafe_yaml_load() -> None:
    assert "CI14_UNSAFE_YAML_LOAD" in _signals(_FN_PACK)


def test_fn_pack_detects_unsafe_deserialization() -> None:
    assert "CI14_UNSAFE_DESERIALIZATION" in _signals(_FN_PACK)


def test_fn_pack_detects_fire_and_forget_task() -> None:
    assert "CI22_FIRE_AND_FORGET_TASK" in _signals(_FN_PACK)


def test_fn_pack_detects_supply_chain_drift() -> None:
    assert "CI14_SUPPLY_CHAIN_DRIFT" in _signals(_FN_PACK)


def test_fn_pack_detects_long_function() -> None:
    assert "CI02_LONG_FUNCTION" in _signals(_FN_PACK)


def test_fn_pack_detects_spaghetti_code() -> None:
    assert "CI02_SPAGHETTI_CODE" in _signals(_FN_PACK)


def test_fn_pack_detects_god_class() -> None:
    assert "CI04_GOD_CLASS" in _signals(_FN_PACK)


def test_fn_pack_detects_copy_paste_code() -> None:
    assert "CI05_COPY_PASTE_CODE" in _signals(_FN_PACK)


def test_fn_pack_detects_todo_hack() -> None:
    assert "CI03_TODO_HACK" in _signals(_FN_PACK)


def test_fn_pack_detects_magic_number() -> None:
    assert "CI06_MAGIC_NUMBER" in _signals(_FN_PACK)


def test_fn_pack_detects_unused_private_symbol() -> None:
    assert "CI07_UNUSED_PRIVATE_SYMBOL" in _signals(_FN_PACK)


def test_fn_pack_detects_poltergeist() -> None:
    assert "CI12_POLTERGEIST" in _signals(_FN_PACK)


def test_fn_pack_detects_circular_import() -> None:
    assert "CI13_CIRCULAR_IMPORT" in _signals(_FN_PACK)


def test_fn_pack_detects_dynamic_code_execution() -> None:
    assert "CI14_DYNAMIC_CODE_EXECUTION" in _signals(_FN_PACK)


def test_fn_pack_detects_plaintext_secret() -> None:
    assert "CI14_PLAINTEXT_SECRET" in _signals(_FN_PACK)


def test_fn_pack_detects_insecure_http() -> None:
    assert "CI14_INSECURE_HTTP" in _signals(_FN_PACK)


def test_fn_pack_detects_subprocess_shell_true() -> None:
    assert "CI14_SUBPROCESS_SHELL_TRUE" in _signals(_FN_PACK)


def test_fn_pack_detects_resource_cleanup_gap() -> None:
    assert "CI22_RESOURCE_CLEANUP_GAP" in _signals(_FN_PACK)


def test_fn_pack_detects_contract_field_drift() -> None:
    assert "CI23_CONTRACT_FIELD_DRIFT" in _signals(_FN_PACK)


# ── Precision replay pack ─────────────────────────────────────────────────

def test_pr_pack_no_false_positive_parameter_cluster() -> None:
    assert "CI18_PARAMETER_CLUSTER" not in _signals(_PR_PACK)


def test_pr_pack_no_false_positive_broad_exception_swallow() -> None:
    assert "CI21_BROAD_EXCEPTION_SWALLOW" not in _signals(_PR_PACK)


def test_pr_pack_no_false_positive_silent_exception_return() -> None:
    assert "CI21_SILENT_EXCEPTION_RETURN" not in _signals(_PR_PACK)


def test_pr_pack_no_false_positive_environment_drift() -> None:
    assert "CI25_ENVIRONMENT_DRIFT" not in _signals(_PR_PACK)


def test_pr_pack_no_false_positive_race_hazard() -> None:
    assert "CI26_RACE_HAZARD" not in _signals(_PR_PACK)


def test_pr_pack_no_false_positive_unsafe_yaml_load() -> None:
    assert "CI14_UNSAFE_YAML_LOAD" not in _signals(_PR_PACK)


def test_pr_pack_no_false_positive_unsafe_deserialization() -> None:
    assert "CI14_UNSAFE_DESERIALIZATION" not in _signals(_PR_PACK)


def test_pr_pack_no_false_positive_fire_and_forget_task() -> None:
    assert "CI22_FIRE_AND_FORGET_TASK" not in _signals(_PR_PACK)


def test_pr_pack_no_false_positive_supply_chain_drift() -> None:
    assert "CI14_SUPPLY_CHAIN_DRIFT" not in _signals(_PR_PACK)


def test_pr_pack_no_false_positive_long_function() -> None:
    assert "CI02_LONG_FUNCTION" not in _signals(_PR_PACK)


def test_pr_pack_no_false_positive_spaghetti_code() -> None:
    assert "CI02_SPAGHETTI_CODE" not in _signals(_PR_PACK)


def test_pr_pack_no_false_positive_god_class() -> None:
    assert "CI04_GOD_CLASS" not in _signals(_PR_PACK)


def test_pr_pack_no_false_positive_copy_paste_code() -> None:
    assert "CI05_COPY_PASTE_CODE" not in _signals(_PR_PACK)


def test_pr_pack_no_false_positive_todo_hack() -> None:
    assert "CI03_TODO_HACK" not in _signals(_PR_PACK)


def test_pr_pack_no_false_positive_magic_number() -> None:
    assert "CI06_MAGIC_NUMBER" not in _signals(_PR_PACK)


def test_pr_pack_no_false_positive_unused_private_symbol() -> None:
    assert "CI07_UNUSED_PRIVATE_SYMBOL" not in _signals(_PR_PACK)


def test_pr_pack_no_false_positive_poltergeist() -> None:
    assert "CI12_POLTERGEIST" not in _signals(_PR_PACK)


def test_pr_pack_no_false_positive_circular_import() -> None:
    assert "CI13_CIRCULAR_IMPORT" not in _signals(_PR_PACK)


def test_pr_pack_no_false_positive_dynamic_code_execution() -> None:
    assert "CI14_DYNAMIC_CODE_EXECUTION" not in _signals(_PR_PACK)


def test_pr_pack_no_false_positive_plaintext_secret() -> None:
    assert "CI14_PLAINTEXT_SECRET" not in _signals(_PR_PACK)


def test_pr_pack_no_false_positive_insecure_http() -> None:
    assert "CI14_INSECURE_HTTP" not in _signals(_PR_PACK)


def test_pr_pack_no_false_positive_subprocess_shell_true() -> None:
    assert "CI14_SUBPROCESS_SHELL_TRUE" not in _signals(_PR_PACK)


def test_pr_pack_no_false_positive_resource_cleanup_gap() -> None:
    assert "CI22_RESOURCE_CLEANUP_GAP" not in _signals(_PR_PACK)


def test_pr_pack_no_false_positive_contract_field_drift() -> None:
    assert "CI23_CONTRACT_FIELD_DRIFT" not in _signals(_PR_PACK)


def test_pr_pack_is_globally_clean() -> None:
    assert _signals(_PR_PACK) == set()
