#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SDD Universal CLI Master Dispatcher (sdd_cli.py)
================================================
Punto de entrada unificado para todas las herramientas deterministas del
framework agéntico SDD. Permite invocar cualquier herramienta mediante:
    ./sdd <comando> [argumentos]
"""

import argparse, json, pathlib, re, subprocess, sys

# Compatibilidad UTF-8 en Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
for _p in (str(ROOT_DIR), str(ROOT_DIR / ".agents" / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from sdd_immutable_feature_guard import resolve_repo_relative_path, strip_win32_extended_prefix  # noqa: E402
from scripts.sdd_git_state import GitRunner, acquire_file_lock, atomic_write_text, is_link_or_junction, sync_active_state_md  # noqa: E402

_WORK_ITEM_ID_RE = re.compile(r"^((?:FEAT|CR|BUG|HOTFIX|FWK)-\d{3,4})(?:-[A-Za-z0-9._-]+)?$", re.IGNORECASE)
_ALLOWED_SPEC_BUCKETS = ("specs/features", "specs/changes", "specs/bugs", ".sdd/framework/work-items")


def run_script(script_path: pathlib.Path, args: list[str]) -> int:
    """Ejecuta un script de Python en el entorno del proyecto pasando argumentos."""
    if not script_path.exists():
        print(f"[ERROR] Script no encontrado en: {script_path}")
        return 1
    return subprocess.run([sys.executable, str(script_path), *args], cwd=str(ROOT_DIR)).returncode


def cmd_setup_hooks(args: list[str]) -> int:
    """Configura los hooks nativos de Git del proyecto (.githooks)."""
    if not (ROOT_DIR / ".githooks").exists():
        print("[ERROR] Directorio .githooks/ no encontrado.")
        return 1
    res = subprocess.run(["git", "config", "core.hooksPath", ".githooks"], cwd=str(ROOT_DIR), capture_output=True, text=True)
    if res.returncode == 0:
        print("[OK] Hooks nativos de Git configurados con éxito: core.hooksPath = .githooks")
        return 0
    print(f"[ERROR] Fallo al configurar core.hooksPath: {res.stderr.strip()}")
    return 1


def _resolve_cli_repo_root(raw_root: str | None) -> pathlib.Path:
    if raw_root is None:
        return ROOT_DIR
    cleaned = strip_win32_extended_prefix(raw_root.strip())
    cand = pathlib.Path(cleaned) if cleaned else None
    if cand is None or is_link_or_junction(cand) or not cand.is_dir():
        raise ValueError(f"Invalid --repo-root directory: {raw_root!r}")
    return pathlib.Path(strip_win32_extended_prefix(str(cand.resolve(strict=True))))


def _resolve_work_item_spec_dir(repo_root: pathlib.Path, raw_id: str, spec_dir_raw: str | None) -> tuple[pathlib.Path, str]:
    clean_id = raw_id.strip()
    match = _WORK_ITEM_ID_RE.match(clean_id) if ".." not in clean_id else None
    if not match:
        raise ValueError(f"Invalid work item ID '{raw_id}'. Expected FEAT|CR|BUG|HOTFIX|FWK-XXX[X][-slug].")
    canonical_id, has_slug = match.group(1).upper(), clean_id.upper() != match.group(1).upper()
    id_re = re.compile(rf"^{re.escape(canonical_id)}(?:-|$)", re.IGNORECASE)

    if spec_dir_raw is not None:
        if not spec_dir_raw.strip():
            raise ValueError("--spec-dir cannot be empty.")
        rel_spec = resolve_repo_relative_path(spec_dir_raw.strip(), repo_root)
        valid = any(
            rel_spec.lower().startswith(b.lower() + "/") and "/" not in (fld := rel_spec[len(b) + 1 :])
            and id_re.match(fld) and (not has_slug or fld.lower() == clean_id.lower())
            for b in _ALLOWED_SPEC_BUCKETS
        )
        spec_dir = repo_root / rel_spec
        if not valid or is_link_or_junction(spec_dir) or not spec_dir.is_dir():
            raise ValueError(f"Invalid or missing spec_dir '{rel_spec}' for '{clean_id}'.")
        return spec_dir, rel_spec

    matches: list[pathlib.Path] = []
    for bucket in _ALLOWED_SPEC_BUCKETS:
        bpath = repo_root / bucket
        if not (bpath.exists() or is_link_or_junction(bpath)):
            continue
        resolve_repo_relative_path(bucket, repo_root)
        if not bpath.is_dir():
            raise ValueError(f"Spec bucket '{bucket}' is not a directory.")
        for entry in sorted(bpath.iterdir()):
            if (entry.name.lower() == clean_id.lower()) if has_slug else bool(id_re.match(entry.name)):
                if is_link_or_junction(entry) or not entry.is_dir():
                    raise ValueError(f"Spec directory '{entry}' must be a real non-link directory.")
                matches.append(entry)
    if len(matches) != 1:
        raise ValueError(f"Could not locate spec directory for '{clean_id}'." if not matches else f"Ambiguous spec directories for '{clean_id}'.")
    return matches[0], matches[0].relative_to(repo_root).as_posix()


def _safe_agents_dir(repo_root: pathlib.Path, *names: str) -> pathlib.Path:
    agents_dir = repo_root / ".agents"
    if is_link_or_junction(agents_dir) or any(is_link_or_junction(agents_dir / n) for n in names):
        raise ValueError("State path under '.agents/' cannot be a symlink or junction.")
    return agents_dir


def _cmd_work_item_show(repo_root: pathlib.Path) -> int:
    state_file = _safe_agents_dir(repo_root, "active_work_item.json") / "active_work_item.json"
    if not state_file.exists():
        print("No active work item configured (.agents/active_work_item.json not found).")
        return 0
    data = json.loads(state_file.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(".agents/active_work_item.json must contain a JSON object.")
    print(json.dumps(data, indent=2, ensure_ascii=False))
    return 0


def _cmd_work_item_set(repo_root: pathlib.Path, work_item_id: str, spec_dir_raw: str | None) -> int:
    spec_path, rel_spec = _resolve_work_item_spec_dir(repo_root, work_item_id, spec_dir_raw)
    agents_dir = _safe_agents_dir(repo_root, "active_work_item.json", "ACTIVE_STATE.md")
    try:
        branch = GitRunner.get_current_branch(cwd=repo_root)
    except (OSError, subprocess.SubprocessError):
        branch = ""
    payload = {
        "active_work_item_id": spec_path.name, "spec_dir": rel_spec, "branch": branch or None, "worktree": None,
        "status": "PENDING_APPROVAL", "gate_1_approved": False, "gate_2_approved": False, "gate_3_approved": False,
        "approved_by_human": False, "enforce_gate_seals": True, "gate_seals": {},
    }
    with acquire_file_lock(agents_dir / ".state.lock"):
        atomic_write_text(agents_dir / "active_work_item.json", json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    try:
        sync_active_state_md(spec_path.name, branch or "N/A", "PENDING_APPROVAL", root_dir=repo_root, spec_dir=rel_spec)
    except (OSError, subprocess.SubprocessError) as exc:
        print(f"[WARN] Could not sync ACTIVE_STATE.md via git: {exc}")
    print(f"[OK] Active work item set to '{spec_path.name}' ({rel_spec}) [PENDING_APPROVAL]")
    return 0


def cmd_work_item(args: list[str]) -> int:
    """Consulta o selecciona el work item activo."""
    parser = argparse.ArgumentParser(prog="sdd work-item", description="Gestiona el work item activo.")
    sub = parser.add_subparsers(dest="action", required=True)
    p_show = sub.add_parser("show", help="Muestra .agents/active_work_item.json")
    p_set = sub.add_parser("set", help="Selecciona el work item activo en modo PENDING_APPROVAL.")
    p_set.add_argument("work_item_id", metavar="ID", help="ID del work item (FEAT|CR|BUG|HOTFIX|FWK-XXX).")
    p_set.add_argument("--spec-dir", default=None, help="Ruta explícita del directorio de especificación.")
    for sp in (p_show, p_set):
        sp.add_argument("--repo-root", default=None, help="Raíz alternativa del repositorio.")
    parsed = parser.parse_args(args)
    try:
        repo_root = _resolve_cli_repo_root(parsed.repo_root)
        return _cmd_work_item_show(repo_root) if parsed.action == "show" else _cmd_work_item_set(repo_root, parsed.work_item_id, parsed.spec_dir)
    except (ValueError, RuntimeError, OSError, json.JSONDecodeError) as exc:
        print(f"[ERROR] {exc}")
        return 1


DISPATCH_MAP = {
    "healthcheck": ROOT_DIR / ".agents" / "scripts" / "sdd_healthcheck.py",
    "git": ROOT_DIR / "scripts" / "sdd_git.py",
    "instincts": ROOT_DIR / "scripts" / "sdd_instincts.py",
    "boundaries": ROOT_DIR / ".agents" / "scripts" / "verify_architecture_boundaries.py",
    "generate": ROOT_DIR / "scripts" / "sdd_agent_generator.py",
    "sync": ROOT_DIR / "scripts" / "sdd_sync.py",
    "repo-map": ROOT_DIR / ".agents" / "scripts" / "sdd_repo_map.py",
    "trim": ROOT_DIR / ".agents" / "scripts" / "sdd_trim_exec.py",
    "tokens": ROOT_DIR / ".agents" / "scripts" / "sdd_token_usage.py",
    "approve-gate": ROOT_DIR / "scripts" / "sdd_gate_seal.py",
    "verify-gates": ROOT_DIR / "scripts" / "sdd_gate_seal.py",
    "ci-verify": ROOT_DIR / "scripts" / "sdd_ci.py",
    "release": ROOT_DIR / "scripts" / "sdd_release.py",
    "adopt": ROOT_DIR / "scripts" / "sdd_brownfield.py",
    "drift": ROOT_DIR / "scripts" / "sdd_drift.py",
}


def print_help() -> None:
    print("""
