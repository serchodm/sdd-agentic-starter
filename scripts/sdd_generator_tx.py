#!/usr/bin/env python3
"""Transactional materializer, canonical lockfile builder, Stack 2.5 DoD resolver, and verifier."""

from __future__ import annotations

from collections.abc import Callable, Collection, Mapping, Sequence
from dataclasses import dataclass, field
import datetime, hashlib, itertools, json, os, re, shutil, sys, tempfile
from pathlib import Path, PurePosixPath
from types import MappingProxyType
from typing import Protocol, runtime_checkable

try:
    from scripts.sdd_pack_registry import CollisionError, InvalidManifestError, ManualModificationConflictError, SddGeneratorError, StackConfigError, parse_stack_config, parse_yaml_subset
except ImportError:
    from sdd_pack_registry import CollisionError, InvalidManifestError, ManualModificationConflictError, SddGeneratorError, StackConfigError, parse_stack_config, parse_yaml_subset

DEFAULT_CORE_AGENTS: tuple[str, ...] = ("orchestrator", "functional-analyst", "architect", "qa-tester", "documentator", "devops")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_OPEN_FENCE_RE = re.compile(r"^[ \t]*(`{3,})(.*)$")
_VERIF_INFO_RE = re.compile(r"^yaml[ \t]+sdd:verification-commands$", re.IGNORECASE)
_YAML_INFO_RE = re.compile(r"^ya?ml(?:[ \t].*)?$", re.IGNORECASE)
_SEC_25_HEADING_RE = re.compile(r"^#{2,3}[ \t]+2\.5\b")
_HEADING_RE = re.compile(r"^(#{1,3})[ \t]+")
_VERIF_SLOTS: tuple[str, ...] = ("lint", "unit_test", "integration_test", "build", "infra", "full_suite")
_ALLOWED_VERIF_KEYS: frozenset[str] = frozenset({*_VERIF_SLOTS, "builders", "overrides"})
_EXACT_GENERIC_DOD: frozenset[str] = frozenset({"migration check", "test command", "todo", "tbd", "n/a"})
_ROLE_COMMAND_MAP: dict[str, tuple[str, ...]] = {
    "back-infra": ("integration_test", "unit_test", "lint"),
    "db-specialist": ("infra", "integration_test", "unit_test"),
    "front-ui": ("build", "lint", "unit_test"),
    "front-engineer": ("build", "unit_test", "lint"),
    "front-logic": ("unit_test", "build", "lint"),
    "front-test": ("unit_test", "build", "lint"),
}
_DEFAULT_ROLE_ORDER: tuple[str, ...] = ("unit_test", "lint", "build", "integration_test")

class InboxReconciliationError(SddGeneratorError):
    """Raised when obsolete agent inboxes contain pending tickets without a drain target."""

@runtime_checkable
class WorkspacePathsLike(Protocol):
    root: Path; agents_dir: Path; inbox_dir: Path; pack_rules_dir: Path; skills_dir: Path; stack_path: Path; lock_file: Path

@runtime_checkable
class PlannedFileLike(Protocol):
    rel_path: str; content: bytes; sha256: str; owner: str; kind: str

@dataclass(frozen=True)
class VerificationCommands:
    """Validated section 2.5 verification commands parsed from `specs/STACK.md`."""
    lint: str | None = None; unit_test: str | None = None; integration_test: str | None = None
    build: str | None = None; infra: str | None = None; full_suite: str | None = None
    builders: Mapping[str, str] = field(default_factory=lambda: MappingProxyType({}))
    def __post_init__(self) -> None: object.__setattr__(self, "builders", MappingProxyType(dict(self.builders)))
    def is_empty(self) -> bool: return not any((*(getattr(self, s) for s in _VERIF_SLOTS), self.builders))

