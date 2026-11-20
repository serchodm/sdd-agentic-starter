#!/usr/bin/env python3
"""
SDD Cryptographic Gate Seal Manager & Verifier (RF-1001).
Computes, embeds, and verifies SHA-256 digests for approved Gate 1..3 specification
artifacts (`01-*`, `02-*`, `03-tasks.md`) to prevent silent post-approval tampering.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import sys
from typing import Sequence

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
for _p in (str(_REPO_ROOT), str(_REPO_ROOT / ".agents" / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from sdd_immutable_feature_guard import resolve_repo_relative_path  # noqa: E402
from sdd_stack_gate_guard import is_link_or_junction, strip_non_normative_markdown  # noqa: E402

_ALLOWED_SPEC_BUCKETS = ("specs/features", "specs/changes", "specs/bugs", ".sdd/framework/work-items")
_SEAL_LINE_RE = re.compile(r"^\s*<!--\s*sdd:gate-seal\b.*?-->\s*$", re.IGNORECASE)
_SEAL_ANY_TAG_RE = re.compile(r"<!--\s*sdd:gate-seal\b.*?-->", re.IGNORECASE | re.DOTALL)
_SEAL_VALID_TAG_RE = re.compile(
    r"^\s*<!--\s*sdd:gate-seal(?:\s+gate=(\d+))?\s+sha256[=:](?:sha256:)?([0-9a-fA-F]{64})\s*-->\s*$",
    re.IGNORECASE,
)
_SHA256_PREFIX_RE = re.compile(r"^sha256:[0-9a-f]{64}$", re.IGNORECASE)
_SHA256_RAW_RE = re.compile(r"^[0-9a-f]{64}$", re.IGNORECASE)
_BROWNFIELD_ORIGIN_RE = re.compile(
    r"^(?:[-*]\s+)?(?:\*\*)?(?:Origin|Origen)(?:\*\*)?\s*:\s*`?brownfield-mined`?\s*$",
    re.IGNORECASE | re.MULTILINE,
)


def compute_gate_doc_sha256(text: str) -> str:
    """Compute canonical SHA-256 digest (`sha256:<64hex>`) excluding inline gate-seal tags."""
    cleaned = text.lstrip("\ufeff").replace("\r\n", "\n").replace("\r", "\n")
    lines = [line for line in cleaned.split("\n") if not _SEAL_LINE_RE.match(line)]
    normalized = "\n".join(lines).rstrip() + "\n"
    return "sha256:" + hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _strip_fences_and_inline_code(text: str) -> str:
    out_lines, in_fence, fence_char, fence_len = [], False, "", 0
    for line in text.lstrip("\ufeff").replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        if in_fence:
            if re.match(rf"^[ \t]*{re.escape(fence_char)}{{{fence_len},}}[ \t]*$", line):
                in_fence = False
            continue
        m = re.match(r"^[ \t]*(`{3,}|~{3,})", line)
        if m:
            in_fence, fence_char, fence_len = True, m.group(1)[0], len(m.group(1))
            continue
        out_lines.append(re.sub(r"`+[^`\n]*`+", "", line))
    return "\n".join(out_lines)


def extract_inline_gate_seal(text: str, gate_num: int | None = None) -> str | None:
    """Extract `sha256:<64hex>` from inline `<!-- sdd:gate-seal ... -->`, or `'INVALID'` if malformed."""
    norm = _strip_fences_and_inline_code(text)
    raw_tags = _SEAL_ANY_TAG_RE.findall(norm)
    seal_lines = [line for line in norm.split("\n") if re.search(r"<!--\s*sdd:gate-seal\b", line, re.IGNORECASE)]
    if not raw_tags and not seal_lines:
        return None
    if len(raw_tags) != len(seal_lines):
        return "INVALID"

    found: str | None = None
    for line in seal_lines:
        match = _SEAL_VALID_TAG_RE.match(line)
        if not match:
            return "INVALID"
        tag_gate, hex_digest = match.group(1), match.group(2).lower()
        if gate_num is not None and tag_gate is not None and int(tag_gate) != gate_num:
            return "INVALID"
        candidate = f"sha256:{hex_digest}"
        if found is not None and found != candidate:
            return "INVALID"
        found = candidate
    return found


def _find_spec_doc(
    spec_dir: pathlib.Path, preferred_names: tuple[str, ...], glob_pattern: str | None = None
) -> pathlib.Path | None:
    for name in preferred_names:
        if (spec_dir / name).exists():
            return spec_dir / name
    if glob_pattern:
        matches = sorted(p for p in spec_dir.glob(glob_pattern) if p.exists())
        return matches[0] if matches else None
    return None


def find_work_item_gate_files(spec_dir: pathlib.Path) -> dict[int, pathlib.Path | None]:
    """Return mapping of Gate 1, 2, 3 numbers to their resolved markdown artifact paths."""
    return {
        1: _find_spec_doc(spec_dir, ("01-spec.md", "01-bug-report.md"), "01-*.md"),
        2: _find_spec_doc(spec_dir, ("02-tech-spec.md", "02-fix-spec.md"), "02-*.md"),
        3: _find_spec_doc(spec_dir, ("03-tasks.md",)),
    }


def _resolve_spec_dir(repo_root: pathlib.Path, state: dict) -> tuple[pathlib.Path | None, str]:
    spec_dir_raw = state.get("spec_dir")
    if isinstance(spec_dir_raw, str) and spec_dir_raw.strip():
        try:
            rel_spec = resolve_repo_relative_path(spec_dir_raw.strip(), repo_root)
        except ValueError as exc:
            return None, f"SDD Gate Cryptographic Seal Violation: Unsafe spec_dir '{spec_dir_raw}': {exc}"
        spec_dir = repo_root / rel_spec
        if is_link_or_junction(spec_dir) or not spec_dir.is_dir():
            return None, f"SDD Gate Cryptographic Seal Violation: spec_dir '{rel_spec}' is not a valid directory."
        return spec_dir, rel_spec

    raw_id = str(state.get("active_work_item_id") or "").strip()
    canonical_match = re.match(r"^((?:FEAT|CR|BUG|HOTFIX|FWK)-\d{3,4})", raw_id, re.IGNORECASE)
    if not canonical_match:
        return None, "SDD Gate Cryptographic Seal Violation: Cannot resolve spec_dir without active_work_item_id."
    canonical_id = canonical_match.group(1).upper()
    id_folder_re = re.compile(rf"^{re.escape(canonical_id)}(?:-|$)", re.IGNORECASE)
    for bucket in _ALLOWED_SPEC_BUCKETS:
        bucket_path = repo_root / bucket
        if bucket_path.is_dir() and not is_link_or_junction(bucket_path):
            for entry in sorted(bucket_path.iterdir()):
                if entry.is_dir() and not is_link_or_junction(entry) and id_folder_re.match(entry.name):
                    return entry, entry.relative_to(repo_root).as_posix()
    return None, f"SDD Gate Cryptographic Seal Violation: Could not locate spec_dir for '{canonical_id}'."


def _normalize_seal_value(raw_val: object) -> str | None:
    if not isinstance(raw_val, str) or not raw_val.strip():
        return None
    val = raw_val.strip().lower()
    if _SHA256_RAW_RE.match(val):
        return f"sha256:{val}"
    return val if _SHA256_PREFIX_RE.match(val) else "INVALID"


def is_brownfield_mined_baseline(spec_dir: pathlib.Path) -> bool:
    """Return True if `01-spec.md` is a regular file declaring `Origin: brownfield-mined`."""
    spec_doc = spec_dir / "01-spec.md"
    if is_link_or_junction(spec_dir) or not spec_dir.is_dir() or is_link_or_junction(spec_doc) or not spec_doc.is_file():
        return False
    try:
        cleaned = strip_non_normative_markdown(spec_doc.read_text(encoding="utf-8").lstrip("\ufeff"))
    except (OSError, UnicodeDecodeError):
        return False
    return bool(_BROWNFIELD_ORIGIN_RE.search(cleaned))


def validate_brownfield_baseline_docs(spec_dir: pathlib.Path, rel_dir: str) -> list[str]:
    """Validate brownfield-mined baseline (`01-spec.md` and `02-tech-spec.md`) with Gate 1 & Gate 2 sign-offs."""
    if is_link_or_junction(spec_dir) or not spec_dir.is_dir():
        return [f"[SDD Brownfield Baseline] '{rel_dir}' is missing or a symlink/junction."]
    errors: list[str] = []
    for gate_num, fname in ((1, "01-spec.md"), (2, "02-tech-spec.md")):
        try:
            _validate_approved_gate_doc(spec_dir / fname, gate_num)
        except (ValueError, OSError, UnicodeDecodeError) as exc:
            errors.append(f"[SDD Brownfield Baseline] '{rel_dir}': {exc}")
    return errors


def _resolve_target_gates(
    spec_dir: pathlib.Path, state: dict, gate_seals: dict, gate_files: dict[int, pathlib.Path | None]
) -> tuple[int, ...]:
    has_g3 = gate_seals.get("3") is not None or gate_seals.get(3) is not None or state.get("gate_3_sha256") is not None
    tasks = spec_dir / "03-tasks.md"
    if is_brownfield_mined_baseline(spec_dir) and gate_files.get(3) is None and not is_link_or_junction(tasks) and not tasks.exists() and not has_g3:
        return (1, 2)
    return (1, 2, 3)


def verify_work_item_gate_seals(
    repo_root: pathlib.Path,
    state: dict | None = None,
    spec_dir: pathlib.Path | None = None,
    *,
    require_seals: bool = False,
) -> tuple[bool, str]:
    """Verify Gate 1..3 SHA-256 seals against state and/or inline markers in fail-closed mode."""
    if state is None:
        state_file = repo_root / ".agents" / "active_work_item.json"
        if is_link_or_junction(state_file) or not state_file.is_file():
            return False, "SDD Gate Cryptographic Seal Violation: Missing or invalid .agents/active_work_item.json."
        try:
            loaded = json.loads(state_file.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            return False, f"SDD Gate Cryptographic Seal Violation: Cannot parse .agents/active_work_item.json ({exc})."
        if not isinstance(loaded, dict):
            return False, "SDD Gate Cryptographic Seal Violation: .agents/active_work_item.json must be a JSON object."
        state = loaded

    if spec_dir is None:
        spec_dir, err_msg = _resolve_spec_dir(repo_root, state)
        if spec_dir is None:
            return False, err_msg
    elif is_link_or_junction(spec_dir) or not spec_dir.is_dir():
        return False, f"SDD Gate Cryptographic Seal Violation: Invalid spec_dir '{spec_dir}'."

    gate_seals_raw = state.get("gate_seals")
    if gate_seals_raw is not None and not isinstance(gate_seals_raw, dict):
        return False, "SDD Gate Cryptographic Seal Violation: 'gate_seals' in active_work_item.json must be a JSON object."
    gate_seals: dict = gate_seals_raw if isinstance(gate_seals_raw, dict) else {}
    has_state_seals = bool(gate_seals) or any(state.get(f"gate_{g}_sha256") is not None for g in (1, 2, 3))
    must_enforce = bool(require_seals or state.get("enforce_gate_seals") is True or has_state_seals)

    gate_files = find_work_item_gate_files(spec_dir)
    target_gates = _resolve_target_gates(spec_dir, state, gate_seals, gate_files)
    if target_gates == (1, 2) and (errs := validate_brownfield_baseline_docs(spec_dir, spec_dir.name)):
        return False, f"SDD Gate Cryptographic Seal Violation: {errs[0]}"
    for g in target_gates:
        doc_path = gate_files.get(g)
        if doc_path is None or is_link_or_junction(doc_path) or not doc_path.is_file():
            return False, f"SDD Gate Cryptographic Seal Violation: Missing Gate {g} artifact in '{spec_dir.name}'."
        try:
            raw_text = doc_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            return False, f"SDD Gate Cryptographic Seal Violation: Cannot read '{doc_path.name}' ({exc})."

        inline_seal = extract_inline_gate_seal(raw_text, g)
        if inline_seal == "INVALID":
            return False, f"SDD Gate Cryptographic Seal Violation: Malformed inline sdd:gate-seal in '{doc_path.name}'."

        raw_state_entry = gate_seals.get(str(g)) if str(g) in gate_seals else gate_seals.get(g, state.get(f"gate_{g}_sha256"))
        state_seal = _normalize_seal_value(raw_state_entry) if raw_state_entry is not None else None
        if state_seal == "INVALID":
            return False, f"SDD Gate Cryptographic Seal Violation: Invalid SHA-256 seal format for Gate {g} ('{doc_path.name}')."
        if state_seal and inline_seal and state_seal.lower() != inline_seal.lower():
            return False, f"SDD Gate Cryptographic Seal Violation: Gate {g} state seal and inline seal mismatch for '{doc_path.name}'."

        expected = state_seal or inline_seal
        if expected is None:
            if must_enforce:
                return (
                    False,
                    f"SDD Gate Cryptographic Seal Violation: Missing SHA-256 seal for Gate {g} ('{doc_path.name}'). "
                    "Run 'sdd approve-gate' to seal approved gates.",
                )
            continue

        actual = compute_gate_doc_sha256(raw_text)
        if actual.lower() != expected.lower():
            return (
                False,
                f"SDD Gate Cryptographic Seal Violation: Gate {g} artifact '{doc_path.name}' was modified after approval "
                f"(expected {expected.lower()}, got {actual.lower()}). Re-approve with 'sdd approve-gate'.",
            )
    return True, "OK"


def _validate_approved_gate_doc(doc_path: pathlib.Path, gate_num: int) -> str:
    if is_link_or_junction(doc_path) or not doc_path.is_file():
        raise ValueError(f"Gate {gate_num} file '{doc_path}' is missing or a symlink/junction.")
    raw_text = doc_path.read_text(encoding="utf-8")
    cleaned = strip_non_normative_markdown(raw_text)
    marker_re = re.compile(rf"\[[xX]\]\s*(?:\*\*)?Gate\s+{gate_num}\s+Approved(?:\*\*)?", re.IGNORECASE)
    if not marker_re.search(cleaned):
        raise ValueError(f"'{doc_path.name}' lacks a valid '[x] Gate {gate_num} Approved' sign-off marker.")
    body_only = re.sub(rf"^.*{marker_re.pattern}.*$", "", cleaned, flags=re.MULTILINE)
    meaningful = re.sub(r"[\s#*\-_`>:|.\[\]()]+", "", body_only)
    if len(cleaned.strip()) < 20 or len(meaningful) < 8:
        raise ValueError(f"'{doc_path.name}' lacks substantive specification content.")
    return raw_text


def seal_work_item_gates(
    repo_root: pathlib.Path,
    work_item_id: str | None = None,
    *,
    gates: Sequence[int] = (1, 2, 3),
    embed_inline: bool = False,
) -> dict[str, str]:
    """Compute and persist SHA-256 seals for approved Gates 1..3 in active_work_item.json (and inline if requested)."""
    state_file = repo_root / ".agents" / "active_work_item.json"
    if is_link_or_junction(state_file) or not state_file.is_file():
        raise ValueError("Missing or invalid .agents/active_work_item.json.")
    state = json.loads(state_file.read_text(encoding="utf-8"))
    if not isinstance(state, dict):
        raise ValueError(".agents/active_work_item.json root must be a JSON object.")

    active_id = str(state.get("active_work_item_id") or "").strip()
    if work_item_id and not active_id.upper().startswith(work_item_id.strip().upper()):
        raise ValueError(f"Requested work_item_id '{work_item_id}' does not match active '{active_id}'.")

    spec_dir, err_msg = _resolve_spec_dir(repo_root, state)
    if spec_dir is None:
        raise ValueError(err_msg)

    gate_files = find_work_item_gate_files(spec_dir)
    existing_raw = state.get("gate_seals")
    if existing_raw is not None and not isinstance(existing_raw, dict):
        raise ValueError("'gate_seals' in active_work_item.json must be a JSON object.")
    existing_seals = existing_raw if isinstance(existing_raw, dict) else {}
    new_seals: dict[str, str] = {str(k): str(v) for k, v in existing_seals.items()}

    target_gates = _resolve_target_gates(spec_dir, state, existing_seals, gate_files) if tuple(gates) == (1, 2, 3) else tuple(gates)
    if tuple(gates) == (1, 2, 3) and target_gates == (1, 2) and (errs := validate_brownfield_baseline_docs(spec_dir, spec_dir.name)):
        raise ValueError(errs[0])

    for g in target_gates:
        doc_path = gate_files.get(g)
        if doc_path is None:
            raise ValueError(f"Missing Gate {g} artifact in '{spec_dir}'.")
        raw_text = _validate_approved_gate_doc(doc_path, g)
        digest = compute_gate_doc_sha256(raw_text)
        new_seals[str(g)] = digest
        if embed_inline:
            hex_part = digest.split(":", 1)[1]
            cleaned = raw_text.lstrip("\ufeff").replace("\r\n", "\n").replace("\r", "\n")
            kept_lines = [line for line in cleaned.split("\n") if not _SEAL_LINE_RE.match(line)]
            updated = "\n".join(kept_lines).rstrip() + f"\n\n<!-- sdd:gate-seal gate={g} sha256={hex_part} -->\n"
            doc_path.write_text(updated, encoding="utf-8")

    state["gate_seals"] = new_seals
    state["enforce_gate_seals"] = True
    state_file.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return new_seals


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="SDD Cryptographic SHA-256 Gate Seal Tool (RF-1001)")
    parser.add_argument("--repo-root", type=pathlib.Path, default=_REPO_ROOT, help="Repository root path.")
    parser.add_argument("--work-item", type=str, default=None, help="Optional work item ID assertion.")
    parser.add_argument("--approve", action="store_true", help="Compute and seal approved Gates 1..3.")
    parser.add_argument("--embed-inline", action="store_true", help="Also embed inline HTML gate-seal comments.")
    parser.add_argument("--verify", action="store_true", help="Verify cryptographic seals for Gates 1..3.")
    args = parser.parse_args(argv)
    repo_root = args.repo_root.resolve()

    if args.verify and not args.approve:
        ok, msg = verify_work_item_gate_seals(repo_root, require_seals=True)
        print(f"[OK] {msg}" if ok else f"[ERROR] {msg}")
        return 0 if ok else 1

    try:
        seals = seal_work_item_gates(repo_root, work_item_id=args.work_item, embed_inline=args.embed_inline)
        print(f"[OK] Sealed gates for active work item: {json.dumps(seals)}")
        if args.verify:
            ok, msg = verify_work_item_gate_seals(repo_root, require_seals=True)
            if not ok:
                print(f"[ERROR] {msg}")
                return 1
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
