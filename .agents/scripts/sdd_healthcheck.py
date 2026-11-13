#!/usr/bin/env python3
"""
Project Global SDD & Architecture Healthcheck (`sdd_healthcheck.py`)
Combines SDD governance invariants with `morluto/rea` and `affaan-m/ecc` verification checks:

1. Verifies that every `FEAT-XXX` in `specs/features/` and every `CR-XXX` in `specs/changes/`
   contains the complete triad of Gate files (`01-spec.md`, `02-tech-spec.md`, `03-tasks.md`).
2. Verifies `RN-SDD-IMMUTABLE-DONE`: ensures zero uncommitted working-tree modifications exist
   inside any `specs/features/FEAT-XXX-*/` folder whose status in `specs/BACKLOG.md` is `Done`.
3. Verifies `RN-SDD-1-TO-1-CR` traceability: ensures every `CR-XXX` folder in `specs/changes/`
   is registered in `specs/BACKLOG.md`.
4. Runs `verify_architecture_boundaries.py` to validate Clean/Hexagonal Architecture boundaries,
   black-box package consumption, and the 800-line file modularity limit.
"""

import pathlib
import re
import subprocess
import sys

from sdd_immutable_feature_guard import get_done_features
from verify_architecture_boundaries import run_boundary_audit


def check_spec_triads(specs_root: pathlib.Path, backlog_path: pathlib.Path) -> list[str]:
    errors: list[str] = []
    backlog_text = backlog_path.read_text(encoding="utf-8", errors="ignore") if backlog_path.exists() else ""
    for category, required_files in (
        ("features", ("01-spec.md", "02-tech-spec.md", "03-tasks.md")),
        ("changes", ("01-spec.md", "02-tech-spec.md", "03-tasks.md")),
        ("bugs", ("01-bug-report.md", "02-fix-spec.md", "03-tasks.md")),
    ):
        cat_dir = specs_root / category
        if not cat_dir.exists():
            continue
        for item_dir in sorted(cat_dir.iterdir()):
            if not item_dir.is_dir():
                continue
            item_id_match = re.match(r"^([A-Za-z]+-\d{3,4})", item_dir.name)
            item_id = item_id_match.group(1).upper() if item_id_match else item_dir.name.upper()

            # Determinar si el expediente se encuentra en fase inicial/propuesta (Gate 1: Draft / Proposed / Propuesto / Gate 1)
            is_gate1_proposed = False
            for line in backlog_text.splitlines():
                line_upper = line.upper()
                line_lower = line.lower()
                if item_id in line_upper:
                    gate1_indicators = ("draft", "proposed", "propuesto", "gate 1")
                    if (
                        any(ind in line_lower for ind in gate1_indicators)
                        and "done" not in line_lower
                        and "completado" not in line_lower
                        and "completed" not in line_lower
                    ):
                        is_gate1_proposed = True
                        break

            # Si está en estado inicial (Gate 1), solo se exige el documento inicial (01-*)
            files_to_check = (required_files[0],) if is_gate1_proposed else required_files
            for req in files_to_check:
                if not (item_dir / req).exists():
                    errors.append(
                        f"[SDD Triad Incomplete] '{item_dir.relative_to(specs_root.parent)}' is missing '{req}'."
                    )
    return errors


def check_done_features_git_clean(repo_root: pathlib.Path, done_features: set[str]) -> list[str]:
    errors: list[str] = []
    features_dir = repo_root / "specs" / "features"
    if not features_dir.exists():
        return errors

    for item_dir in sorted(features_dir.iterdir()):
        if not item_dir.is_dir():
            continue
        m = re.match(r"^(FEAT-\d{3,4})", item_dir.name, re.IGNORECASE)
        if not m:
            continue
        feat_id = m.group(1).upper()
        if feat_id not in done_features:
            continue

        rel_dir = str(item_dir.relative_to(repo_root)).replace("\\", "/")
        res = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=no", "--", rel_dir],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
        )
        if res.returncode == 0 and res.stdout.strip():
            errors.append(
                f"[RN-SDD-IMMUTABLE-DONE Violation] Completed feature '{rel_dir}' has uncommitted modifications:\n"
                f"{res.stdout.strip()}"
            )
    return errors