class _TxJournal:
    """Tracks filesystem mutations for fail-closed rollback across a single transaction."""
    def __init__(self, root: Path, backup_root: Path) -> None:
        self.root, self.backup_root = root.resolve(), backup_root
        self._backed_up: set[Path] = set()
        self.backups: list[tuple[Path, Path]] = []
        self.created_files: list[Path] = []
        self.created_dirs: list[Path] = []
        self.removed_dirs: list[Path] = []

    def mkdir_tracked(self, target_dir: Path) -> None:
        missing, cur = [], target_dir
        while not cur.exists() and not cur.is_symlink():
            missing.append(cur)
            if cur == self.root or cur.parent == cur: break
            cur = cur.parent
        _assert_no_symlink_inside(self.root, target_dir)
        for d in reversed(missing):
            d.mkdir(exist_ok=True); self.created_dirs.append(d)

    def backup_file(self, orig: Path, rel_key: str) -> None:
        if orig in self._backed_up: return
        if orig.is_symlink() or not orig.is_file(): raise ManualModificationConflictError(f"Refusing backup of non-regular file: '{orig}'.")
        bkp = self.backup_root / rel_key
        bkp.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(orig, bkp); self._backed_up.add(orig); self.backups.append((orig, bkp))

    def rollback(self, original_exc: BaseException) -> None:
        errors: list[str] = []
        def _run(label: str, fn: Callable[[], object]) -> None:
            try: fn()
            except OSError as exc: errors.append(f"{label}: {exc}")
        for fp in reversed(self.created_files):
            if fp.is_file() or fp.is_symlink(): _run(f"unlink '{fp}'", fp.unlink)
        for dp in reversed(self.created_dirs):
            if dp.is_dir() and not any(dp.iterdir()): _run(f"rmdir '{dp}'", dp.rmdir)
        for dp in self.removed_dirs: _run(f"mkdir '{dp}'", lambda d=dp: d.mkdir(parents=True, exist_ok=True))
        for orig, bkp in reversed(self.backups):
            _run(f"restore '{orig}'", lambda o=orig, b=bkp: (o.parent.mkdir(parents=True, exist_ok=True), shutil.copy2(b, o)))
        if errors: raise SddGeneratorError(f"Materialization failed ({original_exc}) and rollback failed: {'; '.join(errors)}") from original_exc

def _assert_no_symlink_inside(root: Path, target: Path) -> None:
    root_res, cur = root.resolve(), target
    while cur != root_res and cur.parent != cur:
        if cur.is_symlink(): raise ManualModificationConflictError(f"Symlink path not permitted inside workspace: '{cur}'.")
        if cur.exists() and not cur.resolve().is_relative_to(root_res): raise InvalidManifestError(f"Path escapes repository root: '{cur}'.")
        cur = cur.parent

def _resolve_safe_rel_path(repo_root: Path, rel_path: str) -> Path:
    if not rel_path or "\\" in rel_path or "\x00" in rel_path:
        raise InvalidManifestError(f"Invalid POSIX repo-relative path: {rel_path!r}.")
    posix = PurePosixPath(rel_path)
    if posix.is_absolute() or any(p in ("", ".", "..") for p in posix.parts):
        raise InvalidManifestError(f"Unsafe or traversal path not permitted: {rel_path!r}.")
    root_res = repo_root.resolve()
    target = (root_res / posix).resolve()
    if not target.is_relative_to(root_res) or target == root_res:
        raise InvalidManifestError(f"Target path escapes repository root: {rel_path!r}.")
    return target

def _validate_agent_slug(name: str, label: str) -> str:
    if not isinstance(name, str) or not name.strip() or name != name.strip() or name.startswith(".") or any(c in name for c in ("/", "\\", "..", "\x00")):
        raise InvalidManifestError(f"Invalid or unsafe {label}: {name!r}.")
    return name

