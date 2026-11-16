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
_WORK_ITEM_ID_RE = re.compile(r"^((?:FEAT|CR|BUG|HOTFIX|FWK)-\d{3,4})$", re.IGNORECASE)
_TARGET_PATH_KEYS: tuple[str, ...] = (
    "Path",
    "path",
    "FilePath",
    "file_path",
    "TargetFile",
    "target_file",
    "NotebookPath",
    "notebook_path",
    "AbsolutePath",
    "absolute_path",
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


def extract_tool_call(payload: dict) -> tuple[str, dict]:
    """Extract (tool_name, tool_args) supporting Antigravity (toolCall.args) and legacy tool_input."""
    if not isinstance(payload, dict):
        return "", {}

    tool_call = payload.get("toolCall")
    if isinstance(tool_call, dict):
        name = tool_call.get("name") or payload.get("tool_name") or payload.get("toolName") or ""
        args = tool_call.get("args")
        if isinstance(args, dict):
            return str(name), args

    name = payload.get("tool_name") or payload.get("toolName") or ""
    for container_key in ("tool_input", "toolInput", "args", "arguments", "parameters"):
        container = payload.get(container_key)
        if isinstance(container, dict):
            return str(name), container

    return str(name), {}


def extract_target_path(payload: dict) -> str:
    """Extract target file path from supported PreToolUse payload formats."""
    _, tool_args = extract_tool_call(payload)
    for key in _TARGET_PATH_KEYS:
        val = tool_args.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    return ""


def _walk_and_verify_no_links(
    base: pathlib.Path,
    parts: tuple[str, ...],
    root_resolved: pathlib.Path,
    raw_target: str,
) -> None:
    curr = base
    for part in parts:
        if part in ("", "."):
            continue
        if part == "..":
            curr = curr.parent
            if not curr.is_relative_to(root_resolved):
                raise ValueError(f"Path traversal escapes containment root: {raw_target!r}")
            continue
        curr = curr / part
        if is_link_or_junction(curr):
            raise ValueError(f"Symlink or NTFS junction is forbidden in path: {curr}")


def _normalize_target_path(target_path: str) -> str:
    """Normalize target path slashes/Win32 prefixes and reject Windows drive paths on POSIX."""
    if not isinstance(target_path, str) or not target_path.strip():
        raise ValueError("Target path must be a non-empty string.")
    cleaned = strip_win32_extended_prefix(target_path.strip()).replace("\\", "/")
    if os.name != "nt" and re.match(r"^[A-Za-z]:", cleaned):
        raise ValueError(f"Windows drive paths are disallowed on POSIX: {target_path!r}")
    return cleaned


def resolve_repo_relative_path(target_path: str, repo_root: pathlib.Path) -> str:
    """Canonicalize target_path relative to repo_root and enforce strict containment."""
    cleaned = _normalize_target_path(target_path)

    repo_clean = pathlib.Path(strip_win32_extended_prefix(str(repo_root)))
    repo_resolved = pathlib.Path(strip_win32_extended_prefix(str(repo_clean.resolve(strict=False))))

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


def resolve_target_context(
    target_path: str, payload: dict, base_repo_root: pathlib.Path
) -> tuple[pathlib.Path, str, bool]:
    """Resolve effective (repo_root, rel_posix, is_external_artifact) without weakening containment."""
    try:
        rel_posix = resolve_repo_relative_path(target_path, base_repo_root)
    except ValueError:
        raw_art = payload.get("artifactDirectoryPath")
        if isinstance(raw_art, str) and raw_art.strip():
            cleaned_art = _normalize_target_path(target_path)
            art_clean = pathlib.Path(strip_win32_extended_prefix(raw_art.strip()))
            art_resolved = pathlib.Path(strip_win32_extended_prefix(str(art_clean.resolve(strict=False))))
            base_resolved = pathlib.Path(strip_win32_extended_prefix(str(base_repo_root.resolve(strict=False))))
            cand_art = pathlib.Path(cleaned_art)
            if (
                cand_art.is_absolute()
                and ".." not in cand_art.parts
                and not is_link_or_junction(art_resolved)
            ):
                resolved_art = pathlib.Path(strip_win32_extended_prefix(str(cand_art.resolve(strict=False))))
                if resolved_art.is_relative_to(art_resolved) and not resolved_art.is_relative_to(base_resolved):
                    _walk_and_verify_no_links(
                        art_resolved, resolved_art.relative_to(art_resolved).parts, art_resolved, target_path
                    )
                    return base_resolved, resolved_art.as_posix(), True
        raise

    parts = rel_posix.split("/")
    if len(parts) >= 3 and parts[0] == ".worktrees":
        wt_candidate = base_repo_root / ".worktrees" / parts[1]
        if (
            not is_link_or_junction(base_repo_root / ".worktrees")
            and not is_link_or_junction(wt_candidate)
            and (wt_candidate / ".git").exists()
        ):
            wt_rel = resolve_repo_relative_path(target_path, wt_candidate)
            return wt_candidate, wt_rel, False

    return base_repo_root, rel_posix, False


def get_done_work_items(backlog_path: pathlib.Path, *, fail_if_missing: bool = False) -> set[str]:
    """Parse specs/BACKLOG.md or .sdd/framework/BACKLOG.md and return Done item IDs."""
    if is_link_or_junction(backlog_path):
        raise ValueError(f"BACKLOG.md cannot be a symlink or junction: {backlog_path}")
    if not backlog_path.exists():
        if fail_if_missing:
            raise FileNotFoundError(f"Missing required BACKLOG.md at {backlog_path}")
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
        r"####\s+`?((?:FEAT|CR|BUG|HOTFIX|FWK)-\d{3,4})`?[^\n]*\n(?:-[^\n]*\n){0,3}?-\s+\*\*Estado:\*\*\s+`?(?:Completed|Completado|Done)",
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

        base_repo = get_repo_root()
        repo_root, rel_posix, is_artifact = resolve_target_context(target_path, payload, base_repo)
        if is_artifact:
            print(json.dumps({"decision": "allow"}))
            return 0

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