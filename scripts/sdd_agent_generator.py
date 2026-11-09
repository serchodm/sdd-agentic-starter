#!/usr/bin/env python3
"""
SDD Agent Squad Generator & Materializer
========================================
Compiles and materializes expert agent definitions (.agents/agents/*.md),
inboxes (.agent-inbox/), and active pack assets based on `specs/STACK.md`
and the Ownership Map, using recipes from `.sdd/catalog/`.

Supports:
  - Presets: compact, granular, api-only, spa-only, monorepo, custom.
  - Ownership Map parsing from specs/STACK.md.
  - Clean composition: Archetype + Stack Pack fragments + Project Overrides.
  - Generates `.agents/squad.lock.json` for deterministic tracking.
"""

import argparse
import datetime
import json
import os
import pathlib
import re
import shutil
import sys

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
AGENTS_DIR = ROOT_DIR / ".agents" / "agents"
OVERRIDES_DIR = ROOT_DIR / ".agents" / "overrides"
INBOX_DIR = ROOT_DIR / ".agent-inbox"
STACK_PATH = ROOT_DIR / "specs" / "STACK.md"
LOCK_FILE = ROOT_DIR / ".agents" / "squad.lock.json"

CATALOG_DIR = ROOT_DIR / ".sdd" / "catalog"
ARCHETYPES_DIR = CATALOG_DIR / "archetypes"
SPECIALISTS_DIR = CATALOG_DIR / "specialists"
PACKS_DIR = CATALOG_DIR / "packs"

CORE_AGENTS = [
    "orchestrator",
    "functional-analyst",
    "architect",
    "qa-tester",
    "documentator",
    "devops",
]

