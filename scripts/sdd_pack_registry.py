#!/usr/bin/env python3
"""Pack registry, manifest validation, and sdd:stack-config YAML parser."""

from __future__ import annotations

import json
import re
from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, Literal, NamedTuple

try:
    from scripts.sdd_vendor_update import VendorIntegrityError, verify_vendor_lock
except ImportError:
    from sdd_vendor_update import VendorIntegrityError, verify_vendor_lock

DEFAULT_VALID_PRESETS: tuple[str, ...] = ("compact", "granular", "api-only", "spa-only")
type YamlScalar = str | bool | int | float | None
type YamlValue = YamlScalar | list[YamlValue] | dict[str, YamlValue]

_OPEN_FENCE_RE = re.compile(r"^[ \t]*(`{3,})(.*)$")
_STACK_CONFIG_INFO_RE = re.compile(r"^yaml[ \t]+sdd:stack-config$", re.IGNORECASE)
_HUMAN_SIGNOFF_MARKERS: tuple[str, ...] = ("[x] Gate S0 Approved", "[X] Gate S0 Approved", "[x] Gate 00 Approved", "[X] Gate 00 Approved")
_INT_RE = re.compile(r"^[+-]?[0-9]+$")
_FLOAT_RE = re.compile(r"^[+-]?(?:[0-9]+\.[0-9]*|\.[0-9]+)$")
_DOUBLE_ESCAPES: dict[str, str] = {"n": "\n", "r": "\r", "t": "\t", "\\": "\\", '"': '"', "/": "/"}
_UIUX_ALLOWED_KEYS: frozenset[str] = frozenset({"enabled", "provider", "version", "hifi_format", "brand_constraints"})
_VALID_HIFI_FORMATS: frozenset[str] = frozenset({"html", "figma", "html+figma"})


class SddGeneratorError(Exception): """Base fail-closed error for squad generation (exits with code 1)."""
class StackConfigError(SddGeneratorError): """Raised when specs/STACK.md or its sdd:stack-config block is invalid."""
class InvalidManifestError(SddGeneratorError): """Raised when a pack.json manifest or declared asset path is invalid."""
class PackDependencyError(SddGeneratorError): """Raised when an active pack's declared dependencies are missing."""
class CollisionError(SddGeneratorError): """Raised when materialized destinations collide or hit unmanaged files."""
class ManualModificationConflictError(SddGeneratorError): """Raised when a managed file on disk differs from the recorded lock hash."""

@dataclass(frozen=True)
class StackConfig:
    """Validated configuration parsed from the sdd:stack-config YAML block."""
    stack_approved: bool; preset: str; packs: tuple[str, ...]; uiux: dict[str, Any] | None = None
    def __init__(self, stack_approved: bool | None = None, preset: str = "compact", packs: tuple[str, ...] = (), uiux: dict[str, Any] | None = None, gate00_approved: bool | None = None) -> None:
        val = stack_approved if stack_approved is not None else (gate00_approved if gate00_approved is not None else False)
        object.__setattr__(self, "stack_approved", bool(val)); object.__setattr__(self, "preset", preset)
        object.__setattr__(self, "packs", tuple(packs)); object.__setattr__(self, "uiux", uiux)
    @property
    def gate00_approved(self) -> bool: return self.stack_approved

@dataclass(frozen=True)
class PackActivation:
    """Resolved activation record indicating pack identity and activation source."""
    name: str
    pack_id: str
    source: Literal["stack-config", "manual"]

@dataclass(frozen=True)
class PackManifest:
    """Validated metadata and asset declarations loaded from pack.json."""
    dir_name: str
    pack_id: str
    family: str
    requires: tuple[str, ...]
    description: str
    rules: tuple[str, ...]
    specialists: tuple[str, ...]
    skills: tuple[str, ...]
    workflows: tuple[str, ...]
    targets: tuple[str, ...] = ()
    upstream: dict[str, Any] | None = None

