#!/usr/bin/env python3
"""Isolated vendor updater and SHA-256 lock verifier for capability-ui-design."""

from __future__ import annotations

import argparse
from collections.abc import Callable, Sequence
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_PACK_DIR = ROOT_DIR / ".sdd" / "catalog" / "packs" / "capability-ui-design"
DEFAULT_VENDOR_SUBDIR = "vendor/ui-ux-pro-max"
LOCK_FILENAME = "VENDOR.lock.json"
PACKAGE_NAME = "ui-ux-pro-max-cli"
UPSTREAM_REPO = "nextlevelbuilder/ui-ux-pro-max-skill"
LICENSE_SPDX = "MIT"
TEXT_EXTENSIONS: frozenset[str] = frozenset({".md", ".py", ".csv", ".json", ".txt"})
TEXT_FILENAMES: frozenset[str] = frozenset({"LICENSE"})

_SEMVER_RE = re.compile(
    r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
    r"(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_DEFAULT_MIT_LICENSE = """\
MIT License

Copyright (c) 2024 Next Level Builder

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""


class VendorIntegrityError(Exception):
    """Raised when VENDOR.lock.json or vendorized files fail verification."""


def _validate_safe_rel_posix(rel_path: str) -> tuple[str, ...]:
    """Validate and split a strict relative POSIX path inside vendor_dir."""
    if not isinstance(rel_path, str) or not rel_path:
        raise VendorIntegrityError(f"Invalid empty or non-string vendor path: {rel_path!r}")
    if "\x00" in rel_path or "\\" in rel_path or rel_path.startswith("/"):
        raise VendorIntegrityError(f"Unsafe vendor path syntax: {rel_path!r}")
    if PurePosixPath(rel_path).is_absolute() or PureWindowsPath(rel_path).is_absolute() or PureWindowsPath(rel_path).drive:
        raise VendorIntegrityError(f"Absolute or drive-qualified vendor path rejected: {rel_path!r}")
    parts = rel_path.split("/")
    if any(part in ("", ".", "..") for part in parts):
        raise VendorIntegrityError(f"Traversal or empty segment in vendor path: {rel_path!r}")
    if PurePosixPath(rel_path).as_posix() != rel_path or rel_path == LOCK_FILENAME:
        raise VendorIntegrityError(f"Forbidden vendor manifest entry path: {rel_path!r}")
    return tuple(parts)


def _normalize_text_bytes(path: Path, data: bytes) -> bytes:
    """Normalize CRLF/CR line endings to LF for textual vendor files."""
    if path.suffix.lower() in TEXT_EXTENSIONS or path.name in TEXT_FILENAMES:
        return data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return data


def _read_regular_bytes(path: Path) -> bytes:
    """Read exact raw bytes from a regular file, wrapping OS errors fail-closed."""
    try:
        return path.read_bytes()
    except OSError as exc:
        raise VendorIntegrityError(f"Cannot read vendor file '{path}': {exc}") from exc


def _run_checked_subprocess(cmd: Sequence[str], cwd: Path, label: str) -> None:
    """Run a subprocess without a shell and raise VendorIntegrityError on non-zero exit."""
    proc = subprocess.run(
        list(cmd), cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", check=False
    )
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout).strip() or f"exit code {proc.returncode}"
        raise VendorIntegrityError(f"{label} failed: {detail}")


