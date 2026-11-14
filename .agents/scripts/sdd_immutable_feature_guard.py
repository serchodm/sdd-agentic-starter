#!/usr/bin/env python3
"""
SDD Immutable Feature Guard (PreToolUse Hook for Antigravity 2.0)
Enforces RN-SDD-IMMUTABLE-DONE & RN-SDD-1-TO-1-CR in strict fail-closed mode:
Blocks any edit_file or write_file operation targeting `specs/features/FEAT-XXX-*/`
when `FEAT-XXX` is already marked `Done`, `Completado`, or `Completed` in `specs/BACKLOG.md`,
and blocks malformed hook payloads, path traversal, symlinks/junctions, or missing/unreadable state.
"""

from __future__ import annotations

import json
import os
import pathlib
import re
import subprocess
import sys

_SCRIPTS_DIR = pathlib.Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from sdd_stack_gate_guard import is_link_or_junction  # noqa: E402

_DONE_STATUSES = frozenset({"done", "completado", "completed", "completed / done", "done / completed"})
_WORK_ITEM_ID_RE = re.compile(r"^((?:FEAT|CR|BUG|FWK)-\d{3,4})$", re.IGNORECASE)
_TARGET_PATH_KEYS: tuple[str, ...] = (
    "Path",
    "path",
    "file_path",
    "TargetFile",
    "target_file",
    "NotebookPath",
    "notebook_path",
    "AbsolutePath",
)


def strip_win32_extended_prefix(raw_path: str) -> str:
    """Normalize Win32 extended/UNC prefixes (\\\\?\\, \\\\?\\UNC\\) and reject unsafe device paths."""
    if not isinstance(raw_path, str):
        raise ValueError("Path must be a string.")
    if "\x00" in raw_path:
        raise ValueError("Null byte is not allowed in path.")

    slash_norm = raw_path.replace("\\", "/")
    if slash_norm.startswith("//./"):
        raise ValueError(f"Win32 device namespace paths are disallowed: {raw_path!r}")

    if slash_norm.lower().startswith("//?/unc/"):
        rest = slash_norm[8:].lstrip("/")
        parts = [p for p in rest.split("/") if p]
        if len(parts) < 2:
            raise ValueError(f"Malformed Win32 extended UNC path: {raw_path!r}")
        return "//" + rest

    if slash_norm.startswith("//?/"):
        rest = raw_path[4:]
        if not re.match(r"^[A-Za-z]:[/\\]", rest):
            raise ValueError(f"Unsupported Win32 extended path target: {raw_path!r}")
        return rest

    if re.match(r"^[A-Za-z]:(?![/\\])", raw_path):
        raise ValueError(f"Drive-relative Windows paths are disallowed: {raw_path!r}")

    return raw_path


def get_repo_root() -> pathlib.Path:
    """Resolve active repository or worktree root dynamically."""
    try:
        res = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
            encoding="utf-8",
            errors="strict",
        )
        toplevel = res.stdout.strip()
        if toplevel:
            cleaned = strip_win32_extended_prefix(toplevel)
            resolved = pathlib.Path(cleaned).resolve(strict=False)
            return pathlib.Path(strip_win32_extended_prefix(str(resolved)))
    except (subprocess.SubprocessError, OSError, UnicodeDecodeError, ValueError):
        pass

    fallback = pathlib.Path(__file__).resolve().parents[2]
    return pathlib.Path(strip_win32_extended_prefix(str(fallback)))


def read_hook_payload() -> dict:
    """Read and strictly validate JSON hook payload from stdin."""
    if hasattr(sys.stdin, "buffer"):
        raw_bytes = sys.stdin.buffer.read()
        raw_input = raw_bytes.decode("utf-8-sig")
    else:
        raw_input = sys.stdin.read()
        if raw_input.startswith("\ufeff"):
            raw_input = raw_input[1:]

    if not raw_input or not raw_input.strip():
        raise ValueError("Empty hook stdin payload.")

    payload = json.loads(raw_input.strip())
    if not isinstance(payload, dict):
        raise ValueError("Hook stdin JSON root must be a JSON object.")
    return payload


def extract_target_path(payload: dict) -> str:
    """Extract target file path from supported PreToolUse payload formats."""
    if not isinstance(payload, dict):
        return ""
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return ""
    for key in _TARGET_PATH_KEYS:
        val = tool_input.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    return ""


def _walk_and_verify_no_links(
    base: pathlib.Path,
    parts: tuple[str, ...],
    repo_root_resolved: pathlib.Path,
    raw_target: str,
) -> None:
    curr = base
    for part in parts:
        if part in ("", "."):
            continue
        if part == "..":
            curr = curr.parent
            if not curr.is_relative_to(repo_root_resolved):
                raise ValueError(f"Path traversal escapes repository root: {raw_target!r}")
            continue
        curr = curr / part
        if is_link_or_junction(curr):
            raise ValueError(f"Symlink or NTFS junction is forbidden in path: {curr}")


