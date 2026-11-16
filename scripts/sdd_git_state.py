#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SDD Git Governance, Runner, Dynamic Ref/Remote Resolution & Worktree State."""

from __future__ import annotations

import contextlib, copy, datetime, json, os, pathlib, re, subprocess, sys, tempfile, threading, time
from typing import Any, Dict, Iterator, List, Optional, Tuple

if os.name == "nt":
    import msvcrt
else:
    import fcntl

_DEFAULT_ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
ROOT_DIR = _DEFAULT_ROOT_DIR
STACK_PATH = _DEFAULT_ROOT_DIR / "specs" / "STACK.md"
ACTIVE_STATE_JSON = _DEFAULT_ROOT_DIR / ".agents" / "active_work_item.json"
ACTIVE_STATE_MD = _DEFAULT_ROOT_DIR / ".agents" / "ACTIVE_STATE.md"
DEFAULT_WORKTREES_DIR = _DEFAULT_ROOT_DIR / ".worktrees"
_DEFAULTS = {"ROOT_DIR": ROOT_DIR, "STACK_PATH": STACK_PATH, "ACTIVE_STATE_JSON": ACTIVE_STATE_JSON, "ACTIVE_STATE_MD": ACTIVE_STATE_MD}

_SPEC_BUCKETS = ("specs/features", "specs/changes", "specs/bugs", ".sdd/framework/work-items")
_SAFE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_GIT_FORBIDDEN_CHARS_RE = re.compile(r"[\x00-\x1f\x7f~^:?*\[\\\s]")
_THREAD_LOCKS_GUARD = threading.Lock()
_THREAD_LOCKS: Dict[str, threading.RLock] = {}
_LOCK_STATE = threading.local()

DEFAULT_GOVERNANCE: Dict[str, Any] = {
    "provider": "github", "auth_mode": "cli", "branching_model": "sdd-gitflow",
    "branches": {"production": "main", "integration": "develop", "prefix_feature": "feat/", "prefix_change": "change/", "prefix_bug": "fix/", "prefix_release": "release/", "prefix_hotfix": "hotfix/"},
    "worktrees": {"enabled": True, "directory": ".worktrees"},
    "auto_merge": {"develop": True, "main": False},
}
_MD_TEMPLATE = "# SDD Starter — Active Session Pointer (Managed by @orchestrator)\n- **Timestamp:** \n- **Active Work Item:** `IDLE (No Active Work Item)`\n- **Active Branch:** `N/A`\n- **Spec Folder Path:** `N/A`\n- **Current Gate:** `IDLE`\n- **Active Worktrees:** None\n"


def is_link_or_junction(path: pathlib.Path) -> bool:
    """Return True if path is a symlink or Windows NTFS junction/reparse point."""
    try:
        if path.is_symlink() or (hasattr(os.path, "isjunction") and os.path.isjunction(path)):
            return True
        return os.name == "nt" and bool(getattr(os.lstat(path), "st_file_attributes", 0) & 0x0400)
    except OSError:
        return False


def _patched_attr(attr_name: str, mods: Tuple[str, ...]) -> Optional[pathlib.Path]:
    default_val = _DEFAULTS[attr_name]
    for mod_name in mods:
        val = getattr(sys.modules.get(mod_name), attr_name, None)
        if isinstance(val, pathlib.Path) and val != default_val:
            return val
    return None


def resolve_repo_root(root_dir: Optional[pathlib.Path] = None) -> pathlib.Path:
    """Resolve active repository root honoring monkeypatches on sdd_git.ROOT_DIR."""
    if root_dir is not None:
        return pathlib.Path(root_dir)
    return _patched_attr("ROOT_DIR", ("scripts.sdd_git", "sdd_git", "scripts.sdd_git_worktree", "sdd_git_worktree", __name__)) or ROOT_DIR


def _resolve_repo_file(attr: str, *parts: str, root_dir: Optional[pathlib.Path] = None) -> pathlib.Path:
    if root_dir is not None:
        return pathlib.Path(root_dir).joinpath(*parts)
    return _patched_attr(attr, ("scripts.sdd_git", "sdd_git", __name__)) or resolve_repo_root().joinpath(*parts)


