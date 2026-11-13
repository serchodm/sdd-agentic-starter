#!/usr/bin/env python3
"""
SDD Immutable Feature Guard (PreToolUse Hook for Antigravity 2.0)
Enforces RN-SDD-IMMUTABLE-DONE & RN-SDD-1-TO-1-CR:
Blocks any edit_file or write_file operation targeting `specs/features/FEAT-XXX-*/`
when `FEAT-XXX` is already marked `Done`, `Completado`, or `Completed` in `specs/BACKLOG.md`.
"""

import json
import pathlib
import re
import subprocess
import sys


def get_repo_root() -> pathlib.Path:
    """Resuelve dinámicamente el directorio raíz del repositorio o worktree activo."""
    try:
        res = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
            encoding="utf-8",
            errors="replace",
        )
        toplevel = res.stdout.strip()
        if toplevel:
            return pathlib.Path(toplevel)
    except Exception:
        pass
    return pathlib.Path(__file__).resolve().parents[2]


def extract_target_path(payload: dict) -> str:
    tool_input = payload.get("tool_input") or {}
    for key in ("Path", "path", "file_path", "TargetFile", "target_file"):
        val = tool_input.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    return ""


def get_done_features(backlog_path: pathlib.Path) -> set[str]:
    done_features: set[str] = set()
    if not backlog_path.exists():
        return done_features

    content = backlog_path.read_text(encoding="utf-8", errors="ignore")

    # 1. Check markdown table rows: | `FEAT-004` | ... | `Done` |
    table_pattern = re.compile(
        r"\|\s*`?(FEAT-\d{3,4})`?\s*\|(?:[^|\n]*\|)*?\s*`?(Done|Completado|Completed)`?\s*\|",
        re.IGNORECASE,
    )
    for match in table_pattern.finditer(content):
        done_features.add(match.group(1).upper())

    # 2. Check detail sections: #### `FEAT-004` ... - **Estado:** `Completed / Done`
    section_pattern = re.compile(
        r"####\s+`?(FEAT-\d{3,4})`?[^\n]*\n(?:-[^\n]*\n){0,3}?-\s+\*\*Estado:\*\*\s+`?(?:Completed|Completado|Done)",
        re.IGNORECASE,
    )
    for match in section_pattern.finditer(content):
        done_features.add(match.group(1).upper())

    return done_features


def main() -> int:
    try:
        raw_input = sys.stdin.buffer.read().decode("utf-8-sig", errors="ignore")
        if not raw_input.strip():
            print(json.dumps({"decision": "allow"}))
            return 0
        payload = json.loads(raw_input.strip())
    except Exception:
        # Fail open only on malformed hook stdin so unrelated tools aren't broken
        print(json.dumps({"decision": "allow"}))
        return 0

    target_path = extract_target_path(payload)
    if not target_path:
        print(json.dumps({"decision": "allow"}))
        return 0

    normalized = target_path.replace("\\", "/")
    feat_match = re.search(r"(?:^|/)specs/features/(FEAT-\d{3,4})(?:-[^/]*)?/", normalized, re.IGNORECASE)
    if not feat_match:
        print(json.dumps({"decision": "allow"}))
        return 0

    feat_id = feat_match.group(1).upper()
    repo_root = get_repo_root()
    backlog_path = repo_root / "specs" / "BACKLOG.md"
    done_features = get_done_features(backlog_path)

    if feat_id in done_features:
        reason = (
            f"SDD Governance Lock (RN-SDD-IMMUTABLE-DONE): {feat_id} is marked 'Done' in "
            f"specs/BACKLOG.md and its folder (specs/features/{feat_id}-*/) is an IMMUTABLE "
            f"HISTORICAL BASELINE (Read-Only). Do NOT edit or overwrite completed feature "
            f"specifications. Create a 1:1 Change Request in specs/changes/CR-XXX-<slug>/ "
            f"(01-spec.md, 02-tech-spec.md, 03-tasks.md) instead."
        )
        print(json.dumps({"decision": "deny", "reason": reason}))
        return 0

    print(json.dumps({"decision": "allow"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