SDD Universal CLI - Herramienta Unificada de Ingeniería Agéntica
================================================================
Uso:
    ./sdd <comando> [argumentos]
    .\\sdd.ps1 <comando> [argumentos]

Comandos Disponibles:
    healthcheck      Auditoría integral del arnés SDD, reglas y especificaciones
    git              Gestor de ramas GitFlow SDD, Git Worktrees y Pull Requests
    instincts        Gestor de instintos atómicos y evolución de aprendizaje continuo
    boundaries       Verificación AST de fronteras arquitectónicas e imports prohibidos
    generate         Compilador y materializador del escuadrón agéntico (squad.lock.json)
    sync             Sincronizador bidireccional entre proyecto derivado y plantilla central
    repo-map         Generador de mapa esquelético AST en más de 20 lenguajes
    trim             Recortador determinista de salidas de terminal y tests
    tokens           Telemetría de consumo de tokens y contexto multi-IDE
    approve-gate     Sella criptográficamente (SHA-256) los Gates 1..3 aprobados
    verify-gates     Verifica la integridad SHA-256 de los artefactos de Gates 1..3
    ci-verify        Motor de verificación CI-agnóstico (auto|framework|project)
    release          Motor Gate 6 Release Readiness y CHANGELOG.md (prepare|changelog|verify)
    adopt            Motor de adopción brownfield no destructivo (--dry-run|--apply)
    drift            Auditoría de Spec Drift y migración Strangler Fig
    work-item        Consulta o activa el work item actual (.agents/active_work_item.json)
    setup-hooks      Activa los hooks nativos de Git en .githooks/