@dataclass(frozen=True)
class ResolvedPackAssets:
    """Concrete, traversal-verified catalog paths ready for materialization."""
    manifest: PackManifest
    pack_dir: Path
    agent_files: tuple[Path, ...]
    skill_dirs: tuple[tuple[str, Path], ...]
    rule_files: tuple[Path, ...]
    workflow_files: tuple[Path, ...]

_YamlLine = NamedTuple("_YamlLine", [("line_no", int), ("indent", int), ("text", str)])

def _extract_stack_config_block(content: str) -> str | None:
    """Return the single fenced `yaml sdd:stack-config` body or None if absent."""
    blocks, in_target, other_len, current = [], False, 0, []
    for line in content.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        if in_target and re.match(r"^[ \t]*```[ \t]*$", line):
            blocks.append("\n".join(current))
            in_target = False
        elif in_target:
            current.append(line)
        elif other_len:
            other_len = 0 if re.match(rf"^[ \t]*`{{{other_len},}}[ \t]*$", line) else other_len
        elif m := _OPEN_FENCE_RE.match(line):
            ticks, info = m.group(1), m.group(2).strip()
            in_target, current, other_len = (True, [], 0) if len(ticks) == 3 and _STACK_CONFIG_INFO_RE.match(info) else (False, current, len(ticks))
    if in_target or len(blocks) > 1:
        raise StackConfigError(f"{'Unclosed' if in_target else 'Multiple'} ```yaml sdd:stack-config block(s) in STACK.md.")
    return blocks[0] if blocks else None

def _scan_quoted_end(text: str, start: int, line_no: int) -> int:
    """Return index immediately after the closing quote starting at `start`."""
    quote, i = text[start], start + 1
    while i < len(text):
        ch = text[i]
        if quote == '"' and ch == "\\":
            if i + 1 >= len(text):
                raise StackConfigError(f"Trailing escape in string at line {line_no}.")
            i += 2
        elif quote == "'" and text[i : i + 2] == "''":
            i += 2
        elif ch == quote:
            return i + 1
        else:
            i += 1
    raise StackConfigError(f"Unterminated quoted string at line {line_no}.")

def _consume_quoted(raw: str, line_no: int) -> tuple[str, int]:
    """Read a quoted scalar starting at index 0 and return `(value, end_index)`."""
    end_idx = _scan_quoted_end(raw, 0, line_no)
    inner = raw[1 : end_idx - 1]
    if raw[0] == "'":
        return inner.replace("''", "'"), end_idx
    if bad := next((m.group(1) for m in re.finditer(r"\\(.)", inner) if m.group(1) not in _DOUBLE_ESCAPES), None):
        raise StackConfigError(f"Unsupported escape '\\{bad}' at line {line_no}.")
    return re.sub(r"\\(.)", lambda m: _DOUBLE_ESCAPES[m.group(1)], inner), end_idx

def _tokenize_yaml_lines(block_text: str) -> list[_YamlLine]:
    """Strip outside-quote `#` comments, reject tabs, and tokenize YAML lines."""
    tokens: list[_YamlLine] = []
    for line_no, raw in enumerate(block_text.replace("\r\n", "\n").replace("\r", "\n").split("\n"), start=1):
        i, end = 0, len(raw)
        while i < len(raw):
            ch = raw[i]
            if ch in ('"', "'") and (i == 0 or raw[i - 1] in (" ", "\t", ":", "-", "[", ",", "{")):
                i = _scan_quoted_end(raw, i, line_no)
            elif ch == "#" and (i == 0 or raw[i - 1] in (" ", "\t")):
                end = i; break
            else:
                i += 1
        if not (cleaned := raw[:end].rstrip(" \t")):
            continue
        indent = len(cleaned) - len(cleaned.lstrip(" \t"))
        if "\t" in cleaned[:indent]:
            raise StackConfigError(f"Tab indentation is forbidden in YAML at line {line_no}.")
        tokens.append(_YamlLine(line_no, indent, cleaned[indent:]))
    return tokens

