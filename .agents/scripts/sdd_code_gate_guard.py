#!/usr/bin/env python3
"""
SDD Code Gate & Modularity Guard (PreToolUse Hook for Antigravity 2.0)
Enforces in strict fail-closed mode:
1. RN-SDD-GATE2-CODE-LOCK: Blocks any edit_file or write_file on protected code, tests,
   scripts, hooks, rules, or specs/STACK.md unless Gate S0 is approved AND `.agents/active_work_item.json`
   references an active non-Done work item with real non-empty `01-*`, `02-*`, `03-tasks.md`
   artifacts signed off by the human user (`[x] Gate 1..3 Approved`).
2. RN-ECC-MAX-FILE-LINES: Blocks creating or expanding source files under `src/`, `backend/src/`,
   or `frontend/src/` beyond 800 lines.
3. RN-ECC-DOC-SPRAWL: Blocks creating stray `.md` documentation files inside source directories.
"""

from __future__ import annotations

import json
import pathlib
import posixpath
import re
import sys

_SCRIPTS_DIR = pathlib.Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from sdd_immutable_feature_guard import (  # noqa: E402
    extract_target_path,
    get_done_work_items,
    get_repo_root,
    read_hook_payload,
    resolve_repo_relative_path,
    strip_win32_extended_prefix,
)
from sdd_stack_gate_guard import (  # noqa: E402
    check_stack_gate,
    is_link_or_junction,
    strip_non_normative_markdown,
)

MAX_SOURCE_LINES = 800
CODE_EXTENSIONS = {".py", ".ts", ".tsx", ".js", ".jsx", ".glsl", ".sql"}
_ALLOWED_SPEC_BUCKETS: tuple[str, ...] = (
    "specs/features",
    "specs/changes",
    "specs/bugs",
    ".sdd/framework/work-items",
)
_WORK_ITEM_ID_RE = re.compile(r"^((?:FEAT|CR|BUG|FWK)-\d{3,4})(?:-[A-Za-z0-9._-]+)?$", re.IGNORECASE)
_PROTECTED_PREFIX_RE = re.compile(r"^(src|backend|frontend|DDBB|tests|scripts)(/|$)", re.IGNORECASE)
_PROTECTED_COMPOSE_RE = re.compile(r"(?:^|/)docker-compose[^/]*\.ya?ml$", re.IGNORECASE)
_PROTECTED_AGENTS_RE = re.compile(r"^\.agents/(?:hooks\.json$|(?:scripts|rules)(/|$))", re.IGNORECASE)
_PROTECTED_STACK_RE = re.compile(r"^specs/STACK\.md$", re.IGNORECASE)


def is_protected_code_path(normalized_path: str, repo_root_posix: str = "") -> str | None:
    """
    Return the relative repo path if the target path is inside a protected code, test,
    hook, script, rule, or STACK.md boundary; otherwise return None.
    """
    cleaned = strip_win32_extended_prefix(normalized_path).replace("\\", "/")
    rel = cleaned
    if repo_root_posix:
        root_clean = strip_win32_extended_prefix(repo_root_posix).replace("\\", "/").rstrip("/")
        if rel.lower().startswith(root_clean.lower() + "/"):
            rel = rel[len(root_clean) + 1 :]

    rel_clean = posixpath.normpath(rel.lstrip("/")) if rel.lstrip("/") else ""
    if not rel_clean or rel_clean == "." or rel_clean.startswith("../") or rel_clean == "..":
        return None

    if (
        _PROTECTED_PREFIX_RE.match(rel_clean)
        or _PROTECTED_COMPOSE_RE.match(rel_clean)
        or _PROTECTED_AGENTS_RE.match(rel_clean)
        or _PROTECTED_STACK_RE.match(rel_clean)
    ):
        return rel_clean
    return None


