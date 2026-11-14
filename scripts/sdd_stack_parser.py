#!/usr/bin/env python3
"""Markdown sanitization, strict YAML subset parser, and STACK.md config loader."""

from __future__ import annotations

from collections.abc import Collection
from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
from typing import Any, NamedTuple

DEFAULT_VALID_PRESETS: tuple[str, ...] = ("compact", "granular", "api-only", "spa-only")
type YamlScalar = str | bool | int | float | None
type YamlValue = YamlScalar | list[YamlValue] | dict[str, YamlValue]

_OPEN_FENCE_RE = re.compile(r"^[ \t]*(`{3,}|~{3,})(.*)$")
_STACK_CONFIG_INFO_RE = re.compile(r"^yaml[ \t]+sdd:stack-config$", re.IGNORECASE)
_HUMAN_SIGNOFF_MARKERS: tuple[str, ...] = (
    "[x] Gate S0 Approved",
    "[X] Gate S0 Approved",
    "[x] Gate 00 Approved",
    "[X] Gate 00 Approved",
)
_EJ_PLACEHOLDER_RE = re.compile(r"\[ej:[^\]]*\]", re.IGNORECASE)
_STRIKETHROUGH_RE = re.compile(r"~~[^~\n]*~~")
_INT_RE = re.compile(r"^[+-]?[0-9]+$")
_FLOAT_RE = re.compile(r"^[+-]?(?:[0-9]+\.[0-9]*|\.[0-9]+)$")
_DOUBLE_ESCAPES: dict[str, str] = {"n": "\n", "r": "\r", "t": "\t", "\\": "\\", '"': '"', "/": "/"}
_UIUX_ALLOWED_KEYS: frozenset[str] = frozenset({"enabled", "provider", "version", "hifi_format", "brand_constraints"})
_VALID_HIFI_FORMATS: frozenset[str] = frozenset({"html", "figma", "html+figma"})


class SddGeneratorError(Exception):
    """Base fail-closed error for squad generation (exits with code 1)."""


class StackConfigError(SddGeneratorError):
    """Raised when specs/STACK.md or its sdd:stack-config block is invalid."""


class PackCompatibilityError(StackConfigError):
    """Raised when active packs or UI/UX settings are incompatible with the target preset."""


class InvalidManifestError(SddGeneratorError):
    """Raised when a pack.json manifest or declared asset path is invalid."""


class PackDependencyError(SddGeneratorError):
    """Raised when an active pack's declared dependencies are missing."""


class CollisionError(SddGeneratorError):
    """Raised when materialized destinations collide or hit unmanaged files."""


class ManualModificationConflictError(SddGeneratorError):
    """Raised when a managed file on disk differs from the recorded lock hash."""


@dataclass(frozen=True)
class StackConfig:
    """Validated configuration parsed from the sdd:stack-config YAML block."""

    stack_approved: bool
    preset: str
    packs: tuple[str, ...]
    uiux: dict[str, Any] | None = None

    def __init__(
        self,
        stack_approved: bool | None = None,
        preset: str = "compact",
        packs: tuple[str, ...] = (),
        uiux: dict[str, Any] | None = None,
        gate00_approved: bool | None = None,
    ) -> None:
        val = stack_approved if stack_approved is not None else (gate00_approved if gate00_approved is not None else False)
        object.__setattr__(self, "stack_approved", bool(val))
        object.__setattr__(self, "preset", preset)
        object.__setattr__(self, "packs", tuple(packs))
        object.__setattr__(self, "uiux", uiux)

    @property
    def gate00_approved(self) -> bool:
        return self.stack_approved


_YamlLine = NamedTuple("_YamlLine", [("line_no", int), ("indent", int), ("text", str)])


def _strip_html_comments_line(line: str, in_comment: bool) -> tuple[str, bool]:
    """Strip HTML comments from one non-fenced markdown line while preserving comment state."""
    out: list[str] = []
    i, n = 0, len(line)
    while i < n:
        if in_comment:
            end = line.find("-->", i)
            if end == -1:
                return "".join(out), True
            in_comment, i = False, end + 3
        elif line.startswith("<!--", i):
            in_comment, i = True, i + 4
        else:
            out.append(line[i])
            i += 1
    return "".join(out), in_comment