def _split_top_level(inner: str, line_no: int) -> list[str]:
    """Split comma-separated flow sequence/mapping items outside quotes and brackets."""
    parts, depth_sq, depth_brace, start, i = [], 0, 0, 0, 0
    while i < len(inner):
        ch = inner[i]
        if ch in ('"', "'") and (i == 0 or inner[i - 1] in (" ", "\t", ",", "[", "{", ":")):
            i = _scan_quoted_end(inner, i, line_no); continue
        depth_sq += (ch == "[") - (ch == "]")
        depth_brace += (ch == "{") - (ch == "}")
        if depth_sq < 0 or depth_brace < 0:
            raise StackConfigError(f"Unbalanced '{ch}' in inline collection at line {line_no}.")
        if ch == "," and depth_sq == 0 and depth_brace == 0:
            if not (seg := inner[start:i].strip()):
                raise StackConfigError(f"Empty item in inline collection at line {line_no}.")
            parts.append(seg); start = i + 1
        i += 1
    if depth_sq or depth_brace or not (tail := inner[start:].strip()):
        raise StackConfigError(f"Malformed inline collection at line {line_no}.")
    return [*parts, tail]

def _find_mapping_colon(text: str) -> int | None:
    """Return index of an unquoted mapping `:` followed by whitespace or EOL."""
    if text.startswith(("-", "[", "{", "#")):
        return None
    return next((i for i, c in enumerate(text) if c == ":" and (i + 1 == len(text) or text[i + 1] in (" ", "\t"))), None)

def _is_mapping_entry(text: str, line_no: int) -> bool:
    """Return True when `text` opens a quoted or unquoted `key: ...` mapping entry."""
    if text.startswith(('"', "'")):
        rest = text[_scan_quoted_end(text, 0, line_no) :].lstrip(" ")
        return rest == ":" or rest.startswith((": ", ":\t"))
    return _find_mapping_colon(text) is not None

def _split_mapping_entry(text: str, line_no: int) -> tuple[str, str]:
    """Split a mapping line `key: value` into `(key, raw_value)`."""
    if text.startswith(('"', "'")):
        key, end_idx = _consume_quoted(text, line_no)
        rest = text[end_idx:].lstrip(" ")
        if not key or not rest.startswith(":") or (len(rest) > 1 and rest[1] not in (" ", "\t")):
            raise StackConfigError(f"Invalid quoted mapping key syntax at line {line_no}.")
        return key, rest[1:].strip()
    if (idx := _find_mapping_colon(text)) is None or not (key := text[:idx].strip()):
        raise StackConfigError(f"Invalid YAML mapping entry '{text}' at line {line_no}.")
    return key, text[idx + 1 :].strip()

def _parse_inline_value(raw: str, line_no: int) -> YamlValue:
    """Parse an inline YAML scalar, flow list `[...]`, or flow mapping `{...}`."""
    text = raw.strip()
    if not text or text in ("null", "~"):
        return None
    if text[0] in ('"', "'"):
        val, end_idx = _consume_quoted(text, line_no)
        if text[end_idx:].strip():
            raise StackConfigError(f"Unexpected trailing text after quoted scalar at line {line_no}.")
        return val
    if text[0] in ("[", "{"):
        close = "]" if text[0] == "[" else "}"
        if not text.endswith(close):
            raise StackConfigError(f"Unterminated inline {'list' if close == ']' else 'mapping'} at line {line_no}.")
        inner = text[1:-1].strip()
        items = _split_top_level(inner, line_no) if inner else []
        if close == "]":
            return [_parse_inline_value(item, line_no) for item in items]
        mapping: dict[str, YamlValue] = {}
        for item in items:
            k, v_raw = _split_mapping_entry(item, line_no)
            if k in mapping:
                raise StackConfigError(f"Duplicate key '{k}' in inline mapping at line {line_no}.")
            mapping[k] = _parse_inline_value(v_raw, line_no)
        return mapping
    if text in ("true", "false"):
        return text == "true"
    return int(text) if _INT_RE.match(text) else (float(text) if _FLOAT_RE.match(text) else text)

