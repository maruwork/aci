#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bounded working-mirror sync checks for ACI."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class MirrorPairCheck:
    official: str
    mirror: str
    exists_official: bool
    exists_mirror: bool

    @property
    def ok(self) -> bool:
        return self.exists_official and self.exists_mirror


@dataclass(frozen=True)
class MirrorSyncResult:
    ok: bool
    checks: tuple[MirrorPairCheck, ...]
    mode: str = "monorepo"
    reason: str | None = None

    def as_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "ok": self.ok,
            "mode": self.mode,
            "checks": [asdict(item) | {"ok": item.ok} for item in self.checks],
        }
        if self.reason is not None:
            payload["reason"] = self.reason
        return payload


REQUIRED_MIRROR_PAIRS: tuple[tuple[str, str], ...] = (
    (
        "common/aci/roadmap/aci-independence-goal.md",
        "common/refernce/aci-independence-goal.md",
    ),
    (
        "common/aci/roadmap/aci-independence-path.md",
        "common/refernce/aci-independence-path.md",
    ),
    (
        "common/aci/roadmap/aci-independence-checkpoints.md",
        "common/refernce/aci-independence-checkpoints.md",
    ),
    (
        "common/aci/tasks/aci-independence-task-board.md",
        "common/refernce/aci-independence-tasks.md",
    ),
    (
        "common/aci/design/aci-independence-basic-design.md",
        "common/refernce/aci-independence-design.md",
    ),
    (
        "common/aci/roadmap/aci-generic-hardening-goal.md",
        "common/refernce/aci-generic-hardening-goal.md",
    ),
    (
        "common/aci/roadmap/aci-generic-hardening-path.md",
        "common/refernce/aci-generic-hardening-path.md",
    ),
    (
        "common/aci/roadmap/aci-generic-hardening-checkpoints.md",
        "common/refernce/aci-generic-hardening-checkpoints.md",
    ),
    (
        "common/aci/tasks/aci-generic-hardening-task-board.md",
        "common/refernce/aci-generic-hardening-tasks.md",
    ),
    (
        "common/aci/design/aci-generic-hardening-design.md",
        "common/refernce/aci-generic-hardening-design.md",
    ),
    (
        "common/aci/roadmap/aci-mirror-governance-goal.md",
        "common/refernce/aci-mirror-governance-goal.md",
    ),
    (
        "common/aci/roadmap/aci-mirror-governance-path.md",
        "common/refernce/aci-mirror-governance-path.md",
    ),
    (
        "common/aci/roadmap/aci-mirror-governance-checkpoints.md",
        "common/refernce/aci-mirror-governance-checkpoints.md",
    ),
    (
        "common/aci/tasks/aci-mirror-governance-task-board.md",
        "common/refernce/aci-mirror-governance-tasks.md",
    ),
    (
        "common/aci/design/aci-mirror-governance-design.md",
        "common/refernce/aci-mirror-governance-design.md",
    ),
    (
        "common/aci/roadmap/aci-public-adoption-readiness-goal.md",
        "common/refernce/aci-public-adoption-readiness-goal.md",
    ),
    (
        "common/aci/roadmap/aci-public-adoption-readiness-path.md",
        "common/refernce/aci-public-adoption-readiness-path.md",
    ),
    (
        "common/aci/roadmap/aci-public-adoption-readiness-checkpoints.md",
        "common/refernce/aci-public-adoption-readiness-checkpoints.md",
    ),
    (
        "common/aci/tasks/aci-public-adoption-readiness-task-board.md",
        "common/refernce/aci-public-adoption-readiness-tasks.md",
    ),
    (
        "common/aci/design/aci-public-adoption-readiness-design.md",
        "common/refernce/aci-public-adoption-readiness-design.md",
    ),
    (
        "common/aci/roadmap/aci-public-release-readiness-goal.md",
        "common/refernce/aci-public-release-readiness-goal.md",
    ),
    (
        "common/aci/roadmap/aci-public-release-readiness-path.md",
        "common/refernce/aci-public-release-readiness-path.md",
    ),
    (
        "common/aci/roadmap/aci-public-release-readiness-checkpoints.md",
        "common/refernce/aci-public-release-readiness-checkpoints.md",
    ),
    (
        "common/aci/tasks/aci-public-release-readiness-task-board.md",
        "common/refernce/aci-public-release-readiness-tasks.md",
    ),
    (
        "common/aci/design/aci-public-release-readiness-design.md",
        "common/refernce/aci-public-release-readiness-design.md",
    ),
    (
        "common/aci/roadmap/aci-veil-parity-goal.md",
        "common/refernce/aci-veil-parity-goal.md",
    ),
    (
        "common/aci/roadmap/aci-veil-parity-path.md",
        "common/refernce/aci-veil-parity-path.md",
    ),
    (
        "common/aci/roadmap/aci-veil-parity-checkpoints.md",
        "common/refernce/aci-veil-parity-checkpoints.md",
    ),
    (
        "common/aci/tasks/aci-veil-parity-task-board.md",
        "common/refernce/aci-veil-parity-tasks.md",
    ),
    (
        "common/aci/design/aci-veil-parity-design.md",
        "common/refernce/aci-veil-parity-design.md",
    ),
    (
        "common/aci/roadmap/aci-publication-gate-goal.md",
        "common/refernce/aci-publication-gate-goal.md",
    ),
    (
        "common/aci/roadmap/aci-publication-gate-path.md",
        "common/refernce/aci-publication-gate-path.md",
    ),
    (
        "common/aci/roadmap/aci-publication-gate-checkpoints.md",
        "common/refernce/aci-publication-gate-checkpoints.md",
    ),
    (
        "common/aci/tasks/aci-publication-gate-task-board.md",
        "common/refernce/aci-publication-gate-tasks.md",
    ),
    (
        "common/aci/design/aci-publication-gate-design.md",
        "common/refernce/aci-publication-gate-design.md",
    ),
    (
        "common/aci/roadmap/aci-private-host-bootstrap-goal.md",
        "common/refernce/aci-private-host-bootstrap-goal.md",
    ),
    (
        "common/aci/roadmap/aci-private-host-bootstrap-path.md",
        "common/refernce/aci-private-host-bootstrap-path.md",
    ),
    (
        "common/aci/roadmap/aci-private-host-bootstrap-checkpoints.md",
        "common/refernce/aci-private-host-bootstrap-checkpoints.md",
    ),
    (
        "common/aci/tasks/aci-private-host-bootstrap-task-board.md",
        "common/refernce/aci-private-host-bootstrap-tasks.md",
    ),
    (
        "common/aci/design/aci-private-host-bootstrap-design.md",
        "common/refernce/aci-private-host-bootstrap-design.md",
    ),
)


def check_required_mirror_pairs(repo_root: str | Path) -> MirrorSyncResult:
    root = Path(repo_root)
    if not (root / "common/aci").exists():
        if (root / "python").exists() and (root / "README.md").exists():
            return MirrorSyncResult(
                ok=True,
                checks=(),
                mode="standalone-skip",
                reason="working mirror validation applies only inside the monorepo layout",
            )
    checks = tuple(
        MirrorPairCheck(
            official=official,
            mirror=mirror,
            exists_official=(root / official).exists(),
            exists_mirror=(root / mirror).exists(),
        )
        for official, mirror in REQUIRED_MIRROR_PAIRS
    )
    return MirrorSyncResult(ok=all(item.ok for item in checks), checks=checks)