@contextlib.contextmanager
def acquire_file_lock(lock_path: pathlib.Path, timeout_s: float = 15.0) -> Iterator[None]:
    """Re-entrant cross-thread and cross-process advisory file lock."""
    key = str(lock_path.resolve(strict=False))
    with _THREAD_LOCKS_GUARD:
        tlock = _THREAD_LOCKS.setdefault(key, threading.RLock())
    depths = _LOCK_STATE.__dict__.setdefault("depths", {})
    with tlock:
        if depths.get(key, 0) > 0:
            depths[key] += 1
            try:
                yield
            finally:
                depths[key] -= 1
            return
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        if is_link_or_junction(lock_path):
            raise RuntimeError(f"Lock file cannot be a symlink or junction: {lock_path}")
        fd, locked = os.open(str(lock_path), os.O_CREAT | os.O_RDWR, 0o666), False
        try:
            if os.name == "nt":
                if os.fstat(fd).st_size == 0:
                    os.write(fd, b"\x00")
                deadline = time.monotonic() + timeout_s
                while not locked:
                    try:
                        os.lseek(fd, 0, os.SEEK_SET)
                        msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
                        locked = True
                    except OSError as exc:
                        if time.monotonic() >= deadline:
                            raise TimeoutError(f"Timed out waiting for lock '{lock_path}': {exc}") from exc
                        time.sleep(0.02)
            else:
                fcntl.flock(fd, fcntl.LOCK_EX)
                locked = True
            depths[key] = 1
            yield
        finally:
            depths.pop(key, None)
            if locked:
                if os.name == "nt":
                    os.lseek(fd, 0, os.SEEK_SET)
                    msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(fd, fcntl.LOCK_UN)
            os.close(fd)


def atomic_write_text(target: pathlib.Path, content: str) -> None:
    """Write UTF-8 text atomically via same-directory temp file and os.replace."""
    target.parent.mkdir(parents=True, exist_ok=True)
    if is_link_or_junction(target) or is_link_or_junction(target.parent):
        raise RuntimeError(f"Refusing atomic write through symlink/junction: {target}")
    fd, tmp_name = tempfile.mkstemp(dir=str(target.parent), prefix=f".{target.name}.", suffix=".tmp")
    tmp_path = pathlib.Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, target)
    except Exception:
        tmp_path.unlink(missing_ok=True)
        raise


def _parse_yaml_val(raw: str, key_name: str, is_bool: bool = False) -> Any:
    val = re.sub(r"""^((?:[^'"#]|'[^']*'|"[^"]*")*?)#.*$""", r"\1", raw).strip()
    if len(val) >= 2 and val[0] == val[-1] and val[0] in {"'", '"'}:
        val = val[1:-1]
    if not is_bool:
        return val
    norm = val.strip().lower()
    if norm in {"true", "false"}:
        return norm == "true"
    raise ValueError(f"Invalid boolean value for '{key_name}' in git_governance: {raw!r}")


def load_git_governance(stack_path: Optional[pathlib.Path] = None, root_dir: Optional[pathlib.Path] = None) -> Dict[str, Any]:
    """Load §3.4 git_governance from specs/STACK.md with deepcopy isolation (AUD-003)."""
    config = copy.deepcopy(DEFAULT_GOVERNANCE)
    target_stack = stack_path or _resolve_repo_file("STACK_PATH", "specs", "STACK.md", root_dir=root_dir)
    if not target_stack.exists():
        return config
    if is_link_or_junction(target_stack):
        raise RuntimeError(f"STACK.md cannot be a symlink or junction: {target_stack}")
    match = re.search(r"```ya?ml[^\n]*\n\s*(git_governance:\s*[\s\S]*?)```", target_stack.read_text(encoding="utf-8"), re.IGNORECASE)
    if not match:
        return config
    section = ""
    for raw_line in match.group(1).splitlines():
        stripped = re.sub(r"""^((?:[^'"#]|'[^']*'|"[^"]*")*?)#.*$""", r"\1", raw_line).rstrip()
        line = stripped.strip()
        if not line or ":" not in line:
            continue
        indent, (key, val_raw) = len(stripped) - len(stripped.lstrip(" ")), (p.strip() for p in line.split(":", 1))
        if not val_raw and key in {"git_governance", "branches", "worktrees", "auto_merge"}:
            section = "" if key == "git_governance" else key
        elif indent <= 2 and key in {"provider", "auth_mode", "branching_model"}:
            section, config[key] = "", _parse_yaml_val(val_raw, key)
        elif section == "branches" or key in DEFAULT_GOVERNANCE["branches"]:
            config["branches"][key] = _parse_yaml_val(val_raw, key)
        elif section == "worktrees" or key in DEFAULT_GOVERNANCE["worktrees"]:
            config["worktrees"][key] = _parse_yaml_val(val_raw, key, is_bool=(key == "enabled"))
        elif section == "auto_merge":
            config["auto_merge"][key] = _parse_yaml_val(val_raw, key, is_bool=True)
    return config


