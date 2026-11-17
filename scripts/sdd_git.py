#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SDD Deterministic Git & Worktree Orchestrator (sdd_git.py)
=========================================================
Thin CLI entrypoint and backward-compatible facade over `sdd_git_state` and
`sdd_git_worktree` (FWK-008: AUD-003, AUD-016, AUD-019, AUD-021, AUD-025).
"""

from __future__ import annotations

import argparse
import pathlib
import re
import shutil
import subprocess
import sys
from typing import Any, Dict, Optional
from urllib.parse import urlparse, urlunparse

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

_REPO_PARENT = pathlib.Path(__file__).resolve().parent.parent
if str(_REPO_PARENT) not in sys.path:
    sys.path.insert(0, str(_REPO_PARENT))

from scripts.sdd_git_state import (  # noqa: E402, F401
    ACTIVE_STATE_JSON,
    ACTIVE_STATE_MD,
    DEFAULT_GOVERNANCE,
    DEFAULT_WORKTREES_DIR,
    ROOT_DIR,
    STACK_PATH,
    GitRunner,
    detect_default_base_branch,
    get_base_branch,
    get_origin_remote_url,
    list_worktree_states,
    load_active_work_item,
    load_git_governance,
    remove_worktree_state,
    resolve_branch_name,
    resolve_repo_root,
    sanitize_worktree_id,
    sync_active_state_git,
    sync_active_state_md,
    validate_git_ref_name,
)
from scripts.sdd_git_worktree import (  # noqa: E402, F401
    BACKEND_PORT_RANGE,
    FRONTEND_PORT_RANGE,
    WorktreeManager,
    allocate_worktree_ports,
    is_port_available,
    release_worktree_ports,
)


def format_web_remote_url(remote_url: Optional[str]) -> Optional[str]:
    """Normalize an SSH or HTTPS git remote URL to a credential-free web URL."""
    if not remote_url:
        return None
    raw = remote_url.strip()
    if "://" not in raw:
        ssh_scp = re.match(r"^[^@]+@([^:/]+):(.+?)(?:\.git)?/?$", raw)
        if ssh_scp:
            return f"https://{ssh_scp.group(1)}/{ssh_scp.group(2).lstrip('/')}"
    parsed = urlparse(raw)
    if parsed.scheme in {"http", "https", "ssh"} and parsed.hostname:
        scheme = "https" if parsed.scheme == "ssh" else parsed.scheme
        netloc = f"{parsed.hostname}:{parsed.port}" if parsed.port else parsed.hostname
        path = re.sub(r"\.git/?$", "", parsed.path).rstrip("/")
        return urlunparse((scheme, netloc, path, "", "", ""))
    return None


def build_pr_compare_url(
    provider: str, base: str, branch: str, cwd: Optional[pathlib.Path] = None
) -> Optional[str]:
    """Build a dynamic PR/MR creation URL from the configured git origin remote."""
    web_base = format_web_remote_url(get_origin_remote_url("origin", cwd=cwd))
    if not web_base:
        return None
    if provider == "gitlab":
        return f"{web_base}/-/merge_requests/new?merge_request[source_branch]={branch}&merge_request[target_branch]={base}"
    if provider == "bitbucket":
        return f"{web_base}/pull-requests/new?source={branch}&dest={base}"
    return f"{web_base}/compare/{base}...{branch}"


class GitProviderAdapter:
    """Provider-agnostic PR/MR creator (GitHub / GitLab / Bitbucket / Local)."""

    @staticmethod
    def create_pr(provider: str, branch: str, base: str, title: str, body: str = "") -> Optional[str]:
        eff_root = resolve_repo_root()
        if provider == "github":
            if shutil.which("gh"):
                cmd = ["gh", "pr", "create", "--base", base, "--head", branch, "--title", title, "--body", body or title]
                res = subprocess.run(cmd, cwd=str(eff_root), capture_output=True, text=True, encoding="utf-8", errors="replace")
                if res.returncode == 0:
                    pr_url = res.stdout.strip()
                    print(f"[OK] Pull Request creada con éxito: {pr_url}")
                    return pr_url
                print(f"[WARN] gh CLI falló: {res.stderr.strip()}.")
            else:
                print("[INFO] Proveedor GitHub configurado pero 'gh' CLI no está instalada.")
            compare_url = build_pr_compare_url("github", base, branch, cwd=eff_root)
            if compare_url:
                print(f"       Crea la PR manualmente en: {compare_url}")
            else:
                remote = get_origin_remote_url("origin", cwd=eff_root) or "(sin remoto 'origin')"
                print(f"       Remoto origin={remote}. Crea la PR para '{branch}' -> '{base}'.")
        elif provider == "gitlab":
            if shutil.which("glab"):
                cmd = ["glab", "mr", "create", "--target-branch", base, "--source-branch", branch, "--title", title, "--description", body or title]
                res = subprocess.run(cmd, cwd=str(eff_root), capture_output=True, text=True, encoding="utf-8", errors="replace")
                if res.returncode == 0:
                    return res.stdout.strip()
            if compare_url := build_pr_compare_url("gitlab", base, branch, cwd=eff_root):
                print(f"       Crea la MR manualmente en: {compare_url}")
        elif provider == "bitbucket":
            if compare_url := build_pr_compare_url("bitbucket", base, branch, cwd=eff_root):
                print(f"       Crea la PR manualmente en: {compare_url}")
        elif provider == "local":
            print(f"[LOCAL GIT] Proveedor Local: Se preparó la rama '{branch}' para merge directo a '{base}'.")
            return f"local://{branch}->{base}"
        return None


def cmd_status(_args: argparse.Namespace, governance: Dict[str, Any]) -> int:
    eff_root = resolve_repo_root()
    current_branch = GitRunner.get_current_branch(cwd=eff_root)
    worktrees = GitRunner.get_worktrees(cwd=eff_root)
    clean = GitRunner.is_clean(cwd=eff_root)
    origin_url = format_web_remote_url(get_origin_remote_url("origin", cwd=eff_root)) or get_origin_remote_url("origin", cwd=eff_root) or "(sin remoto)"
    try:
        base_branch = detect_default_base_branch(governance, cwd=eff_root)
    except RuntimeError:
        base_branch = governance["branches"].get("integration", "develop")

    print("\n=== ESTADO DE GOBERNANZA GIT & WORKTREES SDD ===")
    print(f"  Proveedor Git       : {governance.get('provider', 'github').upper()}")
    print(f"  Remoto Origin       : {origin_url}")
    print(f"  Rama Activa Actual  : {current_branch or '(desconectado)'}")
    print(f"  Rama Base Detectada : {base_branch}")
    print(f"  Estado del Árbol    : {'✅ Limpio' if clean else '⚠️ Cambios pendientes sin commit'}")
    print(f"  Rama Integración    : {governance['branches'].get('integration', 'develop')}")
    print(f"  Rama Producción     : {governance['branches'].get('production', 'main')}")

    print(f"\n--- Worktrees Activos ({len(worktrees)}) ---")
    root_resolved = eff_root.resolve(strict=False)
    for wt in worktrees:
        path_str = wt.get("path", "")
        branch_str = wt.get("branch", "(detached)")
        is_main_wt = pathlib.Path(path_str).resolve(strict=False) == root_resolved if path_str else False
        flag = "[RAÍZ]" if is_main_wt else "[ISOLATED]"
        print(f"  {flag} Rama: {branch_str.ljust(25)} -> Ruta: {path_str}")

    if active_data := load_active_work_item(root_dir=eff_root):
        git_data = active_data.get("git", {})
        print("\n--- Active Work Item (.agents/active_work_item.json) ---")
        print(f"  Work Item Activo    : {active_data.get('active_work_item_id') or 'IDLE'}")
        print(f"  Rama Asignada       : {git_data.get('branch_name') or 'Ninguna'}")
        print(f"  Worktree Asignado   : {git_data.get('worktree_path') or 'Ninguno'}")
        print(f"  Estado Git          : {git_data.get('status') or 'IDLE'}")

    if wt_states := list_worktree_states(root_dir=eff_root):
        print(f"\n--- Estados Aislados por Worktree ({len(wt_states)}) ---")
        for st in wt_states:
            g = st.get("git", {})
            ports = f"BE:{g.get('backend_port', '-')} FE:{g.get('frontend_port', '-')}"
            print(f"  [{st.get('worktree_id')}] {st.get('active_work_item_id') or 'IDLE'} | {g.get('branch_name') or '-'} | {ports}")
    print()
    return 0


def cmd_create_branch(args: argparse.Namespace, governance: Dict[str, Any]) -> int:
    branch = resolve_branch_name(args.spec, governance, is_hotfix=args.hotfix, is_release=args.release)
    base = get_base_branch(branch, governance, args.base)
    if GitRunner.branch_exists(branch):
        print(f"[INFO] La rama '{branch}' ya existe.")
        if getattr(args, "checkout", False):
            GitRunner.run(["checkout", branch])
            sync_active_state_git(args.spec, branch, None, "IN_PROGRESS", base_branch=base)
        return 0
    print(f"[+] Creando rama '{branch}' a partir de '{base}'...")
    GitRunner.run(["branch", branch, base])
    if getattr(args, "checkout", False):
        GitRunner.run(["checkout", branch])
    sync_active_state_git(args.spec, branch, None, "IN_PROGRESS" if getattr(args, "checkout", False) else "BRANCH_CREATED", base_branch=base)
    print(f"[OK] Rama '{branch}' creada exitosamente.")
    return 0


def cmd_switch_branch(args: argparse.Namespace, governance: Dict[str, Any]) -> int:
    target = args.branch or (resolve_branch_name(args.spec, governance) if args.spec else "")
    if not target:
        print("[ERROR] Debes indicar --branch o --spec para cambiar de rama.")
        return 1
    validate_git_ref_name(target)
    GitRunner.run(["checkout", target])
    spec_id = args.spec or (target.split("/", 1)[1] if "/" in target else "")
    status = "IDLE" if target in {governance["branches"].get("production", "main"), governance["branches"].get("integration", "develop")} else "IN_PROGRESS"
    sync_active_state_git(spec_id if status != "IDLE" else "", target, None, status)
    print(f"[OK] Cambiado a rama '{target}' y sincronizado .agents/ACTIVE_STATE.md.")
    return 0


def cmd_worktree_create(args: argparse.Namespace, governance: Dict[str, Any]) -> int:
    branch = resolve_branch_name(args.spec, governance, is_hotfix=args.hotfix, is_release=args.release)
    base = get_base_branch(branch, governance, args.base)
    manager = WorktreeManager(governance)
    wt_path = manager.create(branch, base, args.name)
    ports = manager.get_ports_for_worktree(wt_path)
    remote_url = get_origin_remote_url()
    sync_active_state_git(args.spec, branch, wt_path, "IN_PROGRESS", base_branch=base, remote_url=remote_url, ports=ports)
    print("\n[SUCCESS] Worktree listo para trabajo aislado:")
    print(f"  -> Rama     : {branch}")
    print(f"  -> Base     : {base}")
    print(f"  -> Ruta     : {wt_path}")
    print(f"  -> Env Test : {wt_path / '.env.test'}")
    if ports:
        print(f"  -> Puertos  : Backend={ports[0]}, Frontend={ports[1]}")
    print(f"\nPara entrar al worktree:\n  cd {wt_path}")
    return 0


def cmd_worktree_remove(args: argparse.Namespace, governance: Dict[str, Any]) -> int:
    manager = WorktreeManager(governance)
    identifier = args.spec or args.path
    if not identifier:
        print("[ERROR] Debes especificar --spec o --path para eliminar el worktree.")
        return 1
    resolved_target = manager.resolve_target(identifier)
    success = manager.remove(identifier, force=args.force)
    if success:
        sync_active_state_git(args.spec or "", "", resolved_target, "WORKTREE_REMOVED")
    return 0 if success else 1


def cmd_worktree_prune(_args: argparse.Namespace, governance: Dict[str, Any]) -> int:
    manager = WorktreeManager(governance)
    manager.prune()
    eff_root = resolve_repo_root()
    sync_active_state_md("", GitRunner.get_current_branch(eff_root), "PRUNED", root_dir=eff_root)
    return 0


def cmd_pr_create(args: argparse.Namespace, governance: Dict[str, Any]) -> int:
    branch = args.branch or GitRunner.get_current_branch()
    prod_branch = governance["branches"].get("production", "main")
    dev_branch = governance["branches"].get("integration", "develop")
    if not branch or branch in {prod_branch, dev_branch, "main", "develop"}:
        print(f"[ERROR] No puedes abrir una PR desde '{branch}'. Debe ser una rama de feature/change/fix/release.")
        return 1
    base = args.base or get_base_branch(branch, governance)
    if not args.base and branch.startswith(governance["branches"].get("prefix_release", "release/")):
        base = prod_branch if GitRunner.ref_exists(prod_branch) else base
    spec_id = args.spec or (branch.split("/", 1)[1] if "/" in branch else branch)
    title = args.title or f"feat({spec_id.lower()}): implement {spec_id}"
    provider = governance.get("provider", "github")
    print(f"[+] Creando Pull Request: '{branch}' -> '{base}' ({provider})...")
    pr_url = GitProviderAdapter.create_pr(provider, branch, base, title, args.body or "")
    if pr_url:
        sync_active_state_git(spec_id, branch, None, f"PR_OPENED:{pr_url}", base_branch=base)
    return 0


def _run_release_preflight(version: str, stage: str, branch: str | None = None) -> bool:
    """Run fail-closed Gate 6 release preflight (`start` or `finish`) and report failures."""
    try:
        try:
            from scripts.sdd_release import run_release_preflight
        except ImportError:
            from sdd_release import run_release_preflight
        report = run_release_preflight(resolve_repo_root(), version, stage=stage, release_branch=branch)
    except Exception as exc:
        print(f"[ERROR] Release preflight ({stage}) falló: {exc}")
        return False
    if report.overall_status != "PASS":
        print(f"[ERROR] Release preflight ({stage}) bloqueado ({report.release_id}):")
        for chk in (c for c in report.checks if c.status == "FAIL"):
            print(f"  - [{chk.status}] {chk.name}: {chk.detail}")
    return report.overall_status == "PASS"


def _ensure_branch_ready(branch: str, *, require_clean: bool = False) -> bool:
    if not GitRunner.branch_exists(branch):
        print(f"[ERROR] La rama '{branch}' no existe.")
        return False
    if require_clean and not GitRunner.is_clean():
        print("[ERROR] El árbol de trabajo tiene cambios sin commit.")
        return False
    return True


def cmd_release_start(args: argparse.Namespace, governance: Dict[str, Any]) -> int:
    version = args.version.lstrip("v").strip()
    if not re.match(r"^\d+\.\d+\.\d+(-[a-zA-Z0-9.]+)?$", version):
        print(f"[ERROR] Versión inválida '{args.version}'. Debe seguir SemVer (ej: 1.1.0 o v1.1.0).")
        return 1
    branch = f"{governance['branches'].get('prefix_release', 'release/')}v{version}"
    base = get_base_branch(branch, governance)
    if GitRunner.branch_exists(branch):
        print(f"[INFO] La rama de release '{branch}' ya existe.")
        return 0
    if not _run_release_preflight(version, "start"):
        return 1
    print(f"[+] Iniciando Release v{version} desde '{base}'...")
    GitRunner.run(["branch", branch, base])
    if args.worktree:
        manager = WorktreeManager(governance)
        wt_path = manager.create(branch, base, f"release-v{version}")
        sync_active_state_git(f"REL-{version}", branch, wt_path, "RELEASE_STAGING", base_branch=base, ports=manager.get_ports_for_worktree(wt_path))
        print(f"[SUCCESS] Worktree de release montado en: {wt_path}")
    else:
        sync_active_state_git(f"REL-{version}", branch, None, "RELEASE_STAGING", base_branch=base)
        print(f"[SUCCESS] Rama de release '{branch}' creada.")
    return 0


def _finish_branch_flow(governance: Dict[str, Any], *, branch: str, tag: str, wt_slug: str, merge_msg: str, back_msg: str, tag_msg: str, push: bool, require_clean: bool = False) -> int:
    main_branch = governance["branches"].get("production", "main")
    dev_branch = governance["branches"].get("integration", "develop")
    if push and main_branch in {"main", "master"}:
        print(f"[ERROR] RN-SDD-BRANCH-SYNC: prohibido hacer push directo a la rama protegida '{main_branch}'. Usa el modo PR por defecto (sin --local-merge) o --local-merge sin --push.")
        return 1
    if not _ensure_branch_ready(branch, require_clean=require_clean):
        return 1
    GitRunner.run(["checkout", main_branch])
    GitRunner.run(["merge", "--no-ff", branch, "-m", merge_msg])
    GitRunner.run(["tag", "-a", tag, "-m", tag_msg])
    target_after = dev_branch if GitRunner.branch_exists(dev_branch) else main_branch
    if target_after != main_branch:
        GitRunner.run(["checkout", target_after])
        GitRunner.run(["merge", "--no-ff", branch, "-m", back_msg.format(target=target_after)])
    WorktreeManager(governance).remove(wt_slug, force=True)
    GitRunner.run(["branch", "-d", branch], check=False)
    if push:
        refs = [main_branch, dev_branch] if target_after != main_branch else [main_branch]
        GitRunner.run(["push", "origin", *refs, "--tags"])
    sync_active_state_git("", target_after, None, "IDLE")
    return 0


def _pr_finish_flow(governance: Dict[str, Any], *, item_id: str, branch: str, title: str, body: str, require_clean: bool = False) -> int:
    """Prepare or open a PR toward the production branch without touching local main."""
    if not _ensure_branch_ready(branch, require_clean=require_clean):
        return 1
    main_branch = governance["branches"].get("production", "main")
    provider = governance.get("provider", "github")
    print(f"[+] Preparando Pull Request: '{branch}' -> '{main_branch}' ({provider})...")
    pr_url = GitProviderAdapter.create_pr(provider, branch, main_branch, title, body)
    status = f"PR_OPENED:{pr_url}" if pr_url else f"PR_READY:{branch}->{main_branch}"
    sync_active_state_git(item_id, branch, None, status, base_branch=main_branch)
    return 0


def cmd_release_finish(args: argparse.Namespace, governance: Dict[str, Any]) -> int:
    version = args.version.lstrip("v").strip()
    tag = f"v{version}"
    branch = f"{governance['branches'].get('prefix_release', 'release/')}v{version}"
    main_branch = governance["branches"].get("production", "main")
    if not _ensure_branch_ready(branch, require_clean=True):
        return 1
    if not _run_release_preflight(version, "finish", branch=branch):
        return 1
    if getattr(args, "local_merge", False):
        rc = _finish_branch_flow(
            governance, branch=branch, tag=tag, wt_slug=f"release-v{version}",
            merge_msg=f"chore(release): merge {tag} into {main_branch}",
            back_msg=f"chore(release): back-merge {tag} into {{target}}",
            tag_msg=f"Release {tag}", push=getattr(args, "push", False), require_clean=True,
        )
    else:
        rc = _pr_finish_flow(
            governance, item_id=f"REL-{version}", branch=branch,
            title=f"chore(release): release {tag} into {main_branch}",
            body=f"Release {tag} ({branch} -> {main_branch})", require_clean=True,
        )
    if rc == 0:
        print(f"\n[SUCCESS] Release {tag} completada exitosamente.")
    return rc


def cmd_hotfix_start(args: argparse.Namespace, governance: Dict[str, Any]) -> int:
    bug_id = args.bug.strip().upper()
    bug_id = bug_id if bug_id.startswith("BUG-") else f"BUG-{bug_id}"
    branch = f"{governance['branches'].get('prefix_hotfix', 'hotfix/')}{bug_id}"
    base = get_base_branch(branch, governance)
    if GitRunner.branch_exists(branch):
        print(f"[INFO] La rama de hotfix '{branch}' ya existe.")
        return 0
    manager = WorktreeManager(governance)
    wt_path = manager.create(branch, base, f"hotfix-{bug_id}")
    sync_active_state_git(bug_id, branch, wt_path, "HOTFIX_IN_PROGRESS", base_branch=base, ports=manager.get_ports_for_worktree(wt_path))
    print(f"\n[SUCCESS] Worktree de Hotfix listo en: {wt_path}")
    return 0


def cmd_hotfix_finish(args: argparse.Namespace, governance: Dict[str, Any]) -> int:
    bug_id = args.bug.strip().upper()
    bug_id = bug_id if bug_id.startswith("BUG-") else f"BUG-{bug_id}"
    tag = f"v{args.version.lstrip('v').strip()}"
    branch = f"{governance['branches'].get('prefix_hotfix', 'hotfix/')}{bug_id}"
    main_branch = governance["branches"].get("production", "main")
    if getattr(args, "local_merge", False):
        rc = _finish_branch_flow(
            governance, branch=branch, tag=tag, wt_slug=f"hotfix-{bug_id}",
            merge_msg=f"fix(hotfix): apply {bug_id} ({tag})",
            back_msg=f"fix(hotfix): back-merge {bug_id} ({tag}) into {{target}}",
            tag_msg=f"Hotfix {tag} ({bug_id})", push=getattr(args, "push", False),
        )
    else:
        rc = _pr_finish_flow(
            governance, item_id=bug_id, branch=branch,
            title=f"fix(hotfix): apply {bug_id} ({tag})",
            body=f"Hotfix {tag} ({bug_id}: {branch} -> {main_branch})",
        )
    if rc == 0:
        print(f"\n[SUCCESS] Hotfix {bug_id} completado con éxito con versión {tag}.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="SDD Git & Worktree Orchestrator (sdd_git.py)")
    sub = parser.add_subparsers(dest="command", help="Comandos disponibles")
    specs = [
        ("status", [], "Muestra el estado de gobernanza, ramas y worktrees", ()),
        ("create-branch", [], "Crea una rama de trabajo para una especificación", (("--spec", {"required": True}), ("--base", {}), ("--hotfix", {"action": "store_true"}), ("--release", {"action": "store_true"}), ("--checkout", {"action": "store_true"}))),
        ("switch-branch", ["checkout"], "Cambia de rama y sincroniza ACTIVE_STATE.md", (("--spec", {}), ("--branch", {}))),
        ("worktree-create", [], "Crea un worktree aislado para trabajo concurrente", (("--spec", {"required": True}), ("--name", {}), ("--base", {}), ("--hotfix", {"action": "store_true"}), ("--release", {"action": "store_true"}))),
        ("worktree-remove", [], "Desmonta y elimina un worktree completado", (("--spec", {}), ("--path", {}), ("--force", {"action": "store_true"}))),
        ("worktree-prune", [], "Limpia referencias huérfanas de worktrees", ()),
        ("pr-create", [], "Crea una PR agnóstica hacia rama base", (("--spec", {}), ("--branch", {}), ("--base", {}), ("--title", {}), ("--body", {}))),
        ("release-start", [], "Crea una rama de release", (("--version", {"required": True}), ("--worktree", {"action": "store_true"}))),
        ("release-finish", [], "Finaliza la release mediante PR hacia producción (o merge local con --local-merge)", (("--version", {"required": True}), ("--push", {"action": "store_true"}), ("--local-merge", {"action": "store_true"}))),
        ("hotfix-start", [], "Inicia un hotfix de emergencia", (("--bug", {"required": True}),)),
        ("hotfix-finish", [], "Finaliza un hotfix mediante PR hacia producción (o merge local con --local-merge)", (("--bug", {"required": True}), ("--version", {"required": True}), ("--push", {"action": "store_true"}), ("--local-merge", {"action": "store_true"}))),
    ]
    for name, aliases, help_txt, flags in specs:
        p = sub.add_parser(name, aliases=aliases, help=help_txt)
        for flag, kw in flags:
            p.add_argument(flag, **kw)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return 0
    governance = load_git_governance()
    commands = {
        "status": cmd_status,
        "create-branch": cmd_create_branch,
        "switch-branch": cmd_switch_branch,
        "checkout": cmd_switch_branch,
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
    return handler(args, governance) if handler else 0


if __name__ == "__main__":
    sys.exit(main())