def compute_resulting_lines(repo_root: pathlib.Path, rel_path: str, tool_name: str, tool_input: dict) -> int:
    """Compute resulting line count for write_file or edit_file on an existing/new file."""
    file_path = repo_root / rel_path
    if tool_name == "write_file":
        content = tool_input.get("Content") or tool_input.get("content") or ""
        if not isinstance(content, str):
            content = str(content)
        if tool_input.get("Append") and file_path.exists():
            existing = file_path.read_text(encoding="utf-8")
            return len((existing + content).splitlines())
        return len(content.splitlines())

    if tool_name == "edit_file" and file_path.exists():
        existing = file_path.read_text(encoding="utf-8")
        target = tool_input.get("Target") or tool_input.get("target") or ""
        replacement = tool_input.get("Replacement") or tool_input.get("replacement") or ""
        if isinstance(target, str) and isinstance(replacement, str) and target and target in existing:
            updated = existing.replace(target, replacement)
            return len(updated.splitlines())
        return len(existing.splitlines())

    return 0


def _gates_approved_in_state(state: dict) -> bool:
    if state.get("approved_by_human") is not True:
        return False

    gates_obj = state.get("gates")
    flat_keys = ("gate_1_approved", "gate_2_approved", "gate_3_approved")
    if isinstance(gates_obj, dict):
        nested_ok = all(gates_obj.get(k) is True for k in ("1", "2", "3"))
        flat_conflict = any(k in state and state.get(k) is not True for k in flat_keys)
        return nested_ok and not flat_conflict

    return all(state.get(k) is True for k in flat_keys)


def _locate_and_verify_spec_dir(
    repo_root: pathlib.Path, canonical_id: str, spec_dir_raw: object
) -> tuple[pathlib.Path | None, str]:
    id_folder_re = re.compile(rf"^{re.escape(canonical_id)}(?:-|$)", re.IGNORECASE)

    if isinstance(spec_dir_raw, str) and spec_dir_raw.strip():
        try:
            rel_spec = resolve_repo_relative_path(spec_dir_raw.strip(), repo_root)
        except ValueError as exc:
            return None, f"SDD Gate 2 Code-Lock: Unsafe spec_dir '{spec_dir_raw}': {exc}"

        matched_bucket = False
        for bucket in _ALLOWED_SPEC_BUCKETS:
            prefix = bucket.lower() + "/"
            if rel_spec.lower().startswith(prefix):
                folder = rel_spec[len(prefix) :]
                if "/" not in folder and id_folder_re.match(folder):
                    matched_bucket = True
                    break

        if not matched_bucket:
            return (
                None,
                f"SDD Gate 2 Code-Lock: spec_dir '{rel_spec}' must sit directly under one of "
                f"{', '.join(_ALLOWED_SPEC_BUCKETS)} and start with '{canonical_id}'.",
            )

        spec_dir = repo_root / rel_spec
        if is_link_or_junction(spec_dir) or not spec_dir.exists() or not spec_dir.is_dir():
            return None, f"SDD Gate 2 Code-Lock: Referenced spec_dir '{rel_spec}' does not exist as a real directory."
        return spec_dir, rel_spec

    if spec_dir_raw is not None and not (isinstance(spec_dir_raw, str) and not spec_dir_raw.strip()):
        return None, "SDD Gate 2 Code-Lock: Invalid spec_dir type in .agents/active_work_item.json."

    matches: list[pathlib.Path] = []
    for bucket in _ALLOWED_SPEC_BUCKETS:
        bucket_path = repo_root / bucket
        if bucket_path.exists():
            if is_link_or_junction(bucket_path) or not bucket_path.is_dir():
                return None, f"SDD Gate 2 Code-Lock: Spec bucket '{bucket}' cannot be a symlink or junction."
            for entry in sorted(bucket_path.iterdir()):
                if entry.is_dir() and not is_link_or_junction(entry) and id_folder_re.match(entry.name):
                    matches.append(entry)

    if not matches:
        return None, f"SDD Gate 2 Code-Lock: Could not locate spec directory for '{canonical_id}'."
    if len(matches) > 1:
        return None, f"SDD Gate 2 Code-Lock: Ambiguous multiple spec directories found for '{canonical_id}'."
    return matches[0], matches[0].relative_to(repo_root).as_posix()