def compute_vendor_manifest_entries(vendor_dir: Path) -> dict[str, dict[str, object]]:
    """Walk `vendor_dir` deterministically and return sorted `{rel: {sha256, bytes}}`."""
    if vendor_dir.is_symlink() or not vendor_dir.is_dir():
        raise VendorIntegrityError(f"Vendor directory missing or invalid: {vendor_dir}")
    vendor_root = vendor_dir.resolve()
    entries: dict[str, dict[str, object]] = {}

    def _walk(current: Path) -> None:
        try:
            children = sorted(current.iterdir(), key=lambda p: p.name)
        except OSError as exc:
            raise VendorIntegrityError(f"Cannot list vendor directory '{current}': {exc}") from exc
        for entry in children:
            if entry.is_symlink():
                raise VendorIntegrityError(f"Symlink not permitted in vendor directory: {entry}")
            resolved = entry.resolve()
            if not resolved.is_relative_to(vendor_root) or resolved == vendor_root:
                raise VendorIntegrityError(f"Path escapes vendor directory: {entry}")
            if entry.is_dir():
                if entry.name != "__pycache__":
                    _walk(entry)
            elif entry.is_file():
                rel = entry.relative_to(vendor_root).as_posix()
                if rel == LOCK_FILENAME or entry.suffix == ".pyc":
                    continue
                raw = _read_regular_bytes(resolved)
                entries[rel] = {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
            else:
                raise VendorIntegrityError(f"Non-regular filesystem entry rejected: {entry}")

    _walk(vendor_root)
    return {key: entries[key] for key in sorted(entries)}


def verify_vendor_lock(vendor_dir: Path, lock_path: Path | None = None) -> dict[str, Any]:
    """Verify `VENDOR.lock.json` schema, safe paths, and exact SHA-256/byte integrity."""
    # Return type dict[str, Any] matches JSON-serializable contract in 02-tech-spec.md §3.3.
    if vendor_dir.is_symlink() or not vendor_dir.is_dir():
        raise VendorIntegrityError(f"Vendor directory missing or invalid: {vendor_dir}")
    vendor_root = vendor_dir.resolve()
    effective_lock = (vendor_root / LOCK_FILENAME) if lock_path is None else lock_path
    if effective_lock.is_symlink() or not effective_lock.is_file():
        raise VendorIntegrityError(f"Vendor lock file missing or invalid: {effective_lock}")
    try:
        payload = json.loads(effective_lock.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise VendorIntegrityError(f"Invalid vendor lock JSON '{effective_lock}': {exc}") from exc

    if not isinstance(payload, dict):
        raise VendorIntegrityError(f"Vendor lock root must be a JSON object: {effective_lock}")
    if type(payload.get("schema_version")) is not int or payload.get("schema_version") != 1:
        raise VendorIntegrityError(f"Unsupported vendor lock schema_version: {payload.get('schema_version')!r}")
    version = payload.get("version")
    if not isinstance(version, str) or not version.strip():
        raise VendorIntegrityError(f"Vendor lock 'version' must be a non-empty string: {effective_lock}")
    files = payload.get("files")
    if not isinstance(files, dict) or not files:
        raise VendorIntegrityError(f"Vendor lock 'files' must be a non-empty mapping: {effective_lock}")

    expected: dict[str, tuple[str, int]] = {}
    for rel_path, meta in files.items():
        parts = _validate_safe_rel_posix(rel_path)
        if not isinstance(meta, dict):
            raise VendorIntegrityError(f"Invalid file metadata entry for '{rel_path}' in {effective_lock}")
        sha, size = meta.get("sha256"), meta.get("bytes")
        if not isinstance(sha, str) or not _SHA256_RE.fullmatch(sha):
            raise VendorIntegrityError(f"Invalid sha256 digest for '{rel_path}' in {effective_lock}: {sha!r}")
        if type(size) is not int or size < 0:
            raise VendorIntegrityError(f"Invalid byte size for '{rel_path}' in {effective_lock}: {size!r}")
        target = vendor_root.joinpath(*parts)
        if target.is_symlink():
            raise VendorIntegrityError(f"Symlink not permitted for vendor file: '{rel_path}'")
        resolved = target.resolve()
        if not resolved.is_relative_to(vendor_root) or resolved == vendor_root or not resolved.is_file():
            raise VendorIntegrityError(f"Declared vendor file missing or invalid: '{rel_path}' ({target})")
        expected[rel_path] = (sha, size)

    actual = compute_vendor_manifest_entries(vendor_root)
    if extra := sorted(set(actual) - set(expected)):
        raise VendorIntegrityError(f"Undeclared file(s) in vendor directory {vendor_root}: {', '.join(extra)}")
    if missing := sorted(set(expected) - set(actual)):
        raise VendorIntegrityError(f"Missing declared vendor file(s) in {vendor_root}: {', '.join(missing)}")

    for rel_path, (exp_sha, exp_bytes) in sorted(expected.items()):
        act_sha, act_bytes = actual[rel_path]["sha256"], actual[rel_path]["bytes"]
        if act_bytes != exp_bytes:
            raise VendorIntegrityError(f"Byte count mismatch for '{rel_path}': expected {exp_bytes}, got {act_bytes}")
        if act_sha != exp_sha:
            raise VendorIntegrityError(f"SHA-256 mismatch for '{rel_path}': expected {exp_sha}, got {act_sha}")
    return payload


def _validate_semver(version: str) -> str:
    """Validate strict SemVer syntax for upstream package versions."""
    if not isinstance(version, str) or not _SEMVER_RE.fullmatch(version):
        raise ValueError(f"Invalid semver version {version!r}; expected X.Y.Z.")
    return version


def _resolve_npx_executable() -> str:
    """Locate `npx.cmd` / `npx` on PATH without invoking a shell."""
    for name in (("npx.cmd", "npx") if os.name == "nt" else ("npx",)):
        if found := shutil.which(name):
            return found
    raise VendorIntegrityError("Executable 'npx' was not found on PATH.")


def _run_upstream_init(
    version: str, staging_dir: Path, runner: Callable[[Sequence[str], Path], int] | None
) -> None:
    """Install upstream skill bundle into isolated `staging_dir` via runner or npx."""
    pkg_spec = f"{PACKAGE_NAME}@{version}"
    if runner is not None:
        cmd = ["npx", "--yes", pkg_spec, "init", "--ai", "antigravity", "--offline"]
        if (rc := runner(cmd, staging_dir)) != 0:
            raise VendorIntegrityError(f"Vendor staging runner failed with exit code {rc}.")
        return
    cmd = [_resolve_npx_executable(), "--yes", pkg_spec, "init", "--ai", "antigravity", "--offline"]
    _run_checked_subprocess(cmd, staging_dir, f"Upstream '{pkg_spec}' init")


def _validate_staged_skill(staging_dir: Path) -> Path:
    """Verify staged `SKILL.md` presence and run `scripts/validate_data.py` with sys.executable."""
    skill_dir = staging_dir / ".agents" / "skills" / "ui-ux-pro-max"
    if skill_dir.is_symlink() or not skill_dir.is_dir():
        raise VendorIntegrityError(f"Expected staged skill directory missing: {skill_dir}")
    skill_root = skill_dir.resolve()
    skill_md = skill_root / "SKILL.md"
    if skill_md.is_symlink() or not skill_md.is_file():
        raise VendorIntegrityError(f"Expected staged SKILL.md missing: {skill_md}")
    val_script = skill_root / "scripts" / "validate_data.py"
    if val_script.is_symlink() or not val_script.resolve().is_relative_to(skill_root) or not val_script.is_file():
        raise VendorIntegrityError(f"Expected staging validator script missing: {val_script}")
    _run_checked_subprocess([sys.executable, str(val_script)], skill_root, "Staging validate_data.py")
    return skill_root


def _collect_staged_payload(skill_root: Path, staging_dir: Path, existing_vendor_dir: Path) -> dict[str, bytes]:
    """Extract exclusively `ui-ux-pro-max` runtime files, normalize text EOLs, and ensure LICENSE."""
    collected: dict[str, bytes] = {}

    def _walk(current: Path) -> None:
        for entry in sorted(current.iterdir(), key=lambda p: p.name):
            if entry.is_symlink():
                raise VendorIntegrityError(f"Symlink not permitted in staged skill: {entry}")
            resolved = entry.resolve()
            if not resolved.is_relative_to(skill_root) or resolved == skill_root:
                raise VendorIntegrityError(f"Staged asset escapes skill directory: {entry}")
            rel = entry.relative_to(skill_root).as_posix()
            if rel == "scripts/tests" or rel.startswith("scripts/tests/"):
                continue
            if entry.is_dir():
                if entry.name != "__pycache__":
                    _walk(entry)
            elif entry.is_file():
                if rel == LOCK_FILENAME or entry.suffix == ".pyc":
                    continue
                _validate_safe_rel_posix(rel)
                collected[rel] = _normalize_text_bytes(entry, _read_regular_bytes(resolved))
            else:
                raise VendorIntegrityError(f"Non-regular entry in staged skill: {entry}")

    _walk(skill_root)
    if "LICENSE" not in collected:
        raw_license: bytes | None = None
        for candidate in (staging_dir / "LICENSE", existing_vendor_dir / "LICENSE"):
            if candidate.is_symlink():
                raise VendorIntegrityError(f"Symlink LICENSE rejected: {candidate}")
            if candidate.is_file():
                raw_license = _read_regular_bytes(candidate)
                break
        collected["LICENSE"] = _normalize_text_bytes(
            Path("LICENSE"), raw_license if raw_license is not None else _DEFAULT_MIT_LICENSE.encode("utf-8")
        )
    return {key: collected[key] for key in sorted(collected)}


def _read_pack_json(pack_root: Path) -> tuple[dict[str, Any] | None, str | None]:
    """Load optional `pack.json` and extract current `upstream.version` fail-closed."""
    pack_json = pack_root / "pack.json"
    if pack_json.is_symlink():
        raise VendorIntegrityError(f"Symlink pack.json not permitted: {pack_json}")
    if not pack_json.is_file():
        return None, None
    try:
        data = json.loads(pack_json.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise VendorIntegrityError(f"Cannot parse pack manifest '{pack_json}': {exc}") from exc
    if not isinstance(data, dict):
        raise VendorIntegrityError(f"Pack manifest root must be a JSON object: {pack_json}")
    upstream = data.get("upstream")
    if upstream is not None and not isinstance(upstream, dict):
        raise VendorIntegrityError(f"Field 'upstream' in '{pack_json}' must be a JSON object.")
    cur_ver = upstream.get("version") if isinstance(upstream, dict) else None
    return data, cur_ver if isinstance(cur_ver, str) else None


def _apply_vendor_files(
    target_vendor_dir: Path, staged_files: dict[str, bytes], lock_payload: dict[str, Any]
) -> None:
    """Atomically write normalized vendor files and `VENDOR.lock.json`, then verify."""
    if target_vendor_dir.is_symlink():
        raise VendorIntegrityError(f"Target vendor path cannot be a symlink: {target_vendor_dir}")
    vendor_parent = target_vendor_dir.parent
    vendor_parent.mkdir(parents=True, exist_ok=True)
    stage_target = Path(tempfile.mkdtemp(prefix=".staging-ui-ux-pro-max-", dir=vendor_parent))
    backup_dir: Path | None = None
    try:
        for rel_path, content in staged_files.items():
            dest = stage_target.joinpath(*_validate_safe_rel_posix(rel_path))
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(content)
        lock_bytes = (json.dumps(lock_payload, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
        (stage_target / LOCK_FILENAME).write_bytes(lock_bytes)
        verify_vendor_lock(stage_target)
        if target_vendor_dir.exists():
            backup_dir = Path(tempfile.mkdtemp(prefix=".backup-ui-ux-pro-max-", dir=vendor_parent))
            backup_dir.rmdir()
            target_vendor_dir.rename(backup_dir)
        stage_target.rename(target_vendor_dir)
        if backup_dir is not None and backup_dir.exists():
            shutil.rmtree(backup_dir)
    except Exception:
        if backup_dir is not None and backup_dir.exists() and not target_vendor_dir.exists():
            backup_dir.rename(target_vendor_dir)
        raise
    finally:
        if stage_target.exists():
            shutil.rmtree(stage_target, ignore_errors=True)


def update_vendor(
    version: str,
    pack_dir: Path,
    *,
    apply: bool = False,
    runner: Callable[[Sequence[str], Path], int] | None = None,
) -> dict[str, Any]:
    """Stage, validate, diff, and optionally apply an isolated vendor update."""
    # Return type dict[str, Any] matches JSON-serializable summary contract in 02-tech-spec.md §3.3.
    clean_version = _validate_semver(version)
    if pack_dir.is_symlink() or (pack_dir.exists() and not pack_dir.is_dir()):
        raise VendorIntegrityError(f"Pack directory path is invalid: {pack_dir}")
    pack_root = pack_dir.resolve()
    target_vendor_dir = pack_root / "vendor" / "ui-ux-pro-max"
    pack_data, old_pack_version = _read_pack_json(pack_root)

    with tempfile.TemporaryDirectory(prefix="sdd-vendor-stage-") as tmp_str:
        staging_dir = Path(tmp_str)
        _run_upstream_init(clean_version, staging_dir, runner)
        skill_root = _validate_staged_skill(staging_dir)
        staged_files = _collect_staged_payload(skill_root, staging_dir, target_vendor_dir)

    new_entries: dict[str, dict[str, object]] = {
        rel: {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)} for rel, data in staged_files.items()
    }
    current_entries = compute_vendor_manifest_entries(target_vendor_dir) if target_vendor_dir.is_dir() else {}
    added = sorted(k for k in new_entries if k not in current_entries)
    removed = sorted(k for k in current_entries if k not in new_entries)
    modified = sorted(k for k in new_entries if k in current_entries and new_entries[k] != current_entries[k])
    summary: dict[str, Any] = {
        "version": clean_version,
        "applied": False,
        "vendor_dir": str(target_vendor_dir),
        "added": added,
        "modified": modified,
        "removed": removed,
        "unchanged_count": len(new_entries) - len(added) - len(modified),
        "file_count": len(new_entries),
        "pack_version_change": {
            "from": old_pack_version, "to": clean_version, "changed": pack_data is not None and old_pack_version != clean_version,
        },
    }
    if not apply:
        return summary

    lock_payload: dict[str, Any] = {
        "schema_version": 1, "package": PACKAGE_NAME, "version": clean_version, "license": LICENSE_SPDX,
        "upstream_repo": UPSTREAM_REPO, "updated_at": datetime.now(timezone.utc).isoformat(),
        "vendor_subdir": DEFAULT_VENDOR_SUBDIR, "files": new_entries,
    }
    _apply_vendor_files(target_vendor_dir, staged_files, lock_payload)
    if pack_data is not None and old_pack_version != clean_version:
        upstream = pack_data.get("upstream")
        if not isinstance(upstream, dict):
            upstream = {}
            pack_data["upstream"] = upstream
        upstream["version"] = clean_version
        (pack_root / "pack.json").write_bytes((json.dumps(pack_data, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))
    verify_vendor_lock(target_vendor_dir)
    summary["applied"] = True
    summary["lock"] = lock_payload
    return summary


def _print_diff_summary(summary: dict[str, Any]) -> None:
    """Print human-readable vendor update diff summary to stdout."""
    pvc = summary["pack_version_change"]
    print(f"Vendor target : {summary['vendor_dir']}")
    print(f"Target version: {summary['version']} (files: {summary['file_count']})")
    print(f"pack.json ver : {pvc['from']} -> {pvc['to']} (changed={pvc['changed']})")
    print(
        f"Diff summary  : +{len(summary['added'])} added, ~{len(summary['modified'])} modified, "
        f"-{len(summary['removed'])} removed, {summary['unchanged_count']} unchanged"
    )
    for label, key in (("Added", "added"), ("Modified", "modified"), ("Removed", "removed")):
        for rel in summary[key]:
            print(f"  [{label}] {rel}")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Verify VENDOR.lock.json or stage/apply isolated ui-ux-pro-max updates.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--verify", action="store_true", help="Verify VENDOR.lock.json SHA-256 integrity.")
    mode.add_argument("--version", type=str, help="Semver version of ui-ux-pro-max-cli to inspect or apply.")
    parser.add_argument("--apply", action="store_true", help="Apply staged vendor changes to pack_dir.")
    parser.add_argument("--yes", action="store_true", help="Skip interactive [y/N] confirmation (with --apply).")
    parser.add_argument("--pack-dir", type=Path, default=DEFAULT_PACK_DIR, help="Path to capability-ui-design pack.")
    parser.add_argument("--vendor-dir", type=Path, default=None, help="Explicit vendor dir override for --verify.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entrypoint for vendor lock verification and isolated updates."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except (AttributeError, OSError, ValueError) as exc:
                print(f"[WARN] Could not configure UTF-8 stream: {exc}", file=sys.stderr)

    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.yes and not args.apply:
        parser.error("--yes requires --apply.")
    if args.apply and not args.version:
        parser.error("--apply requires --version <X.Y.Z>.")
    if args.vendor_dir is not None and args.version:
        parser.error("--vendor-dir is only supported with --verify.")

    try:
        if args.verify:
            target_vendor = args.vendor_dir if args.vendor_dir is not None else args.pack_dir / "vendor" / "ui-ux-pro-max"
            lock_data = verify_vendor_lock(target_vendor)
            print(f"[OK] Verified {LOCK_FILENAME}: version={lock_data['version']}, files={len(lock_data['files'])}")
            return 0
        if args.version:
            if args.apply and args.yes:
                summary = update_vendor(args.version, args.pack_dir, apply=True)
                _print_diff_summary(summary)
                print(f"[OK] Applied vendor update {summary['version']} and verified {LOCK_FILENAME}.")
                return 0
            preview = update_vendor(args.version, args.pack_dir, apply=False)
            _print_diff_summary(preview)
            if not args.apply:
                print("[DRY-RUN] No changes written. Re-run with --apply to update vendor files.")
                return 0
            try:
                answer = input(f"Apply vendor update to '{args.pack_dir}'? [y/N]: ")
            except (EOFError, KeyboardInterrupt):
                print("\n[ABORTED] Confirmation cancelled.", file=sys.stderr)
                return 1
            if answer.strip().lower() not in {"y", "yes"}:
                print("[ABORTED] Vendor update cancelled; workspace unchanged.", file=sys.stderr)
                return 1
            applied = update_vendor(args.version, args.pack_dir, apply=True)
            print(f"[OK] Applied vendor update {applied['version']} and verified {LOCK_FILENAME}.")
            return 0
        parser.print_help()
        return 0
    except (VendorIntegrityError, ValueError, OSError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1


__all__ = [
    "VendorIntegrityError", "compute_vendor_manifest_entries", "main", "update_vendor", "verify_vendor_lock",
]

if __name__ == "__main__":
    sys.exit(main())
