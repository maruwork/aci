from __future__ import annotations

from contextlib import contextmanager
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import tomllib
import warnings
import zipfile

from setuptools.build_meta import build_sdist, build_wheel


REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGING_SNAPSHOT_PATHS = (
    Path("LICENSE"),
    Path("README.md"),
    Path("pyproject.toml"),
    Path("shared/python"),
)


@contextmanager
def _pushd(path: Path):
    previous = Path.cwd()
    try:
        path.chdir()  # type: ignore[attr-defined]
    except AttributeError:
        import os

        os.chdir(path)
    try:
        yield
    finally:
        try:
            previous.chdir()  # type: ignore[attr-defined]
        except AttributeError:
            import os

            os.chdir(previous)


def _copy_packaging_snapshot(destination: Path) -> None:
    for relative in PACKAGING_SNAPSHOT_PATHS:
        source = REPO_ROOT / relative
        target = destination / relative
        if source.is_dir():
            shutil.copytree(source, target, dirs_exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)


def _build_artifacts(tmp_path: Path) -> tuple[Path, Path]:
    snapshot = tmp_path / "snapshot"
    dist_dir = tmp_path / "dist"
    _copy_packaging_snapshot(snapshot)
    dist_dir.mkdir(parents=True, exist_ok=True)
    with _pushd(snapshot):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            wheel_name = build_wheel(str(dist_dir))
            sdist_name = build_sdist(str(dist_dir))
        ignored_package_warnings = [
            warning
            for warning in caught
            if "Package would be ignored" in str(warning.message)
        ]
    assert not ignored_package_warnings
    return dist_dir / wheel_name, dist_dir / sdist_name


def _project_distribution_name() -> str:
    data = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    return str(data.get("project", {}).get("name") or "aci")


def _artifact_distribution_prefix(distribution_name: str) -> str:
    return re.sub(r"[-_.]+", "_", distribution_name).lower()


def _project_version() -> str:
    data = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    return str(data.get("project", {}).get("version") or "0.0.0")


def _assert_installed_package_check(install_target: Path) -> None:
    command = [
        sys.executable,
        "-c",
        (
            "import json, sys; "
            "from pathlib import Path; "
            "target = Path(sys.argv[1]).resolve(); "
            "sys.path.insert(0, str(target)); "
            "from aci.aci_installed_package_verification import run_installed_package_check; "
            "result = run_installed_package_check(target); "
            "checks = {item['check']: item['ok'] for item in result['checks']}; "
            "assert result['ok'] is True; "
            "assert checks['built_contract.analyzer_asset_rule'] is True; "
            "assert checks['built_contract.report_helper_module'] is True; "
            "assert checks['release_gate.version_consistency'] is True; "
            "print(json.dumps({'ok': result['ok'], 'checks': checks}, ensure_ascii=False))"
        ),
        str(install_target),
    ]
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout


def test_built_artifacts_include_packaged_analyzer_assets_and_helpers(tmp_path: Path) -> None:
    wheel_path, sdist_path = _build_artifacts(tmp_path)
    distribution_name = _project_distribution_name()
    version = _project_version()
    sdist_prefix = f"{_artifact_distribution_prefix(distribution_name)}-{version}"

    with zipfile.ZipFile(wheel_path) as wheel:
        names = set(wheel.namelist())
    assert "aci/aci_github_summary.py" in names
    assert "aci/package_assets/__init__.py" in names
    assert "aci/package_assets/analyzers/__init__.py" in names
    assert "aci/package_assets/analyzers/aci-semgrep-rules.yml" in names
    assert "aci/package_assets/report/examples/__init__.py" in names

    with tarfile.open(sdist_path, "r:gz") as sdist:
        names = set(sdist.getnames())
    assert f"{sdist_prefix}/shared/python/aci_github_summary.py" in names
    assert f"{sdist_prefix}/shared/python/package_assets/__init__.py" in names
    assert f"{sdist_prefix}/shared/python/package_assets/analyzers/__init__.py" in names
    assert f"{sdist_prefix}/shared/python/package_assets/analyzers/aci-semgrep-rules.yml" in names
    assert f"{sdist_prefix}/shared/python/package_assets/report/examples/__init__.py" in names


def test_wheel_and_sdist_target_installs_preserve_analyzer_asset_contract(tmp_path: Path) -> None:
    wheel_path, sdist_path = _build_artifacts(tmp_path)

    for artifact_path in (wheel_path, sdist_path):
        install_target = tmp_path / artifact_path.stem / "site"
        pip_cache_dir = tmp_path / artifact_path.stem / "pip-cache"
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--no-cache-dir",
                "--no-deps",
                "--no-build-isolation",
                "--target",
                str(install_target),
                str(artifact_path),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            env=os.environ | {"PIP_CACHE_DIR": str(pip_cache_dir)},
        )
        assert completed.returncode == 0, completed.stderr or completed.stdout
        _assert_installed_package_check(install_target)