PRESET_CONFIGS = {
    "compact": {
        "description": "Escuadron Compacto (7 roles core para proyectos agiles/MVPs)",
        "builders": [
            {
                "name": "back-engineer",
                "archetype": "tier-backend",
                "zone_paths": ["src/backend/**", "src/api/**", "src/domain/**", "src/infrastructure/**"],
                "dod": "dotnet test / pytest / npm test",
                "forbidden": "UI components, frontend direct code",
            },
            {
                "name": "front-engineer",
                "archetype": "tier-frontend",
                "zone_paths": ["src/frontend/**", "src/ui/**", "src/web/**"],
                "dod": "npm run build && npm test",
                "forbidden": "backend database migrations, direct SQL",
            },
        ],
    },
    "granular": {
        "description": "Escuadron Especializado Granular (Alta especializacion y aislamiento de capas)",
        "builders": [
            {
                "name": "back-domain",
                "archetype": "layer-domain",
                "zone_paths": ["src/backend/domain/**", "src/backend/application/**", "src/domain/**"],
                "dod": "pytest tests/unit/domain -q",
                "forbidden": "fastapi, sqlalchemy, sqlmodel, direct infrastructure/api imports",
            },
            {
                "name": "back-infra",
                "archetype": "layer-infra",
                "zone_paths": ["src/backend/infrastructure/**", "src/infrastructure/**"],
                "dod": "pytest tests/integration -q",
                "forbidden": "domain direct mutations, frontend code",
            },
            {
                "name": "back-api",
                "archetype": "layer-api",
                "zone_paths": ["src/backend/api/**", "src/api/**"],
                "dod": "pytest tests/unit/api -q",
                "forbidden": "direct SQL/ORM queries without use cases",
            },
            {
                "name": "db-specialist",
                "archetype": "layer-db",
                "zone_paths": ["src/backend/migrations/**", "DDBB/**", "migrations/**"],
                "dod": "alembic check / dotnet ef migrations has-pending-model-changes",
                "forbidden": "application controllers, UI code",
            },
            {
                "name": "back-test",
                "archetype": "layer-test",
                "zone_paths": ["tests/unit/**", "tests/integration/**", "tests/backend/**"],
                "dod": "pytest tests/ -q",
                "forbidden": "production code modification without bug report",
            },
            {
                "name": "front-logic",
                "archetype": "front-logic",
                "zone_paths": ["src/frontend/src/store/**", "src/frontend/src/api/**", "src/frontend/src/hooks/**"],
                "dod": "npm run test:logic",
                "forbidden": "backend internal routes, direct DB queries",
            },
            {
                "name": "front-ui",
                "archetype": "front-ui",
                "zone_paths": ["src/frontend/src/components/**", "src/frontend/src/views/**"],
                "dod": "npm run build",
                "forbidden": "backend code, raw API network mutations without store/hook",
            },
            {
                "name": "front-test",
                "archetype": "front-test",
                "zone_paths": ["src/frontend/tests/**", "tests/frontend/**"],
                "dod": "npm test",
                "forbidden": "production code modifications",
            },
        ],
    },
    "api-only": {
        "description": "Solo Backend / Microservicios API (Sin capa visual)",
        "builders": [
            {
                "name": "back-domain",
                "archetype": "layer-domain",
                "zone_paths": ["src/domain/**", "src/application/**"],
                "dod": "pytest tests/unit/domain",
                "forbidden": "web framework, ORM imports",
            },
            {
                "name": "back-infra",
                "archetype": "layer-infra",
                "zone_paths": ["src/infrastructure/**"],
                "dod": "pytest tests/integration",
                "forbidden": "domain direct mutations",
            },
            {
                "name": "back-api",
                "archetype": "layer-api",
                "zone_paths": ["src/api/**"],
                "dod": "pytest tests/unit/api",
                "forbidden": "direct SQL/ORM without application layer",
            },
            {
                "name": "db-specialist",
                "archetype": "layer-db",
                "zone_paths": ["migrations/**"],
                "dod": "migration check",
                "forbidden": "application logic",
            },
        ],
    },
    "spa-only": {
        "description": "Solo Frontend SPA / Cliente Web",
        "builders": [
            {
                "name": "front-logic",
                "archetype": "front-logic",
                "zone_paths": ["src/store/**", "src/api/**", "src/hooks/**"],
                "dod": "npm test",
                "forbidden": "direct styling without design system",
            },
            {
                "name": "front-ui",
                "archetype": "front-ui",
                "zone_paths": ["src/components/**", "src/pages/**"],
                "dod": "npx tsc --noEmit && npm run build",
                "forbidden": "raw fetch without API layer",
            },
        ],
    },
}


def ensure_inbox(agent_name: str):
    agent_inbox = INBOX_DIR / agent_name
    agent_inbox.mkdir(parents=True, exist_ok=True)
    gitkeep = agent_inbox / ".gitkeep"
    if not gitkeep.exists():
        gitkeep.touch()


def compile_builder_agent(builder: dict, tech_stack: str) -> str:
    agent_name = builder["name"]
    archetype_name = builder.get("archetype", "tier-backend")
    
    # Check project override first
    override_path = OVERRIDES_DIR / f"{agent_name}.md"
    if override_path.exists():
        print(f"  -> [OVERRIDE] Aplicando override especifico de proyecto: {override_path.name}")
        return override_path.read_text(encoding="utf-8")

    archetype_file = ARCHETYPES_DIR / f"{archetype_name}.archetype.md"
    if not archetype_file.exists():
        # Fallback to general archetype
        archetype_file = ARCHETYPES_DIR / "tier-backend.archetype.md"

    template = archetype_file.read_text(encoding="utf-8")
    zone_lines = "\n".join(f"  - `{p}`" for p in builder.get("zone_paths", []))
    
    compiled = (
        template.replace("{{AGENT_NAME}}", agent_name)
        .replace("{{ZONE_PATHS}}", zone_lines)
        .replace("{{TECH_STACK}}", tech_stack)
        .replace("{{DOD_COMMAND}}", builder.get("dod", "test command"))
        .replace("{{FORBIDDEN_IMPORTS}}", builder.get("forbidden", "None"))
    )

    header = f"<!-- GENERATED by sdd_agent_generator from archetype '{archetype_name}'. Do not edit directly; use .agents/overrides/{agent_name}.md -->\n"
    return header + compiled