def _is_seq_line(text: str) -> bool:
    """Return True if a stripped line opens a YAML block sequence item."""
    return text == "-" or text.startswith(("- ", "-\t"))

def _parse_sequence(tokens: list[_YamlLine], pos: int, base_indent: int) -> tuple[list[YamlValue], int]:
    """Parse a YAML block sequence starting at `pos` with indentation `base_indent`."""
    items: list[YamlValue] = []
    while pos < len(tokens):
        tok = tokens[pos]
        if tok.indent < base_indent or (tok.indent == base_indent and not _is_seq_line(tok.text)):
            break
        if tok.indent > base_indent:
            raise StackConfigError(f"Inconsistent indentation in YAML list at line {tok.line_no}.")
        after_dash = tok.text[1:].lstrip(" \t")
        if not after_dash:
            pos += 1
            if pos < len(tokens) and tokens[pos].indent > base_indent:
                nxt = tokens[pos]
                val, pos = (_parse_sequence if _is_seq_line(nxt.text) else _parse_mapping)(tokens, pos, nxt.indent)
            else:
                val = None
            items.append(val)
        elif _is_mapping_entry(after_dash, tok.line_no):
            item_indent = base_indent + len(tok.text) - len(after_dash)
            tokens[pos] = _YamlLine(tok.line_no, item_indent, after_dash)
            val, pos = _parse_mapping(tokens, pos, item_indent)
            items.append(val)
        else:
            items.append(_parse_inline_value(after_dash, tok.line_no)); pos += 1
    return items, pos

def _parse_mapping(tokens: list[_YamlLine], pos: int, base_indent: int) -> tuple[dict[str, YamlValue], int]:
    """Parse a YAML block mapping starting at `pos` with indentation `base_indent`."""
    mapping: dict[str, YamlValue] = {}
    while pos < len(tokens):
        tok = tokens[pos]
        if tok.indent < base_indent:
            break
        if tok.indent > base_indent or _is_seq_line(tok.text):
            raise StackConfigError(f"Unexpected YAML structure or indentation at line {tok.line_no}.")
        key, raw_val = _split_mapping_entry(tok.text, tok.line_no)
        if key in mapping:
            raise StackConfigError(f"Duplicate YAML key '{key}' at line {tok.line_no}.")
        pos += 1
        if raw_val:
            mapping[key] = _parse_inline_value(raw_val, tok.line_no)
        elif pos < len(tokens) and (tokens[pos].indent > base_indent or (tokens[pos].indent == base_indent and _is_seq_line(tokens[pos].text))):
            nxt = tokens[pos]
            mapping[key], pos = (_parse_sequence if _is_seq_line(nxt.text) else _parse_mapping)(tokens, pos, nxt.indent)
        else:
            mapping[key] = None
    return mapping, pos

def parse_yaml_subset(block_text: str) -> dict[str, YamlValue]:
    """Parse a deterministic YAML subset into a dictionary without external libraries."""
    if not (tokens := _tokenize_yaml_lines(block_text)):
        return {}
    if _is_seq_line(tokens[0].text):
        raise StackConfigError(f"Expected YAML mapping at top level (line {tokens[0].line_no}).")
    data, next_pos = _parse_mapping(tokens, 0, tokens[0].indent)
    if next_pos < len(tokens):
        raise StackConfigError(f"Inconsistent top-level indentation at line {tokens[next_pos].line_no}.")
    return data