class GitRunner:
    """Deterministic Git command runner."""

    @staticmethod
    def run(args: List[str], cwd: Optional[pathlib.Path] = None, check: bool = True) -> subprocess.CompletedProcess[str]:
        res = subprocess.run(["git", *args], cwd=str(cwd or resolve_repo_root()), capture_output=True, text=True, encoding="utf-8", errors="replace")
        if check and res.returncode != 0:
            raise RuntimeError(f"Fallo en Git ({' '.join(args)}): {res.stderr.strip() or res.stdout.strip()}")
        return res

    @staticmethod
    def _rev_path(flag: str, work_dir: pathlib.Path) -> Optional[pathlib.Path]:
        if not work_dir.exists():
            return None
        res = GitRunner.run(["rev-parse", flag], cwd=work_dir, check=False)
        raw = pathlib.Path(res.stdout.strip()) if res.returncode == 0 and res.stdout.strip() else None
        return (raw.resolve(strict=False) if raw.is_absolute() else (work_dir / raw).resolve(strict=False)) if raw else None

    @staticmethod
    def get_current_branch(cwd: Optional[pathlib.Path] = None) -> str:
        res = GitRunner.run(["branch", "--show-current"], cwd=cwd, check=False)
        return res.stdout.strip() if res.returncode == 0 else ""

    @staticmethod
    def ref_exists(ref_name: str, cwd: Optional[pathlib.Path] = None) -> bool:
        return bool(ref_name and ref_name.strip()) and GitRunner.run(["rev-parse", "--verify", "--quiet", f"{ref_name}^{{commit}}"], cwd=cwd, check=False).returncode == 0

    @staticmethod
    def branch_exists(branch_name: str, cwd: Optional[pathlib.Path] = None) -> bool:
        return bool(branch_name and branch_name.strip()) and GitRunner.run(["show-ref", "--verify", "--quiet", f"refs/heads/{branch_name}"], cwd=cwd, check=False).returncode == 0

    @staticmethod
    def is_clean(cwd: Optional[pathlib.Path] = None) -> bool:
        return not bool(GitRunner.run(["status", "--porcelain"], cwd=cwd, check=False).stdout.strip())

    @staticmethod
    def get_common_repo_root(cwd: Optional[pathlib.Path] = None) -> pathlib.Path:
        wd = pathlib.Path(cwd) if cwd is not None else resolve_repo_root()
        c = GitRunner._rev_path("--git-common-dir", wd)
        return c.parent if (c and c.name == ".git") else wd.resolve(strict=False)

    @staticmethod
    def is_linked_worktree(cwd: Optional[pathlib.Path] = None) -> bool:
        wd = pathlib.Path(cwd) if cwd is not None else resolve_repo_root()
        g, c = GitRunner._rev_path("--git-dir", wd), GitRunner._rev_path("--git-common-dir", wd)
        return g is not None and c is not None and g != c

    @staticmethod
    def get_worktrees(cwd: Optional[pathlib.Path] = None) -> List[Dict[str, str]]:
        res = GitRunner.run(["worktree", "list", "--porcelain"], cwd=cwd, check=False)
        if res.returncode != 0:
            return []
        wts, cur = [], {}
        for line in (raw.strip() for raw in res.stdout.splitlines()):
            if not line and cur:
                wts, cur = [*wts, cur], {}
            elif line.startswith(("worktree ", "branch ", "HEAD ")):
                k, v = line.split(" ", 1)
                cur[{"worktree": "path", "HEAD": "commit"}.get(k, k)] = v.replace("refs/heads/", "") if k == "branch" else v
            elif line in {"bare", "detached", "locked", "prunable"}:
                cur[line] = "true"
        return [*wts, cur] if cur else wts