def resolve_repo_relative_path(target_path: str, repo_root: pathlib.Path) -> str:
    """
    Canonicalize target_path relative to repo_root and enforce strict containment:
    - Normalizes Win32 \\\\?\\ and \\\\?\\UNC\\ prefixes
    - Resolves with Path.resolve(strict=False)
    - Denies escapes outside repo_root.resolve(strict=False)
    - Denies symlinks or Windows NTFS junctions within the repository tree
    """
    if not isinstance(target_path, str) or not target_path.strip():
        raise ValueError("Target path must be a non-empty string.")

    repo_clean = pathlib.Path(strip_win32_extended_prefix(str(repo_root)))
    repo_resolved = pathlib.Path(strip_win32_extended_prefix(str(repo_clean.resolve(strict=False))))

    cleaned = strip_win32_extended_prefix(target_path.strip()).replace("\\", "/")
    cand = pathlib.Path(cleaned)

    joined = cand if cand.is_absolute() else (repo_resolved / cand)
    resolved = pathlib.Path(strip_win32_extended_prefix(str(joined.resolve(strict=False))))

    if not resolved.is_relative_to(repo_resolved):
        raise ValueError(f"Containment violation: '{target_path}' resolves outside repository root.")

    if not cand.is_absolute():
        _walk_and_verify_no_links(repo_resolved, cand.parts, repo_resolved, target_path)
    elif cand.is_relative_to(repo_resolved):
        _walk_and_verify_no_links(
            repo_resolved, cand.relative_to(repo_resolved).parts, repo_resolved, target_path
        )
    elif cand.is_relative_to(repo_clean):
        _walk_and_verify_no_links(
            repo_resolved, cand.relative_to(repo_clean).parts, repo_resolved, target_path
        )
    else:
        if ".." in cand.parts:
            raise ValueError(f"External path traversal into repository is disallowed: {target_path!r}")
        _walk_and_verify_no_links(
            repo_resolved, resolved.relative_to(repo_resolved).parts, repo_resolved, target_path
        )

    return resolved.relative_to(repo_resolved).as_posix()


def get_done_work_items(backlog_path: pathlib.Path, *, fail_if_missing: bool = False) -> set[str]:
    """Parse specs/BACKLOG.md and return IDs of work items marked Done/Completado/Completed."""
    if is_link_or_junction(backlog_path):
        raise ValueError(f"BACKLOG.md cannot be a symlink or junction: {backlog_path}")
    if not backlog_path.exists():
        if fail_if_missing:
            raise FileNotFoundError(f"Missing required specs/BACKLOG.md at {backlog_path}")
        return set()
    if not backlog_path.is_file():
        raise ValueError(f"BACKLOG.md is not a regular file: {backlog_path}")

    content = backlog_path.read_text(encoding="utf-8")
    done_items: set[str] = set()
    status_col_idx: int | None = None
    in_table = False

    for line in content.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or stripped.count("|") < 2:
            in_table = False
            status_col_idx = None
            continue

        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if cells and all(re.match(r"^:?-{1,}:?$", c.replace(" ", "")) for c in cells):
            in_table = True
            continue

        lowered_headers = [c.strip("` *_").lower() for c in cells]
        if not in_table and any(h in {"estado", "estado final", "status"} for h in lowered_headers):
            for idx, h in enumerate(lowered_headers):
                if h in {"estado", "estado final", "status"}:
                    status_col_idx = idx
                    break
            continue

        first_cell = cells[0].strip("` *_")
        id_match = _WORK_ITEM_ID_RE.match(first_cell)
        if not id_match:
            continue

        idx = status_col_idx if (status_col_idx is not None and status_col_idx < len(cells)) else len(cells) - 1
        status_val = cells[idx].strip("` *_").lower()
        if status_val in _DONE_STATUSES:
            done_items.add(id_match.group(1).upper())

    section_pattern = re.compile(
        r"####\s+`?((?:FEAT|CR|BUG|FWK)-\d{3,4})`?[^\n]*\n(?:-[^\n]*\n){0,3}?-\s+\*\*Estado:\*\*\s+`?(?:Completed|Completado|Done)",
        re.IGNORECASE,
    )
    for match in section_pattern.finditer(content):
        done_items.add(match.group(1).upper())

    return done_items


def get_done_features(backlog_path: pathlib.Path, *, fail_if_missing: bool = False) -> set[str]:
    """Return FEAT-XXX identifiers marked Done/Completado/Completed in BACKLOG.md."""
    return {
        item for item in get_done_work_items(backlog_path, fail_if_missing=fail_if_missing) if item.startswith("FEAT-")
    }


def _deny(reason: str) -> int:
    print(json.dumps({"decision": "deny", "reason": reason}))
    return 0


def main() -> int:
    try:
        payload = read_hook_payload()
        target_path = extract_target_path(payload)
        if not target_path:
            return _deny("SDD Immutable Feature Guard (fail-closed): Missing target file path in hook payload.")

        repo_root = get_repo_root()
        rel_posix = resolve_repo_relative_path(target_path, repo_root)

        feat_match = re.match(r"^specs/features/(FEAT-\d{3,4})(?:-[^/]*)?(?:/|$)", rel_posix, re.IGNORECASE)
        if not feat_match:
            print(json.dumps({"decision": "allow"}))
            return 0

        feat_id = feat_match.group(1).upper()
        backlog_path = repo_root / "specs" / "BACKLOG.md"
        done_features = get_done_features(backlog_path, fail_if_missing=True)

        if feat_id in done_features:
            return _deny(
                f"SDD Governance Lock (RN-SDD-IMMUTABLE-DONE): {feat_id} is marked 'Done' in "
                f"specs/BACKLOG.md and its folder (specs/features/{feat_id}-*/) is an IMMUTABLE "
                f"HISTORICAL BASELINE (Read-Only). Do NOT edit or overwrite completed feature "
                f"specifications. Create a 1:1 Change Request in specs/changes/CR-XXX-<slug>/ "
                f"(01-spec.md, 02-tech-spec.md, 03-tasks.md) instead."
            )

        print(json.dumps({"decision": "allow"}))
        return 0
    except Exception as exc:
        return _deny(f"SDD Immutable Feature Guard (fail-closed): {exc}")


if __name__ == "__main__":
    sys.exit(main())
