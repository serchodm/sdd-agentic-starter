#!/usr/bin/env python3
"""Pack registry, manifest validation, compatibility checks, and asset resolution."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import json
from pathlib import Path, PurePosixPath
from typing import Any, Literal

try:
    from scripts.sdd_stack_parser import (
        CollisionError,
        DEFAULT_VALID_PRESETS,
        InvalidManifestError,
        ManualModificationConflictError,
        PackCompatibilityError,
        PackDependencyError,
        SddGeneratorError,
        StackConfig,
        StackConfigError,
        YamlScalar,
        YamlValue,
        _extract_stack_config_block,
        _require_nonempty_str,
        _validate_safe_rel_parts,
        parse_stack_config,
        parse_yaml_subset,
        strip_non_normative_markdown,
    )
    from scripts.sdd_vendor_update import VendorIntegrityError, verify_vendor_lock
except ImportError:
    from sdd_stack_parser import (
        CollisionError,
        DEFAULT_VALID_PRESETS,
        InvalidManifestError,
        ManualModificationConflictError,
        PackCompatibilityError,
        PackDependencyError,
        SddGeneratorError,
        StackConfig,
        StackConfigError,
        YamlScalar,
        YamlValue,
        _extract_stack_config_block,
        _require_nonempty_str,
        _validate_safe_rel_parts,
        parse_stack_config,
        parse_yaml_subset,
        strip_non_normative_markdown,
    )
    from sdd_vendor_update import VendorIntegrityError, verify_vendor_lock

_PRESET_IMPLIED_TARGETS: dict[str, frozenset[str]] = {
    "compact": frozenset({"compact", "fullstack", "web", "frontend", "spa", "ui", "api", "backend", "server", "cli", "database", "db"}),
    "granular": frozenset({"granular", "fullstack", "web", "frontend", "spa", "ui", "api", "backend", "server", "cli", "database", "db"}),
    "api-only": frozenset({"api-only", "api", "backend", "server", "cli", "database", "db", "microservice", "microservices"}),
    "spa-only": frozenset({"spa-only", "spa", "web", "frontend", "ui", "client", "browser"}),
}
_WILDCARD_TARGETS: frozenset[str] = frozenset({"*", "all", "any", "universal"})
_API_FORBIDDEN_PACKS: frozenset[str] = frozenset({
    "capability-web-frontend",
    "capability:web-frontend",
    "capability-ui-design",
    "capability:ui-design",
    "framework-react",
    "framework:react",
    "framework-vue",
    "framework:vue",
})
_SPA_FORBIDDEN_PACKS: frozenset[str] = frozenset({
    "framework-fastapi",
    "framework:fastapi",
    "framework-django",
    "framework:django",
    "framework-spring",
    "framework:spring",
    "lang-sql",
    "lang:sql",
})


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
        if not isinstance(upstream, dict):
            raise InvalidManifestError(f"Field 'upstream' in {manifest_path} must be a JSON object.")
        if "vendor_lock" in upstream:
            _require_nonempty_str(upstream["vendor_lock"], f"Field 'upstream.vendor_lock' in {manifest_path}", InvalidManifestError)
    return PackManifest(
        dir_name=pack_dir.name,
        pack_id=data["id"],
        family=data["family"],
        description=description,
        targets=targets,
        upstream=upstream,
        **lists,
    )


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
    agent_files = tuple(sorted((_resolve_safe_pack_path(pack_root, e, "specialists") for e in manifest.specialists), key=lambda p: p.name))
    for target in agent_files:
        if not target.is_file() or target.suffix != ".md":
            raise InvalidManifestError(f"Specialist must be an existing .md file in {pack_root.name}: '{target.name}'.")
    skill_dirs: list[tuple[str, Path]] = []
    for entry in manifest.skills:
        target_dir = _resolve_safe_pack_path(pack_root, entry, "skills")
        skill_md = (target_dir / "SKILL.md").resolve()
        if not target_dir.is_dir() or not skill_md.is_relative_to(target_dir) or not skill_md.is_file():
            raise InvalidManifestError(f"Skill directory missing SKILL.md in {pack_root.name}: {entry!r}.")
        skill_dirs.append((PurePosixPath(entry.replace("\\", "/").rstrip("/")).name, target_dir))
    return ResolvedPackAssets(
        manifest=manifest,
        pack_dir=pack_root,
        agent_files=agent_files,
        skill_dirs=tuple(sorted(skill_dirs, key=lambda item: item[0])),
        rule_files=tuple(sorted((_resolve_file_with_fallback(pack_root, e, "rules", "rules") for e in manifest.rules), key=lambda p: p.name)),
        workflow_files=tuple(sorted((_resolve_file_with_fallback(pack_root, e, "workflows", "workflows") for e in manifest.workflows), key=lambda p: p.name)),
    )


def validate_pack_preset_compatibility(
    preset: str,
    manifests: Sequence[PackManifest],
    uiux: Mapping[str, Any] | None = None,
    *,
    effective_gate00_approved: bool = False,
) -> None:
    """Validate that resolved pack `targets` and UI/UX state are compatible with `preset`."""
    if effective_gate00_approved and isinstance(uiux, Mapping) and uiux.get("enabled") is True and preset == "api-only":
        raise PackCompatibilityError("'uiux.enabled: true' is incompatible with preset 'api-only'.")
    allowed = _PRESET_IMPLIED_TARGETS.get(preset)
    for manifest in manifests:
        if manifest.targets:
            norm_targets = {t.strip().lower() for t in manifest.targets if t.strip()}
            if norm_targets and not (norm_targets & _WILDCARD_TARGETS) and allowed is not None and not (norm_targets & allowed):
                raise PackCompatibilityError(
                    f"Pack '{manifest.dir_name}' ({manifest.pack_id}) targets {list(manifest.targets)} "
                    f"are incompatible with preset '{preset}'."
                )
        if preset == "api-only" and (manifest.dir_name in _API_FORBIDDEN_PACKS or manifest.pack_id in _API_FORBIDDEN_PACKS):
            raise PackCompatibilityError(f"Frontend/UI pack '{manifest.dir_name}' is incompatible with preset 'api-only'.")
        if preset == "spa-only" and (manifest.dir_name in _SPA_FORBIDDEN_PACKS or manifest.pack_id in _SPA_FORBIDDEN_PACKS):
            raise PackCompatibilityError(f"Backend/database pack '{manifest.dir_name}' is incompatible with preset 'spa-only'.")


def resolve_active_packs(
    config: StackConfig,
    effective_gate00_approved: bool,
    cli_packs: Sequence[str] | None,
    packs_dir: Path,
    registry: Mapping[str, PackManifest] | None = None,
    *,
    effective_preset: str | None = None,
) -> tuple[tuple[PackActivation, ...], tuple[ResolvedPackAssets, ...]]:
    """Resolve, deduplicate, compatibility-check, dependency-check, and asset-validate packs."""
    target_preset = effective_preset if effective_preset is not None else config.preset
    if effective_gate00_approved:
        has_ui_pack = any(p.strip() in {"capability-ui-design", "capability:ui-design"} for p in config.packs)
        uiux_enabled = isinstance(config.uiux, dict) and config.uiux.get("enabled") is True
        if uiux_enabled != has_ui_pack:
            raise StackConfigError("Inconsistent sdd:stack-config: 'uiux.enabled' and 'capability-ui-design' in 'packs' must match when Gate S0 is approved.")
        if uiux_enabled and target_preset == "api-only":
            raise PackCompatibilityError("'uiux.enabled: true' is incompatible with preset 'api-only'.")

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

    ordered_keys = sorted(resolved)
    manifests = [resolved[k][1] for k in ordered_keys]
    validate_pack_preset_compatibility(
        target_preset,
        manifests,
        config.uiux,
        effective_gate00_approved=effective_gate00_approved,
    )
    active_refs = {ref for m in manifests for ref in (m.dir_name, m.pack_id)}
    for m in manifests:
        if missing := sorted(req for req in m.requires if req not in active_refs):
            raise PackDependencyError(f"Pack '{m.dir_name}' ({m.pack_id}) requires missing pack(s): {', '.join(missing)}.")
    return tuple(resolved[k][0] for k in ordered_keys), tuple(resolve_pack_assets(m, packs_dir / m.dir_name) for m in manifests)


__all__ = [
    "CollisionError",
    "DEFAULT_VALID_PRESETS",
    "InvalidManifestError",
    "ManualModificationConflictError",
    "PackActivation",
    "PackCompatibilityError",
    "PackDependencyError",
    "PackManifest",
    "ResolvedPackAssets",
    "SddGeneratorError",
    "StackConfig",
    "StackConfigError",
    "YamlScalar",
    "YamlValue",
    "load_catalog_registry",
    "load_pack_manifest",
    "parse_stack_config",
    "parse_yaml_subset",
    "resolve_active_packs",
    "resolve_pack_assets",
    "strip_non_normative_markdown",
    "validate_pack_preset_compatibility",
]
