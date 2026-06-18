#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cross-platform wheel/sdist verification helper for ACI CI flows."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import subprocess
import sys
import tomllib


def _venv_bin_dir(venv_root: Path) -> Path:
    return venv_root / ("Scripts" if os.name == "nt" else "bin")


def _venv_executable(venv_root: Path, name: str) -> Path:
    suffix = ".exe" if os.name == "nt" else ""
    return _venv_bin_dir(venv_root) / f"{name}{suffix}"


def _project_distribution_name() -> str:
    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        return "aci"
    data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    name = str(data.get("project", {}).get("name") or "").strip()
    return name or "aci"


def _artifact_distribution_prefix(distribution_name: str) -> str:
    return re.sub(r"[-_.]+", "_", distribution_name).lower()


def _workspace_temp_env(outdir: Path) -> dict[str, str]:
    temp_root = (outdir.parent / "tmp").resolve()
    temp_root.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    temp_value = str(temp_root)
    env["TMP"] = temp_value
    env["TEMP"] = temp_value
    env["TMPDIR"] = temp_value
    return env


def _build_distribution(kind: str, outdir: Path) -> Path:
    outdir.mkdir(parents=True, exist_ok=True)
    build_args = [sys.executable, "-m", "build", "--no-isolation", f"--{kind}", "--outdir", str(outdir)]
    subprocess.run(build_args, check=True, env=_workspace_temp_env(outdir))
    distribution_name = _project_distribution_name()
    artifact_prefix = _artifact_distribution_prefix(distribution_name)
    pattern = f"{artifact_prefix}-*.whl" if kind == "wheel" else f"{artifact_prefix}-*.tar.gz"
    artifact = next(outdir.glob(pattern), None)
    if artifact is None:
        raise FileNotFoundError(f"No {kind} artifact found in {outdir}")
    return artifact


def verify_distribution(kind: str, outdir: Path) -> int:
    artifact = _build_distribution(kind, outdir)
    venv_root = outdir.parent / f".venv-{kind}-check"
    env = _workspace_temp_env(outdir)
    subprocess.run([sys.executable, "-m", "venv", str(venv_root)], check=True, env=env)
    pip_exe = _venv_executable(venv_root, "pip")
    aci_exe = _venv_executable(venv_root, "aci")
    subprocess.run([str(pip_exe), "install", str(artifact)], check=True, env=env)
    for command in ("automation-smoke", "installed-package-check", "fixture-check"):
        subprocess.run([str(aci_exe), command], check=True, env=env)
    print(f"verified {kind}: {artifact.name}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify ACI wheel/sdist install in a clean venv.")
    parser.add_argument("--kind", choices=["wheel", "sdist"], required=True)
    parser.add_argument("--outdir", type=Path, default=Path("dist-ci"))
    args = parser.parse_args()
    return verify_distribution(args.kind, args.outdir)


if __name__ == "__main__":
    raise SystemExit(main())
