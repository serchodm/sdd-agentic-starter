#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SDD Dynamic Base/Remote Detection, Collision-Free Port Allocator & WorktreeManager."""

from __future__ import annotations

import copy
import errno
import hashlib
import json
import pathlib
import re
import shutil
import socket
import sys
from typing import Any, Dict, List, Optional, Set, Tuple

_REPO_PARENT = pathlib.Path(__file__).resolve().parent.parent
if str(_REPO_PARENT) not in sys.path:
    sys.path.insert(0, str(_REPO_PARENT))

from scripts.sdd_git_state import (  # noqa: E402
    GitRunner,
    acquire_file_lock,
    atomic_write_text,
    detect_default_base_branch,
    get_base_branch,
    get_origin_remote_url,
    is_link_or_junction,
    remove_worktree_state,
    resolve_branch_name,
    resolve_repo_root,
    sanitize_worktree_id,
    sync_active_state_md,
    validate_git_ref_name,
)

BACKEND_PORT_RANGE: Tuple[int, int] = (8000, 8899)
FRONTEND_PORT_RANGE: Tuple[int, int] = (3000, 3899)
_ENV_PORT_KEYS = ("PORT", "TEST_PORT", "BACKEND_PORT", "FRONTEND_PORT")
_BUSY_ERRNOS = frozenset({
    errno.EADDRINUSE,
    getattr(errno, "WSAEADDRINUSE", 10048),
    errno.EACCES,
    getattr(errno, "WSAEACCES", 10013),
})


def _try_bind_tcp(family: int, host: str, port: int, *, ignore_unsupported: bool = False) -> bool:
    with socket.socket(family, socket.SOCK_STREAM) as sock:
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        else:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 0)
        try:
            sock.bind((host, port))
            return True
        except OSError as exc:
            if ignore_unsupported and exc.errno not in _BUSY_ERRNOS and getattr(exc, "winerror", None) not in {10048, 10013}:
                return True
            return False


def is_port_available(port: int) -> bool:
    """Verify loopback and wildcard TCP bind availability for `port` (AUD-016)."""
    if not (1 <= port <= 65535):
        return False
    if not (_try_bind_tcp(socket.AF_INET, "127.0.0.1", port) and _try_bind_tcp(socket.AF_INET, "0.0.0.0", port)):
        return False
    if socket.has_ipv6 and not _try_bind_tcp(socket.AF_INET6, "::1", port, ignore_unsupported=True):
        return False
    return True


def _states_dir(common_root: pathlib.Path) -> pathlib.Path:
    return common_root / ".agents" / "worktree_states"


def _ports_registry_path(common_root: pathlib.Path) -> pathlib.Path:
    return _states_dir(common_root) / "ports_registry.json"


def _ports_lock_path(common_root: pathlib.Path) -> pathlib.Path:
    return _states_dir(common_root) / ".ports.lock"