def _require_nonempty_str(val: object, label: str, exc_cls: type[SddGeneratorError]) -> str:
    """Validate that `val` is a non-empty string, raising `exc_cls` otherwise."""
    if not isinstance(val, str) or not val.strip():
        raise exc_cls(f"{label} must be a non-empty string.")
    return val

def _validate_safe_rel_parts(entry: str, field_name: str, exc_cls: type[SddGeneratorError]) -> list[str]:
    """Validate relative path syntax without absolutes, drive letters, or `..` traversal."""
    if "\x00" in entry or entry.startswith(("/", "\\")) or PurePosixPath(entry).is_absolute() or PureWindowsPath(entry).is_absolute() or PureWindowsPath(entry).drive:
        raise exc_cls(f"Absolute or unsafe path not permitted in '{field_name}': {entry!r}.")
    parts = [part for part in entry.replace("\\", "/").split("/") if part and part != "."]
    if not parts or ".." in parts:
        raise exc_cls(f"Invalid or traversal path in '{field_name}': {entry!r}.")
    return parts

def _validate_uiux_config(uiux: object, preset: str) -> dict[str, Any] | None:
    """Validate the optional `uiux` configuration block in sdd:stack-config."""
    if uiux is None: return None
    if not isinstance(uiux, dict): raise StackConfigError("'uiux' in sdd:stack-config must be a YAML mapping when specified.")
    if unknown := sorted(set(uiux) - _UIUX_ALLOWED_KEYS):
        raise StackConfigError(f"Unknown key(s) in 'uiux': {', '.join(unknown)}.")
    if not isinstance(enabled := uiux.get("enabled"), bool):
        raise StackConfigError("'uiux.enabled' in sdd:stack-config must be a strict boolean (true/false).")
    if enabled and preset == "api-only":
        raise StackConfigError("'uiux.enabled: true' is incompatible with preset 'api-only'.")
    for key in ("provider", "version"):
        if key in uiux: _require_nonempty_str(uiux[key], f"'uiux.{key}'", StackConfigError)
    if enabled and uiux.get("provider", "ui-ux-pro-max") != "ui-ux-pro-max":
        raise StackConfigError(f"Invalid 'uiux.provider' {uiux['provider']!r}; expected 'ui-ux-pro-max'.")
    if "hifi_format" in uiux and (not isinstance(fmt := uiux["hifi_format"], str) or fmt not in _VALID_HIFI_FORMATS):
        raise StackConfigError(f"Invalid 'uiux.hifi_format' {fmt!r}; expected one of: figma, html, html+figma.")
    if "brand_constraints" in uiux and uiux["brand_constraints"] is not None:
        bc = _require_nonempty_str(uiux["brand_constraints"], "'uiux.brand_constraints'", StackConfigError)
        _validate_safe_rel_parts(bc, "uiux.brand_constraints", StackConfigError)
    return uiux