def validate_git_ref_name(ref_name: str) -> str:
    clean = ref_name.strip()
    if not clean or clean.startswith(("-", "/", ".")) or clean.endswith(("/", ".", ".lock")) or ".." in clean or "//" in clean or "@{" in clean or _GIT_FORBIDDEN_CHARS_RE.search(clean):
        raise ValueError(f"Invalid Git ref name: {ref_name!r}")
    return clean


def sanitize_worktree_id(raw_id: str) -> str:
    clean = raw_id.strip()
    if not clean or not _SAFE_ID_RE.match(clean) or ".." in clean:
        raise ValueError(f"Unsafe worktree identifier: {raw_id!r}")
    return clean


def resolve_branch_name(spec_id: str, governance: Dict[str, Any], is_hotfix: bool = False, is_release: bool = False) -> str:
    """Resolve canonical branch name from spec ID and governance prefixes."""
    clean_id = spec_id.strip()
    if not clean_id:
        raise ValueError("spec_id cannot be empty.")
    p = governance["branches"]
    if is_hotfix:
        return validate_git_ref_name(f"{p['prefix_hotfix']}{clean_id if clean_id.startswith('BUG-') else f'BUG-{clean_id}'}")
    if is_release:
        return validate_git_ref_name(f"{p['prefix_release']}v{clean_id.lstrip('v')}")
    for sp, gk in (("FEAT-", "prefix_feature"), ("CR-", "prefix_change"), ("BUG-", "prefix_bug")):
        if clean_id.startswith(sp):
            return validate_git_ref_name(f"{p[gk]}{clean_id}")
    return validate_git_ref_name(f"{p['prefix_feature']}{clean_id}")


def get_origin_remote_url(remote: str = "origin", cwd: Optional[pathlib.Path] = None) -> Optional[str]:
    """Detect remote URL dynamically via git (AUD-016)."""
    for args in (["remote", "get-url", remote], ["config", "--get", f"remote.{remote}.url"]):
        res = GitRunner.run(args, cwd=cwd, check=False)
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout.strip()
    return None


def detect_default_base_branch(governance: Dict[str, Any], cwd: Optional[pathlib.Path] = None, prefer_integration: bool = True) -> str:
    """Dynamically resolve an existing base branch via git refs, upstream, and origin/HEAD."""
    work_dir, b = cwd or resolve_repo_root(), governance.get("branches", {})
    dev_b, prod_b = b.get("integration", "develop"), b.get("production", "main")
    up = GitRunner.run(["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"], cwd=work_dir, check=False)
    oh = GitRunner.run(["symbolic-ref", "--short", "refs/remotes/origin/HEAD"], cwd=work_dir, check=False)
    raw = ([dev_b, f"origin/{dev_b}"] if prefer_integration else [prod_b, f"origin/{prod_b}"]) + [
        up.stdout.strip() if up.returncode == 0 else "", oh.stdout.strip() if oh.returncode == 0 else "",
        *([prod_b, f"origin/{prod_b}"] if prefer_integration else []),
        "main", "origin/main", "master", "origin/master", GitRunner.get_current_branch(cwd=work_dir), "HEAD",
    ]
    seen = list(dict.fromkeys(c for item in raw for c in ((item.split("/", 1)[1], item) if item.startswith("origin/") else (item,)) if c))
    for cand in seen:
        if GitRunner.ref_exists(cand, cwd=work_dir):
            return cand
    raise RuntimeError("No se pudo detectar una rama base válida en el repositorio Git.")


def get_base_branch(branch_name: str, governance: Dict[str, Any], explicit_base: Optional[str] = None, cwd: Optional[pathlib.Path] = None) -> str:
    """Determine base branch using explicit override or dynamic git resolution."""
    if explicit_base is not None:
        if not explicit_base.strip():
            raise ValueError("explicit_base cannot be empty.")
        return explicit_base.strip()
    return detect_default_base_branch(governance, cwd=cwd, prefer_integration=not branch_name.startswith(governance.get("branches", {}).get("prefix_hotfix", "hotfix/")))


