#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SDD Deterministic Git & Worktree Orchestrator (sdd_git.py)
=========================================================
Provee gestion de ramas estructuradas (GitFlow SDD), aislamiento físico
mediante Git Worktrees (.worktrees/) y soporte para proveedores Git
(GitHub, GitLab, Local) de forma 100% agnóstica y determinista.

Uso:
    python scripts/sdd_git.py status
    python scripts/sdd_git.py create-branch --spec FEAT-001 [--base develop]
    python scripts/sdd_git.py worktree-create --spec FEAT-001
    python scripts/sdd_git.py worktree-remove --spec FEAT-001 [--force]
    python scripts/sdd_git.py worktree-prune
    python scripts/sdd_git.py pr-create --spec FEAT-001 --title "..."
"""

import argparse
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
from typing import Any, Dict, List, Optional, Tuple

# Compatibilidad UTF-8 en Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
STACK_PATH = ROOT_DIR / "specs" / "STACK.md"
ACTIVE_STATE_JSON = ROOT_DIR / ".agents" / "active_work_item.json"
DEFAULT_WORKTREES_DIR = ROOT_DIR / ".worktrees"


# ==============================================================================
# 1. Configuración de Gobernanza Git (§3.4 specs/STACK.md)
# ==============================================================================

DEFAULT_GOVERNANCE = {
    "provider": "github",
    "auth_mode": "cli",
    "branching_model": "sdd-gitflow",
    "branches": {
        "production": "main",
        "integration": "develop",
        "prefix_feature": "feat/",
        "prefix_change": "change/",
        "prefix_bug": "fix/",
        "prefix_release": "release/",
        "prefix_hotfix": "hotfix/",
    },
    "worktrees": {
        "enabled": True,
        "directory": ".worktrees",
    },
    "auto_merge": {
        "develop": True,
        "main": False,
    },
}


def load_git_governance() -> Dict[str, Any]:
    """Carga la sección §3.4 de specs/STACK.md o devuelve la configuración por defecto."""
    if not STACK_PATH.exists():
        return DEFAULT_GOVERNANCE

    try:
        content = STACK_PATH.read_text(encoding="utf-8", errors="ignore")
        match = re.search(r"```ya?ml\s+(git_governance:\s*[\s\S]*?)```", content, re.IGNORECASE)
        if not match:
            return DEFAULT_GOVERNANCE

        raw_yaml = match.group(1)
        config = dict(DEFAULT_GOVERNANCE)

        # Parseo simple key-value sin depender de PyYAML externo
        for line in raw_yaml.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # Quitar comentarios inline
            if "#" in line:
                line = line.split("#", 1)[0].strip()

            if line.startswith("provider:"):
                config["provider"] = line.split(":", 1)[1].strip().strip("\"'")
            elif line.startswith("auth_mode:"):
                config["auth_mode"] = line.split(":", 1)[1].strip().strip("\"'")
            elif line.startswith("production:"):
                config["branches"]["production"] = line.split(":", 1)[1].strip().strip("\"'")
            elif line.startswith("integration:"):
                config["branches"]["integration"] = line.split(":", 1)[1].strip().strip("\"'")
            elif line.startswith("directory:"):
                config["worktrees"]["directory"] = line.split(":", 1)[1].strip().strip("\"'")

        return config
    except Exception:
        return DEFAULT_GOVERNANCE


# ==============================================================================
# 2. Motor Git Base (Comandos Deterministas)
# ==============================================================================

class GitRunner:
    """Ejecutor determinista de comandos Git."""

    @staticmethod
    def run(args: List[str], cwd: Optional[pathlib.Path] = None, check: bool = True) -> subprocess.CompletedProcess:
        cwd = cwd or ROOT_DIR
        cmd = ["git"] + args
        res = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)
        if check and res.returncode != 0:
            err_msg = res.stderr.strip() or res.stdout.strip()
            raise RuntimeError(f"Fallo en Git ({' '.join(args)}): {err_msg}")
        return res

    @classmethod
    def get_current_branch(cls, cwd: Optional[pathlib.Path] = None) -> str:
        res = cls.run(["branch", "--show-current"], cwd=cwd, check=False)
        return res.stdout.strip() if res.returncode == 0 else ""

    @classmethod
    def branch_exists(cls, branch_name: str) -> bool:
        res = cls.run(["branch", "--list", branch_name], check=False)
        return bool(res.stdout.strip())

    @classmethod
    def is_clean(cls, cwd: Optional[pathlib.Path] = None) -> bool:
        res = cls.run(["status", "--porcelain"], cwd=cwd, check=False)
        return not bool(res.stdout.strip())

    @classmethod
    def get_worktrees(cls) -> List[Dict[str, str]]:
        """Devuelve la lista de worktrees activos parseando 'git worktree list --porcelain'."""
        res = cls.run(["worktree", "list", "--porcelain"], check=False)
        if res.returncode != 0:
            return []

        worktrees = []
        current: Dict[str, str] = {}
        for line in res.stdout.splitlines():
            line = line.strip()
            if not line:
                if current:
                    worktrees.append(current)
                    current = {}
                continue
            if line.startswith("worktree "):
                current["path"] = line.split(" ", 1)[1]
            elif line.startswith("branch "):
                current["branch"] = line.split(" ", 1)[1].replace("refs/heads/", "")
            elif line.startswith("HEAD "):
                current["commit"] = line.split(" ", 1)[1]
            elif line == "bare":
                current["bare"] = "true"
        if current:
            worktrees.append(current)
        return worktrees


# ==============================================================================
# 3. Mapeo de Specs a Ramas y Rutas
# ==============================================================================

def resolve_branch_name(spec_id: str, governance: Dict[str, Any], is_hotfix: bool = False, is_release: bool = False) -> str:
    """Resuelve el nombre canónico de rama según el ID de especificación."""
    prefixes = governance["branches"]
    clean_id = spec_id.strip()

    if is_hotfix:
        clean = clean_id if clean_id.startswith("BUG-") else f"BUG-{clean_id}"
        return f"{prefixes['prefix_hotfix']}{clean}"

    if is_release:
        version = clean_id.lstrip("v")
        return f"{prefixes['prefix_release']}v{version}"

    if clean_id.startswith("FEAT-"):
        return f"{prefixes['prefix_feature']}{clean_id}"
    if clean_id.startswith("CR-"):
        return f"{prefixes['prefix_change']}{clean_id}"
    if clean_id.startswith("BUG-"):
        return f"{prefixes['prefix_bug']}{clean_id}"

    # Default a feature
    return f"{prefixes['prefix_feature']}{clean_id}"


def get_base_branch(branch_name: str, governance: Dict[str, Any], explicit_base: Optional[str] = None) -> str:
    """Determina la rama base canónica desde la cual bifurcar."""
    if explicit_base:
        return explicit_base

    prefixes = governance["branches"]
    prod_branch = prefixes.get("production", "main")
    dev_branch = prefixes.get("integration", "develop")

    if branch_name.startswith(prefixes.get("prefix_hotfix", "hotfix/")):
        return prod_branch
    return dev_branch


# ==============================================================================
# 4. Gestor de Worktrees Aislados
# ==============================================================================

class WorktreeManager:
    """Gestiona el ciclo de vida de los directorios de trabajo aislados."""

    def __init__(self, governance: Dict[str, Any]):
        self.governance = governance
        rel_dir = governance.get("worktrees", {}).get("directory", ".worktrees")
        self.worktrees_root = ROOT_DIR / rel_dir

    def create(self, branch_name: str, base_branch: str, custom_slug: Optional[str] = None) -> pathlib.Path:
        """Crea una rama (si no existe) y monta un worktree físico."""
        self.worktrees_root.mkdir(parents=True, exist_ok=True)

        slug = custom_slug or branch_name.replace("/", "-")
        target_path = self.worktrees_root / slug

        if target_path.exists():
            print(f"[INFO] El worktree ya existe en: {target_path}")
            return target_path

        # 1. Asegurar existencia de la rama
        if not GitRunner.branch_exists(branch_name):
            print(f"  -> Creando rama '{branch_name}' desde '{base_branch}'...")
            GitRunner.run(["branch", branch_name, base_branch])

        # 2. Montar worktree
        print(f"  -> Montando Git Worktree en '{target_path}'...")
        GitRunner.run(["worktree", "add", str(target_path), branch_name])

        # 3. Aislar entorno (.env.test con offset de puerto)
        self._isolate_environment(target_path, slug)

        return target_path

    def remove(self, identifier: str, force: bool = False) -> bool:
        """Elimina un worktree por ruta o por nombre de rama o spec."""
        worktrees = GitRunner.get_worktrees()
        found_path: Optional[pathlib.Path] = None

        candidate_branch = resolve_branch_name(identifier, self.governance)
        candidate_slug = candidate_branch.replace("/", "-")

        for wt in worktrees:
            p = pathlib.Path(wt.get("path", ""))
            b = wt.get("branch", "")
            if identifier in (p.name, str(p), b) or candidate_branch == b or candidate_slug == p.name:
                found_path = p
                break

        if not found_path:
            # Fallback a buscar en carpeta
            target = self.worktrees_root / identifier
            if target.exists():
                found_path = target
            elif (self.worktrees_root / candidate_slug).exists():
                found_path = self.worktrees_root / candidate_slug

        if not found_path or not found_path.exists():
            print(f"[WARN] No se encontró el worktree para: {identifier}")
            return False

        print(f"  -> Desmontando worktree en '{found_path}'...")
        args = ["worktree", "remove", str(found_path)]
        if force:
            args.append("--force")
        GitRunner.run(args, check=False)

        # Si aún queda residuo en disco, limpiar
        if found_path.exists():
            try:
                shutil.rmtree(found_path, ignore_errors=True)
            except Exception:
                pass

        GitRunner.run(["worktree", "prune"], check=False)
        print(f"[OK] Worktree '{found_path.name}' eliminado con éxito.")
        return True

    def prune(self) -> None:
        """Limpia referencias a worktrees eliminados manualmente."""
        print("  -> Ejecutando git worktree prune...")
        GitRunner.run(["worktree", "prune"], check=False)
        print("[OK] Referencias de worktrees saneadas.")

    def _isolate_environment(self, wt_path: pathlib.Path, slug: str) -> None:
        """Configura variables de entorno aisladas para evitar colisión de puertos."""
        env_example = ROOT_DIR / ".env.example"
        env_test = wt_path / ".env.test"

        # Generar un puerto pseudo-aleatorio o hash para la tarea
        port_offset = sum(ord(c) for c in slug) % 100
        assigned_port = 8000 + port_offset

        lines = [
            f"# Entorno Aislado para Worktree: {slug}",
            f"PORT={assigned_port}",
            f"TEST_PORT={assigned_port}",
            f"DATABASE_URL=sqlite:///./test_{slug}.sqlite",
            f"WORKTREE_NAME={slug}",
        ]

        if env_example.exists():
            content = env_example.read_text(encoding="utf-8", errors="ignore")
            lines.append("\n# Variables heredadas de .env.example:")
            lines.append(content)

        env_test.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ==============================================================================
# 5. Sincronización con Estado Activo (.agents/active_work_item.json)
# ==============================================================================

def sync_active_state_git(spec_id: str, branch_name: str, wt_path: Optional[pathlib.Path] = None, status: str = "IN_PROGRESS") -> None:
    """Actualiza la sección git dentro de .agents/active_work_item.json."""
    if not ACTIVE_STATE_JSON.exists():
        return

    try:
        data = json.loads(ACTIVE_STATE_JSON.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        data = {}

    git_info = data.get("git", {})
    git_info.update({
        "branch_name": branch_name,
        "worktree_path": str(wt_path.relative_to(ROOT_DIR)) if wt_path and wt_path.is_relative_to(ROOT_DIR) else str(wt_path) if wt_path else None,
        "status": status,
    })
    data["git"] = git_info
    if spec_id:
        data["active_work_item_id"] = spec_id

    ACTIVE_STATE_JSON.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


# ==============================================================================
# 6. Proveedores Remotos Agnósticos (GitHub / GitLab / Local)
# ==============================================================================

class GitProviderAdapter:
    """Adaptador agnóstico de proveedores Git remotos."""

    @staticmethod
    def create_pr(provider: str, branch: str, base: str, title: str, body: str = "") -> Optional[str]:
        if provider == "github":
            if shutil.which("gh"):
                cmd = ["gh", "pr", "create", "--base", base, "--head", branch, "--title", title, "--body", body or title]
                res = subprocess.run(cmd, cwd=str(ROOT_DIR), capture_output=True, text=True)
                if res.returncode == 0:
                    pr_url = res.stdout.strip()
                    print(f"[OK] Pull Request creada con éxito: {pr_url}")
                    return pr_url
                else:
                    print(f"[WARN] gh CLI falló: {res.stderr.strip()}. Abriendo navegador o registrando local.")
            else:
                print(f"[INFO] Proveedor GitHub configurado pero 'gh' CLI no está instalada.")
                print(f"       Crea la PR manualmente en: https://github.com/serchodm/sdd-agentic-starter/compare/{base}...{branch}")

        elif provider == "gitlab":
            if shutil.which("glab"):
                cmd = ["glab", "mr", "create", "--target-branch", base, "--source-branch", branch, "--title", title, "--description", body or title]
                res = subprocess.run(cmd, cwd=str(ROOT_DIR), capture_output=True, text=True)
                if res.returncode == 0:
                    return res.stdout.strip()

        elif provider == "local":
            print(f"[LOCAL GIT] Proveedor Local: Se preparó la rama '{branch}' para merge directo a '{base}'.")
            return f"local://{branch}->{base}"

        return None


# ==============================================================================
# 7. Subcomandos CLI
# ==============================================================================

def cmd_status(args: argparse.Namespace, governance: Dict[str, Any]) -> int:
    current_branch = GitRunner.get_current_branch()
    worktrees = GitRunner.get_worktrees()
    clean = GitRunner.is_clean()

    print("\n=== ESTADO DE GOBERNANZA GIT & WORKTREES SDD ===")
    print(f"  Proveedor Git       : {governance.get('provider', 'github').upper()}")
    print(f"  Rama Activa Actual  : {current_branch or '(desconectado)'}")
    print(f"  Estado del Árbol    : {'✅ Limpio' if clean else '⚠️ Cambios pendientes sin commit'}")
    print(f"  Rama Integración    : {governance['branches'].get('integration', 'develop')}")
    print(f"  Rama Producción     : {governance['branches'].get('production', 'main')}")

    print(f"\n--- Worktrees Activos ({len(worktrees)}) ---")
    for wt in worktrees:
        path_str = wt.get("path", "")
        branch_str = wt.get("branch", "(detached)")
        is_main_wt = path_str == str(ROOT_DIR)
        flag = "[RAÍZ]" if is_main_wt else "[ISOLATED]"
        print(f"  {flag} Rama: {branch_str.ljust(25)} -> Ruta: {path_str}")

    if ACTIVE_STATE_JSON.exists():
        try:
            data = json.loads(ACTIVE_STATE_JSON.read_text(encoding="utf-8", errors="ignore"))
            git_data = data.get("git", {})
            print(f"\n--- Active Work Item (.agents/active_work_item.json) ---")
            print(f"  Work Item Activo    : {data.get('active_work_item_id') or 'IDLE'}")
            print(f"  Rama Asignada       : {git_data.get('branch_name') or 'Ninguna'}")
            print(f"  Worktree Asignado   : {git_data.get('worktree_path') or 'Ninguno'}")
            print(f"  Estado Git          : {git_data.get('status') or 'IDLE'}")
        except Exception:
            pass

    print()
    return 0


def cmd_create_branch(args: argparse.Namespace, governance: Dict[str, Any]) -> int:
    branch = resolve_branch_name(args.spec, governance, is_hotfix=args.hotfix, is_release=args.release)
    base = get_base_branch(branch, governance, args.base)

    if GitRunner.branch_exists(branch):
        print(f"[INFO] La rama '{branch}' ya existe.")
        return 0

    print(f"[+] Creando rama '{branch}' a partir de '{base}'...")
    GitRunner.run(["branch", branch, base])
    sync_active_state_git(args.spec, branch, None, "BRANCH_CREATED")
    print(f"[OK] Rama '{branch}' creada exitosamente.")
    return 0


def cmd_worktree_create(args: argparse.Namespace, governance: Dict[str, Any]) -> int:
    branch = resolve_branch_name(args.spec, governance, is_hotfix=args.hotfix, is_release=args.release)
    base = get_base_branch(branch, governance, args.base)

    manager = WorktreeManager(governance)
    wt_path = manager.create(branch, base, args.name)
    sync_active_state_git(args.spec, branch, wt_path, "IN_PROGRESS")

    print(f"\n[SUCCESS] Worktree listo para trabajo aislado:")
    print(f"  -> Rama     : {branch}")
    print(f"  -> Ruta     : {wt_path}")
    print(f"  -> Env Test : {wt_path / '.env.test'}")
    print(f"\nPara entrar al worktree:")
    print(f"  cd {wt_path}")
    return 0


def cmd_worktree_remove(args: argparse.Namespace, governance: Dict[str, Any]) -> int:
    manager = WorktreeManager(governance)
    identifier = args.spec or args.path
    if not identifier:
        print("[ERROR] Debes especificar --spec o --path para eliminar el worktree.")
        return 1

    success = manager.remove(identifier, force=args.force)
    if success:
        sync_active_state_git(args.spec or "", "", None, "WORKTREE_REMOVED")
    return 0 if success else 1


def cmd_worktree_prune(args: argparse.Namespace, governance: Dict[str, Any]) -> int:
    manager = WorktreeManager(governance)
    manager.prune()
    return 0


def cmd_pr_create(args: argparse.Namespace, governance: Dict[str, Any]) -> int:
    current_branch = GitRunner.get_current_branch()
    branch = args.branch or current_branch

    if not branch or branch in ("main", "develop"):
        print(f"[ERROR] No puedes abrir una PR desde '{branch}'. Debe ser una rama de feature/change/fix/release.")
        return 1

    base = args.base or governance["branches"].get("integration", "develop")
    if branch.startswith(governance["branches"].get("prefix_release", "release/")) or branch.startswith(governance["branches"].get("prefix_hotfix", "hotfix/")):
        base = governance["branches"].get("production", "main")

    spec_id = args.spec or (branch.split("/", 1)[1] if "/" in branch else branch)
    title = args.title or f"feat({spec_id.lower()}): implement {spec_id}"
    provider = governance.get("provider", "github")

    print(f"[+] Creando Pull Request: '{branch}' -> '{base}' ({provider})...")
    pr_url = GitProviderAdapter.create_pr(provider, branch, base, title, args.body or "")

    if pr_url:
        sync_active_state_git(spec_id, branch, None, f"PR_OPENED:{pr_url}")
    return 0


def cmd_release_start(args: argparse.Namespace, governance: Dict[str, Any]) -> int:
    version = args.version.lstrip("v").strip()
    if not re.match(r"^\d+\.\d+\.\d+(-[a-zA-Z0-9.]+)?$", version):
        print(f"[ERROR] Versión inválida '{args.version}'. Debe seguir SemVer (ej: 1.1.0 o 1.1.0-rc.1).")
        return 1

    branch = f"{governance['branches'].get('prefix_release', 'release/')}v{version}"
    base = governance["branches"].get("integration", "develop")

    if GitRunner.branch_exists(branch):
        print(f"[INFO] La rama de release '{branch}' ya existe.")
        return 0

    print(f"[+] Iniciando Release v{version}...")
    print(f"  -> Creando rama '{branch}' desde '{base}'...")
    GitRunner.run(["branch", branch, base])

    if args.worktree:
        manager = WorktreeManager(governance)
        wt_path = manager.create(branch, base, f"release-v{version}")
        sync_active_state_git(f"REL-{version}", branch, wt_path, "RELEASE_STAGING")
        print(f"[SUCCESS] Worktree de release montado en: {wt_path}")
    else:
        sync_active_state_git(f"REL-{version}", branch, None, "RELEASE_STAGING")
        print(f"[SUCCESS] Rama de release '{branch}' creada. Para cambiar a ella: git checkout {branch}")

    return 0


def cmd_release_finish(args: argparse.Namespace, governance: Dict[str, Any]) -> int:
    version = args.version.lstrip("v").strip()
    tag = f"v{version}"
    branch = f"{governance['branches'].get('prefix_release', 'release/')}v{version}"
    main_branch = governance["branches"].get("production", "main")
    dev_branch = governance["branches"].get("integration", "develop")

    if not GitRunner.branch_exists(branch):
        print(f"[ERROR] La rama de release '{branch}' no existe.")
        return 1

    if not GitRunner.is_clean():
        print("[ERROR] El árbol de trabajo tiene cambios sin commit. Limpia el árbol antes de finalizar la release.")
        return 1

    print(f"\n[+] Finalizando Release {tag}...")

    # 1. Merge release into main
    print(f"  -> Fusionando '{branch}' en '{main_branch}'...")
    GitRunner.run(["checkout", main_branch])
    GitRunner.run(["merge", "--no-ff", branch, "-m", f"chore(release): merge {tag} into {main_branch}"])

    # 2. Tag version on main
    print(f"  -> Creando tag Git '{tag}'...")
    GitRunner.run(["tag", "-a", tag, "-m", f"Release {tag}"])

    # 3. Back-merge release into develop
    print(f"  -> Sincronizando '{branch}' de vuelta en '{dev_branch}'...")
    GitRunner.run(["checkout", dev_branch])
    GitRunner.run(["merge", "--no-ff", branch, "-m", f"chore(release): back-merge {tag} into {dev_branch}"])

    # 4. Clean worktree and delete release branch
    manager = WorktreeManager(governance)
    manager.remove(f"release-v{version}", force=True)

    print(f"  -> Eliminando rama local '{branch}'...")
    GitRunner.run(["branch", "-d", branch], check=False)

    # 5. Push if requested
    if args.push:
        print(f"  -> Empujando '{main_branch}', '{dev_branch}' y tags a origin...")
        GitRunner.run(["push", "origin", main_branch, dev_branch, "--tags"])

    sync_active_state_git("", dev_branch, None, "IDLE")
    print(f"\n[SUCCESS] Release {tag} completada exitosamente.")
    print(f"  -> Producción ({main_branch}): Actualizada con tag {tag}")
    print(f"  -> Integración ({dev_branch}): Sincronizada con parches de la release")
    return 0


def cmd_hotfix_start(args: argparse.Namespace, governance: Dict[str, Any]) -> int:
    bug_id = args.bug.strip().upper()
    if not bug_id.startswith("BUG-"):
        bug_id = f"BUG-{bug_id}"

    branch = f"{governance['branches'].get('prefix_hotfix', 'hotfix/')}{bug_id}"
    base = governance["branches"].get("production", "main")

    if GitRunner.branch_exists(branch):
        print(f"[INFO] La rama de hotfix '{branch}' ya existe.")
        return 0

    print(f"[+] Iniciando Hotfix de emergencia '{bug_id}' desde '{base}'...")
    manager = WorktreeManager(governance)
    wt_path = manager.create(branch, base, f"hotfix-{bug_id}")
    sync_active_state_git(bug_id, branch, wt_path, "HOTFIX_IN_PROGRESS")

    print(f"\n[SUCCESS] Worktree de Hotfix listo en: {wt_path}")
    print(f"  -> Rama : {branch}")
    return 0


def cmd_hotfix_finish(args: argparse.Namespace, governance: Dict[str, Any]) -> int:
    bug_id = args.bug.strip().upper()
    if not bug_id.startswith("BUG-"):
        bug_id = f"BUG-{bug_id}"

    version = args.version.lstrip("v").strip()
    tag = f"v{version}"
    branch = f"{governance['branches'].get('prefix_hotfix', 'hotfix/')}{bug_id}"
    main_branch = governance["branches"].get("production", "main")
    dev_branch = governance["branches"].get("integration", "develop")

    if not GitRunner.branch_exists(branch):
        print(f"[ERROR] La rama de hotfix '{branch}' no existe.")
        return 1

    print(f"\n[+] Finalizando Hotfix {bug_id} con versión {tag}...")

    # 1. Merge into main
    print(f"  -> Fusionando '{branch}' en '{main_branch}'...")
    GitRunner.run(["checkout", main_branch])
    GitRunner.run(["merge", "--no-ff", branch, "-m", f"fix(hotfix): apply {bug_id} ({tag})"])
    GitRunner.run(["tag", "-a", tag, "-m", f"Hotfix {tag} ({bug_id})"])

    # 2. Back-merge into develop
    print(f"  -> Sincronizando '{branch}' de vuelta en '{dev_branch}'...")
    GitRunner.run(["checkout", dev_branch])
    GitRunner.run(["merge", "--no-ff", branch, "-m", f"fix(hotfix): back-merge {bug_id} ({tag}) into {dev_branch}"])

    # 3. Clean worktree and delete branch
    manager = WorktreeManager(governance)
    manager.remove(f"hotfix-{bug_id}", force=True)
    GitRunner.run(["branch", "-d", branch], check=False)

    if args.push:
        print(f"  -> Empujando '{main_branch}', '{dev_branch}' y tags a origin...")
        GitRunner.run(["push", "origin", main_branch, dev_branch, "--tags"])

    sync_active_state_git("", dev_branch, None, "IDLE")
    print(f"\n[SUCCESS] Hotfix {bug_id} completado con éxito con versión {tag}.")
    return 0


# ==============================================================================
# 8. Entrypoint Principal
# ==============================================================================

def main() -> int:
    parser = argparse.ArgumentParser(
        description="SDD Git & Worktree Orchestrator (sdd_git.py)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponibles")

    # status
    subparsers.add_parser("status", help="Muestra el estado de gobernanza, ramas y worktrees")

    # create-branch
    p_branch = subparsers.add_parser("create-branch", help="Crea una rama de trabajo para una especificación")
    p_branch.add_argument("--spec", required=True, help="Identificador de la spec (ej: FEAT-001, CR-002, BUG-003)")
    p_branch.add_argument("--base", help="Rama base de la bifurcación (por defecto 'develop')")
    p_branch.add_argument("--hotfix", action="store_true", help="Marca la rama como hotfix (bifurca de main)")
    p_branch.add_argument("--release", action="store_true", help="Marca la rama como release (bifurca de develop)")

    # worktree-create
    p_wt_c = subparsers.add_parser("worktree-create", help="Crea un worktree aislado para trabajo concurrente")
    p_wt_c.add_argument("--spec", required=True, help="Identificador de la spec")
    p_wt_c.add_argument("--name", help="Slug personalizado para la carpeta en .worktrees/")
    p_wt_c.add_argument("--base", help="Rama base de bifurcación")
    p_wt_c.add_argument("--hotfix", action="store_true", help="Marca como hotfix")
    p_wt_c.add_argument("--release", action="store_true", help="Marca como release")

    # worktree-remove
    p_wt_r = subparsers.add_parser("worktree-remove", help="Desmonta y elimina un worktree completado")
    p_wt_r.add_argument("--spec", help="Identificador de la spec asignada al worktree")
    p_wt_r.add_argument("--path", help="Ruta o nombre de la carpeta del worktree")
    p_wt_r.add_argument("--force", action="store_true", help="Forzar eliminación aunque tenga cambios")

    # worktree-prune
    subparsers.add_parser("worktree-prune", help="Limpia referencias huérfanas de worktrees")

    # pr-create
    p_pr = subparsers.add_parser("pr-create", help="Crea una PR agnóstica hacia develop o main")
    p_pr.add_argument("--spec", help="Identificador de la spec")
    p_pr.add_argument("--branch", help="Rama de origen (por defecto la activa)")
    p_pr.add_argument("--base", help="Rama destino")
    p_pr.add_argument("--title", help="Título de la PR (Conventional Commits)")
    p_pr.add_argument("--body", help="Descripción de la PR")

    # release-start
    p_rel_s = subparsers.add_parser("release-start", help="Crea una rama de release desde develop")
    p_rel_s.add_argument("--version", required=True, help="Versión SemVer objetivo (ej: 1.1.0 o v1.1.0)")
    p_rel_s.add_argument("--worktree", action="store_true", help="Monta un worktree aislado para la release")

    # release-finish
    p_rel_f = subparsers.add_parser("release-finish", help="Finaliza la release fusionando en main (tag) y develop")
    p_rel_f.add_argument("--version", required=True, help="Versión SemVer a finalizar (ej: 1.1.0)")
    p_rel_f.add_argument("--push", action="store_true", help="Empuja main, develop y tags a origin automáticamente")

    # hotfix-start
    p_hot_s = subparsers.add_parser("hotfix-start", help="Inicia un hotfix de emergencia bifurcando de main")
    p_hot_s.add_argument("--bug", required=True, help="Identificador del bug (ej: BUG-901)")

    # hotfix-finish
    p_hot_f = subparsers.add_parser("hotfix-finish", help="Finaliza un hotfix fusionando en main (tag) y develop")
    p_hot_f.add_argument("--bug", required=True, help="Identificador del bug")
    p_hot_f.add_argument("--version", required=True, help="Nueva versión PATCH (ej: 1.0.1)")
    p_hot_f.add_argument("--push", action="store_true", help="Empuja main, develop y tags a origin")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    governance = load_git_governance()

    commands = {
        "status": cmd_status,
        "create-branch": cmd_create_branch,
        "worktree-create": cmd_worktree_create,
        "worktree-remove": cmd_worktree_remove,
        "worktree-prune": cmd_worktree_prune,
        "pr-create": cmd_pr_create,
        "release-start": cmd_release_start,
        "release-finish": cmd_release_finish,
        "hotfix-start": cmd_hotfix_start,
        "hotfix-finish": cmd_hotfix_finish,
    }

    handler = commands.get(args.command)
    if handler:
        return handler(args, governance)

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
