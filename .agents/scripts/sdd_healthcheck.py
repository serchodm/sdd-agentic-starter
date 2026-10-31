#!/usr/bin/env python3
"""
SDD Framework Healthcheck
Verifica la integridad de la estructura de gobernanza, buzones, especificaciones y documentación.
"""
import pathlib
import sys

# Asegurar compatibilidad en consolas Windows (cp1252 / utf-8)
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

def run_healthcheck(root: pathlib.Path) -> bool:
    errors = []

    # 1. Ficheros Core
    core_files = [
        "AGENTS.md",
        "README.md",
        ".gitignore",
        "specs/STACK.md",
        "specs/BACKLOG.md",
        "specs/SDD_FRAMEWORK.md",
        ".agents/active_work_item.json",
        ".agents/hooks.json"
    ]
    for cf in core_files:
        if not (root / cf).exists():
            errors.append(f"Falta fichero esencial: {cf}")

    # 2. Buzones de Agentes
    inboxes = ["orchestrator", "architect", "back-engineer", "front-engineer", "qa-tester", "documentator"]
    for ib in inboxes:
        ib_dir = root / ".agent-inbox" / ib
        if not ib_dir.exists() or not ib_dir.is_dir():
            errors.append(f"Falta carpeta de buzon: .agent-inbox/{ib}")

    # 3. Agentes Definidos
    agents = ["orchestrator.md", "architect.md", "back-engineer.md", "front-engineer.md", "qa-tester.md", "documentator.md"]
    for ag in agents:
        if not (root / ".agents" / "agents" / ag).exists():
            errors.append(f"Falta definicion de agente: .agents/agents/{ag}")

    # 4. Reglas
    rules = ["00-stack-lock.md", "01-sdd-lifecycle.md", "02-ears-requirements.md", "03-functional-doc-0dd.md", "04-multiagent-dag.md", "05-security-and-secrets.md"]
    for r in rules:
        if not (root / ".agents" / "rules" / r).exists():
            errors.append(f"Falta regla esencial: .agents/rules/{r}")

    print("=== SDD FRAMEWORK HEALTHCHECK ===")
    if errors:
        print("[ERRORES DETECTADOS]")
        for e in errors:
            print(f"  [X] {e}")
        return False
    else:
        print("[OK] Estructura agentica integra y conforme a los estandares SDD.")
        return True

if __name__ == "__main__":
    repo_root = pathlib.Path(__file__).resolve().parent.parent.parent
    ok = run_healthcheck(repo_root)
    sys.exit(0 if ok else 1)