def parse_stack_config(stack_path: Path, valid_presets: Collection[str] = DEFAULT_VALID_PRESETS) -> tuple[StackConfig, bool]:
    """Parse specs/STACK.md and return `(StackConfig, effective_approved)`."""
    if not stack_path.exists():
        return StackConfig(stack_approved=False, preset="compact", packs=()), False
    try:
        content = stack_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise StackConfigError(f"Cannot read stack file '{stack_path}': {exc}") from exc
    has_human_signoff = any(marker in content for marker in _HUMAN_SIGNOFF_MARKERS)
    if (block := _extract_stack_config_block(content)) is None:
        if has_human_signoff:
            raise StackConfigError("Gate S0 is signed off in STACK.md, but ```yaml sdd:stack-config is missing.")
        return StackConfig(stack_approved=False, preset="compact", packs=()), False
    data = parse_yaml_subset(block)
    has_stack, has_gate00 = "stack_approved" in data, "gate00_approved" in data
    if not has_stack and not has_gate00: raise StackConfigError("Missing 'stack_approved' (or legacy 'gate00_approved') in sdd:stack-config.")
    stack_val, gate00_val = data.get("stack_approved"), data.get("gate00_approved")
    if has_stack and not isinstance(stack_val, bool): raise StackConfigError("'stack_approved' in sdd:stack-config must be a strict boolean (true/false).")
    if has_gate00 and not isinstance(gate00_val, bool): raise StackConfigError("'gate00_approved' in sdd:stack-config must be a strict boolean (true/false).")
    if has_stack and has_gate00 and stack_val != gate00_val: raise StackConfigError("Conflicting 'stack_approved' and legacy 'gate00_approved' in sdd:stack-config.")
    approved, preset, packs = (stack_val if has_stack else gate00_val), data.get("preset", "compact"), data.get("packs", [])
    if not isinstance(preset, str) or preset not in valid_presets:
        raise StackConfigError(f"Invalid preset {preset!r}; expected one of: {', '.join(sorted(valid_presets))}.")
    if not isinstance(packs, list) or any(not isinstance(p, str) or not p.strip() for p in packs):
        raise StackConfigError("'packs' in sdd:stack-config must be a list of non-empty strings.")
    return StackConfig(stack_approved=approved, preset=preset, packs=tuple(packs), uiux=_validate_uiux_config(data.get("uiux"), preset)), has_human_signoff and approved

def _validate_str_list(data: Mapping[str, object], key: str, manifest_path: Path) -> tuple[str, ...]:
    """Validate that `data[key]` is present and contains only non-empty strings."""
    value = data.get(key)
    if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
        raise InvalidManifestError(f"Field '{key}' in {manifest_path} must be a list of non-empty strings.")
    return tuple(value)

def load_pack_manifest(pack_dir: Path) -> PackManifest:
    """Load and schema-validate `<pack_dir>/pack.json`."""
    manifest_path = pack_dir / "pack.json"
    if not manifest_path.is_file():
        raise InvalidManifestError(f"Missing pack manifest: {manifest_path}.")
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InvalidManifestError(f"Invalid pack manifest JSON at {manifest_path}: {exc}") from exc
    if not isinstance(data, dict):
        raise InvalidManifestError(f"Pack manifest root must be a JSON object: {manifest_path}.")
    for req_str in ("id", "family"):
        _require_nonempty_str(data.get(req_str), f"Field '{req_str}' in {manifest_path}", InvalidManifestError)
    if not isinstance(description := data.get("description"), str):
        raise InvalidManifestError(f"Field 'description' must be a string in {manifest_path}.")
    lists = {k: _validate_str_list(data, k, manifest_path) for k in ("requires", "rules", "specialists", "skills", "workflows")}
    targets = _validate_str_list(data, "targets", manifest_path) if "targets" in data else ()
    upstream = data.get("upstream")
    if "upstream" in data:
        if not isinstance(upstream, dict): raise InvalidManifestError(f"Field 'upstream' in {manifest_path} must be a JSON object.")
        if "vendor_lock" in upstream: _require_nonempty_str(upstream["vendor_lock"], f"Field 'upstream.vendor_lock' in {manifest_path}", InvalidManifestError)
    return PackManifest(dir_name=pack_dir.name, pack_id=data["id"], family=data["family"], description=description, targets=targets, upstream=upstream, **lists)

def load_catalog_registry(packs_dir: Path) -> dict[str, PackManifest]:
    """Load and validate all pack manifests under `packs_dir`, indexed by dir_name."""
    if not packs_dir.exists():
        return {}
    if not packs_dir.is_dir():
        raise InvalidManifestError(f"Packs catalog path is not a directory: {packs_dir}.")
    registry: dict[str, PackManifest] = {}
    seen_ids: dict[str, str] = {}
    for child in sorted(packs_dir.iterdir(), key=lambda p: p.name):
        if child.is_dir() and not child.name.startswith(".") and (child / "pack.json").exists():
            manifest = load_pack_manifest(child)
            if manifest.pack_id in seen_ids:
                raise InvalidManifestError(f"Duplicate pack id '{manifest.pack_id}' in '{seen_ids[manifest.pack_id]}' and '{child.name}'.")
            seen_ids[manifest.pack_id] = manifest.dir_name
            registry[manifest.dir_name] = manifest
    return registry

