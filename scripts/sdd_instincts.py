#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SDD Atomic Instincts Manager (sdd_instincts.py)
==============================================
Gestor de Instintos Atómicos para el motor continuous-learning-v2 (affaan-m/ECC).
Permite capturar en caliente lecciones, preferencias y refinamientos con puntuación
de confianza (0.30 - 0.95), alcance (agent/project/global) y evolución hacia reglas o skills.
"""

import argparse
import datetime
import json
import os
import pathlib
import sys
import tempfile

# Compatibilidad UTF-8 en Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
INSTINCTS_FILE = ROOT_DIR / ".agents" / "instincts.json"


def load_instincts() -> list[dict]:
    """Carga los instintos desde .agents/instincts.json."""
    if not INSTINCTS_FILE.exists():
        return []
    try:
        with open(INSTINCTS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("instincts", [])
    except Exception as e:
        print(f"[WARN] Error al cargar instintos: {e}")
        return []


def save_instincts(instincts: list[dict]) -> None:
    """Guarda atómicamente la lista de instintos en .agents/instincts.json."""
    INSTINCTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": "2.0.0",
        "standard": "affaan-m/ECC continuous-learning-v2",
        "last_updated": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "total_instincts": len(instincts),
        "instincts": instincts,
    }

    dir_path = INSTINCTS_FILE.parent
    with tempfile.NamedTemporaryFile("w", dir=str(dir_path), delete=False, encoding="utf-8") as tf:
        json.dump(payload, tf, indent=2, ensure_ascii=False)
        temp_name = tf.name

    os.replace(temp_name, str(INSTINCTS_FILE))


def cmd_list(args: argparse.Namespace) -> int:
    """Lista los instintos atómicos almacenados con filtros opcionales."""
    instincts = load_instincts()
    if not instincts:
        print("[INFO] No hay instintos atómicos registrados aún en .agents/instincts.json.")
        print("       Usa 'sdd instincts seed' para inicializar con lecciones del proyecto.")
        return 0

    filtered = instincts
    if args.scope:
        filtered = [i for i in filtered if i.get("scope") == args.scope]
    if args.min_confidence is not None:
        filtered = [i for i in filtered if i.get("confidence", 0) >= args.min_confidence]
    if args.category:
        filtered = [i for i in filtered if i.get("category") == args.category]

    print(f"\n=== INSTINTOS ATÓMICOS REGISTRADOS ({len(filtered)}/{len(instincts)}) ===")
    print(f"Estándar: affaan-m/ECC continuous-learning-v2 | Archivo: .agents/instincts.json\n")

    for i, inst in enumerate(filtered, 1):
        cid = inst.get("id", f"inst-{i:03d}")
        scope = inst.get("scope", "global").upper()
        conf = inst.get("confidence", 0.7)
        cat = inst.get("category", "self_lesson")
        trigger = inst.get("trigger", "")
        action = inst.get("action", "")
        agent = inst.get("agent", "all")

        conf_badge = "🟢 Consolidado" if conf >= 0.85 else ("🟡 Fuerte" if conf >= 0.70 else "⚪ Tentativo")

        print(f"[{cid}] [{scope}] ({conf_badge} - {conf:.2f}) [Cat: {cat}] [Agente: {agent}]")
        print(f"  ⚡ DISPARADOR: {trigger}")
        print(f"  🎯 ACCIÓN    : {action}")
        print("-" * 75)

    return 0


def cmd_record(args: argparse.Namespace) -> int:
    """Registra un nuevo instinto atómico."""
    instincts = load_instincts()

    # Generar ID correlativo
    idx = len(instincts) + 1
    new_id = f"inst-{idx:03d}"

    # Validar confianza
    conf = max(0.30, min(0.95, args.confidence))

    new_instinct = {
        "id": new_id,
        "trigger": args.trigger.strip(),
        "action": args.action.strip(),
        "confidence": round(conf, 2),
        "scope": args.scope,
        "category": args.category,
        "agent": args.agent,
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "evidence_count": 1,
    }

    instincts.append(new_instinct)
    save_instincts(instincts)

    print(f"\n[OK] Instinto atómico registrado con éxito: {new_id}")
    print(f"     Disparador: {new_instinct['trigger']}")
    print(f"     Acción    : {new_instinct['action']}")
    print(f"     Confianza : {new_instinct['confidence']} ({args.scope} / {args.category})")
    return 0


def cmd_seed(args: argparse.Namespace) -> int:
    """Siembra los instintos atómicos consolidados del starter template."""
    existing = {i["id"]: i for i in load_instincts()}

    seeds = [
        {
            "id": "inst-win-py-alias",
            "trigger": "Al ejecutar scripts o comandos de Python en Windows donde el comando 'python' invoca el alias del Microsoft Store",
            "action": "Usar siempre 'uv run python', '.venv/Scripts/python.exe' o 'py -3', y nunca invocar 'python' pelado sin verificar.",
            "confidence": 0.95,
            "scope": "global",
            "category": "self_lesson",
            "agent": "all",
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "evidence_count": 5,
        },
        {
            "id": "inst-anti-rubber-stamp",
            "trigger": "Al auditar o validar Gate 00, Gate 1, Gate 2 o Gate 3",
            "action": "Requerir sign-off humano explícito en el chat y jamás autoaprobar casillas [x] de validación humana (anti-rubber-stamping).",
            "confidence": 0.95,
            "scope": "global",
            "category": "user_preference",
            "agent": "@orchestrator",
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "evidence_count": 8,
        },
        {
            "id": "inst-branch-sync-main-lock",
            "trigger": "Al preparar un commit o push hacia ramas remotas",
            "action": "Verificar la rama activa mediante 'git branch --show-current' y bloquear terminantemente commits o pushes directos a 'main' (RN-SDD-BRANCH-SYNC).",
            "confidence": 0.95,
            "scope": "global",
            "category": "self_lesson",
            "agent": "all",
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "evidence_count": 6,
        },
        {
            "id": "inst-worktree-isolation",
            "trigger": "Al despachar tareas concurrentes o agentes paralelos en Gate 4",
            "action": "Crear y aislar la ejecución en un Git Worktree bajo .worktrees/ con puertos e instancias de test independientes.",
            "confidence": 0.90,
            "scope": "project",
            "category": "self_lesson",
            "agent": "@orchestrator",
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "evidence_count": 3,
        },
    ]

    added = 0
    for seed in seeds:
        if seed["id"] not in existing:
            existing[seed["id"]] = seed
            added += 1

    save_instincts(list(existing.values()))
    print(f"[OK] Sembrado de instintos completado. {added} nuevos instintos incorporados ({len(existing)} en total).")
    return 0


def cmd_evolve(args: argparse.Namespace) -> int:
    """Analiza instintos y detecta candidatos a promoción hacia reglas permanentes o skills."""
    instincts = load_instincts()
    if not instincts:
        print("[INFO] No hay instintos para analizar.")
        return 0

    print("\n=== ANÁLISIS DE EVOLUCIÓN DE INSTINTOS (CICLO /evolve) ===")
    print("Criterio: >= 3 instintos con confianza >= 0.75 en un mismo dominio/categoría.\n")

    # Agrupar por categoría
    groups: dict[str, list[dict]] = {}
    for i in instincts:
        if i.get("confidence", 0) >= 0.75:
            cat = i.get("category", "other")
            groups.setdefault(cat, []).append(i)

    evolved = 0
    for cat, items in groups.items():
        if len(items) >= 3:
            evolved += 1
            print(f"✨ [CANDIDATO A PROMOCIÓN] Dominio/Categoría: '{cat}' ({len(items)} instintos consolidados):")
            for item in items:
                print(f"   - [{item['id']}] (Confianza: {item['confidence']}): {item['trigger']} -> {item['action']}")
            print(f"   💡 Recomendación: Integrar en '.agents/rules/' o destilar en una skill permanente.\n")

    if evolved == 0:
        print("[INFO] Ningún dominio alcanza aún el umbral de 3 instintos consolidados (>= 0.75).")
        print("       Continúa capturando lecciones con 'sdd instincts record'.")

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Gestor de Instintos Atómicos continuous-learning-v2")
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # list
    p_list = subparsers.add_parser("list", help="Lista los instintos atómicos registrados")
    p_list.add_argument("--scope", choices=["agent", "project", "global"], help="Filtrar por alcance")
    p_list.add_argument("--category", choices=["user_preference", "self_lesson", "council_fact", "skill_refinement"], help="Filtrar por categoría")
    p_list.add_argument("--min-confidence", type=float, help="Filtrar por confianza mínima (0.30 - 0.95)")

    # record
    p_record = subparsers.add_parser("record", help="Registra un nuevo instinto atómico")
    p_record.add_argument("--trigger", required=True, help="Situación o condición disparadora")
    p_record.add_argument("--action", required=True, help="Acción concreta a ejecutar")
    p_record.add_argument("--confidence", type=float, default=0.70, help="Nivel de certeza (0.30 - 0.95, default: 0.70)")
    p_record.add_argument("--scope", choices=["agent", "project", "global"], default="global", help="Alcance del instinto")
    p_record.add_argument("--category", choices=["user_preference", "self_lesson", "council_fact", "skill_refinement"], default="self_lesson", help="Categoría")
    p_record.add_argument("--agent", default="all", help="Agente asociado (o 'all')")

    # seed
    subparsers.add_parser("seed", help="Siembra los instintos atómicos consolidados del starter")

    # evolve
    subparsers.add_parser("evolve", help="Analiza y detecta candidatos a promoción de reglas/skills")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.subcommand == "list":
        return cmd_list(args)
    elif args.subcommand == "record":
        return cmd_record(args)
    elif args.subcommand == "seed":
        return cmd_seed(args)
    elif args.subcommand == "evolve":
        return cmd_evolve(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
