#!/usr/bin/env python3
"""
SDD Code Gate & Modularity Guard (PreToolUse Hook for Antigravity 2.0)
Inspired by morluto/rea (Fail-Closed & Human Gate Ownership) and affaan-m/ecc (GateGuard & 800-line ceiling).

Enforces:
1. RN-SDD-GATE2-CODE-LOCK: Blocks any edit_file or write_file on production/test code
   (`backend/`, `frontend/`, `DDBB/`, `docker-compose*`) unless `.agents/active_work_item.json`
   has an active work item (`FEAT-XXX`, `CR-XXX`, or `BUG-XXX`) with Gates 1, 2, and 3
   explicitly approved by the human user, and whose target spec folder exists and is not a `Done` feature.
2. RN-ECC-MAX-FILE-LINES: Blocks creating or expanding any `.py`, `.ts`, `.tsx`, `.js`, `.jsx` file
   under `backend/src/` or `frontend/src/` beyond 800 lines.
3. RN-ECC-DOC-SPRAWL: Blocks creating stray `.md` documentation files inside `backend/src/` or `frontend/src/`.
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

try:
    from sdd_stack_gate_guard import check_stack_gate
except ImportError:
    check_stack_gate = None
from sdd_immutable_feature_guard import extract_target_path, get_done_features

MAX_SOURCE_LINES = 800
CODE_EXTENSIONS = {".py", ".ts", ".tsx", ".js", ".jsx", ".glsl", ".sql"}


def is_protected_code_path(normalized_path: str, repo_root_posix: str) -> str | None:
    """
    Returns the relative repo path if the target path is inside a production/test code boundary,
    or None if it is outside (e.g., specs/, docs/, .agents/, roadmap/).
    """
    rel = normalized_path
    if normalized_path.lower().startswith(repo_root_posix.lower() + "/"):
        rel = normalized_path[len(repo_root_posix) + 1 :]
    rel_clean = rel.lstrip("/")

    if re.match(r"^(src|backend|frontend|DDBB)(/|$)", rel_clean, re.IGNORECASE):
        return rel_clean
    if re.match(r"^docker-compose[^/]*\.ya?ml$", rel_clean, re.IGNORECASE):
        return rel_clean
    return None


def compute_resulting_lines(repo_root: pathlib.Path, rel_path: str, tool_name: str, tool_input: dict) -> int:
    file_path = repo_root / rel_path
    if tool_name == "write_file":
        content = tool_input.get("Content") or tool_input.get("content") or ""
        if tool_input.get("Append") and file_path.exists():
            existing = file_path.read_text(encoding="utf-8", errors="ignore")
            return len((existing + content).splitlines())
        return len(content.splitlines())

    if tool_name == "edit_file" and file_path.exists():
        existing = file_path.read_text(encoding="utf-8", errors="ignore")
        target = tool_input.get("Target") or tool_input.get("target") or ""
        replacement = tool_input.get("Replacement") or tool_input.get("replacement") or ""
        if target and target in existing:
            updated = existing.replace(target, replacement)
            return len(updated.splitlines())
        return len(existing.splitlines())

    return 0


def validate_active_work_item(repo_root: pathlib.Path) -> tuple[bool, str]:
    state_file = repo_root / ".agents" / "active_work_item.json"
    if not state_file.exists():
        return (
            False,
            "SDD Gate 2 Code-Lock (RN-SDD-GATE2-CODE-LOCK): Missing .agents/active_work_item.json. "
            "Production/test code cannot be modified without a formally approved work item.",
        )

    try:
        state = json.loads(state_file.read_text(encoding="utf-8"))
    except Exception as exc:
        return False, f"SDD Gate 2 Code-Lock: Invalid JSON in .agents/active_work_item.json ({exc})."

    work_item_id = (state.get("active_work_item_id") or "").strip()
    spec_dir_rel = (state.get("spec_dir") or "").strip().replace("\\", "/")
    g1 = bool(state.get("gate_1_approved"))
    g2 = bool(state.get("gate_2_approved"))
    g3 = bool(state.get("gate_3_approved"))
    human_ok = bool(state.get("approved_by_human"))

    if not work_item_id or not spec_dir_rel or not (g1 and g2 and g3 and human_ok):
        return (
            False,
            "SDD Gate 2 Code-Lock (RN-SDD-GATE2-CODE-LOCK): Production/test code is LOCKED. "
            "No active work item has human-approved Gates 1, 2, and 3 in `.agents/active_work_item.json`. "
            "Complete `01-spec.md`, `02-tech-spec.md`, and `03-tasks.md` first, obtain explicit user sign-off, "
            "and register the active work item before editing `backend/`, `frontend/`, `DDBB/`, or `docker-compose*`.",
        )

    spec_dir = repo_root / spec_dir_rel
    if not spec_dir.exists() or not spec_dir.is_dir():
        return (
            False,
            f"SDD Gate 2 Code-Lock: Referenced spec_dir '{spec_dir_rel}' does not exist on disk.",
        )

    # Check required spec files
    has_func = (spec_dir / "01-spec.md").exists() or (spec_dir / "01-bug-report.md").exists()
    has_tech = (spec_dir / "02-tech-spec.md").exists() or (spec_dir / "02-fix-spec.md").exists()
    has_tasks = (spec_dir / "03-tasks.md").exists()
    if not (has_func and has_tech and has_tasks):
        return (
            False,
            f"SDD Gate 2 Code-Lock: '{spec_dir_rel}' is missing one or more required gate artifacts "
            "(01-spec.md, 02-tech-spec.md, 03-tasks.md).",
        )

    # Ensure work_item_id is not an already-Done FEAT-XXX
    feat_match = re.match(r"^(FEAT-\d{3,4})", work_item_id, re.IGNORECASE)
    if feat_match:
        feat_id = feat_match.group(1).upper()
        done_features = get_done_features(repo_root / "specs" / "BACKLOG.md")
        if feat_id in done_features:
            return (
                False,
                f"SDD Immutability Lock (RN-SDD-IMMUTABLE-DONE): Active work item '{feat_id}' is already marked "
                f"'Done' in specs/BACKLOG.md. Create and activate a Change Request (CR-XXX) instead.",
            )

    return True, "OK"


def main() -> int:
    try:
        raw_input = sys.stdin.buffer.read().decode("utf-8-sig", errors="ignore")
        if not raw_input.strip():
            print(json.dumps({"decision": "allow"}))
            return 0
        payload = json.loads(raw_input.strip())
    except Exception:
        print(json.dumps({"decision": "allow"}))
        return 0

    target_path = extract_target_path(payload)
    if not target_path:
        print(json.dumps({"decision": "allow"}))
        return 0

    repo_root = get_repo_root()
    repo_root_posix = str(repo_root).replace("\\", "/")
    normalized = target_path.replace("\\", "/")

    rel_code_path = is_protected_code_path(normalized, repo_root_posix)
    if not rel_code_path:
        print(json.dumps({"decision": "allow"}))
        return 0

    # Ignore virtualenv / node_modules if ever targeted
    if "/.venv/" in f"/{rel_code_path}/" or "/node_modules/" in f"/{rel_code_path}/":
        print(json.dumps({"decision": "allow"}))
        return 0

    # 0. Check Gate 00 (Stack Lock) if stack guard is present
    if check_stack_gate:
        stack_ok, stack_msg = check_stack_gate(repo_root)
        if not stack_ok:
            print(json.dumps({"decision": "deny", "reason": stack_msg}))
            return 0

    # 1. Enforce Gate 2 Code-Lock
    ok, reason = validate_active_work_item(repo_root)
    if not ok:
        print(json.dumps({"decision": "deny", "reason": reason}))
        return 0

    # 2. Enforce Doc Sprawl Guard inside source directories
    ext = pathlib.Path(rel_code_path).suffix.lower()
    if ext == ".md" and re.match(r"^(src|backend/src|frontend/src)/", rel_code_path, re.IGNORECASE):
        print(
            json.dumps(
                {
                    "decision": "deny",
                    "reason": (
                        f"Doc Sprawl Guard (RN-ECC-DOC-SPRAWL): Do not create markdown documentation files "
                        f"inside source code directories ({rel_code_path}). Place specs in `specs/` and "
                        f"living documentation in `docs/`."
                    ),
                }
            )
        )
        return 0

    # 3. Enforce 800-line Modularity Ceiling on source files
    if ext in CODE_EXTENSIONS and re.match(r"^(src|backend/src|frontend/src)/", rel_code_path, re.IGNORECASE):
        tool_name = payload.get("tool_name") or ""
        tool_input = payload.get("tool_input") or {}
        line_count = compute_resulting_lines(repo_root, rel_code_path, tool_name, tool_input)
        if line_count > MAX_SOURCE_LINES:
            print(
                json.dumps(
                    {
                        "decision": "deny",
                        "reason": (
                            f"Modularity Guard (RN-ECC-MAX-FILE-LINES): '{rel_code_path}' would have "
                            f"{line_count} lines, exceeding the maximum ceiling of {MAX_SOURCE_LINES} lines. "
                            f"Decompose into smaller, high-cohesion modules (target 200-400 lines)."
                        ),
                    }
                )
            )
            return 0

    print(json.dumps({"decision": "allow"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