def _scan_stack_markdown(content: str) -> tuple[str, str | None]:
    """Return `(normative_prose, stack_config_yaml_or_none)` ignoring HTML comments and non-target fences."""
    prose_lines: list[str] = []
    blocks: list[str] = []
    current_block: list[str] = []
    in_comment = False
    fence_char = ""
    fence_len = 0
    in_target = False

    for line in content.lstrip("\ufeff").replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        if fence_char:
            if re.match(rf"^[ \t]*{re.escape(fence_char)}{{{fence_len},}}[ \t]*$", line):
                if in_target:
                    blocks.append("\n".join(current_block))
                fence_char, fence_len, in_target, current_block = "", 0, False, []
            elif in_target:
                current_block.append(line)
            continue

        cleaned, in_comment = _strip_html_comments_line(line, in_comment)
        if m := _OPEN_FENCE_RE.match(cleaned):
            ticks, info = m.group(1), m.group(2).strip()
            ch = ticks[0]
            if not (ch == "`" and "`" in info):
                fence_char, fence_len = ch, len(ticks)
                is_target = ch == "`" and len(ticks) == 3 and bool(_STACK_CONFIG_INFO_RE.match(info))
                in_target, current_block = is_target, []
                continue
        prose_lines.append(cleaned)

    if in_target or len(blocks) > 1:
        raise StackConfigError(f"{'Unclosed' if in_target else 'Multiple'} ```yaml sdd:stack-config block(s) in STACK.md.")
    prose = _STRIKETHROUGH_RE.sub("", _EJ_PLACEHOLDER_RE.sub("", "\n".join(prose_lines)))
    return prose, (blocks[0] if blocks else None)


def strip_non_normative_markdown(content: str) -> str:
    """Strip HTML comments, fenced code blocks, and placeholder/strikethrough spans."""
    prose, _ = _scan_stack_markdown(content)
    return prose


def _extract_stack_config_block(content: str) -> str | None:
    """Return the single active fenced `yaml sdd:stack-config` body or None if absent."""
    _, block = _scan_stack_markdown(content)
    return block


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
                end = i
                break
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
            i = _scan_quoted_end(inner, i, line_no)
            continue
        depth_sq += (ch == "[") - (ch == "]")
        depth_brace += (ch == "{") - (ch == "}")
        if depth_sq < 0 or depth_brace < 0:
            raise StackConfigError(f"Unbalanced '{ch}' in inline collection at line {line_no}.")
        if ch == "," and depth_sq == 0 and depth_brace == 0:
            if not (seg := inner[start:i].strip()):
                raise StackConfigError(f"Empty item in inline collection at line {line_no}.")
            parts.append(seg)
            start = i + 1
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
    low = text.lower()
    if low in ("true", "false"):
        return low == "true"
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
            items.append(_parse_inline_value(after_dash, tok.line_no))
            pos += 1
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
    if uiux is None:
        return None
    if not isinstance(uiux, dict):
        raise StackConfigError("'uiux' in sdd:stack-config must be a YAML mapping when specified.")
    if unknown := sorted(set(uiux) - _UIUX_ALLOWED_KEYS):
        raise StackConfigError(f"Unknown key(s) in 'uiux': {', '.join(unknown)}.")
    if not isinstance(enabled := uiux.get("enabled"), bool):
        raise StackConfigError("'uiux.enabled' in sdd:stack-config must be a strict boolean (true/false).")
    if enabled and preset == "api-only":
        raise PackCompatibilityError("'uiux.enabled: true' is incompatible with preset 'api-only'.")
    for key in ("provider", "version"):
        if key in uiux:
            _require_nonempty_str(uiux[key], f"'uiux.{key}'", StackConfigError)
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
    normative_prose, block = _scan_stack_markdown(content)
    has_human_signoff = any(marker in normative_prose for marker in _HUMAN_SIGNOFF_MARKERS)
    if block is None:
        if has_human_signoff:
            raise StackConfigError("Gate S0 is signed off in STACK.md, but ```yaml sdd:stack-config is missing.")
        return StackConfig(stack_approved=False, preset="compact", packs=()), False
    data = parse_yaml_subset(block)
    has_stack, has_gate00 = "stack_approved" in data, "gate00_approved" in data
    if not has_stack and not has_gate00:
        raise StackConfigError("Missing 'stack_approved' (or legacy 'gate00_approved') in sdd:stack-config.")
    stack_val, gate00_val = data.get("stack_approved"), data.get("gate00_approved")
    if has_stack and not isinstance(stack_val, bool):
        raise StackConfigError("'stack_approved' in sdd:stack-config must be a strict boolean (true/false).")
    if has_gate00 and not isinstance(gate00_val, bool):
        raise StackConfigError("'gate00_approved' in sdd:stack-config must be a strict boolean (true/false).")
    if has_stack and has_gate00 and stack_val != gate00_val:
        raise StackConfigError("Conflicting 'stack_approved' and legacy 'gate00_approved' in sdd:stack-config.")
    approved, preset, packs = (stack_val if has_stack else gate00_val), data.get("preset", "compact"), data.get("packs", [])
    if not isinstance(preset, str) or preset not in valid_presets:
        raise StackConfigError(f"Invalid preset {preset!r}; expected one of: {', '.join(sorted(valid_presets))}.")
    if not isinstance(packs, list) or any(not isinstance(p, str) or not p.strip() for p in packs):
        raise StackConfigError("'packs' in sdd:stack-config must be a list of non-empty strings.")
    return (
        StackConfig(stack_approved=approved, preset=preset, packs=tuple(packs), uiux=_validate_uiux_config(data.get("uiux"), preset)),
        has_human_signoff and approved,
    )
