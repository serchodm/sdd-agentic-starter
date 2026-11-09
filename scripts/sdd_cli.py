#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SDD Universal CLI Master Dispatcher (sdd_cli.py)
================================================
Punto de entrada unificado para todas las herramientas deterministas del
framework agéntico SDD. Permite invocar cualquier herramienta mediante:
    ./sdd <comando> [argumentos]
"""

import argparse
import pathlib
import subprocess
import sys

# Compatibilidad UTF-8 en Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent


def run_script(script_path: pathlib.Path, args: list[str]) -> int:
    """Ejecuta un script de Python en el entorno del proyecto pasando argumentos."""
    if not script_path.exists():
        print(f"[ERROR] Script no encontrado en: {script_path}")
        return 1

    cmd = [sys.executable, str(script_path)] + args
    res = subprocess.run(cmd, cwd=str(ROOT_DIR))
    return res.returncode


def cmd_setup_hooks(args: list[str]) -> int:
    """Configura los hooks nativos de Git del proyecto (.githooks)."""
    hooks_dir = ROOT_DIR / ".githooks"
    if not hooks_dir.exists():
        print("[ERROR] Directorio .githooks/ no encontrado.")
        return 1

    res = subprocess.run(["git", "config", "core.hooksPath", ".githooks"], cwd=str(ROOT_DIR), capture_output=True, text=True)
    if res.returncode == 0:
        print("[OK] Hooks nativos de Git configurados con éxito: core.hooksPath = .githooks")
        return 0
    else:
        print(f"[ERROR] Fallo al configurar core.hooksPath: {res.stderr.strip()}")
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
    setup-hooks      Activa los hooks nativos de Git en .githooks/

Ejemplos:
    ./sdd healthcheck
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