def _find_spec_doc(
    spec_dir: pathlib.Path, preferred_names: tuple[str, ...], glob_pattern: str | None = None
) -> pathlib.Path | None:
    for name in preferred_names:
        cand = spec_dir / name
        if cand.exists():
            return cand
    if glob_pattern:
        matches = sorted(p for p in spec_dir.glob(glob_pattern) if p.exists())
        if len(matches) == 1:
            return matches[0]
    return None


def _validate_gate_doc(file_path: pathlib.Path, gate_num: int, rel_dir: str) -> tuple[bool, str]:
    if is_link_or_junction(file_path) or not file_path.is_file():
        return False, f"SDD Gate 2 Code-Lock: '{rel_dir}/{file_path.name}' must be a regular non-link file."

    try:
        raw_text = file_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return False, f"SDD Gate 2 Code-Lock: Cannot read '{rel_dir}/{file_path.name}' ({exc})."

    cleaned = strip_non_normative_markdown(raw_text)
    marker_re = re.compile(rf"\[[xX]\]\s*(?:\*\*)?Gate\s+{gate_num}\s+Approved(?:\*\*)?", re.IGNORECASE)
    if not marker_re.search(cleaned):
        return (
            False,
            f"SDD Gate 2 Code-Lock: '{rel_dir}/{file_path.name}' lacks a valid human sign-off "
            f"marker '[x] Gate {gate_num} Approved' outside comments/code fences.",
        )

    body_only = re.sub(rf"^.*{marker_re.pattern}.*$", "", cleaned, flags=re.MULTILINE)
    meaningful = re.sub(r"[\s#*\-_`>:|.\[\]()]+", "", body_only)
    if len(cleaned.strip()) < 20 or len(meaningful) < 8:
        return (
            False,
            f"SDD Gate 2 Code-Lock: '{rel_dir}/{file_path.name}' is empty or lacks substantive spec content.",
        )
    return True, "OK"