def parse_stack_specs() -> tuple[str, list[dict], list[str]]:
    """Parses specs/STACK.md to extract tech stack, builders, and active packs."""
    tech_stack = "Multi-Stack"
    preset = "compact"
    active_packs = []

    if not STACK_PATH.exists():
        return tech_stack, PRESET_CONFIGS[preset]["builders"], active_packs

    content = STACK_PATH.read_text(encoding="utf-8")

    # Detect preset or mode
    match_preset = re.search(r"Modalidad(?:\s+y\s+Topología)?.*:\s*`?([a-zA-Z0-9_-]+)`?", content, re.IGNORECASE)
    if match_preset:
        raw_p = match_preset.group(1).lower()
        if "granular" in raw_p:
            preset = "granular"
        elif "api" in raw_p:
            preset = "api-only"
        elif "spa" in raw_p:
            preset = "spa-only"
        else:
            preset = "compact"

    # Detect active languages & frameworks from STACK.md
    if re.search(r"python", content, re.IGNORECASE):
        active_packs.append("lang-python")
    if re.search(r"fastapi", content, re.IGNORECASE):
        active_packs.append("framework-fastapi")
    if re.search(r"django", content, re.IGNORECASE):
        active_packs.append("framework-django")
    if re.search(r"typescript|javascript|node", content, re.IGNORECASE):
        active_packs.append("lang-typescript")
    if re.search(r"react", content, re.IGNORECASE):
        active_packs.append("framework-react")
    if re.search(r"vue|nuxt", content, re.IGNORECASE):
        active_packs.append("framework-vue")
    if re.search(r"c#|\.net", content, re.IGNORECASE):
        active_packs.append("lang-csharp")
    if re.search(r"\bgo\b|golang", content, re.IGNORECASE):
        active_packs.append("lang-go")
    if re.search(r"rust", content, re.IGNORECASE):
        active_packs.append("lang-rust")
    if re.search(r"java|spring", content, re.IGNORECASE):
        active_packs.append("lang-java")
    if re.search(r"postgres|mysql|redis|database|sql", content, re.IGNORECASE):
        active_packs.append("capability-database")
    if re.search(r"docker|kubernetes|container|deploy", content, re.IGNORECASE):
        active_packs.append("capability-devops")
    if re.search(r"frontend|html|css|web", content, re.IGNORECASE):
        active_packs.append("capability-web-frontend")

    builders = PRESET_CONFIGS.get(preset, PRESET_CONFIGS["compact"])["builders"]
    return tech_stack, builders, active_packs