def _resolve_safe_pack_path(pack_root: Path, entry: str, field_name: str) -> Path:
    """Resolve a manifest entry inside `pack_root`, rejecting absolute or traversal paths."""
    parts = _validate_safe_rel_parts(entry, field_name, InvalidManifestError)
    candidate = pack_root.joinpath(*parts).resolve()
    if not candidate.is_relative_to(pack_root) or candidate == pack_root:
        raise InvalidManifestError(f"Asset path escapes pack directory in '{field_name}': {entry!r}.")
    return candidate

def _resolve_file_with_fallback(pack_root: Path, entry: str, field_name: str, fallback_dir: str) -> Path:
    """Resolve a pack file via direct path or `<pack_root>/<fallback_dir>/<basename>`."""
    primary = _resolve_safe_pack_path(pack_root, entry, field_name)
    if primary.is_file():
        return primary
    fallback = (pack_root / fallback_dir / PurePosixPath(entry.replace("\\", "/")).name).resolve()
    if fallback.is_relative_to(pack_root) and fallback.is_file():
        return fallback
    raise InvalidManifestError(f"Declared {field_name} asset not found in {pack_root.name}: {entry!r}.")

def resolve_pack_assets(manifest: PackManifest, pack_dir: Path) -> ResolvedPackAssets:
    """Verify and resolve all specialist, skill, rule, workflow, and vendor-lock paths for a pack."""
    pack_root = pack_dir.resolve()
    if manifest.upstream and "vendor_lock" in manifest.upstream:
        lock_rel = _require_nonempty_str(manifest.upstream["vendor_lock"], f"Field 'upstream.vendor_lock' in {manifest.dir_name}", InvalidManifestError)
        if pack_root.joinpath(*_validate_safe_rel_parts(lock_rel, "upstream.vendor_lock", InvalidManifestError)).is_symlink():
            raise InvalidManifestError(f"Symlink not permitted for 'upstream.vendor_lock': {lock_rel!r}.")
        lock_path = _resolve_safe_pack_path(pack_root, lock_rel, "upstream.vendor_lock")
        if not lock_path.is_file():
            raise InvalidManifestError(f"Declared upstream.vendor_lock file not found in {pack_root.name}: {lock_rel!r}.")
        try:
            verify_vendor_lock(lock_path.parent, lock_path)
        except VendorIntegrityError as exc:
            raise InvalidManifestError(str(exc)) from exc
    agent_files = tuple(_resolve_safe_pack_path(pack_root, e, "specialists") for e in manifest.specialists)
    for entry, target in zip(manifest.specialists, agent_files):
        if not target.is_file() or target.suffix != ".md":
            raise InvalidManifestError(f"Specialist must be an existing .md file in {pack_root.name}: {entry!r}.")
    skill_dirs: list[tuple[str, Path]] = []
    for entry in manifest.skills:
        target_dir = _resolve_safe_pack_path(pack_root, entry, "skills")
        skill_md = (target_dir / "SKILL.md").resolve()
        if not target_dir.is_dir() or not skill_md.is_relative_to(target_dir) or not skill_md.is_file():
            raise InvalidManifestError(f"Skill directory missing SKILL.md in {pack_root.name}: {entry!r}.")
        skill_dirs.append((PurePosixPath(entry.replace("\\", "/").rstrip("/")).name, target_dir))
    return ResolvedPackAssets(
        manifest=manifest, pack_dir=pack_root, agent_files=agent_files, skill_dirs=tuple(skill_dirs),
        rule_files=tuple(_resolve_file_with_fallback(pack_root, e, "rules", "rules") for e in manifest.rules),
        workflow_files=tuple(_resolve_file_with_fallback(pack_root, e, "workflows", "workflows") for e in manifest.workflows),
    )