Ejemplos:
    ./sdd healthcheck
    ./sdd adopt --dry-run
    ./sdd adopt --apply
    ./sdd ci-verify --mode auto --run-stack-if-approved
    ./sdd release prepare --version v1.2.0
    ./sdd release changelog --version v1.2.0
    ./sdd release verify --version v1.2.0
    ./sdd work-item show
    ./sdd work-item set FEAT-001
    ./sdd approve-gate --embed-inline
    ./sdd verify-gates
    ./sdd git status
    ./sdd git worktree-create --spec FEAT-001
    ./sdd instincts list
    ./sdd generate --materialize
    ./sdd setup-hooks
""")


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help", "help"):
        print_help()
        return 0

    command = sys.argv[1].lower()
    sub_args = sys.argv[2:]

    if command == "setup-hooks":
        return cmd_setup_hooks(sub_args)
    if command == "work-item":
        return cmd_work_item(sub_args)
    if command == "approve-gate":
        return run_script(DISPATCH_MAP["approve-gate"], ["--approve"] + sub_args)
    if command == "verify-gates":
        return run_script(DISPATCH_MAP["verify-gates"], ["--verify"] + sub_args)

    target_script = DISPATCH_MAP.get(command)
    if target_script:
        return run_script(target_script, sub_args)

    # Si se pasa directamente la ruta de un script existente de Python, ejecutarlo
    candidate = pathlib.Path(sys.argv[1])
    if candidate.exists() and candidate.suffix == ".py":
        return run_script(candidate.resolve(), sub_args)

    print(f"[ERROR] Comando desconocido: '{command}'")
    print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