def materialize_squad(preset_name: str | None = None, requested_packs: list[str] | None = None):
    tech_stack, builders, detected_packs = parse_stack_specs()
    if preset_name and preset_name in PRESET_CONFIGS:
        builders = PRESET_CONFIGS[preset_name]["builders"]
    packs = list(set((requested_packs or []) + detected_packs))

    AGENTS_DIR.mkdir(parents=True, exist_ok=True)
    INBOX_DIR.mkdir(parents=True, exist_ok=True)
    OVERRIDES_DIR.mkdir(parents=True, exist_ok=True)

    print(f"\n[+] Materializando Escuadron Agentico SDD...")
    print(f"  -> Stack Detectado: {tech_stack}")
    print(f"  -> Stack Packs Activos: {', '.join(packs) if packs else '(Ninguno)'}")

    lock_record = {
        "timestamp": datetime.datetime.now().isoformat(),
        "preset": preset_name or "detected",
        "tech_stack": tech_stack,
        "core_agents": CORE_AGENTS,
        "builders": [],
        "specialists": [],
        "active_packs": packs,
    }

    # 1. Verify Core Agents and ensure inboxes
    for core in CORE_AGENTS:
        ensure_inbox(core)
        core_file = AGENTS_DIR / f"{core}.md"
        if core_file.exists():
            print(f"  -> [CORE] Verificado agente coordinador: @{core}")

    # 2. Materialize Builders based on Ownership Map / Preset
    for b in builders:
        b_name = b["name"]
        compiled = compile_builder_agent(b, tech_stack)
        target_path = AGENTS_DIR / f"{b_name}.md"
        target_path.write_text(compiled, encoding="utf-8")
        ensure_inbox(b_name)
        lock_record["builders"].append(b_name)
        print(f"  -> [BUILDER] Materializado dueno de zona: @{b_name} ({b.get('archetype')})")

    # 3. Materialize Universal Specialists from Catalog
    if SPECIALISTS_DIR.exists():
        for spec_file in SPECIALISTS_DIR.glob("*.md"):
            name = spec_file.stem
            target_path = AGENTS_DIR / spec_file.name
            target_path.write_text(spec_file.read_text(encoding="utf-8"), encoding="utf-8")
            ensure_inbox(name)
            lock_record["specialists"].append(name)
            print(f"  -> [SPECIALIST] Cargado especialista universal ECC: @{name}")

    # 4. Materialize Pack Specialists & Rules
    for pack_name in packs:
        pack_dir = PACKS_DIR / pack_name
        if not pack_dir.exists():
            continue
        # Agents from pack
        pack_agents_dir = pack_dir / "agents"
        if pack_agents_dir.exists():
            for a_file in pack_agents_dir.glob("*.md"):
                name = a_file.stem
                target_path = AGENTS_DIR / a_file.name
                target_path.write_text(a_file.read_text(encoding="utf-8"), encoding="utf-8")
                ensure_inbox(name)
                print(f"  -> [PACK:{pack_name}] Agente activado: @{name}")

    # Write squad.lock.json
    LOCK_FILE.write_text(json.dumps(lock_record, indent=2), encoding="utf-8")
    print(f"\n[SUCCESS] Escuadron materializado con exito. Registro actualizado en: {LOCK_FILE.name}")


def list_catalog():
    print("\n=== ARQUETIPOS EN .sdd/catalog/archetypes/ ===")
    if ARCHETYPES_DIR.exists():
        for f in sorted(ARCHETYPES_DIR.glob("*.archetype.md")):
            print(f"  - {f.name.replace('.archetype.md', '')}")

    print("\n=== ESPECIALISTAS UNIVERSALES EN .sdd/catalog/specialists/ ===")
    if SPECIALISTS_DIR.exists():
        for f in sorted(SPECIALISTS_DIR.glob("*.md")):
            print(f"  - @{f.stem}")

    print("\n=== STACK PACKS DISPONIBLES EN .sdd/catalog/packs/ ===")
    if PACKS_DIR.exists():
        for d in sorted(PACKS_DIR.iterdir()):
            if d.is_dir():
                print(f"  - {d.name}")

    print("\n=== PRESETS PREDEFINIDOS ===")
    for p_name, p_val in PRESET_CONFIGS.items():
        print(f"  * {p_name}: {p_val['description']}")


def main():
    parser = argparse.ArgumentParser(description="SDD Agent Squad Generator & Materializer")
    parser.add_argument("--materialize", action="store_true", help="Materializa el escuadron segun specs/STACK.md")
    parser.add_argument("--mode", choices=list(PRESET_CONFIGS.keys()), help="Preset especifico de escuadron")
    parser.add_argument("--packs", nargs="*", help="Stack packs adicionales a activar")
    parser.add_argument("--list", action="store_true", help="Muestra el contenido del catalogo y presets")

    args = parser.parse_args()

    if args.list:
        list_catalog()
    elif args.materialize or args.mode:
        materialize_squad(preset_name=args.mode, requested_packs=args.packs)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