def validate_active_work_item(repo_root: pathlib.Path) -> tuple[bool, str]:
    """Verify active_work_item.json, spec triad existence, real Gate 1..3 markers, and BACKLOG state."""
    agents_dir = repo_root / ".agents"
    if agents_dir.exists() and is_link_or_junction(agents_dir):
        return False, "SDD Gate 2 Code-Lock: .agents directory cannot be a symlink or junction."

    state_file = agents_dir / "active_work_item.json"
    if is_link_or_junction(state_file):
        return False, "SDD Gate 2 Code-Lock: .agents/active_work_item.json cannot be a symlink or junction."
    if not state_file.exists() or not state_file.is_file():
        return (
            False,
            "SDD Gate 2 Code-Lock (RN-SDD-GATE2-CODE-LOCK): Missing .agents/active_work_item.json. "
            "Protected files cannot be modified without a formally approved work item.",
        )

    try:
        state = json.loads(state_file.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return False, f"SDD Gate 2 Code-Lock: Invalid or unreadable .agents/active_work_item.json ({exc})."

    if not isinstance(state, dict):
        return False, "SDD Gate 2 Code-Lock: .agents/active_work_item.json root must be a JSON object."

    raw_id = state.get("active_work_item_id")
    work_item_id = raw_id.strip() if isinstance(raw_id, str) else ""
    id_match = _WORK_ITEM_ID_RE.match(work_item_id)
    if not id_match or not _gates_approved_in_state(state):
        return (
            False,
            "SDD Gate 2 Code-Lock (RN-SDD-GATE2-CODE-LOCK): Protected paths are LOCKED. "
            "No valid active work item has human-approved Gates 1, 2, and 3 in `.agents/active_work_item.json`.",
        )

    canonical_id = id_match.group(1).upper()
    spec_dir, spec_info = _locate_and_verify_spec_dir(repo_root, canonical_id, state.get("spec_dir"))
    if spec_dir is None:
        return False, spec_info

    file_01 = _find_spec_doc(spec_dir, ("01-spec.md", "01-bug-report.md"), "01-*.md")
    file_02 = _find_spec_doc(spec_dir, ("02-tech-spec.md", "02-fix-spec.md"), "02-*.md")
    file_03 = _find_spec_doc(spec_dir, ("03-tasks.md",))
    if not (file_01 and file_02 and file_03):
        return (
            False,
            f"SDD Gate 2 Code-Lock: '{spec_info}' is missing required gate artifacts "
            "(01-*, 02-*, 03-tasks.md).",
        )

    for gate_num, doc_path in ((1, file_01), (2, file_02), (3, file_03)):
        doc_ok, doc_msg = _validate_gate_doc(doc_path, gate_num, spec_info)
        if not doc_ok:
            return False, doc_msg

    backlog_path = repo_root / "specs" / "BACKLOG.md"
    try:
        done_items = get_done_work_items(backlog_path, fail_if_missing=True)
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        return False, f"SDD Gate 2 Code-Lock (fail-closed): Cannot verify specs/BACKLOG.md ({exc})."

    if canonical_id in done_items:
        return (
            False,
            f"SDD Immutability Lock (RN-SDD-IMMUTABLE-DONE): Active work item '{canonical_id}' is already marked "
            "'Done' in specs/BACKLOG.md. Create and activate a new Change Request (CR-XXX) instead.",
        )

    return True, "OK"


def _deny(reason: str) -> int:
    print(json.dumps({"decision": "deny", "reason": reason}))
    return 0


def main() -> int:
    try:
        payload = read_hook_payload()
        target_path = extract_target_path(payload)
        if not target_path:
            return _deny("SDD Code Gate Guard (fail-closed): Missing target file path in hook payload.")

        repo_root = get_repo_root()
        rel_posix = resolve_repo_relative_path(target_path, repo_root)

        rel_code_path = is_protected_code_path(rel_posix)
        if not rel_code_path:
            print(json.dumps({"decision": "allow"}))
            return 0

        stack_ok, stack_msg = check_stack_gate(repo_root)
        if not stack_ok:
            return _deny(stack_msg)

        ok, reason = validate_active_work_item(repo_root)
        if not ok:
            return _deny(reason)

        ext = pathlib.Path(rel_code_path).suffix.lower()
        if ext == ".md" and re.match(r"^(src|backend/src|frontend/src)/", rel_code_path, re.IGNORECASE):
            return _deny(
                f"Doc Sprawl Guard (RN-ECC-DOC-SPRAWL): Do not create markdown documentation files "
                f"inside source code directories ({rel_code_path}). Place specs in `specs/` and "
                f"living documentation in `docs/`."
            )

        if ext in CODE_EXTENSIONS and re.match(r"^(src|backend/src|frontend/src)/", rel_code_path, re.IGNORECASE):
            tool_name = payload.get("tool_name") or ""
            tool_input = payload.get("tool_input") if isinstance(payload.get("tool_input"), dict) else {}
            line_count = compute_resulting_lines(repo_root, rel_code_path, str(tool_name), tool_input)
            if line_count > MAX_SOURCE_LINES:
                return _deny(
                    f"Modularity Guard (RN-ECC-MAX-FILE-LINES): '{rel_code_path}' would have "
                    f"{line_count} lines, exceeding the maximum ceiling of {MAX_SOURCE_LINES} lines. "
                    f"Decompose into smaller, high-cohesion modules (target 200-400 lines)."
                )

        print(json.dumps({"decision": "allow"}))
        return 0
    except Exception as exc:
        return _deny(f"SDD Code Gate Guard (fail-closed): {exc}")


if __name__ == "__main__":
    sys.exit(main())