def atomic_write_json(path: Path, payload: Mapping[str, object]) -> None:
    """Write JSON atomically via a same-directory temporary file and `os.replace()`."""
    if path.is_symlink(): raise ManualModificationConflictError(f"Refusing atomic write to symlink: '{path}'.")
    target = path.resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    raw = (json.dumps(payload, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    tmp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(mode="wb", dir=target.parent, prefix=f".{target.name}.", suffix=".tmp", delete=False) as fh:
            tmp_path = Path(fh.name)
            fh.write(raw); fh.flush(); os.fsync(fh.fileno())
        os.replace(tmp_path, target)
    except Exception:
        if tmp_path is not None:
            try: tmp_path.unlink(missing_ok=True)
            except OSError as exc: print(f"[WARN] Failed to clean temp file '{tmp_path}': {exc}", file=sys.stderr)
        raise

def is_generic_dod_placeholder(command: str) -> bool:
    """Return True if `command` is empty or an unconfigured multi-stack/template placeholder."""
    s = command.strip(); low = s.lower()
    return not s or low in _EXACT_GENERIC_DOD or " / " in s or " | " in s or "[ej:" in low or "<path/to/" in low or "[comando" in low or (s.startswith("[") and s.endswith("]"))

def _extract_verification_yaml(content: str) -> str | None:
    explicit, yaml_blocks, buf, in_comment, in_sec25, sec25_lvl, ticks, info = [], [], [], False, False, 0, 0, ""
    for line in content.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        if ticks:
            if re.match(rf"^[ \t]*`{{{ticks},}}[ \t]*$", line):
                body = "\n".join(buf)
                if ticks == 3 and _VERIF_INFO_RE.match(info): explicit.append(body)
                elif _YAML_INFO_RE.match(info): yaml_blocks.append((in_sec25, body))
                ticks, info, buf = 0, "", []
            else: buf.append(line)
            continue
        out, i = [], 0
        while i < len(line):
            if in_comment:
                end = line.find("-->", i); in_comment, i = (True, len(line)) if end == -1 else (False, end + 3)
            elif line.startswith("<!--", i): in_comment, i = True, i + 4
            else: out.append(line[i]); i += 1
        cleaned = "".join(out)
        if hm := _HEADING_RE.match(cleaned):
            lvl = len(hm.group(1))
            in_sec25, sec25_lvl = (True, lvl) if _SEC_25_HEADING_RE.match(cleaned) else ((False, 0) if in_sec25 and lvl <= sec25_lvl else (in_sec25, sec25_lvl))
        if m := _OPEN_FENCE_RE.match(cleaned):
            ticks, info, buf = len(m.group(1)), m.group(2).strip(), []
    if ticks and ((ticks == 3 and _VERIF_INFO_RE.match(info)) or (in_sec25 and _YAML_INFO_RE.match(info))):
        raise StackConfigError("Unclosed verification commands YAML block in STACK.md.")
    if len(explicit) > 1: raise StackConfigError("Multiple ```yaml sdd:verification-commands blocks in STACK.md.")
    if explicit: return explicit[0]
    matched = [b for f25, b in yaml_blocks if (p := parse_yaml_subset(b) if f25 or "verification_commands:" in b else {}) and ("verification_commands" in p or (f25 and any(k in _ALLOWED_VERIF_KEYS for k in p)))]
    if len(matched) > 1: raise StackConfigError("Multiple verification_commands YAML blocks in STACK.md.")
    return matched[0] if matched else None

def _validate_cmd_str(val: object, field_name: str) -> str | None:
    if val is None: return None
    if not isinstance(val, str) or not val.strip():
        raise StackConfigError(f"Field '{field_name}' in verification_commands must be a non-empty string or null.")
    clean = val.strip()
    if clean.lower() == "n/a": return None
    if is_generic_dod_placeholder(clean):
        raise StackConfigError(f"Placeholder command not allowed in '{field_name}': {clean!r}.")
    return clean

def _build_verification_commands(raw: Mapping[str, object], prefix: str = "") -> VerificationCommands:
    if unknown := sorted(set(raw) - _ALLOWED_VERIF_KEYS):
        raise StackConfigError(f"Unknown key(s) in verification_commands: {', '.join(unknown)}.")
    if "builders" in raw and "overrides" in raw:
        raise StackConfigError("Specify either 'builders' or 'overrides' in verification_commands, not both.")
    raw_b, builders_map = raw.get("builders", raw.get("overrides")), {}
    if raw_b is not None:
        if not isinstance(raw_b, Mapping): raise StackConfigError("'verification_commands.builders' must be a YAML mapping.")
        for b_name, b_cmd in raw_b.items():
            slug = _validate_agent_slug(str(b_name), "verification_commands builder name")
            if cmd := _validate_cmd_str(b_cmd, f"{prefix}builders.{slug}"): builders_map[slug] = cmd
    return VerificationCommands(**{s: _validate_cmd_str(raw.get(s), f"{prefix}{s}") for s in _VERIF_SLOTS}, builders=builders_map)

def parse_verification_commands(stack_path: Path) -> VerificationCommands:
    """Parse optional section 2.5 `sdd:verification-commands` / `verification_commands` from `STACK.md`."""
    if not stack_path.exists(): return VerificationCommands()
    try: content = stack_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc: raise StackConfigError(f"Cannot read stack file '{stack_path}': {exc}") from exc
    if (block := _extract_verification_yaml(content)) is None: return VerificationCommands()
    raw = parse_yaml_subset(block)
    if "verification_commands" in raw:
        if len(raw) != 1 or not isinstance(raw["verification_commands"], dict):
            raise StackConfigError("'verification_commands' must be a standalone YAML mapping in STACK.md section 2.5.")
        raw = raw["verification_commands"]
    return _build_verification_commands(raw, prefix="verification_commands.")

def resolve_builder_dod(
    builder_name: str, default_dod: str, commands: VerificationCommands | Mapping[str, object] | None, gate_s0_approved: bool = False,
) -> str:
    """Resolve builder DoD command from section 2.5 `VerificationCommands` and reject placeholders on approved S0."""
    cmds = commands if isinstance(commands, VerificationCommands) else (VerificationCommands() if commands is None else _build_verification_commands(commands))
    clean_name = builder_name.lstrip("@")
    if override := cmds.builders.get(clean_name) or cmds.builders.get(builder_name): return override
    for slot in _ROLE_COMMAND_MAP.get(clean_name, _DEFAULT_ROLE_ORDER):
        if resolved := getattr(cmds, slot): return str(resolved)
    if gate_s0_approved and is_generic_dod_placeholder(default_dod):
        raise StackConfigError(f"Unconfigured generic DoD placeholder {default_dod!r} for builder '{builder_name}' is forbidden when Gate S0 is approved; configure specs/STACK.md section 2.5.")
    return default_dod

def collect_core_agent_files(agents_dir: Path, core_agents: Sequence[str] = DEFAULT_CORE_AGENTS) -> dict[str, dict[str, str]]:
    """Hash existing regular core agent `.md` files in `agents_dir` for lock tracking."""
    if not agents_dir.exists(): return {}
    if agents_dir.is_symlink() or not agents_dir.is_dir(): raise InvalidManifestError(f"Agents path must be a regular directory: '{agents_dir}'.")
    tracked: dict[str, dict[str, str]] = {}
    for name in sorted(set(core_agents)):
        slug = _validate_agent_slug(name, "core agent")
        rel, candidate = f".agents/agents/{slug}.md", agents_dir / f"{slug}.md"
        if candidate.is_symlink() or (candidate.exists() and not candidate.is_file()):
            raise ManualModificationConflictError(f"Core agent file must be a regular file (not symlink): '{rel}'.")
        if candidate.is_file():
            try: tracked[rel] = {"sha256": hashlib.sha256(candidate.read_bytes()).hexdigest(), "owner": "core", "kind": "agent"}
            except OSError as exc: raise InvalidManifestError(f"Cannot read '{rel}': {exc}") from exc
    return tracked

def detect_orphan_agents(
    agents_dir: Path, expected_agents: Collection[str], *, strict: bool = False, prev_managed_agents: Collection[str] = (),
) -> list[str]:
    """Return sorted unmanaged/orphan `.md` filenames in `agents_dir` (raising if `strict=True`)."""
    if not agents_dir.exists(): return []
    if agents_dir.is_symlink() or not agents_dir.is_dir(): raise InvalidManifestError(f"Agents directory is invalid: '{agents_dir}'.")
    exp = {a[:-3] if a.endswith(".md") else a for a in expected_agents}
    prev = {a[:-3] if a.endswith(".md") else a for a in prev_managed_agents}
    dir_res = agents_dir.resolve()
    orphans = [
        e.name for e in sorted(agents_dir.iterdir(), key=lambda p: p.name)
        if e.suffix.lower() == ".md" and (e.is_symlink() or not e.is_file() or not e.resolve().is_relative_to(dir_res) or (e.stem not in exp and e.stem not in prev))
    ]
    if strict and orphans: raise CollisionError(f"Unmanaged/orphan agent file(s) in '{agents_dir}': {', '.join(orphans)}.")
    return orphans

def _plan_inbox_reconciliation(
    inbox_dir: Path, active_agents: Collection[str], obsolete_candidates: Collection[str] | None, drain_to: str | None, fail_on_nonempty: bool,
) -> tuple[list[tuple[Path, Path]], list[Path], list[Path], Path | None, list[str]]:
    if not inbox_dir.exists(): return [], [], [], None, []
    if inbox_dir.is_symlink() or not inbox_dir.is_dir(): raise InboxReconciliationError(f"Inbox path must be a regular directory: '{inbox_dir}'.")
    inbox_root = inbox_dir.resolve()
    active_set = {_validate_agent_slug(a, "active agent") for a in active_agents}
    drain_slug = _validate_agent_slug(drain_to, "drain_to") if drain_to is not None else None
    target_dir = (inbox_root / drain_slug).resolve() if drain_slug is not None else None
    if target_dir is not None and ((inbox_root / drain_slug).is_symlink() or (target_dir.exists() and not target_dir.is_dir())):
        raise InboxReconciliationError(f"Invalid drain target directory: '.agent-inbox/{drain_slug}'.")
    stale_names = (
        sorted(e.name for e in inbox_root.iterdir() if e.is_dir() and not e.name.startswith(".") and e.name not in active_set and e.name != drain_slug)
        if obsolete_candidates is None else sorted({a for a in obsolete_candidates if a not in active_set and a != drain_slug})
    )
    moves, unlinks, rm_dirs, summary, claimed = [], [], [], [], set()
    for stale in stale_names:
        stale_dir = (inbox_root / _validate_agent_slug(stale, "stale inbox agent")).resolve()
        if (inbox_root / stale).is_symlink() or not stale_dir.is_relative_to(inbox_root) or stale_dir == inbox_root:
            raise InboxReconciliationError(f"Unsafe obsolete inbox directory: '{stale}'.")
        if not stale_dir.is_dir(): continue
        files, subdirs = [], []
        for entry in sorted(stale_dir.rglob("*"), key=lambda p: p.as_posix()):
            if entry.is_symlink() or not entry.resolve().is_relative_to(stale_dir):
                raise InboxReconciliationError(f"Symlink or escape inside obsolete inbox '{stale}': '{entry.name}'.")
            (files if entry.is_file() else subdirs).append(entry)
        tickets = [f for f in files if not (f.parent == stale_dir and f.name == ".gitkeep")]
        if tickets and target_dir is None:
            if fail_on_nonempty:
                raise InboxReconciliationError(f"Obsolete inbox '.agent-inbox/{stale}' has {len(tickets)} pending file(s); pass drain_to (--drain-inboxes) explicitly.")
            print(f"  -> [WARN] Conservando buzon '{stale_dir}' porque contiene ficheros pendientes.", file=sys.stderr); continue
        if tickets and target_dir is not None:
            for src in tickets:
                rel_name = src.relative_to(stale_dir).as_posix().replace("/", "__")
                dst = target_dir / rel_name
                if dst.exists() or dst in claimed:
                    dst = next(c for i in itertools.count(1) if (c := target_dir / (f"{stale}__{rel_name}" if i == 1 else f"{stale}__{i - 1}__{rel_name}")) not in claimed and not c.exists())
                claimed.add(dst); moves.append((src, dst))
            summary.append(f"drained:{stale}->{drain_slug}({len(tickets)})")
        else: summary.append(f"removed:{stale}")
        if (gk := stale_dir / ".gitkeep").is_file(): unlinks.append(gk)
        rm_dirs.extend([*reversed(subdirs), stale_dir])
    return moves, unlinks, rm_dirs, (target_dir if moves else None), summary

def _execute_inbox_plan(
    moves: Sequence[tuple[Path, Path]], unlinks: Sequence[Path], rm_dirs: Sequence[Path], create_target: Path | None, journal: _TxJournal,
) -> None:
    if create_target is not None: journal.mkdir_tracked(create_target)
    for idx, (src, dst) in enumerate(moves):
        journal.backup_file(src, f"inbox_mv/{idx}_{src.name}"); journal.created_files.append(dst); shutil.copy2(src, dst); src.unlink()
    for idx, gk in enumerate(unlinks):
        if gk.is_file(): journal.backup_file(gk, f"inbox_gk/{idx}_{gk.parent.name}.gitkeep"); gk.unlink()
    for dp in rm_dirs:
        if dp.is_dir(): dp.rmdir(); journal.removed_dirs.append(dp)

def reconcile_obsolete_inboxes(
    inbox_dir: Path, active_agents: Collection[str], obsolete_candidates: Collection[str] | None = None,
    *, drain_to: str | None = None, fail_on_nonempty: bool = True,
) -> list[str]:
    """Fail closed on non-empty obsolete inboxes unless `drain_to` is specified, then drain atomically."""
    mv, ul, rmd, ct, summary = _plan_inbox_reconciliation(inbox_dir, active_agents, obsolete_candidates, drain_to, fail_on_nonempty)
    if not (mv or ul or rmd): return []
    with tempfile.TemporaryDirectory(prefix="sdd_inbox_tx_") as tmp_str:
        journal = _TxJournal(inbox_dir.resolve(), Path(tmp_str))
        try: _execute_inbox_plan(mv, ul, rmd, ct, journal)
        except Exception as exc: journal.rollback(exc); raise
    return summary

def _prune_empty_dirs(base_dir: Path, deleted: Sequence[Path], remove_base: bool, journal: _TxJournal) -> None:
    if not base_dir.is_dir() or base_dir.is_symlink(): return
    base_res = base_dir.resolve()
    for df in (p for p in deleted if p.is_relative_to(base_res)):
        cur = df.parent
        while cur != base_res and cur.is_relative_to(base_res) and cur.is_dir() and not any(cur.iterdir()):
            cur.rmdir(); journal.removed_dirs.append(cur); cur = cur.parent
    if remove_base and base_res.is_dir() and not any(base_res.iterdir()):
        base_res.rmdir(); journal.removed_dirs.append(base_res)

def apply_plan_transactionally(
    ws_paths: WorkspacePathsLike, desired: Mapping[str, PlannedFileLike], prev_files: Mapping[str, Mapping[str, str]],
    active_agents: Sequence[str], prev_agents: Collection[str], lock_payload: Mapping[str, object] | None = None,
    *, write_lock: bool = True, drain_to: str | None = None, fail_on_nonempty_inbox: bool = True,
    strict_agents: bool = False, protected_rel_paths: Collection[str] = (),
) -> list[str]:
    """Apply deletions, writes, inbox reconciliation, and `squad.lock.json` update with full rollback."""
    if strict_agents: detect_orphan_agents(ws_paths.agents_dir, active_agents, strict=True, prev_managed_agents=prev_agents)
    protected = set(protected_rel_paths)
    delete_rels = sorted(r for r in (set(prev_files) - set(desired)) if prev_files[r].get("owner") != "core" and r not in protected)
    for rel in (*delete_rels, *sorted(desired)): _resolve_safe_rel_path(ws_paths.root, rel)
    with tempfile.TemporaryDirectory(prefix="sdd_tx_") as tmp_str:
        journal = _TxJournal(ws_paths.root, Path(tmp_str))
        try:
            for d in (ws_paths.agents_dir, ws_paths.inbox_dir, ws_paths.root / ".agents" / "overrides"): journal.mkdir_tracked(d)
            deleted = []
            for rel in delete_rels:
                disk = _resolve_safe_rel_path(ws_paths.root, rel)
                if disk.is_symlink(): raise ManualModificationConflictError(f"Refusing deletion of symlink '{rel}'.")
                if disk.is_file(): journal.backup_file(disk, f"files/{rel}"); disk.unlink(); deleted.append(disk)
            _prune_empty_dirs(ws_paths.skills_dir, deleted, False, journal)
            _prune_empty_dirs(ws_paths.pack_rules_dir, deleted, True, journal)
            for rel, planned in sorted(desired.items()):
                disk = _resolve_safe_rel_path(ws_paths.root, rel)
                if disk.is_symlink(): raise ManualModificationConflictError(f"Refusing overwrite of symlink '{rel}'.")
                if disk.is_file() and disk.read_bytes() == planned.content: continue
                if disk.is_file(): journal.backup_file(disk, f"files/{rel}")
                elif disk.exists(): raise ManualModificationConflictError(f"Refusing overwrite of non-regular path '{rel}'.")
                else: journal.mkdir_tracked(disk.parent); journal.created_files.append(disk)
                disk.write_bytes(planned.content)
            inbox_root = ws_paths.inbox_dir.resolve()
            for name in sorted({_validate_agent_slug(a, "agent") for a in active_agents}):
                agent_dir = (inbox_root / name).resolve()
                journal.mkdir_tracked(agent_dir)
                if not (gk := agent_dir / ".gitkeep").exists(): journal.created_files.append(gk); gk.touch()
            mv, ul, rmd, ct, summary = _plan_inbox_reconciliation(ws_paths.inbox_dir, active_agents, set(prev_agents) - set(active_agents), drain_to, fail_on_nonempty_inbox)
            _execute_inbox_plan(mv, ul, rmd, ct, journal)
            if write_lock and lock_payload is not None:
                _assert_no_symlink_inside(ws_paths.root, ws_paths.lock_file)
                if ws_paths.lock_file.is_symlink(): raise ManualModificationConflictError(f"Refusing write to symlink '{ws_paths.lock_file}'.")
                if ws_paths.lock_file.is_file(): journal.backup_file(ws_paths.lock_file, "lock/squad.lock.json")
                elif ws_paths.lock_file.exists(): raise ManualModificationConflictError(f"Refusing overwrite of non-regular '{ws_paths.lock_file}'.")
                else: journal.mkdir_tracked(ws_paths.lock_file.parent); journal.created_files.append(ws_paths.lock_file)
                atomic_write_json(ws_paths.lock_file, lock_payload)
            return summary
        except Exception as exc: journal.rollback(exc); raise

def compute_content_digest(payload: Mapping[str, object]) -> str:
    """Compute canonical SHA-256 over structural lock fields excluding `timestamp` and `content_digest`."""
    body = {k: v for k, v in payload.items() if k not in {"timestamp", "content_digest"}}
    return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()

_PACK_KEYS = (("name", "name"), ("id", "pack_id"), ("source", "source"))
_FILE_KEYS = (("sha256", "sha256"), ("owner", "owner"), ("kind", "kind"))
def _extract_fields(obj: object, keys: tuple[tuple[str, str], ...]) -> dict[str, str]:
    return {dst: str(obj[dst] if isinstance(obj, Mapping) else getattr(obj, attr)) for dst, attr in keys}

def build_deterministic_lock_payload(
    *, stack_approved: bool, preset: str, tech_stack: str, core_agents: Sequence[str], builders: Sequence[str],
    specialists: Sequence[str], active_packs: Sequence[object], files: Mapping[str, object],
    core_agent_files: Mapping[str, Mapping[str, str]] | None = None,
    prev_payload: Mapping[str, object] | None = None, timestamp: str | None = None,
) -> dict[str, object]:
    """Build canonically sorted `squad.lock.json` v2 payload with deterministic `content_digest`."""
    merged = {rel: _extract_fields(meta, _FILE_KEYS) for rel, meta in files.items()}
    for rel, meta in (core_agent_files or {}).items(): merged.setdefault(rel, _extract_fields(meta, _FILE_KEYS))
    structural: dict[str, object] = {
        "schema_version": 2, "stack_approved": bool(stack_approved), "gate00_approved": bool(stack_approved),
        "preset": preset, "tech_stack": tech_stack, "core_agents": sorted(set(core_agents)),
        "builders": sorted(set(builders)), "specialists": sorted(set(specialists)),
        "active_packs": sorted((_extract_fields(p, _PACK_KEYS) for p in active_packs), key=lambda p: (p["name"], p["id"], p["source"])),
        "files": {rel: merged[rel] for rel in sorted(merged)},
    }
    digest = compute_content_digest(structural)
    prev_ts = prev_payload.get("timestamp") if isinstance(prev_payload, Mapping) else None
    same = (isinstance(prev_payload, Mapping) and isinstance(prev_ts, str) and bool(prev_ts.strip()) and prev_payload.get("content_digest") == digest
            and {k: v for k, v in prev_payload.items() if k not in {"timestamp", "content_digest"}} == structural)
    eff_ts = timestamp if timestamp is not None else (str(prev_ts) if same else datetime.datetime.now(datetime.timezone.utc).isoformat())
    return {"schema_version": 2, "timestamp": eff_ts, "content_digest": digest, **{k: v for k, v in structural.items() if k != "schema_version"}}

def _verify_lock_schema(payload: Mapping[str, object], core_agents: Sequence[str]) -> list[str]:
    errs: list[str] = []
    if type(payload.get("schema_version")) is not int or payload.get("schema_version") != 2: errs.append("Invalid 'schema_version' (expected 2).")
    sa, ga = payload.get("stack_approved"), payload.get("gate00_approved")
    if type(sa) is not bool or type(ga) is not bool or sa != ga: errs.append("'stack_approved' and 'gate00_approved' must be equal strict booleans.")
    if not isinstance(payload.get("preset"), str) or not str(payload["preset"]).strip(): errs.append("Field 'preset' must be a non-empty string.")
    for key in ("core_agents", "builders", "specialists"):
        val = payload.get(key)
        if not isinstance(val, list) or any(not isinstance(x, str) or not x.strip() for x in val): errs.append(f"Field '{key}' must be a list of non-empty strings.")
        elif val != sorted(set(val)): errs.append(f"Field '{key}' is not canonically sorted and deduplicated.")
    if isinstance(payload.get("core_agents"), list) and sorted(set(core_agents)) != sorted(set(payload["core_agents"])):
        errs.append("Field 'core_agents' does not match expected core agent roster.")
    packs = payload.get("active_packs")
    if not isinstance(packs, list) or any(not isinstance(p, dict) or not all(isinstance(p.get(k), str) and p[k].strip() for k in ("name", "id", "source")) for p in packs):
        errs.append("Field 'active_packs' must be a list of {name, id, source} objects.")
    elif packs != sorted(packs, key=lambda p: (p["name"], p["id"], p["source"])): errs.append("Field 'active_packs' is not canonically sorted.")
    digest = payload.get("content_digest")
    if not isinstance(digest, str) or not _SHA256_RE.match(digest): errs.append("Missing or malformed 'content_digest' SHA-256 in squad.lock.json.")
    elif digest != compute_content_digest(payload): errs.append("Lockfile 'content_digest' mismatch (metadata tampered or non-canonical).")
    return errs

def verify_lock_integrity(
    ws_paths: WorkspacePathsLike, *, expected_files: Mapping[str, object] | None = None,
    expected_meta: Mapping[str, object] | None = None, core_agents: Sequence[str] = DEFAULT_CORE_AGENTS, strict_agents: bool = True,
) -> list[str]:
    """Read-only verification of `squad.lock.json` against disk, `CORE_AGENTS`, orphans, and expected plan."""
    if ws_paths.lock_file.is_symlink() or not ws_paths.lock_file.is_file(): return [f"Missing or symlinked lockfile '{ws_paths.lock_file}'."]
    try: payload = json.loads(ws_paths.lock_file.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc: return [f"Unreadable or invalid JSON in '{ws_paths.lock_file}': {exc}"]
    if not isinstance(payload, dict): return [f"Lockfile root must be a JSON object: '{ws_paths.lock_file}'."]
    mismatches, raw_files = _verify_lock_schema(payload, core_agents), payload.get("files")
    if not isinstance(raw_files, dict): return [*mismatches, "Field 'files' must be a JSON object."]
    if list(raw_files.keys()) != sorted(raw_files.keys()): mismatches.append("Field 'files' keys are not canonically sorted.")
    verified: dict[str, dict[str, str]] = {}
    for rel, meta in raw_files.items():
        if not isinstance(rel, str) or not isinstance(meta, dict): mismatches.append(f"Corrupt file lock entry: {rel!r}."); continue
        try: disk = _resolve_safe_rel_path(ws_paths.root, rel)
        except InvalidManifestError as exc: mismatches.append(str(exc)); continue
        sha = meta.get("sha256")
        if not isinstance(sha, str) or not _SHA256_RE.match(sha): mismatches.append(f"Invalid sha256 metadata for '{rel}'."); continue
        verified[rel] = {k: str(meta.get(k, "")) for k in ("sha256", "owner", "kind")}
        try:
            if disk.is_symlink() or not disk.is_file(): mismatches.append(f"Missing, non-regular, or symlinked managed file on disk: '{rel}'.")
            elif (actual := hashlib.sha256(disk.read_bytes()).hexdigest()) != sha: mismatches.append(f"Hash mismatch on disk for '{rel}': expected {sha}, got {actual}.")
        except OSError as exc: mismatches.append(f"Cannot read managed file '{rel}': {exc}")
    exp_core = {f".agents/agents/{_validate_agent_slug(c, 'core agent')}.md" for c in core_agents}
    mismatches.extend(f"Unexpected lockfile entry claiming 'core' owner: '{r}'." for r, m in verified.items() if m["owner"] == "core" and r not in exp_core)
    for cname in sorted(set(core_agents)):
        rel, cpath = f".agents/agents/{cname}.md", ws_paths.agents_dir / f"{cname}.md"
        if cpath.is_symlink(): mismatches.append(f"Core agent file must not be a symlink: '{rel}'.")
        elif cpath.is_file() and (rel not in verified or verified[rel]["owner"] != "core"): mismatches.append(f"Core agent '{rel}' missing or mis-owned in squad.lock.json['files'].")
    if strict_agents and ws_paths.agents_dir.exists():
        try:
            stems = {PurePosixPath(r).stem for r in verified if r.startswith(".agents/agents/") and r.endswith(".md")}
            mismatches.extend(f"Unmanaged/orphan agent file on disk: '.agents/agents/{o}'." for o in detect_orphan_agents(ws_paths.agents_dir, stems))
        except SddGeneratorError as exc: mismatches.append(str(exc))
    if ws_paths.stack_path.exists():
        try:
            cfg, eff = parse_stack_config(ws_paths.stack_path); parse_verification_commands(ws_paths.stack_path)
            if payload.get("stack_approved") != eff: mismatches.append(f"Lock 'stack_approved' ({payload.get('stack_approved')}) != STACK.md ({eff}).")
            if expected_meta is None:
                if payload.get("preset") != cfg.preset: mismatches.append(f"Lock 'preset' ({payload.get('preset')!r}) != STACK.md ({cfg.preset!r}).")
                sc = [p for p in (payload.get("active_packs") or []) if isinstance(p, dict) and p.get("source") == "stack-config"]
                reqs, refs = ({p.strip() for p in cfg.packs} if eff else set()), {ref for p in sc for ref in (p.get("name"), p.get("id"))}
                if any(r not in refs for r in reqs) or any(p.get("name") not in reqs and p.get("id") not in reqs for p in sc):
                    mismatches.append("Lock 'active_packs' (stack-config) diverges from STACK.md packs.")
        except StackConfigError as exc: mismatches.append(f"Invalid STACK.md: {exc}")
    if expected_files is not None:
        exp_norm, actual_gen = {rel: _extract_fields(m, _FILE_KEYS) for rel, m in expected_files.items()}, {r: m for r, m in verified.items() if m["owner"] != "core"}
        mismatches.extend(f"Expected generated file missing from lockfile: '{r}'." for r in sorted(set(exp_norm) - set(actual_gen)))
        mismatches.extend(f"Unexpected non-core file in lockfile: '{r}'." for r in sorted(set(actual_gen) - set(exp_norm)))
        mismatches.extend(f"Lock entry for '{r}' diverges from catalog/STACK.md expected build." for r in sorted(set(exp_norm) & set(actual_gen)) if actual_gen[r] != exp_norm[r])
    if expected_meta is not None:
        mismatches.extend(f"Lock '{k}' ({payload.get(k)!r}) != expected ({v!r})." for k, v in expected_meta.items() if payload.get(k) != v)
    return mismatches

__all__ = ["DEFAULT_CORE_AGENTS", "InboxReconciliationError", "PlannedFileLike", "VerificationCommands", "WorkspacePathsLike", "apply_plan_transactionally", "atomic_write_json", "build_deterministic_lock_payload", "collect_core_agent_files", "compute_content_digest", "detect_orphan_agents", "is_generic_dod_placeholder", "parse_verification_commands", "reconcile_obsolete_inboxes", "resolve_builder_dod", "verify_lock_integrity"]