def _read_registry(registry_path: pathlib.Path) -> Dict[str, Dict[str, int]]:
    if is_link_or_junction(registry_path):
        raise RuntimeError(f"Port registry cannot be a symlink or junction: {registry_path}")
    if not registry_path.exists():
        return {}
    raw = json.loads(registry_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Invalid port registry format in '{registry_path}'.")
    return {
        slug: {"backend_port": entry["backend_port"], "frontend_port": entry["frontend_port"]}
        for slug, entry in raw.items()
        if isinstance(slug, str) and isinstance(entry, dict)
        and isinstance(entry.get("backend_port"), int) and isinstance(entry.get("frontend_port"), int)
    }


def _scan_used_ports(worktrees_root: pathlib.Path, common_root: pathlib.Path, exclude_slug: str) -> Set[int]:
    used: Set[int] = set()
    port_re = re.compile(r"^\s*(?:" + "|".join(_ENV_PORT_KEYS) + r")=(\d+)\s*$")
    if worktrees_root.is_dir() and not is_link_or_junction(worktrees_root):
        for entry in worktrees_root.iterdir():
            env_file = entry / ".env.test"
            if entry.is_dir() and entry.name != exclude_slug and not is_link_or_junction(entry) and env_file.is_file() and not is_link_or_junction(env_file):
                for line in env_file.read_text(encoding="utf-8", errors="ignore").splitlines():
                    if m := port_re.match(line):
                        used.add(int(m.group(1)))

    sdir = _states_dir(common_root)
    if sdir.is_dir() and not is_link_or_junction(sdir):
        for st_file in sdir.glob("*.json"):
            if st_file.name == "ports_registry.json" or st_file.stem == exclude_slug or is_link_or_junction(st_file):
                continue
            try:
                data = json.loads(st_file.read_text(encoding="utf-8"))
                git_info = data.get("git", {}) if isinstance(data, dict) else {}
                for k in ("backend_port", "frontend_port", "port"):
                    if isinstance(git_info.get(k), int):
                        used.add(git_info[k])
            except (OSError, ValueError, json.JSONDecodeError):
                continue
    return used


def _probe_port(port_range: Tuple[int, int], seed: int, reserved: Set[int]) -> int:
    start, end = port_range
    span = end - start + 1
    offset = seed % span
    for i in range(span):
        candidate = start + ((offset + i) % span)
        if candidate not in reserved and is_port_available(candidate):
            return candidate
    raise RuntimeError(f"No available TCP ports found in range {start}-{end}.")


def allocate_worktree_ports(
    slug: str, *, worktrees_root: Optional[pathlib.Path] = None, root_dir: Optional[pathlib.Path] = None
) -> Tuple[int, int]:
    """Allocate non-colliding (backend_port, frontend_port) under file lock + loopback socket probe."""
    safe_slug = sanitize_worktree_id(slug)
    eff_root = resolve_repo_root(root_dir)
    common_root = GitRunner.get_common_repo_root(eff_root)
    eff_wt_root = worktrees_root or (eff_root / ".worktrees")
    registry_path = _ports_registry_path(common_root)

    with acquire_file_lock(_ports_lock_path(common_root)):
        registry = _read_registry(registry_path)
        other_reserved = _scan_used_ports(eff_wt_root, common_root, exclude_slug=safe_slug)
        for reg_slug, rec in registry.items():
            if reg_slug != safe_slug:
                other_reserved.update((rec["backend_port"], rec["frontend_port"]))

        existing = registry.get(safe_slug)
        if existing:
            bp, fp = existing["backend_port"], existing["frontend_port"]
            if bp != fp and bp not in other_reserved and fp not in other_reserved:
                if (eff_wt_root / safe_slug).is_dir() or (is_port_available(bp) and is_port_available(fp)):
                    return bp, fp

        digest = hashlib.sha256(safe_slug.encode("utf-8")).digest()
        backend_port = _probe_port(BACKEND_PORT_RANGE, int.from_bytes(digest[:4], "big"), other_reserved)
        other_reserved.add(backend_port)
        frontend_port = _probe_port(FRONTEND_PORT_RANGE, int.from_bytes(digest[4:8], "big"), other_reserved)

        registry[safe_slug] = {"backend_port": backend_port, "frontend_port": frontend_port}
        atomic_write_text(registry_path, json.dumps(registry, indent=2, sort_keys=True) + "\n")
        return backend_port, frontend_port


def release_worktree_ports(slug: str, *, root_dir: Optional[pathlib.Path] = None) -> None:
    """Release port reservation for a removed worktree if present."""
    safe_slug = sanitize_worktree_id(slug)
    eff_root = resolve_repo_root(root_dir)
    common_root = GitRunner.get_common_repo_root(eff_root)
    registry_path = _ports_registry_path(common_root)
    if not registry_path.exists():
        return
    with acquire_file_lock(_ports_lock_path(common_root)):
        registry = _read_registry(registry_path)
        if safe_slug in registry:
            del registry[safe_slug]
            atomic_write_text(registry_path, json.dumps(registry, indent=2, sort_keys=True) + "\n")


class WorktreeManager:
    """Manages isolated Git worktrees with containment enforcement and collision-free ports."""

    def __init__(self, governance: Dict[str, Any], root_dir: Optional[pathlib.Path] = None):
        self.governance = copy.deepcopy(governance)
        self.root_dir = resolve_repo_root(root_dir)
        self.common_root = GitRunner.get_common_repo_root(self.root_dir)
        rel_dir = str(self.governance.get("worktrees", {}).get("directory", ".worktrees")).strip() or ".worktrees"
        rel_path = pathlib.Path(rel_dir)
        if rel_path.is_absolute() or ".." in rel_path.parts:
            raise ValueError(f"Unsafe worktrees directory configuration: {rel_dir!r}")
        self.worktrees_root = self.root_dir / rel_path
        self._last_ports: Dict[str, Tuple[int, int]] = {}

    def _resolved_worktrees_root(self) -> pathlib.Path:
        if self.worktrees_root.exists() and is_link_or_junction(self.worktrees_root):
            raise RuntimeError(f"Worktrees root cannot be a symlink or junction: {self.worktrees_root}")
        resolved_root = self.worktrees_root.resolve(strict=False)
        if not resolved_root.is_relative_to(self.root_dir.resolve(strict=False)):
            raise RuntimeError(f"Worktrees root escapes repository root: {resolved_root}")
        return resolved_root

    def _is_contained(self, path_obj: pathlib.Path, worktrees_root: Optional[pathlib.Path] = None) -> Optional[pathlib.Path]:
        """Enforce AUD-021 containment: reject symlinks, junctions, worktrees_root itself, or outside paths."""
        wt_root = worktrees_root or self._resolved_worktrees_root()
        if is_link_or_junction(self.worktrees_root) or is_link_or_junction(path_obj):
            return None
        try:
            curr = self.worktrees_root
            for part in path_obj.relative_to(self.worktrees_root).parts:
                if part in ("", "."):
                    continue
                if part == "..":
                    return None
                curr = curr / part
                if is_link_or_junction(curr):
                    return None
        except ValueError:
            pass
        resolved = path_obj.resolve(strict=False)
        return None if (resolved == wt_root or not resolved.is_relative_to(wt_root)) else resolved

    def _locate_target(self, identifier: str, wt_root: pathlib.Path) -> Tuple[Optional[pathlib.Path], Optional[str]]:
        """Locate worktree candidate path and return (found_path, containment_rejected_label)."""
        candidate_branch, candidate_slug = "", ""
        try:
            candidate_branch = resolve_branch_name(identifier, self.governance)
            candidate_slug = candidate_branch.replace("/", "-")
        except ValueError:
            pass

        for wt in GitRunner.get_worktrees(cwd=self.root_dir):
            raw_path = wt.get("path", "")
            if not raw_path:
                continue
            p, b = pathlib.Path(raw_path), wt.get("branch", "")
            if identifier in (p.name, str(p), b) or (candidate_branch and candidate_branch == b) or (candidate_slug and candidate_slug == p.name):
                return p, None

        for label in (identifier, candidate_slug):
            if not label:
                continue
            cand = self.worktrees_root / label
            if self._is_contained(cand, wt_root) is None:
                return None, label
            if cand.exists():
                return cand, None
        return None, None

    def create(self, branch_name: str, base_branch: str, custom_slug: Optional[str] = None) -> pathlib.Path:
        """Create branch (if needed), mount physical worktree, and isolate ports atomically."""
        validate_git_ref_name(branch_name)
        slug = sanitize_worktree_id(custom_slug or branch_name.replace("/", "-"))

        with acquire_file_lock(_ports_lock_path(self.common_root)):
            self.worktrees_root.mkdir(parents=True, exist_ok=True)
            wt_root = self._resolved_worktrees_root()
            target_path = self.worktrees_root / slug
            if self._is_contained(target_path, wt_root) is None:
                raise ValueError(f"Worktree target escapes containment '{wt_root}': {target_path}")

            if target_path.exists():
                print(f"[INFO] El worktree ya existe en: {target_path}")
                if not (target_path / ".env.test").exists():
                    self._last_ports[slug] = self._isolate_environment(target_path, slug)
                elif ports := self.get_ports_for_worktree(target_path):
                    self._last_ports[slug] = ports
                return target_path

            if not GitRunner.branch_exists(branch_name, cwd=self.root_dir):
                print(f"  -> Creando rama '{branch_name}' desde '{base_branch}'...")
                GitRunner.run(["branch", branch_name, base_branch], cwd=self.root_dir)

            print(f"  -> Montando Git Worktree en '{target_path}'...")
            GitRunner.run(["worktree", "add", str(target_path), branch_name], cwd=self.root_dir)
            self._last_ports[slug] = self._isolate_environment(target_path, slug)
            return target_path

    def resolve_target(self, identifier: str) -> Optional[pathlib.Path]:
        if not identifier or not identifier.strip():
            return None
        wt_root = self._resolved_worktrees_root()
        found, rejected = self._locate_target(identifier, wt_root)
        if rejected or not found:
            return None
        return self._is_contained(found, wt_root)

    def remove(self, identifier: str, force: bool = False) -> bool:
        """Remove a worktree strictly contained inside worktrees_root (AUD-021)."""
        if not identifier or not identifier.strip():
            print("[ERROR] Identificador de worktree vacío.")
            return False

        worktrees_root = self._resolved_worktrees_root()
        found_path, rejected_label = self._locate_target(identifier, worktrees_root)
        if rejected_label is not None:
            print(f"[ERROR] Ruta de worktree rechazada por estar fuera de '{worktrees_root}': {rejected_label}")
            return False
        if not found_path:
            print(f"[WARN] No se encontró el worktree para: {identifier}")
            return False

        resolved_target = self._is_contained(found_path, worktrees_root)
        if resolved_target is None:
            print(f"[ERROR] Ruta de worktree rechazada por estar fuera de '{worktrees_root}': {found_path}")
            return False
        if not resolved_target.exists():
            print(f"[WARN] No se encontró el worktree para: {identifier}")
            return False

        print(f"  -> Desmontando worktree en '{resolved_target}'...")
        args = ["worktree", "remove", str(resolved_target)] + (["--force"] if force else [])
        GitRunner.run(args, cwd=self.root_dir, check=False)

        if resolved_target.exists():
            reverified = self._is_contained(found_path, worktrees_root)
            if reverified is None or reverified != resolved_target or not reverified.is_dir():
                print(f"[ERROR] Contención invalidada antes de limpiar '{resolved_target}'.")
                return False
            try:
                shutil.rmtree(reverified)
            except OSError as exc:
                print(f"[ERROR] No se pudo eliminar el directorio de worktree '{reverified}': {exc}")
                return False

        GitRunner.run(["worktree", "prune"], cwd=self.root_dir, check=False)
        release_worktree_ports(resolved_target.name, root_dir=self.root_dir)
        remove_worktree_state(resolved_target.name, root_dir=self.root_dir)
        sync_active_state_md("", GitRunner.get_current_branch(self.common_root), "WORKTREE_REMOVED", root_dir=self.common_root)
        print(f"[OK] Worktree '{resolved_target.name}' eliminado con éxito.")
        return True

    def prune(self) -> None:
        """Prune orphaned git worktree metadata, port reservations, and stale worktree states."""
        print("  -> Ejecutando git worktree prune...")
        GitRunner.run(["worktree", "prune"], cwd=self.root_dir, check=False)
        active_names = {pathlib.Path(wt["path"]).name for wt in GitRunner.get_worktrees(cwd=self.root_dir) if wt.get("path")}
        registry_path = _ports_registry_path(self.common_root)
        if registry_path.exists():
            with acquire_file_lock(_ports_lock_path(self.common_root)):
                registry = _read_registry(registry_path)
                stale = [s for s in registry if s not in active_names and not (self.worktrees_root / s).exists()]
                if stale:
                    for s in stale:
                        del registry[s]
                    atomic_write_text(registry_path, json.dumps(registry, indent=2, sort_keys=True) + "\n")
        sdir = _states_dir(self.common_root)
        if sdir.is_dir():
            for st_file in sdir.glob("*.json"):
                if st_file.name != "ports_registry.json" and not is_link_or_junction(st_file):
                    if st_file.stem not in active_names and not (self.worktrees_root / st_file.stem).exists():
                        remove_worktree_state(st_file.stem, root_dir=self.root_dir)
        print("[OK] Referencias de worktrees saneadas.")

    def get_ports_for_worktree(self, wt_path: pathlib.Path) -> Optional[Tuple[int, int]]:
        if wt_path.name in self._last_ports:
            return self._last_ports[wt_path.name]
        env_test = wt_path / ".env.test"
        if env_test.is_file() and not is_link_or_junction(env_test):
            vals = {}
            for line in env_test.read_text(encoding="utf-8", errors="ignore").splitlines():
                if m := re.match(r"^\s*(BACKEND_PORT|FRONTEND_PORT|PORT)=(\d+)\s*$", line):
                    vals[m.group(1)] = int(m.group(2))
            bp, fp = vals.get("BACKEND_PORT") or vals.get("PORT"), vals.get("FRONTEND_PORT")
            if bp is not None and fp is not None:
                return bp, fp
        return None

    def _isolate_environment(self, wt_path: pathlib.Path, slug: str) -> Tuple[int, int]:
        """Configure isolated .env.test with collision-free backend & frontend ports."""
        env_example = self.root_dir / ".env.example"
        backend_port, frontend_port = allocate_worktree_ports(slug, worktrees_root=self.worktrees_root, root_dir=self.root_dir)
        lines = [
            f"# Entorno Aislado para Worktree: {slug}",
            f"PORT={backend_port}",
            f"TEST_PORT={backend_port}",
            f"BACKEND_PORT={backend_port}",
            f"FRONTEND_PORT={frontend_port}",
            f"DATABASE_URL=sqlite:///./test_{slug}.sqlite",
            f"WORKTREE_NAME={slug}",
        ]
        if env_example.exists() and not is_link_or_junction(env_example):
            lines.extend(["\n# Variables heredadas de .env.example:", env_example.read_text(encoding="utf-8", errors="ignore")])
        atomic_write_text(wt_path / ".env.test", "\n".join(lines) + "\n")
        return backend_port, frontend_port