def _discover_spec_dir(base_root: pathlib.Path, spec_id: str) -> Optional[str]:
    if not spec_id:
        return None
    pat = re.compile(rf"^{re.escape(spec_id)}(?:-|$)", re.IGNORECASE)
    for bucket in _SPEC_BUCKETS:
        bp = base_root / bucket
        if bp.is_dir() and not is_link_or_junction(bp):
            for entry in sorted(bp.iterdir()):
                if entry.is_dir() and not is_link_or_junction(entry) and pat.match(entry.name):
                    return f"{bucket}/{entry.name}"
    return None


def _read_json_dict(path: pathlib.Path) -> Dict[str, Any]:
    if is_link_or_junction(path):
        raise RuntimeError(f"State file cannot be a symlink or junction: {path}")
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object in '{path}'.")
    return data


def list_worktree_states(root_dir: Optional[pathlib.Path] = None) -> List[Dict[str, Any]]:
    """List isolated per-worktree states with backward-compatible worktree-local fallback."""
    eff_root = resolve_repo_root(root_dir)
    common_root = GitRunner.get_common_repo_root(eff_root)
    states: Dict[str, Dict[str, Any]] = {}
    sdir = common_root / ".agents" / "worktree_states"
    if sdir.is_dir() and not is_link_or_junction(sdir):
        for p in sorted(sdir.glob("*.json")):
            if p.name != "ports_registry.json" and not is_link_or_junction(p):
                with contextlib.suppress(OSError, ValueError, json.JSONDecodeError):
                    payload = _read_json_dict(p)
                    states[str(payload.get("worktree_id") or p.stem)] = payload
    for wt in GitRunner.get_worktrees(cwd=eff_root):
        wp = pathlib.Path(wt["path"]).resolve(strict=False) if wt.get("path") else None
        lj = (wp / ".agents" / "active_work_item.json") if wp else None
        if wp and lj and wp != common_root.resolve(strict=False) and wp.name not in states and lj.is_file():
            with contextlib.suppress(OSError, ValueError, json.JSONDecodeError):
                states[wp.name] = {**_read_json_dict(lj), "worktree_id": wp.name}
    return [states[k] for k in sorted(states)]


def load_active_work_item(wt_path: Optional[pathlib.Path] = None, root_dir: Optional[pathlib.Path] = None) -> Optional[Dict[str, Any]]:
    """Load worktree-isolated active work item with fallback to legacy root singleton."""
    eff_root = resolve_repo_root(root_dir)
    common_root = GitRunner.get_common_repo_root(eff_root)
    target = wt_path if wt_path is not None else (eff_root if GitRunner.is_linked_worktree(eff_root) else None)
    if target is not None:
        lj, st = target / ".agents" / "active_work_item.json", common_root / ".agents" / "worktree_states" / f"{sanitize_worktree_id(target.name)}.json"
        chosen = lj if lj.exists() else (st if st.exists() else None)
        return _read_json_dict(chosen) if chosen else None
    rj = _resolve_repo_file("ACTIVE_STATE_JSON", ".agents", "active_work_item.json", root_dir=eff_root if root_dir is not None else None)
    return _read_json_dict(rj) if rj.exists() else None


def remove_worktree_state(wt_id_or_path: str | pathlib.Path, root_dir: Optional[pathlib.Path] = None) -> bool:
    common_root = GitRunner.get_common_repo_root(resolve_repo_root(root_dir))
    raw_name = wt_id_or_path.name if isinstance(wt_id_or_path, pathlib.Path) else pathlib.Path(wt_id_or_path).name
    sdir = common_root / ".agents" / "worktree_states"
    sf = sdir / f"{sanitize_worktree_id(raw_name)}.json"
    if not sf.exists():
        return False
    with acquire_file_lock(sdir / ".state.lock"):
        if sf.exists() and not is_link_or_junction(sf):
            sf.unlink()
            return True
    return False


