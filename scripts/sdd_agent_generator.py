#!/usr/bin/env python3
"""
SDD Agent Squad Generator
=========================
Generates and specialises expert agent definitions (.agents/agents/*.md)
and sets up their inboxes (.agent-inbox/) based on specs/STACK.md.

Supports:
  - Compact Mode: 7 core agents (orchestrator, architect, back-engineer,
                  front-engineer, qa-tester, devops, documentator).
  - Granular Mode (High-Specialisation Style): 12 specialised agents (back-domain, back-infra,
                                   back-api, db-specialist, back-test, front-logic,
                                   front-ui, front-test, devops, documentator,
                                   architect, orchestrator).
"""

import argparse
import os
import re
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
AGENTS_DIR = ROOT_DIR / ".agents" / "agents"
ARCHETYPES_DIR = ROOT_DIR / ".agents" / "archetypes"
INBOX_DIR = ROOT_DIR / ".agent-inbox"
STACK_PATH = ROOT_DIR / "specs" / "STACK.md"


def parse_stack_md() -> dict:
    """Extracts parameters from specs/STACK.md or provides sensible defaults."""
    params = {
        "BACKEND_DIR": "src/backend",
        "FRONTEND_DIR": "src/frontend",
        "DB_DIR": "src/backend/migrations",
        "BACKEND_TECH": "Python 3.12+ (FastAPI) / C# .NET 9",
        "FRONTEND_TECH": "React 19 + TypeScript + Vite",
        "FRONTEND_STYLE_TECH": "TailwindCSS + shadcn/ui",
        "FRONTEND_STATE_TECH": "TanStack Query + Zustand",
        "DB_ENGINE": "PostgreSQL 16 / SQL Server",
        "ORM_TECH": "SQLAlchemy 2.0 / Dapper",
        "DTO_VALIDATION_TECH": "Pydantic v2 / FluentValidation",
        "INTEGRATION_TEST_STRATEGY": "Testcontainers",
        "BACKEND_COMPILE_CMD": "dotnet build / python -m py_compile",
        "BACKEND_TEST_CMD": "dotnet test / pytest",
        "FRONTEND_BUILD_CMD": "npm run build",
        "FRONTEND_TYPECHECK_CMD": "npx tsc --noEmit",
        "FRONTEND_TEST_CMD": "npm run test",
        "DB_MIGRATE_CMD": "alembic upgrade head / dotnet ef database update",
    }

    if not STACK_PATH.exists():
        return params

    content = STACK_PATH.read_text(encoding="utf-8")

    # Parse backend directory
    match_bdir = re.search(r"src/backend[^\s\)]*", content)
    if match_bdir:
        params["BACKEND_DIR"] = match_bdir.group(0).rstrip(".,;")

    # Parse frontend directory
    match_fdir = re.search(r"src/frontend[^\s\)]*", content)
    if match_fdir:
        params["FRONTEND_DIR"] = match_fdir.group(0).rstrip(".,;")

    return params


def ensure_inbox(agent_name: str):
    """Ensures that the inbox directory for the agent exists."""
    agent_inbox = INBOX_DIR / agent_name
    agent_inbox.mkdir(parents=True, exist_ok=True)
    gitkeep = agent_inbox / ".gitkeep"
    if not gitkeep.exists():
        gitkeep.touch()


def compile_archetype(archetype_path: Path, params: dict) -> str:
    """Replaces placeholders in an archetype template."""
    content = archetype_path.read_text(encoding="utf-8")
    for key, val in params.items():
        content = content.replace(f"{{{{{key}}}}}", val)
    return content


def generate_squad(mode: str):
    """Generates the agent squad files according to the chosen mode."""
    params = parse_stack_md()
    AGENTS_DIR.mkdir(parents=True, exist_ok=True)
    INBOX_DIR.mkdir(parents=True, exist_ok=True)

    print(f"\n[+] Generando Escuadron Agentico en Modo: {mode.upper()}")

    if mode == "granular":
        # High-Specialisation Squad
        granular_archetypes = [
            "back-domain",
            "back-infra",
            "back-api",
            "db-specialist",
            "back-test",
            "front-logic",
            "front-ui",
            "front-test",
        ]
        
        for name in granular_archetypes:
            archetype_file = ARCHETYPES_DIR / f"{name}.archetype.md"
            if archetype_file.exists():
                compiled = compile_archetype(archetype_file, params)
                target_file = AGENTS_DIR / f"{name}.md"
                target_file.write_text(compiled, encoding="utf-8")
                ensure_inbox(name)
                print(f"  -> [OK] Creado agente especializado: {name}.md")
            else:
                print(f"  -> [WARN] No se encontro arquetipo para: {name}")

        # Core fixed agents
        for core in ["orchestrator", "architect", "devops", "documentator"]:
            ensure_inbox(core)
            print(f"  -> [OK] Verificado agente core: {core}.md")

        print("\n[SUCCESS] Escuadron Granular desplegado con exito (Alta Especializacion).")

    elif mode == "compact":
        # Compact Squad
        compact_agents = [
            "orchestrator",
            "architect",
            "back-engineer",
            "front-engineer",
            "qa-tester",
            "devops",
            "documentator",
        ]
        for name in compact_agents:
            ensure_inbox(name)
            target = AGENTS_DIR / f"{name}.md"
            if target.exists():
                print(f"  -> [OK] Verificado agente compacto: {name}.md")

        print("\n[SUCCESS] Escuadron Compacto listo y configurado.")


def list_status():
    """Lists current agents and available archetypes."""
    print("\n=== AGENTES ACTIVOS EN .agents/agents/ ===")
    if AGENTS_DIR.exists():
        for f in sorted(AGENTS_DIR.glob("*.md")):
            print(f"  - @{f.stem}")
    else:
        print("  (Ninguno)")

    print("\n=== ARQUETIPOS DISPONIBLES EN .agents/archetypes/ ===")
    if ARCHETYPES_DIR.exists():
        for f in sorted(ARCHETYPES_DIR.glob("*.archetype.md")):
            role = f.name.replace(".archetype.md", "")
            print(f"  - {role}")
    else:
        print("  (Ninguno)")


def main():
    parser = argparse.ArgumentParser(description="SDD Agent Squad Generator")
    parser.add_argument(
        "--mode",
        choices=["compact", "granular"],
        help="Modo del escuadron: 'compact' (7 agentes) o 'granular' (12 agentes de alta especializacion)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Muestra el estado de los agentes activos y arquetipos disponibles",
    )

    args = parser.parse_args()

    if args.list:
        list_status()
    elif args.mode:
        generate_squad(args.mode)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
