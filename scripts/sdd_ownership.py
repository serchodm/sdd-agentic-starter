#!/usr/bin/env python3
"""Declarative sdd:ownership-map parser, overlap/coverage validator, and builder compiler."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
from typing import Any, Literal

try:
    from scripts.sdd_pack_registry import SddGeneratorError, StackConfigError, parse_yaml_subset
    from scripts.sdd_stack_parser import _strip_html_comments_line
except ImportError:
    from sdd_pack_registry import SddGeneratorError, StackConfigError, parse_yaml_subset
    from sdd_stack_parser import _strip_html_comments_line

DEFAULT_CANDIDATE_ROOTS: tuple[str, ...] = ("src", "backend", "frontend", "DDBB")
_OPEN_FENCE_RE = re.compile(r"^[ \t]*(`{3,}|~{3,})(.*)$")
_OWNERSHIP_INFO_RE = re.compile(r"^yaml[ \t]+sdd:ownership-map$", re.IGNORECASE)
_OWNER_SLUG_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
_TOP_KEYS: frozenset[str] = frozenset({"zones", "unowned_policy", "preset"})
_ZONE_KEYS: frozenset[str] = frozenset(
    {"id", "zone_id", "name", "owner", "builder", "paths", "zone_paths", "archetype", "dod", "forbid_imports", "governance"}
)
VALID_ZONE_GOVERNANCE: frozenset[str] = frozenset({"governed", "legacy-readonly"})
_POLICY_ALIASES: dict[str, Literal["error", "warn"]] = {"error": "error", "fail-closed": "error", "warn": "warn"}
_IGNORED_FILES: frozenset[str] = frozenset({".gitkeep", ".keep", ".DS_Store", "Thumbs.db"})
_IGNORED_DIRS: frozenset[str] = frozenset(
    {"__pycache__", ".mypy_cache", ".pytest_cache", ".ruff_cache", "node_modules", ".venv", "venv", ".git"}
)
_IGNORED_SUFFIXES: frozenset[str] = frozenset({".pyc", ".pyo"})
_DOD_PRIORITY: tuple[str, ...] = ("unit", "suite", "lint_typecheck", "integration", "build", "env")
_SAMPLE_ASCII: tuple[str, ...] = tuple(chr(c) for c in range(32, 127) if chr(c) != "/")


class OwnershipError(SddGeneratorError):
    """Fail-closed error raised when sdd:ownership-map is malformed, overlapping, or incomplete."""


@dataclass(frozen=True)
class OwnershipZone:
    """Single declared ownership zone parsed from sdd:ownership-map."""
    zone_id: str
    owner: str
    paths: tuple[str, ...]
    archetype: str | None = None
    dod: str | None = None
    forbid_imports: tuple[str, ...] = ()
    governance: Literal["governed", "legacy-readonly"] = "governed"

    def __post_init__(self) -> None:
        object.__setattr__(self, "paths", tuple(self.paths))
        object.__setattr__(self, "forbid_imports", tuple(self.forbid_imports))
        if self.governance not in VALID_ZONE_GOVERNANCE:
            raise OwnershipError(f"Invalid zone governance {self.governance!r}; expected 'governed' or 'legacy-readonly'.")

    @property
    def id(self) -> str: return self.zone_id
    @property
    def builder(self) -> str: return self.owner
    @property
    def zone_paths(self) -> tuple[str, ...]: return self.paths


@dataclass(frozen=True)
class OwnershipMapConfig:
    """Validated sdd:ownership-map configuration extracted from specs/STACK.md."""
    zones: tuple[OwnershipZone, ...]
    unowned_policy: Literal["error", "warn"] = "error"
    preset: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "zones", tuple(self.zones))
        if self.unowned_policy not in ("error", "warn"):
            raise OwnershipError(f"Invalid unowned_policy {self.unowned_policy!r}; expected 'error' or 'warn'.")


def _extract_ownership_block(content: str) -> str | None:
    """Return the single active fenced `yaml sdd:ownership-map` body or None if absent."""
    blocks: list[str] = []
    current: list[str] = []
    in_comment, fence_char, fence_len, in_target = False, "", 0, False

    for line in content.lstrip("\ufeff").replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        if fence_char:
            if re.match(rf"^[ \t]*{re.escape(fence_char)}{{{fence_len},}}[ \t]*$", line):
                if in_target:
                    blocks.append("\n".join(current))
                fence_char, fence_len, in_target, current = "", 0, False, []
            elif in_target:
                current.append(line)
            continue

        cleaned, in_comment = _strip_html_comments_line(line, in_comment)
        if m := _OPEN_FENCE_RE.match(cleaned):
            ticks, info = m.group(1), m.group(2).strip()
            ch = ticks[0]
            if not (ch == "`" and "`" in info):
                fence_char, fence_len = ch, len(ticks)
                in_target = ch == "`" and bool(_OWNERSHIP_INFO_RE.match(info))
                current = []
                continue

    if in_target or len(blocks) > 1:
        raise OwnershipError(f"{'Unclosed' if in_target else 'Multiple'} ```yaml sdd:ownership-map block(s) in STACK.md.")
    return blocks[0] if blocks else None

def _require_str(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise OwnershipError(f"{label} must be a non-empty string.")
    return value.strip()

def _normalize_owner(raw: object, label: str) -> str:
    text = _require_str(raw, label).lstrip("@").strip()
    if not text or not _OWNER_SLUG_RE.match(text):
        raise OwnershipError(f"{label} contains invalid agent identifier: {raw!r}.")
    return text

def _expand_braces(pattern: str) -> tuple[str, ...]:
    """Expand non-nested `{a,b}` glob alternatives deterministically (max 16)."""
    if "{" not in pattern and "}" not in pattern:
        return (pattern,)
    if re.search(r"\{[^{}]*\{", pattern):
        raise OwnershipError(f"Nested brace group not supported in ownership glob: {pattern!r}.")
    items = [pattern]
    while any("{" in p or "}" in p for p in items):
        nxt: list[str] = []
        for item in items:
            if not (m := re.search(r"\{([^{}]+)\}", item)):
                raise OwnershipError(f"Malformed brace group in ownership glob: {pattern!r}.")
            opts = m.group(1).split(",")
            if any(not o for o in opts):
                raise OwnershipError(f"Empty alternative in brace group of ownership glob: {pattern!r}.")
            nxt.extend(item[: m.start()] + o + item[m.end() :] for o in opts)
        if len(nxt) > 16:
            raise OwnershipError(f"Too many brace alternatives (>16) in ownership glob: {pattern!r}.")
        items = nxt
    return tuple(items)

def _normalize_glob(raw: object) -> tuple[tuple[str, ...], ...]:
    """Validate a POSIX glob pattern and return expanded normalized segment tuples."""
    if not isinstance(raw, str) or not raw or raw != raw.strip():
        raise OwnershipError(f"Ownership path glob must be a non-empty trimmed string: {raw!r}.")
    if "\x00" in raw or "\\" in raw or "//" in raw:
        raise OwnershipError(f"Invalid characters or separator in ownership glob: {raw!r}.")
    cleaned = raw[:-1] + "/**" if raw.endswith("/") and len(raw) > 1 else raw
    expanded: list[tuple[str, ...]] = []
    for variant in _expand_braces(cleaned):
        if variant.startswith("/") or PurePosixPath(variant).is_absolute() or PureWindowsPath(variant).is_absolute() or PureWindowsPath(variant).drive:
            raise OwnershipError(f"Absolute paths are forbidden in ownership glob: {raw!r}.")
        parts = variant.split("/")
        if any(not part or part in (".", "..") for part in parts):
            raise OwnershipError(f"Relative '.' or '..' traversal forbidden in ownership glob: {raw!r}.")
        collapsed: list[str] = []
        for part in parts:
            if part != "**":
                collapsed.append(re.sub(r"\*{2,}", "*", part))
            elif not collapsed or collapsed[-1] != "**":
                collapsed.append("**")
        expanded.append(tuple(collapsed))
    return tuple(expanded)

def _compile_seg_tokens(pattern: str) -> tuple[tuple[str, Any], ...]:
    """Compile a single path-segment glob pattern into linear NFA tokens."""
    tokens: list[tuple[str, Any]] = []
    i, n = 0, len(pattern)
    while i < n:
        ch = pattern[i]
        if ch == "*" or ch == "?":
            if ch == "?" or not tokens or tokens[-1][0] != "*":
                tokens.append((ch, None))
            i += 1
        elif ch == "[":
            k0 = i + 1 + (1 if i + 1 < n and pattern[i + 1] in ("!", "^") else 0)
            j = pattern.find("]", k0 + (1 if k0 < n and pattern[k0] == "]" else 0))
            if j == -1 or j == k0:
                tokens.append(("lit", "["))
                i += 1
                continue
            neg, spec = k0 > i + 1, pattern[k0:j]
            chars, ranges, k = set(), [], 0
            while k < len(spec):
                if k + 2 < len(spec) and spec[k + 1] == "-":
                    if spec[k] <= spec[k + 2]:
                        ranges.append((spec[k], spec[k + 2]))
                    k += 3
                else:
                    chars.add(spec[k])
                    k += 1
            tokens.append(("class", (neg, frozenset(chars), tuple(ranges))))
            i = j + 1
        else:
            tokens.append(("lit", ch))
            i += 1
    return tuple(tokens)

def _tok_match(tok: tuple[str, Any], ch: str) -> bool:
    if tok[0] in ("*", "?"):
        return True
    if tok[0] == "lit":
        return ch == tok[1]
    neg, chars, ranges = tok[1]
    hit = ch in chars or any(lo <= ch <= hi for lo, hi in ranges)
    return not hit if neg else hit

def _tok_share(t1: tuple[str, Any], t2: tuple[str, Any]) -> bool:
    if t1[0] in ("*", "?") and t2[0] in ("*", "?"):
        return True
    if t1[0] == "lit" or t2[0] == "lit":
        return _tok_match(t2, t1[1]) if t1[0] == "lit" else _tok_match(t1, t2[1])
    cands = set(_SAMPLE_ASCII) | {"\u00e9"}
    for kind, val in (t1, t2):
        if kind == "class":
            cands.update(val[1], *(x for pair in val[2] for x in pair))
    cands.discard("/")
    return any(_tok_match(t1, c) and _tok_match(t2, c) for c in cands)

def _tokens_intersect(ta: tuple[tuple[str, Any], ...], tb: tuple[tuple[str, Any], ...]) -> bool:
    na, nb, stack, visited = len(ta), len(tb), [(0, 0, False)], set()
    while stack:
        if (state := stack.pop()) in visited:
            continue
        visited.add(state)
        ia, ib, ne = state
        if ia == na and ib == nb and ne:
            return True
        if ia < na and ta[ia][0] == "*":
            stack.append((ia + 1, ib, ne))
        if ib < nb and tb[ib][0] == "*":
            stack.append((ia, ib + 1, ne))
        if ia < na and ib < nb and _tok_share(ta[ia], tb[ib]):
            stack.append((ia if ta[ia][0] == "*" else ia + 1, ib if tb[ib][0] == "*" else ib + 1, True))
    return False

def _segs_intersect(segs_a: tuple[str, ...], segs_b: tuple[str, ...], *, b_is_literal: bool = False) -> bool:
    """Return True iff `segs_a` and `segs_b` can match a common concrete file path."""
    na, nb, stack, visited = len(segs_a), len(segs_b), [(0, 0, False, False)], set()
    while stack:
        if (state := stack.pop()) in visited:
            continue
        visited.add(state)
        ia, ib, ua, ub = state
        if ia == na and ib == nb:
            return True
        a_s2, b_s2 = ia < na and segs_a[ia] == "**", not b_is_literal and ib < nb and segs_b[ib] == "**"
        if a_s2 and (ia < na - 1 or ua):
            stack.append((ia + 1, ib, ua, ub))
        if b_s2 and (ib < nb - 1 or ub):
            stack.append((ia, ib + 1, ua, ub))
        if ia < na and ib < nb:
            nua, nub = ua or (a_s2 and ia == na - 1), ub or (b_s2 and ib == nb - 1)
            if a_s2 and b_s2:
                stack.append((ia, ib, nua, nub))
            elif a_s2 or b_s2:
                stack.append((ia if a_s2 else ia + 1, ib + 1 if a_s2 else ib, nua if a_s2 else ua, ub if a_s2 else nub))
            else:
                tb = tuple(("lit", c) for c in segs_b[ib]) if b_is_literal else _compile_seg_tokens(segs_b[ib])
                if _tokens_intersect(_compile_seg_tokens(segs_a[ia]), tb):
                    stack.append((ia + 1, ib + 1, ua, ub))
    return False

def glob_matches_path(glob_pattern: str, rel_posix_path: str) -> bool:
    """Return True iff POSIX glob `glob_pattern` matches repo-relative file `rel_posix_path`."""
    path_segs = tuple(p for p in rel_posix_path.split("/") if p)
    return bool(path_segs) and any(_segs_intersect(gs, path_segs, b_is_literal=True) for gs in _normalize_glob(glob_pattern))

def zone_matches_path(zone: OwnershipZone, rel_posix_path: str) -> bool:
    """Return True iff any glob in `zone.paths` matches `rel_posix_path`."""
    return any(glob_matches_path(pattern, rel_posix_path) for pattern in zone.paths)

def resolve_path_zone(config: OwnershipMapConfig, rel_posix_path: str) -> OwnershipZone | None:
    """Return the declared OwnershipZone matching `rel_posix_path`, or None."""
    return next((z for z in config.zones if zone_matches_path(z, rel_posix_path)), None)

def derive_candidate_roots(config: OwnershipMapConfig, base_roots: Sequence[str] = DEFAULT_CANDIDATE_ROOTS) -> tuple[str, ...]:
    """Merge `base_roots` with static top-level directory prefixes extracted from `config.zones`."""
    extra = (
        segs[0] for z in config.zones for p in z.paths for segs in _normalize_glob(p)
        if len(segs) > 1 and segs[0] not in (".", "..") and not any(ch in segs[0] for ch in "*?[")
    )
    return tuple(dict.fromkeys((*base_roots, *extra)))

def _parse_dod(raw_dod: object, label: str) -> str | None:
    if raw_dod is None:
        return None
    if isinstance(raw_dod, str):
        return _require_str(raw_dod, label)
    if isinstance(raw_dod, list) and raw_dod:
        return " && ".join(_require_str(item, label) for item in raw_dod)
    if isinstance(raw_dod, dict) and raw_dod:
        return " && ".join(_require_str(val, f"{label}.{k}") for k, val in raw_dod.items())
    raise OwnershipError(f"{label} must be a non-empty string, list, or mapping of strings.")

def _parse_forbid_imports(raw: object, label: str) -> tuple[str, ...]:
    if raw is None:
        return ()
    if not isinstance(raw, list):
        raise OwnershipError(f"{label} must be a list of non-empty module strings.")
    seen: list[str] = []
    for item in raw:
        cleaned = _require_str(item, label)
        if any(ch in cleaned for ch in ("\x00", "\n", "\r", ",", ";")):
            raise OwnershipError(f"Invalid character in {label} entry: {item!r}.")
        if cleaned not in seen:
            seen.append(cleaned)
    return tuple(seen)

def _parse_zone_entry(zone_id: str, raw: object, label: str) -> OwnershipZone:
    if not isinstance(raw, dict):
        raise OwnershipError(f"{label} must be a YAML mapping.")
    if unknown := sorted(set(raw) - _ZONE_KEYS):
        raise OwnershipError(f"Unknown key(s) in {label}: {', '.join(unknown)}.")
    if "owner" in raw and "builder" in raw and _normalize_owner(raw["owner"], f"{label}.owner") != _normalize_owner(raw["builder"], f"{label}.builder"):
        raise OwnershipError(f"Conflicting 'owner' and 'builder' in {label}.")
    if (raw_owner := raw.get("owner") if "owner" in raw else raw.get("builder")) is None:
        raise OwnershipError(f"Missing required 'owner' (or 'builder') in {label}.")
    owner = _normalize_owner(raw_owner, f"{label}.owner")
    if "paths" in raw and "zone_paths" in raw and raw["paths"] != raw["zone_paths"]:
        raise OwnershipError(f"Conflicting 'paths' and 'zone_paths' in {label}.")
    raw_paths = raw.get("paths") if "paths" in raw else raw.get("zone_paths")
    if not isinstance(raw_paths, list) or not raw_paths:
        raise OwnershipError(f"Field 'paths' (or 'zone_paths') in {label} must be a non-empty list.")
    paths = tuple(_require_str(p, f"{label}.paths") for p in raw_paths)
    for p in paths:
        _normalize_glob(p)
    archetype = _require_str(raw["archetype"], f"{label}.archetype") if raw.get("archetype") is not None else None
    if archetype is not None and ("/" in archetype or "\\" in archetype or ".." in archetype):
        raise OwnershipError(f"Invalid archetype name in {label}: {archetype!r}.")
    raw_gov = raw.get("governance")
    norm_gov = raw_gov.strip().lower() if isinstance(raw_gov, str) else None
    if raw_gov is not None and norm_gov not in VALID_ZONE_GOVERNANCE:
        raise OwnershipError(f"Invalid 'governance' {raw_gov!r} in {label}; expected 'governed' or 'legacy-readonly'.")
    governance: Literal["governed", "legacy-readonly"] = "legacy-readonly" if norm_gov == "legacy-readonly" else "governed"
    return OwnershipZone(
        zone_id=zone_id, owner=owner, paths=paths, archetype=archetype, governance=governance,
        dod=_parse_dod(raw.get("dod"), f"{label}.dod"),
        forbid_imports=_parse_forbid_imports(raw.get("forbid_imports"), f"{label}.forbid_imports"),
    )

def parse_ownership_map(stack_path: Path) -> OwnershipMapConfig | None:
    """Parse 0 or 1 ```yaml sdd:ownership-map block from `stack_path` (fail-closed)."""
    if not stack_path.exists() and not stack_path.is_symlink():
        return None
    if not stack_path.is_file():
        raise OwnershipError(f"Stack path is not a regular file: '{stack_path}'.")
    try:
        content = stack_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise OwnershipError(f"Cannot read stack file '{stack_path}': {exc}") from exc
    if (block := _extract_ownership_block(content)) is None:
        return None
    try:
        data = parse_yaml_subset(block)
    except StackConfigError as exc:
        raise OwnershipError(f"Malformed YAML in sdd:ownership-map: {exc}") from exc
    if "ownership" in data and len(data) == 1 and isinstance(data["ownership"], dict):
        data = data["ownership"]
    if unknown := sorted(set(data) - _TOP_KEYS):
        raise OwnershipError(f"Unknown key(s) in sdd:ownership-map: {', '.join(unknown)}.")
    if "zones" not in data:
        raise OwnershipError("Missing required 'zones' field in sdd:ownership-map.")
    raw_zones, zones, seen_ids = data["zones"], [], set()
    if isinstance(raw_zones, dict):
        items = [(k, e, f"zones.{k}", False) for k, e in raw_zones.items()]
    elif isinstance(raw_zones, list):
        items = [(None, e, f"zones[{idx}]", True) for idx, e in enumerate(raw_zones, start=1)]
    else:
        raise OwnershipError("'zones' in sdd:ownership-map must be a YAML mapping or list.")
    for key, entry, label, is_list in items:
        if not isinstance(entry, dict):
            raise OwnershipError(f"{label} in sdd:ownership-map must be a YAML mapping.")
        exp = entry.get("id") or entry.get("zone_id") or (entry.get("name") if is_list else None)
        zid = (_require_str(exp, f"{label}.id") if exp is not None else f"zone-{len(zones) + 1}") if is_list else _require_str(key, "zone id")
        if not is_list and exp is not None and _require_str(exp, f"{label}.id") != zid:
            raise OwnershipError(f"Mismatched zone id '{exp}' under key '{zid}'.")
        if zid in seen_ids:
            raise OwnershipError(f"Duplicate zone id '{zid}' in sdd:ownership-map.")
        seen_ids.add(zid)
        zones.append(_parse_zone_entry(zid, entry, label))
    raw_policy = data.get("unowned_policy")
    if raw_policy is None:
        policy: Literal["error", "warn"] = "error"
    elif isinstance(raw_policy, str) and raw_policy.strip().lower() in _POLICY_ALIASES:
        policy = _POLICY_ALIASES[raw_policy.strip().lower()]
    else:
        raise OwnershipError(f"Invalid 'unowned_policy' {raw_policy!r}; expected 'error' or 'warn'.")
    preset = _require_str(data["preset"], "sdd:ownership-map.preset") if data.get("preset") is not None else None
    return OwnershipMapConfig(zones=tuple(zones), unowned_policy=policy, preset=preset)

def detect_zone_overlaps(target: OwnershipMapConfig | Sequence[OwnershipZone]) -> None:
    """Fail closed if any two distinct zones can match the same path or overlap hierarchically."""
    zones = target.zones if isinstance(target, OwnershipMapConfig) else tuple(target)
    expanded = []
    for zone in zones:
        if not zone.paths:
            raise OwnershipError(f"Zone '{zone.zone_id}' has no declared paths.")
        for raw_glob in zone.paths:
            expanded.extend((zone, raw_glob, segs) for segs in _normalize_glob(raw_glob))
    for i, (zi, raw_i, segs_i) in enumerate(expanded):
        for zj, raw_j, segs_j in expanded[i + 1 :]:
            if zi.zone_id != zj.zone_id and _segs_intersect(segs_i, segs_j):
                raise OwnershipError(f"Ownership overlap between zone '{zi.zone_id}' (@{zi.owner}, {raw_i!r}) and zone '{zj.zone_id}' (@{zj.owner}, {raw_j!r}).")

def _scan_candidate_root(root_dir: Path, repo_root: Path, globs: Sequence[str]) -> list[str]:
    unowned: list[str] = []
    def _walk(current: Path, is_root: bool) -> None:
        try:
            entries = sorted(current.iterdir(), key=lambda p: p.name)
        except OSError as exc:
            raise OwnershipError(f"Cannot inspect candidate directory '{current}': {exc}") from exc
        has_child = False
        for entry in entries:
            if entry.name in _IGNORED_DIRS or entry.name in _IGNORED_FILES or entry.suffix.lower() in _IGNORED_SUFFIXES:
                continue
            if entry.is_symlink() and (not entry.exists() or not entry.resolve().is_relative_to(repo_root)):
                raise OwnershipError(f"Unsafe or broken symlink under ownership root: '{entry}'.")
            if entry.is_dir():
                has_child = True
                _walk(entry, False)
            elif entry.is_file():
                has_child = True
                rel = entry.relative_to(repo_root).as_posix()
                if not any(glob_matches_path(g, rel) for g in globs):
                    unowned.append(rel)
        if not is_root and not has_child:
            rel_dir = current.relative_to(repo_root).as_posix()
            probe = tuple(p for p in rel_dir.split("/") if p) + ("**",)
            if not any(_segs_intersect(probe, gs) for g in globs for gs in _normalize_glob(g)):
                unowned.append(f"{rel_dir}/")
    _walk(root_dir, True)
    return unowned

def validate_repo_coverage(config: OwnershipMapConfig, repo_root: Path, candidate_roots: Sequence[str] | None = None) -> list[str]:
    """Check source files/subdirs under `candidate_roots`; raise OwnershipError when policy is 'error'."""
    root_resolved = repo_root.resolve()
    all_globs = [g for zone in config.zones for g in zone.paths]
    unowned, seen_roots = [], set()
    for root_name in (derive_candidate_roots(config) if candidate_roots is None else candidate_roots):
        candidate = root_resolved / root_name
        if not candidate.exists() and not candidate.is_symlink():
            continue
        resolved = candidate.resolve()
        if candidate.is_symlink() and (not candidate.exists() or not resolved.is_relative_to(root_resolved)):
            raise OwnershipError(f"Candidate root '{candidate}' escapes repository root.")
        if resolved in seen_roots:
            continue
        seen_roots.add(resolved)
        if candidate.is_dir():
            unowned.extend(_scan_candidate_root(candidate, root_resolved, all_globs))
        elif not any(glob_matches_path(g, rel := candidate.relative_to(root_resolved).as_posix()) for g in all_globs):
            unowned.append(rel)
    if not unowned:
        return []
    messages = [f"Unowned source path '{p}' does not match any zone in sdd:ownership-map." for p in unowned]
    if config.unowned_policy == "error":
        raise OwnershipError(" | ".join(messages))
    return messages

def _resolve_zone_dod(raw_dod: str | None, verification_commands: Mapping[str, str] | None) -> str:
    cmds = verification_commands or {}
    if raw_dod:
        return cmds[raw_dod] if raw_dod in cmds else raw_dod
    for key in (*_DOD_PRIORITY, *sorted(cmds)):
        if key in cmds and cmds[key].strip():
            return cmds[key].strip()
    return "Verify according to specs/STACK.md §2.5"

def compile_ownership_builders(config: OwnershipMapConfig, verification_commands: Mapping[str, str] | None = None) -> list[dict[str, Any]]:
    """Compile ownership zones grouped per owner into BuilderSpec-compatible dictionaries."""
    detect_zone_overlaps(config)
    grouped: dict[str, list[OwnershipZone]] = {}
    for zone in config.zones:
        grouped.setdefault(zone.owner, []).append(zone)
    builders: list[dict[str, Any]] = []
    for owner, owner_zones in grouped.items():
        explicit_arch = {z.archetype for z in owner_zones if z.archetype is not None}
        if len(explicit_arch) > 1:
            raise OwnershipError(f"Conflicting archetypes {sorted(explicit_arch)} declared for owner '@{owner}'.")
        zone_paths, forbidden, dods = [], [], []
        for z in owner_zones:
            zone_paths.extend(p for p in z.paths if p not in zone_paths)
            forbidden.extend(m for m in z.forbid_imports if m not in forbidden)
            if (cmd := _resolve_zone_dod(z.dod, verification_commands)) not in dods:
                dods.append(cmd)
        builders.append({
            "name": owner, "archetype": next(iter(explicit_arch), "tier-backend"),
            "zone_paths": zone_paths, "dod": " && ".join(dods),
            "forbidden": ", ".join(forbidden) if forbidden else "None",
        })
    return builders

__all__ = [
    "DEFAULT_CANDIDATE_ROOTS", "OwnershipError", "OwnershipMapConfig", "OwnershipZone", "VALID_ZONE_GOVERNANCE",
    "compile_ownership_builders", "derive_candidate_roots", "detect_zone_overlaps", "glob_matches_path",
    "parse_ownership_map", "resolve_path_zone", "validate_repo_coverage", "zone_matches_path",
]