def _write_md_locked(md_path: pathlib.Path, common_root: pathlib.Path, *, active_item: Optional[str], active_branch: Optional[str], spec_dir: Optional[str], current_gate: Optional[str]) -> pathlib.Path:
    md_path.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    with acquire_file_lock(md_path.parent / ".active_state_md.lock"):
        states = list_worktree_states(common_root)
        wt_sum = "None" if not states else ", ".join(f"`{s.get('worktree_id', 'unknown')}` ({s.get('git', {}).get('branch_name') or '?'} / {s.get('active_work_item_id') or 'IDLE'})" for s in states)
        prev = md_path.read_text(encoding="utf-8") if md_path.exists() and not is_link_or_junction(md_path) else ""
        lines = (prev if prev.strip() else _MD_TEMPLATE).splitlines()
        repls = {p: f"{p} {v}" if p == "- **Timestamp:**" else f"{p} `{v}`" for p, v in (("- **Timestamp:**", ts), ("- **Active Work Item:**", active_item), ("- **Active Branch:**", active_branch), ("- **Spec Folder Path:**", spec_dir), ("- **Current Gate:**", current_gate)) if v is not None}
        repls["- **Active Worktrees:**"] = f"- **Active Worktrees:** {wt_sum}"
        found_wt = False
        for idx, line in enumerate(lines):
            for prefix, new_line in repls.items():
                if line.startswith(prefix):
                    lines[idx], found_wt = new_line, found_wt or (prefix == "- **Active Worktrees:**")
                    break
        if not found_wt:
            lines.insert(next((i + 1 for i, l in enumerate(lines) if l.startswith("- **Current Gate:**")), len(lines)), repls["- **Active Worktrees:**"])
        atomic_write_text(md_path, "\n".join(lines).rstrip() + "\n")
    return md_path


def sync_active_state_md(spec_id: str, branch_name: str, status: str, *, wt_path: Optional[pathlib.Path] = None, root_dir: Optional[pathlib.Path] = None, spec_dir: Optional[str] = None) -> Optional[pathlib.Path]:
    """Synchronize .agents/ACTIVE_STATE.md on branch/worktree transitions (AUD-019)."""
    eff_root = resolve_repo_root(root_dir)
    common_root = GitRunner.get_common_repo_root(eff_root)
    if wt_path is not None and wt_path.resolve(strict=False) != common_root.resolve(strict=False):
        wt_md = wt_path / ".agents" / "ACTIVE_STATE.md"
        if wt_path.is_dir():
            _write_md_locked(wt_md, common_root, active_item=spec_id or "IDLE (No Active Work Item)", active_branch=branch_name or GitRunner.get_current_branch(wt_path) or "N/A", spec_dir=spec_dir or _discover_spec_dir(wt_path, spec_id) or "N/A", current_gate=status or "IN_PROGRESS")
        if (common_root / ".agents").is_dir():
            root_md = _resolve_repo_file("ACTIVE_STATE_MD", ".agents", "ACTIVE_STATE.md", root_dir=None if (root_dir is None and eff_root == common_root) else common_root)
            _write_md_locked(root_md, common_root, active_item=None, active_branch=GitRunner.get_current_branch(common_root) or None, spec_dir=None, current_gate=None)
        return wt_md
    target_md = _resolve_repo_file("ACTIVE_STATE_MD", ".agents", "ACTIVE_STATE.md", root_dir=root_dir)
    if not (eff_root / ".agents").is_dir() and not target_md.parent.is_dir():
        return None
    is_idle = status == "IDLE" and not spec_id
    return _write_md_locked(target_md, common_root, active_item="IDLE (No Active Work Item)" if is_idle else (spec_id or None), active_branch=branch_name or GitRunner.get_current_branch(eff_root) or "N/A", spec_dir="N/A" if is_idle else (spec_dir or _discover_spec_dir(eff_root, spec_id)), current_gate=status or "IDLE")


def _build_git_payload(existing: Dict[str, Any], *, spec_id: str, branch_name: str, status: str, wt_rel_path: Optional[str], wt_id: Optional[str], base_branch: Optional[str], remote_url: Optional[str], ports: Optional[Tuple[int, int]], spec_dir: Optional[str]) -> Dict[str, Any]:
    data, prev_id = copy.deepcopy(existing), existing.get("active_work_item_id")
    git_info = {**(data.get("git") if isinstance(data.get("git"), dict) else {}), "branch_name": branch_name, "worktree_path": wt_rel_path, "status": status, "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")}
    if wt_id:
        git_info["worktree_id"] = data["worktree_id"] = wt_id
    for k, v in (("base_branch", base_branch), ("remote_url", remote_url)):
        if v:
            git_info[k] = v
    if ports is not None:
        git_info["backend_port"], git_info["frontend_port"] = ports
    data["git"] = git_info
    if spec_id:
        data["active_work_item_id"] = spec_id
        if prev_id != spec_id or not data.get("spec_dir"):
            data["spec_dir"] = spec_dir
        if not data.get("spec_dir"):
            data.pop("spec_dir", None)
    elif status == "IDLE":
        data["active_work_item_id"] = None
        data.pop("spec_dir", None)
    return data


