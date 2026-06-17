from __future__ import annotations

from pathlib import Path

from aci.aci_scan import scan_target


def write_fixture(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def clean_startup_report(tmp_path: Path) -> dict:
    write_fixture(tmp_path / "clean.py", "x = 1\n")
    return scan_target(tmp_path, "startup", "core-only", include_external_analyzers=False)


def insecure_http_fixture_line() -> str:
    return 'ENDPOINT = "' + "http" "://api.acme-corp.com/v1/charge" + '"\n'
