#!/usr/bin/env python3
"""Deterministic brownfield repository discovery and non-destructive SDD adoption."""

from __future__ import annotations

import argparse, json, os, re, sys, tomllib
from dataclasses import asdict, dataclass
from pathlib import Path

_FRAMEWORK_ROOT = Path(__file__).resolve().parent.parent
for _p in (str(_FRAMEWORK_ROOT), str(_FRAMEWORK_ROOT / "scripts"), str(_FRAMEWORK_ROOT / ".agents" / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from sdd_immutable_feature_guard import strip_win32_extended_prefix  # noqa: E402
from sdd_repo_map import EXTENSION_PARSERS, IGNORED_DIRS, build_repo_map_lines  # noqa: E402
from scripts.sdd_ci import split_safe_chained_command  # noqa: E402
from scripts.sdd_git_state import atomic_write_text, is_link_or_junction  # noqa: E402
from scripts.sdd_pack_registry import StackConfigError, parse_stack_config  # noqa: E402

MAX_SCAN_DEPTH = 3
SKIP_DIRS: frozenset[str] = frozenset(IGNORED_DIRS) | {".agents", ".worktrees", ".sdd"}
VALID_PRESET_OVERRIDES: frozenset[str] = frozenset({"auto", "compact", "granular"})
_CODE_ROOT_NAMES: frozenset[str] = frozenset({"src", "app", "lib", "backend", "frontend", "api", "web", "services", "packages", "cmd", "internal", "DDBB", "tests"})
_SRC_SPLIT_NAMES: frozenset[str] = frozenset({"backend", "frontend", "api", "web", "domain", "infra", "infrastructure"})
_FRONTEND_HINTS: frozenset[str] = frozenset({"frontend", "web", "ui", "client"})
_TEST_HINTS: frozenset[str] = frozenset({"tests", "test", "__tests__"})
_TECH_STOPWORDS: frozenset[str] = frozenset({"utils", "util", "common", "shared", "config", "configs", "migrations", "static", "assets", "public", "types", "tests", "__tests__", "test"})
_EXT_LANG: dict[str, str] = {
    ".py": "python", ".ts": "typescript", ".tsx": "typescript", ".js": "javascript", ".jsx": "javascript", ".mjs": "javascript",
    ".cjs": "javascript", ".go": "go", ".rs": "rust", ".cs": "csharp", ".java": "java", ".kt": "kotlin", ".kts": "kotlin",
    ".cpp": "cpp", ".cc": "cpp", ".cxx": "cpp", ".c": "c", ".h": "c", ".hpp": "cpp", ".dart": "dart", ".swift": "swift", ".sql": "sql", ".php": "php", ".rb": "ruby",
}
_FRONT_EXTS: frozenset[str] = frozenset({".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"})
_BACK_EXTS: frozenset[str] = frozenset({".py", ".go", ".rs", ".cs", ".java", ".kt", ".kts", ".cpp", ".c", ".php", ".rb"})
_COMPOSE_RE = re.compile(r"^(?:docker-)?compose.*\.ya?ml$", re.IGNORECASE)
_REQ_TXT_RE = re.compile(r"^requirements.*\.txt$", re.IGNORECASE)
_DEP_SPLIT_RE = re.compile(r"[<>=!~;\[\s]")
_SIMPLE_MANIFESTS: dict[str, tuple[str, str, tuple[tuple[str, str], ...]]] = {
    "go.mod": ("go", "lang-go", (("lint", "go vet ./..."), ("unit_test", "go test ./..."), ("build", "go build ./..."))),
    "Cargo.toml": ("rust", "lang-rust", (("lint", "cargo clippy"), ("unit_test", "cargo test"), ("build", "cargo build --release"))),
    "pom.xml": ("java", "lang-java", (("unit_test", "mvn test"), ("build", "mvn package -DskipTests"))),
    "build.gradle": ("java", "lang-java", (("unit_test", "gradle test"), ("build", "gradle build"))),
    "build.gradle.kts": ("kotlin", "lang-kotlin", (("unit_test", "gradle test"), ("build", "gradle build"))),
    "CMakeLists.txt": ("cpp", "lang-cpp", ()),
    "pubspec.yaml": ("dart", "lang-dart", (("unit_test", "dart test"),)),
    "Package.swift": ("swift", "lang-swift", (("unit_test", "swift test"), ("build", "swift build"))),
}

class BrownfieldError(ValueError):
    """Fail-closed error raised on invalid repo roots, unsafe paths, or bad options."""

@dataclass(frozen=True)
class CandidateZone:
    """Candidate ownership zone discovered in a brownfield repository."""
    zone_id: str; owner: str; paths: tuple[str, ...]; file_count: int; languages: tuple[str, ...]; dod_slot: str

@dataclass(frozen=True)
class BrownfieldDiscovery:
    """Deterministic discovery summary of a brownfield repository."""
    repo_root: str; manifests: tuple[str, ...]; ci_files: tuple[str, ...]; ecosystems: tuple[str, ...]
    suggested_packs: tuple[str, ...]; suggested_preset: str; verification_commands: dict[str, str]
    rejected_commands: tuple[str, ...]; candidate_zones: tuple[CandidateZone, ...]; bounded_contexts: tuple[str, ...]
    existing_sdd_files: tuple[str, ...]; stack_s0_approved: bool; warnings: tuple[str, ...]

@dataclass(frozen=True)
class AdoptPlan:
    """Non-destructive brownfield adoption plan or execution outcome."""
    dry_run: bool; applied: bool; created: tuple[str, ...]; skipped_existing: tuple[str, ...]; discovery: BrownfieldDiscovery

def validate_repo_root(repo_root: Path | str) -> Path:
    """Validate and normalize `repo_root` fail-closed against symlinks, junctions, and missing dirs."""
    raw = str(repo_root).strip()
    if not raw:
        raise BrownfieldError("Repository root path cannot be empty.")
    try:
        cand = Path(strip_win32_extended_prefix(raw))
    except ValueError as exc:
        raise BrownfieldError(str(exc)) from exc
    for check_path in (cand, cand.parent):
        if is_link_or_junction(check_path):
            raise BrownfieldError(f"Refusing symlink or junction in repo_root path: {check_path}")
    if not cand.exists() or not cand.is_dir():
        raise BrownfieldError(f"Repository root must be an existing directory: {cand}")
    try:
        resolved = Path(strip_win32_extended_prefix(str(cand.resolve(strict=True))))
    except (OSError, ValueError) as exc:
        raise BrownfieldError(f"Cannot resolve repository root {cand}: {exc}") from exc
    if is_link_or_junction(resolved) or not resolved.is_dir():
        raise BrownfieldError(f"Resolved repository root is invalid or a symlink/junction: {resolved}")
    return resolved

def _ensure_safe_target(repo_root: Path, rel_path: str) -> Path:
    """Verify `repo_root / rel_path` stays inside `repo_root` with no symlinks or junctions."""
    rel_parts = Path(rel_path).parts
    if Path(rel_path).is_absolute() or ".." in rel_parts:
        raise BrownfieldError(f"Unsafe relative target path: {rel_path!r}")
    cur = repo_root
    for part in rel_parts:
        cur = cur / part
        if is_link_or_junction(cur):
            raise BrownfieldError(f"Refusing symlink or junction on target path: {cur}")
    target = repo_root / rel_path
    try:
        if not target.resolve(strict=False).is_relative_to(repo_root):
            raise BrownfieldError(f"Target path escapes repository root: {rel_path!r}")
    except OSError as exc:
        raise BrownfieldError(f"Cannot resolve target path {rel_path!r}: {exc}") from exc
    return target

def _add_unique(items: list[str], value: str) -> None:
    if value not in items: items.append(value)

def _merge_command(verif: dict[str, str], rejected: list[str], warnings: list[str], slot: str, cmd: str, source: str = "") -> None:
    try:
        split_safe_chained_command(cmd)
    except ValueError as exc:
        _add_unique(rejected, f"{source}: {cmd}" if source else cmd)
        _add_unique(warnings, f"Rejected unsafe command in {source or slot}: {exc}")
        return
    if slot not in verif: verif[slot] = cmd
    elif cmd not in verif[slot].split(" && "):
        try:
            split_safe_chained_command(combined := f"{verif[slot]} && {cmd}"); verif[slot] = combined
        except ValueError: _add_unique(warnings, f"Skipped chaining {slot} command from {source or slot}.")

def _iter_bounded_files(repo_root: Path) -> list[tuple[Path, str]]:
    found: list[tuple[Path, str]] = []
    for cur_str, dirnames, filenames in os.walk(repo_root, topdown=True, followlinks=False):
        cur = Path(cur_str)
        rel_dir = cur.relative_to(repo_root)
        depth = 0 if rel_dir == Path(".") else len(rel_dir.parts)
        dirnames[:] = [] if depth >= MAX_SCAN_DEPTH else sorted(d for d in dirnames if d not in SKIP_DIRS and not is_link_or_junction(cur / d))
        for fname in sorted(filenames):
            fpath = cur / fname
            if not is_link_or_junction(fpath) and fpath.is_file():
                found.append((fpath, fpath.relative_to(repo_root).as_posix()))
    return found

def _inspect_python_manifest(
    fpath: Path, rel: str, base_dir: Path, ecosystems: list[str], packs: list[str],
    verif: dict[str, str], rejected: list[str], warnings: list[str],
) -> None:
    _add_unique(ecosystems, "python"); _add_unique(packs, "lang-python")
    try:
        text = fpath.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        _add_unique(warnings, f"Cannot read {rel}: {exc}"); return
    deps: set[str] = set()
    tool: dict[str, object] = {}
    if fpath.name == "pyproject.toml":
        try:
            data = tomllib.loads(text)
        except tomllib.TOMLDecodeError as exc:
            _add_unique(warnings, f"Malformed TOML in {rel}: {exc}"); data = {}
        project = data.get("project") if isinstance(data.get("project"), dict) else {}
        raw_deps = list(project.get("dependencies", []) or [])
        for src in ((project.get("optional-dependencies") or {}).values(), (data.get("dependency-groups") or {}).values()):
            for grp in src:
                if isinstance(grp, list):
                    raw_deps.extend(x for x in grp if isinstance(x, str))
        deps.update(_DEP_SPLIT_RE.split(item.strip(), maxsplit=1)[0].lower() for item in raw_deps if isinstance(item, str) and item.strip())
        tool = data.get("tool") if isinstance(data.get("tool"), dict) else {}
        poetry = tool.get("poetry") if isinstance(tool.get("poetry"), dict) else {}
        deps.update(str(k).lower() for k in (poetry.get("dependencies") or {}))
        for grp in (poetry.get("group") or {}).values():
            if isinstance(grp, dict) and isinstance(grp.get("dependencies"), dict):
                deps.update(str(k).lower() for k in grp["dependencies"])
    else:
        low = text.lower()
        deps.update(p for p in ("fastapi", "django", "sqlalchemy", "alembic", "ruff", "mypy", "pytest") if re.search(rf"(?<![a-z0-9_-]){p}(?![a-z0-9_-])", low))
    has_ruff, has_mypy, has_pytest = ("ruff" in tool or "ruff" in deps), ("mypy" in tool or "mypy" in deps), ("pytest" in tool or "pytest" in deps)
    if "fastapi" in deps: _add_unique(packs, "framework-fastapi")
    if "django" in deps: _add_unique(packs, "framework-django")
    if deps & {"sqlalchemy", "alembic"}: _add_unique(packs, "capability-database")
    prefix = "uv run " if (base_dir / "uv.lock").is_file() or (fpath.parent / "uv.lock").is_file() else ""
    if lint_parts := [p for p, ok in ((f"{prefix}ruff check .", has_ruff), (f"{prefix}mypy .", has_mypy)) if ok]:
        _merge_command(verif, rejected, warnings, "lint", " && ".join(lint_parts), rel)
    if has_pytest:
        _merge_command(verif, rejected, warnings, "unit_test", f"{prefix}pytest -q", rel)

def _inspect_node_manifest(
    fpath: Path, rel: str, base_dir: Path, ecosystems: list[str], packs: list[str],
    verif: dict[str, str], rejected: list[str], warnings: list[str],
) -> None:
    _add_unique(ecosystems, "typescript"); _add_unique(packs, "lang-typescript")
    if fpath.name != "package.json":
        return
    try:
        data = json.loads(fpath.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        _add_unique(warnings, f"Malformed or unreadable {rel}: {exc}"); return
    if not isinstance(data, dict):
        _add_unique(warnings, f"Expected JSON object in {rel}."); return
    dep_keys = {str(k).lower() for sec in ("dependencies", "devDependencies", "peerDependencies") if isinstance(data.get(sec), dict) for k in data[sec]}
    if dep_keys & {"react", "next"}: _add_unique(packs, "framework-react"); _add_unique(packs, "capability-web-frontend")
    if dep_keys & {"vue", "nuxt"}: _add_unique(packs, "framework-vue"); _add_unique(packs, "capability-web-frontend")
    if dep_keys & {"prisma", "@prisma/client", "typeorm", "drizzle-orm"}: _add_unique(packs, "capability-database")
    runner = next(("pnpm run" if (d / "pnpm-lock.yaml").is_file() else "bun run" for d in (fpath.parent, base_dir)
                   if (d / "pnpm-lock.yaml").is_file() or (d / "bun.lock").is_file() or (d / "bun.lockb").is_file()), "npm run")
    if not isinstance(scripts := data.get("scripts"), dict):
        return
    for script_key, slot in (("lint", "lint"), ("typecheck", "lint"), ("test", "unit_test"), ("build", "build")):
        raw_script = scripts.get(script_key)
        if not isinstance(raw_script, str) or not raw_script.strip():
            continue
        try:
            split_safe_chained_command(raw_script)
        except ValueError as exc:
            _add_unique(rejected, f"{rel}#scripts.{script_key}: {raw_script}")
            _add_unique(warnings, f"Rejected unsafe script '{script_key}' in {rel}: {exc}")
            continue
        _merge_command(verif, rejected, warnings, slot, f"{runner} {script_key}", f"{rel}#scripts.{script_key}")

def _available_catalog_packs(repo_root: Path) -> set[str]:
    for base in (repo_root, _FRAMEWORK_ROOT):
        packs_dir = base / ".sdd" / "catalog" / "packs"
        if packs_dir.is_dir() and not is_link_or_junction(packs_dir):
            return {p.name for p in packs_dir.iterdir() if p.is_dir() and not is_link_or_junction(p)}
    return set()

def _safe_subdirs(parent: Path) -> list[Path]:
    return [s for s in sorted(parent.iterdir(), key=lambda p: p.name) if s.is_dir() and not is_link_or_junction(s) and s.name not in SKIP_DIRS]

def _count_zone_files(zone_dir: Path) -> tuple[int, set[str], int, int]:
    count, langs, front_n, back_n = 0, set(), 0, 0
    for cur_str, dirnames, filenames in os.walk(zone_dir, topdown=True, followlinks=False):
        cur = Path(cur_str)
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS and not is_link_or_junction(cur / d))
        for fname in filenames:
            fpath = cur / fname; ext = fpath.suffix.lower()
            if not is_link_or_junction(fpath) and fpath.is_file() and ext in EXTENSION_PARSERS:
                count += 1; langs.add(_EXT_LANG.get(ext, ext.lstrip(".")))
                front_n += int(ext in _FRONT_EXTS); back_n += int(ext in _BACK_EXTS)
    return count, langs, front_n, back_n

def _collect_zone_dirs(repo_root: Path) -> list[Path]:
    dirs: list[Path] = []
    for entry in _safe_subdirs(repo_root):
        if entry.name not in _CODE_ROOT_NAMES:
            continue
        if entry.name in {"services", "packages"}:
            dirs.extend(_safe_subdirs(entry) or [entry])
        elif entry.name == "src":
            subs = _safe_subdirs(entry)
            dirs.extend(subs if any(s.name.lower() in _SRC_SPLIT_NAMES for s in subs) else [entry])
        else:
            dirs.append(entry)
    return dirs

def _assign_zone_meta(rel_dir: str, preset: str, front_n: int, back_n: int, verif: dict[str, str]) -> tuple[str, str]:
    leaf = rel_dir.rsplit("/", 1)[-1].lower()
    if leaf in _TEST_HINTS:
        return "qa-tester", "unit_test"
    if leaf in _FRONTEND_HINTS or (front_n > 0 and back_n == 0 and leaf not in {"ddbb", "db", "infra", "infrastructure"}):
        return ("front-ui" if preset == "granular" else "front-engineer"), ("build" if "build" in verif else ("lint" if "lint" in verif else "unit_test"))
    if leaf in {"domain", "core"}:
        return ("back-domain" if preset == "granular" else "back-engineer"), "unit_test"
    if leaf in {"ddbb", "db", "migrations", "infra", "infrastructure"}:
        return ("back-infra" if preset == "granular" else "back-engineer"), ("infra" if "infra" in verif else "unit_test")
    return ("back-api" if preset == "granular" else "back-engineer"), ("unit_test" if "unit_test" in verif else "lint")

def _build_zones_and_contexts(repo_root: Path, preset_override: str, verif: dict[str, str]) -> tuple[str, tuple[CandidateZone, ...], tuple[str, ...]]:
    zone_dirs = _collect_zone_dirs(repo_root)
    raw_zones = [(d.relative_to(repo_root).as_posix(), c, tuple(sorted(ls)), fn, bn)
                 for d in zone_dirs for c, ls, fn, bn in [_count_zone_files(d)] if c > 0]
    total_files = sum(item[1] for item in raw_zones)
    preset = preset_override if preset_override != "auto" else ("granular" if (len(raw_zones) >= 3 or total_files >= 50) else "compact")
    zones, seen_ids = [], set()
    for rel_dir, cnt, langs, fn, bn in raw_zones:
        zid = re.sub(r"[^a-z0-9_-]+", "-", rel_dir.lower()).strip("-_") or "zone"
        while zid in seen_ids:
            zid = f"{zid}-zone"
        seen_ids.add(zid)
        owner, dod_slot = _assign_zone_meta(rel_dir, preset, fn, bn, verif)
        zones.append(CandidateZone(zid, owner, (f"{rel_dir}/**",), cnt, langs, dod_slot))
    contexts: list[str] = []
    for d in zone_dirs:
        if d.name.lower() not in _TEST_HINTS:
            for sub in _safe_subdirs(d):
                if sub.name.lower() not in _TECH_STOPWORDS and _count_zone_files(sub)[0] > 0:
                    _add_unique(contexts, sub.relative_to(repo_root).as_posix())
    if not contexts:
        for rd, *_ in raw_zones:
            if rd.rsplit("/", 1)[-1].lower() not in _TEST_HINTS: _add_unique(contexts, rd)
    return preset, tuple(zones), tuple(contexts)

def discover_brownfield_repo(repo_root: Path | str, preset_override: str = "auto") -> BrownfieldDiscovery:
    """Inspect an existing repository read-only and produce a deterministic discovery report."""
    if preset_override not in VALID_PRESET_OVERRIDES:
        raise BrownfieldError(f"Invalid preset {preset_override!r}; expected one of {sorted(VALID_PRESET_OVERRIDES)}.")
    root = validate_repo_root(repo_root)
    manifests, ci_files, ecosystems, packs, rejected, warnings = [], [], [], [], [], []
    verif: dict[str, str] = {}
    for fpath, rel in _iter_bounded_files(root):
        name, low = fpath.name, fpath.name.lower()
        if rel.startswith(".github/workflows/") and fpath.suffix.lower() in {".yml", ".yaml"} or low in {".gitlab-ci.yml", "bitbucket-pipelines.yml"}:
            _add_unique(ci_files, rel); _add_unique(packs, "capability-devops")
        elif name == "pyproject.toml" or _REQ_TXT_RE.match(name) or name == "setup.py":
            _add_unique(manifests, rel); _inspect_python_manifest(fpath, rel, root, ecosystems, packs, verif, rejected, warnings)
        elif name in {"package.json", "tsconfig.json"}:
            _add_unique(manifests, rel); _inspect_node_manifest(fpath, rel, root, ecosystems, packs, verif, rejected, warnings)
        elif name in _SIMPLE_MANIFESTS:
            eco, pack, cmds = _SIMPLE_MANIFESTS[name]
            _add_unique(manifests, rel); _add_unique(ecosystems, eco); _add_unique(packs, pack)
            for s, c in cmds:
                _merge_command(verif, rejected, warnings, s, c, rel)
        elif fpath.suffix.lower() in {".csproj", ".sln"}:
            _add_unique(manifests, rel); _add_unique(ecosystems, "csharp"); _add_unique(packs, "lang-csharp")
            for s, c in (("unit_test", "dotnet test"), ("build", "dotnet build")):
                _merge_command(verif, rejected, warnings, s, c, rel)
        elif name == "Dockerfile" or _COMPOSE_RE.match(name):
            _add_unique(manifests, rel); _add_unique(packs, "capability-devops")
            if _COMPOSE_RE.match(name):
                _merge_command(verif, rejected, warnings, "infra", "docker compose config", rel)
    if catalog := _available_catalog_packs(root):
        packs = [p for p in packs if p in catalog]
    preset, zones, contexts = _build_zones_and_contexts(root, preset_override, verif)
    existing = [rel for rel in ("specs/STACK.md", "specs/BACKLOG.md", "docs/knowledge/BROWNFIELD_INVENTORY.md") if (root / rel).exists()]
    s0_approved, stack_path = False, root / "specs" / "STACK.md"
    if stack_path.is_file() and not is_link_or_junction(stack_path):
        try:
            _, s0_approved = parse_stack_config(stack_path)
        except StackConfigError as exc:
            _add_unique(warnings, f"Existing specs/STACK.md failed validation: {exc}")
    return BrownfieldDiscovery(
        repo_root=str(root), manifests=tuple(manifests), ci_files=tuple(ci_files), ecosystems=tuple(ecosystems),
        suggested_packs=tuple(packs), suggested_preset=preset, verification_commands=verif,
        rejected_commands=tuple(rejected), candidate_zones=zones, bounded_contexts=contexts,
        existing_sdd_files=tuple(existing), stack_s0_approved=s0_approved, warnings=tuple(warnings),
    )

def render_draft_stack_md(discovery: BrownfieldDiscovery) -> str:
    """Render a draft `specs/STACK.md` compatible with SDD parsers and Gate S0 unapproved."""
    verif_lines = [f"{slot}: {json.dumps(cmd)}" for slot, cmd in discovery.verification_commands.items()]
    verif_lines.extend(f"# TODO(S0): configure '{s}' command" for s in ("lint", "unit_test", "build", "infra") if s not in discovery.verification_commands)
    zone_lines = ["unowned_policy: fail-closed", f"preset: {discovery.suggested_preset}",
                  *(["zones: []"] if not discovery.candidate_zones else ["zones:", *[l for z in discovery.candidate_zones for l in (f"  - id: {z.zone_id}", f"    owner: {z.owner}", f"    paths: {json.dumps(list(z.paths))}", f"    dod: {z.dod_slot}")]])]
    pack_lines = ["packs: []"] if not discovery.suggested_packs else ["packs:", *(f"  - {p}" for p in discovery.suggested_packs)]
    return "\n".join([
        "# Especificación del Stack Tecnológico (Gate S0: Stack Lock)", "",
        "> **ESTADO DE LA PUERTA:** `[ ] Gate S0 Approved (Human Sign-off)`",
        "> *(Borrador generado por `sdd adopt`. Requiere revisión y aprobación humana explícita antes de editar `src/`).*", "",
        "## 1. Identificación y Topología del Sistema",
        f"- **Ecosistemas Detectados**: `{', '.join(discovery.ecosystems) or 'unknown'}`",
        f"- **Preset Sugerido**: `{discovery.suggested_preset}`", "",
        "## 2.5. Comandos Deterministas de Verificación DoD", "",
        "```yaml sdd:verification-commands", *verif_lines, "```", "",
        "## 3.2. Ownership Map", "",
        "```yaml sdd:ownership-map", *zone_lines, "```", "",
        "## 3.3. Stack Packs Activos", "",
        "```yaml sdd:stack-config", "stack_approved: false", "gate00_approved: false",
        f"preset: {discovery.suggested_preset}", *pack_lines, "uiux:", "  enabled: false", "```", "",
        "## 7. Firmas de Aprobación de Gate S0",
        "- [ ] `@orchestrator`: Especificación del stack, Ownership Map y comandos DoD validados.",
        "- [ ] **Usuario Humano**: `[ ] Gate S0 Approved (Human Sign-off)`", "",
    ])

def render_brownfield_inventory_md(discovery: BrownfieldDiscovery, repo_map_excerpt: str = "") -> str:
    """Render `docs/knowledge/BROWNFIELD_INVENTORY.md` summarizing discovery and bounded contexts."""
    lines = [
        "# Brownfield Inventory & Spec-Miner Handoff", "",
        f"- **Repository Root:** `{discovery.repo_root}`", f"- **Suggested Preset:** `{discovery.suggested_preset}`",
        f"- **Gate S0 Approved:** `{discovery.stack_s0_approved}`",
        f"- **Ecosystems:** {', '.join(f'`{e}`' for e in discovery.ecosystems) or '*(none)*'}",
        f"- **Suggested Packs:** {', '.join(f'`{p}`' for p in discovery.suggested_packs) or '*(none)*'}", "",
        "## Manifests & CI Files",
        *([f"- `{m}`" for m in discovery.manifests] + [f"- `{c}` *(CI)*" for c in discovery.ci_files] or ["- *(none detected)*"]),
        "", "## Verification Commands (Sanitized)",
        *([f"- **{s}:** `{c}`" for s, c in discovery.verification_commands.items()] or ["- *(none inferred)*"]),
    ]
    if discovery.rejected_commands:
        lines.extend(["", "### Rejected Unsafe Commands", *(f"- `{c}`" for c in discovery.rejected_commands)])
    lines.extend(["", "## Candidate Ownership Zones"])
    if discovery.candidate_zones:
        lines.extend(["| Zone ID | Owner | Paths | Files | Languages | DoD Slot |", "| :--- | :--- | :--- | ---: | :--- | :--- |",
                      *(f"| `{z.zone_id}` | `@{z.owner}` | `{', '.join(z.paths)}` | {z.file_count} | `{', '.join(z.languages)}` | `{z.dod_slot}` |" for z in discovery.candidate_zones)])
    else:
        lines.append("- *(none detected)*")
    lines.extend(["", "## Suggested Bounded Contexts (`@spec-miner`)", *(f"- `{c}`" for c in (discovery.bounded_contexts or ("*(none)*",)))])
    if discovery.warnings:
        lines.extend(["", "## Warnings", *(f"- {w}" for w in discovery.warnings)])
    if repo_map_excerpt.strip():
        lines.extend(["", "## Repo Map Excerpt", "```text", repo_map_excerpt.strip(), "```"])
    return "\n".join([*lines, ""])

def render_initial_backlog_md() -> str:
    """Render a clean initial `specs/BACKLOG.md` template."""
    return "\n".join([
        "# Backlog de Producto y Control de Puertas SDD", "",
        "> **Gate S0 (Stack Lock):** Registrado y formalizado en [`specs/STACK.md`](STACK.md).", "",
        "## Matriz de Control de Puertas (Gate 0 a Gate 5)", "",
        "| ID | Tipo | Título | Gate 0 (Intake) | Gate 1 (Spec) | Gate 2 (Tech) | Gate 3 (Tasks) | Gate 4 (QA) | Gate 5 (Docs) | Estado Final |",
        "| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |",
        "| *(Vacío)* | - | - | - | - | - | - | - | - | - |", "",
    ])

def apply_adopt(
    repo_root: Path | str, *, dry_run: bool = True, preset_override: str = "auto",
    overwrite_inventory: bool = False, with_repo_map: bool = False,
) -> AdoptPlan:
    """Plan or apply non-destructive brownfield SDD scaffolding in `repo_root`."""
    root = validate_repo_root(repo_root)
    discovery = discover_brownfield_repo(root, preset_override=preset_override)
    excerpt = ""
    if with_repo_map:
        rm_lines, _, _ = build_repo_map_lines(root)
        excerpt = "\n".join(rm_lines if len(rm_lines) <= 120 else [*rm_lines[:120], f"... (truncated to 120 of {len(rm_lines)} lines)"])
    targets = (
        ("specs/STACK.md", render_draft_stack_md(discovery), False),
        ("docs/knowledge/BROWNFIELD_INVENTORY.md", render_brownfield_inventory_md(discovery, excerpt), overwrite_inventory),
        ("specs/BACKLOG.md", render_initial_backlog_md(), False),
    )
    created, skipped = [], []
    for rel, content, allow_overwrite in targets:
        target = _ensure_safe_target(root, rel)
        if target.exists() and not allow_overwrite:
            skipped.append(rel)
            continue
        created.append(rel)
        if not dry_run:
            atomic_write_text(target, content)
    return AdoptPlan(dry_run=dry_run, applied=not dry_run, created=tuple(created), skipped_existing=tuple(skipped), discovery=discovery)

def plan_adopt(
    repo_root: Path | str, *, preset_override: str = "auto", overwrite_inventory: bool = False, with_repo_map: bool = False
) -> AdoptPlan:
    """Return a read-only dry-run `AdoptPlan` without writing files."""
    return apply_adopt(repo_root, dry_run=True, preset_override=preset_override, overwrite_inventory=overwrite_inventory, with_repo_map=with_repo_map)

def _format_text(plan: AdoptPlan) -> str:
    d = plan.discovery
    return "\n".join([
        f"SDD Brownfield Adopt ({'DRY-RUN' if plan.dry_run else 'APPLIED'})",
        f"  repo_root: {d.repo_root}", f"  ecosystems: {', '.join(d.ecosystems) or '(none)'}",
        f"  suggested_preset: {d.suggested_preset}", f"  suggested_packs: {', '.join(d.suggested_packs) or '(none)'}",
        f"  stack_s0_approved: {d.stack_s0_approved}", f"  created: {', '.join(plan.created) or '(none)'}",
        f"  skipped_existing: {', '.join(plan.skipped_existing) or '(none)'}",
    ])

def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for `sdd adopt` brownfield discovery and scaffolding."""
    parser = argparse.ArgumentParser(description="Discover a brownfield repository and scaffold non-destructive SDD files.")
    parser.add_argument("--repo-root", default=".", help="Target repository root directory (default: .)")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true", help="Write missing SDD draft files atomically")
    mode.add_argument("--dry-run", action="store_true", help="Preview plan without writing files (default)")
    parser.add_argument("--preset", choices=("auto", "compact", "granular"), default="auto", help="Preset override (default: auto)")
    parser.add_argument("--with-repo-map", action="store_true", help="Include bounded AST repo-map excerpt in inventory")
    parser.add_argument("--overwrite-inventory", action="store_true", help="Overwrite docs/knowledge/BROWNFIELD_INVENTORY.md if present")
    parser.add_argument("--format", choices=("text", "json"), default="text", help="Output format (default: text)")
    args = parser.parse_args(argv)
    try:
        plan = apply_adopt(args.repo_root, dry_run=not args.apply, preset_override=args.preset, overwrite_inventory=args.overwrite_inventory, with_repo_map=args.with_repo_map)
    except (BrownfieldError, OSError, ValueError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    print(json.dumps(asdict(plan), indent=2, ensure_ascii=False) if args.format == "json" else _format_text(plan))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