def resolve_active_packs(
    config: StackConfig, effective_gate00_approved: bool, cli_packs: Sequence[str] | None,
    packs_dir: Path, registry: Mapping[str, PackManifest] | None = None,
) -> tuple[tuple[PackActivation, ...], tuple[ResolvedPackAssets, ...]]:
    """Resolve, deduplicate, dependency-check, and asset-validate active packs."""
    if effective_gate00_approved:
        has_ui_pack = any(p.strip() in {"capability-ui-design", "capability:ui-design"} for p in config.packs)
        uiux_enabled = isinstance(config.uiux, dict) and config.uiux.get("enabled") is True
        if uiux_enabled != has_ui_pack:
            raise StackConfigError("Inconsistent sdd:stack-config: 'uiux.enabled' and 'capability-ui-design' in 'packs' must match when Gate 00 is approved.")
    requests: list[tuple[str, Literal["stack-config", "manual"]]] = [
        *((p, "stack-config") for p in (config.packs if effective_gate00_approved else ())),
        *((p, "manual") for p in (cli_packs or ())),
    ]
    if not requests:
        return (), ()
    if not packs_dir.is_dir():
        raise InvalidManifestError(f"Packs catalog directory does not exist: {packs_dir}.")
    lookup = {k: m for m in registry.values() for k in (m.dir_name, m.pack_id)} if registry is not None else {}
    catalog_loaded, packs_root = registry is not None, packs_dir.resolve()
    resolved: dict[str, tuple[PackActivation, PackManifest]] = {}
    for raw_ref, source in requests:
        clean_ref = raw_ref.strip()
        if not clean_ref or "/" in clean_ref or "\\" in clean_ref or ".." in clean_ref:
            raise InvalidManifestError(f"Invalid pack identifier: {raw_ref!r}.")
        manifest = lookup.get(clean_ref)
        if manifest is None and ":" not in clean_ref:
            direct_dir = (packs_root / clean_ref).resolve()
            if direct_dir.is_relative_to(packs_root) and direct_dir.is_dir():
                manifest = load_pack_manifest(direct_dir)
                lookup[manifest.dir_name] = lookup[manifest.pack_id] = manifest
        if manifest is None and not catalog_loaded:
            lookup.update({k: m for m in load_catalog_registry(packs_dir).values() for k in (m.dir_name, m.pack_id)})
            catalog_loaded, manifest = True, lookup.get(clean_ref)
        if manifest is None:
            raise InvalidManifestError(f"Requested pack {raw_ref!r} not found in catalog {packs_dir}.")
        resolved.setdefault(manifest.dir_name, (PackActivation(manifest.dir_name, manifest.pack_id, source), manifest))
    manifests = [m for _, m in resolved.values()]
    active_refs = {ref for m in manifests for ref in (m.dir_name, m.pack_id)}
    for m in manifests:
        if missing := [req for req in m.requires if req not in active_refs]:
            raise PackDependencyError(f"Pack '{m.dir_name}' ({m.pack_id}) requires missing pack(s): {', '.join(missing)}.")
    return tuple(act for act, _ in resolved.values()), tuple(resolve_pack_assets(m, packs_dir / m.dir_name) for m in manifests)

__all__ = [
    "CollisionError", "DEFAULT_VALID_PRESETS", "InvalidManifestError", "ManualModificationConflictError",
    "PackActivation", "PackDependencyError", "PackManifest", "ResolvedPackAssets", "SddGeneratorError",
    "StackConfig", "StackConfigError", "load_catalog_registry", "load_pack_manifest",
    "parse_stack_config", "parse_yaml_subset", "resolve_active_packs", "resolve_pack_assets",
]