def sync_active_state_git(spec_id: str, branch_name: str, wt_path: Optional[pathlib.Path] = None, status: str = "IN_PROGRESS", *, base_branch: Optional[str] = None, remote_url: Optional[str] = None, ports: Optional[Tuple[int, int]] = None, root_dir: Optional[pathlib.Path] = None) -> None:
    """Update isolated per-worktree state without clobbering root/sibling states (AUD-016)."""
    eff_root = resolve_repo_root(root_dir)
    common_root = GitRunner.get_common_repo_root(eff_root)

    if wt_path is not None and wt_path.resolve(strict=False) != common_root.resolve(strict=False):
        wt_id = sanitize_worktree_id(wt_path.name)
        if status == "WORKTREE_REMOVED":
            remove_worktree_state(wt_id, root_dir=common_root)
            sync_active_state_md("", GitRunner.get_current_branch(common_root), "WORKTREE_REMOVED", root_dir=common_root)
            return
        rel_wt = wt_path.relative_to(common_root).as_posix() if wt_path.is_relative_to(common_root) else str(wt_path)
        disc_spec = _discover_spec_dir(wt_path, spec_id) or _discover_spec_dir(common_root, spec_id)
        sdir = common_root / ".agents" / "worktree_states"
        default_local = {"gate_0_approved": False, "gate_1_approved": False, "gate_2_approved": False, "gate_3_approved": False, "approved_by_human": False}
        with acquire_file_lock(sdir / ".state.lock"):
            for tgt, fb in [(sdir / f"{wt_id}.json", {}), *([(wt_path / ".agents" / "active_work_item.json", default_local)] if wt_path.is_dir() else [])]:
                atomic_write_text(tgt, json.dumps(_build_git_payload(_read_json_dict(tgt) if tgt.exists() else fb, spec_id=spec_id, branch_name=branch_name, status=status, wt_rel_path=rel_wt, wt_id=wt_id, base_branch=base_branch, remote_url=remote_url, ports=ports, spec_dir=disc_spec), indent=2) + "\n")
        sync_active_state_md(spec_id, branch_name, status, wt_path=wt_path, root_dir=common_root, spec_dir=disc_spec)
        return

    if status == "WORKTREE_REMOVED":
        for st in list_worktree_states(common_root):
            st_id = st.get("worktree_id")
            if st_id and ((spec_id and st.get("active_work_item_id") == spec_id) or (branch_name and st.get("git", {}).get("branch_name") == branch_name)):
                remove_worktree_state(st_id, root_dir=common_root)
        sync_active_state_md("", GitRunner.get_current_branch(common_root), "WORKTREE_REMOVED", root_dir=common_root)
        return

    if GitRunner.is_linked_worktree(eff_root):
        sync_active_state_git(spec_id, branch_name, wt_path=eff_root, status=status, base_branch=base_branch, remote_url=remote_url, ports=ports, root_dir=common_root)
        return

    root_json = _resolve_repo_file("ACTIVE_STATE_JSON", ".agents", "active_work_item.json", root_dir=root_dir)
    disc_spec = _discover_spec_dir(eff_root, spec_id)
    if root_json.exists():
        with acquire_file_lock(root_json.parent / ".state.lock"):
            atomic_write_text(root_json, json.dumps(_build_git_payload(_read_json_dict(root_json), spec_id=spec_id, branch_name=branch_name, status=status, wt_rel_path=None, wt_id=None, base_branch=base_branch, remote_url=remote_url, ports=ports, spec_dir=disc_spec), indent=2) + "\n")
    sync_active_state_md(spec_id, branch_name, status, root_dir=root_dir, spec_dir=disc_spec)
