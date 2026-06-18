from __future__ import annotations

import importlib.util
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "shared" / "tools" / "aci_verify_distribution.py"
SPEC = importlib.util.spec_from_file_location("aci_verify_distribution_tool", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
verify_distribution_tool = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verify_distribution_tool)


def test_build_distribution_uses_project_name_and_workspace_temp_env(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "pyproject.toml").write_text(
        """
[project]
name = "ac-inspector"
version = "0.1.3"
""".strip(),
        encoding="utf-8",
    )
    outdir = tmp_path / "workspace" / "dist"
    outdir.mkdir(parents=True, exist_ok=True)
    artifact = outdir / "ac_inspector-0.1.3.whl"
    artifact.write_bytes(b"wheel")

    captured: dict[str, object] = {}

    def _fake_run(args, check, env):
        captured["args"] = list(args)
        captured["env"] = dict(env)

    monkeypatch.setattr(verify_distribution_tool.subprocess, "run", _fake_run)

    result = verify_distribution_tool._build_distribution("wheel", outdir)

    assert result == artifact
    assert "--no-isolation" in captured["args"]
    env = captured["env"]
    expected_tmp = str((outdir.parent / "tmp").resolve())
    assert env["TMP"] == expected_tmp
    assert env["TEMP"] == expected_tmp
    assert env["TMPDIR"] == expected_tmp


def test_artifact_distribution_prefix_normalizes_pypi_distribution_names() -> None:
    assert verify_distribution_tool._artifact_distribution_prefix("ac-inspector") == "ac_inspector"
    assert verify_distribution_tool._artifact_distribution_prefix("ACI.Public") == "aci_public"