def check_cr_backlog_registration(repo_root: pathlib.Path) -> list[str]:
    errors: list[str] = []
    backlog_path = repo_root / "specs" / "BACKLOG.md"
    changes_dir = repo_root / "specs" / "changes"
    if not backlog_path.exists() or not changes_dir.exists():
        return errors

    backlog_text = backlog_path.read_text(encoding="utf-8", errors="ignore")
    for cr_dir in sorted(changes_dir.iterdir()):
        if not cr_dir.is_dir():
            continue
        m = re.match(r"^(CR-\d{3,4})", cr_dir.name, re.IGNORECASE)
        if not m:
            continue
        cr_id = m.group(1).upper()
        if cr_id not in backlog_text:
            errors.append(
                f"[Backlog Traceability Error] Change Request '{cr_dir.name}' ({cr_id}) is not registered in specs/BACKLOG.md."
            )
    return errors


def check_git_sync_status(repo_root: pathlib.Path) -> list[str]:
    warnings: list[str] = []
    res_curr_branch = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
    )
    current_branch = res_curr_branch.stdout.strip() if res_curr_branch.returncode == 0 else "main"

    res_status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
    )
    if res_status.returncode == 0 and res_status.stdout.strip():
        count = len(res_status.stdout.strip().splitlines())
        target_push = f"origin {current_branch}" if current_branch else "origin <branch>"
        warnings.append(
            f"[RN-SDD-BRANCH-SYNC Reminder] Working tree has {count} uncommitted file(s)/folder(s). "
            f"Remember to run `git add`, `git commit`, and `git push {target_push}` once validated."
        )

    res_branch = subprocess.run(
        ["git", "status", "-sb"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
    )
    if res_branch.returncode == 0 and "ahead" in res_branch.stdout:
        target_push = f"origin {current_branch}" if current_branch else "origin <branch>"
        warnings.append(
            f"[RN-SDD-BRANCH-SYNC Reminder] Local branch '{current_branch}' is ahead of remote. Remember to run `git push {target_push}`."
        )
    return warnings


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    repo_root = pathlib.Path(__file__).resolve().parents[2]
    specs_root = repo_root / "specs"
    backlog_path = specs_root / "BACKLOG.md"

    done_features = get_done_features(backlog_path)
    errors: list[str] = []
    warnings: list[str] = []

    print("=== Project SDD & Agent Harness 2.0 Healthcheck ===")
    print(f"Detected Done/Immutable Features ({len(done_features)}): {', '.join(sorted(done_features))}")

    # 1. Spec Triads
    errors.extend(check_spec_triads(specs_root, backlog_path))

    # 2. Done Features Git Cleanliness
    errors.extend(check_done_features_git_clean(repo_root, done_features))

    # 3. CR Registration in BACKLOG.md
    errors.extend(check_cr_backlog_registration(repo_root))

    # 4. Architecture Boundaries & Modularity
    arch_errors, arch_warnings = run_boundary_audit(repo_root)
    errors.extend(arch_errors)
    warnings.extend(arch_warnings)

    # 5. Git Sync Status (RN-SDD-GIT-SYNC)
    warnings.extend(check_git_sync_status(repo_root))

    for w in warnings:
        print(f"  [WARN]  {w}")
    for e in errors:
        print(f"  [ERROR] {e}")

    if errors:
        print(f"\n❌ SDD Healthcheck FAILED with {len(errors)} error(s) and {len(warnings)} warning(s).")
        return 1

    print(f"\n✅ SDD Healthcheck PASSED (0 errors, {len(warnings)} warning(s)).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
