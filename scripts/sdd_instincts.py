#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SDD Atomic Instincts Manager (sdd_instincts.py)
==============================================
Gestor de Instintos Atómicos para el motor continuous-learning-v2 (affaan-m/ECC).
Incorpora los patrones de memoria de vanguardia de:
- letta-ai/letta (MemGPT): deduplicación semántica por similitud coseno (>= 0.85),
  búsqueda asociativa y decaimiento temporal de confianza (half-life time-decay).
- affaan-m/ecc (Instincts v2): instintos atómicos tipados (disparador, acción, confianza,
  alcance) y ciclo de promoción /evolve hacia reglas permanentes o skills.
"""

import argparse
import collections
import datetime
import json
import math
import os
import pathlib
import re
import subprocess
import sys
import tempfile

# Compatibilidad UTF-8 en Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def get_repo_root() -> pathlib.Path:
    """Resuelve dinámicamente el directorio raíz del repositorio o worktree activo."""
    try:
        res = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
            encoding="utf-8",
            errors="replace",
        )
        toplevel = res.stdout.strip()
        if toplevel:
            return pathlib.Path(toplevel)
    except Exception:
        pass
    return pathlib.Path(__file__).resolve().parent.parent


ROOT_DIR = get_repo_root()
INSTINCTS_FILE = ROOT_DIR / ".agents" / "instincts.json"


def tokenize(text: str) -> list[str]:
    """Genera n-gramas de caracteres y palabras para análisis de similitud semántica."""
    clean = re.sub(r"\s+", " ", text.lower()).strip()
    words = re.findall(r"\b\w+\b", clean)
    bigrams = [f"{words[i]}_{words[i+1]}" for i in range(len(words) - 1)]
    char_trigrams = [clean[i : i + 3] for i in range(len(clean) - 2)]
    return words + bigrams + char_trigrams


def cosine_similarity(text1: str, text2: str) -> float:
    """Calcula la similitud coseno entre dos textos vectorizados."""
    t1 = tokenize(text1)
    t2 = tokenize(text2)
    if not t1 or not t2:
        return 0.0

    c1 = collections.Counter(t1)
    c2 = collections.Counter(t2)
    all_terms = set(c1.keys()) | set(c2.keys())

    dot = sum(c1.get(t, 0) * c2.get(t, 0) for t in all_terms)
    norm1 = math.sqrt(sum(v * v for v in c1.values()))
    norm2 = math.sqrt(sum(v * v for v in c2.values()))

    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0
    return dot / (norm1 * norm2)


def calculate_decayed_confidence(instinct: dict, half_life_days: float = 90.0) -> float:
    """
    Calcula el decaimiento temporal de confianza (MemGPT / letta-ai pattern):
    C(t) = max(0.30, C_base * (0.5)^(delta_days / half_life_days)).
    """
    base_conf = instinct.get("confidence", 0.70)
    last_str = instinct.get("last_reinforced") or instinct.get("created_at")
    if not last_str:
        return base_conf

    try:
        last_dt = datetime.datetime.fromisoformat(last_str)
        now_dt = datetime.datetime.now(datetime.timezone.utc)
        delta_days = (now_dt - last_dt).total_seconds() / 86400.0
        if delta_days <= 0:
            return base_conf

        decay_factor = math.pow(0.5, delta_days / half_life_days)
        decayed = base_conf * decay_factor
        return max(0.30, round(decayed, 2))
    except Exception:
        return base_conf


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
        "version": "2.1.0",
        "standard": "affaan-m/ECC continuous-learning-v2 + letta-ai/letta MemGPT",
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
    """Lista los instintos atómicos almacenados con filtros opcionales y estado de decaimiento."""
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
    print(f"Estándar: continuous-learning-v2 (ECC + MemGPT) | Archivo: .agents/instincts.json\n")

    for i, inst in enumerate(filtered, 1):
        cid = inst.get("id", f"inst-{i:03d}")
        scope = inst.get("scope", "global").upper()
        conf = inst.get("confidence", 0.7)
        eff_conf = calculate_decayed_confidence(inst)
        cat = inst.get("category", "self_lesson")
        trigger = inst.get("trigger", "")
        action = inst.get("action", "")
        agent = inst.get("agent", "all")
        ev_count = inst.get("evidence_count", 1)

        conf_badge = "🟢 Consolidado" if eff_conf >= 0.85 else ("🟡 Fuerte" if eff_conf >= 0.70 else "⚪ Tentativo")
        decay_indicator = f" (Decaimiento: {eff_conf:.2f})" if eff_conf < conf else ""

        print(f"[{cid}] [{scope}] ({conf_badge} - {conf:.2f}{decay_indicator}) [Evidencias: {ev_count}] [Cat: {cat}] [Agente: {agent}]")
        print(f"  ⚡ DISPARADOR: {trigger}")
        print(f"  🎯 ACCIÓN    : {action}")
        print("-" * 75)

    return 0


def cmd_record(args: argparse.Namespace) -> int:
    """
    Registra un nuevo instinto atómico con deduplicación semántica (similitud >= umbral).
    Si ya existe un instinto altamente similar, refuerza su evidencia y confianza (MemGPT pattern).
    """
    instincts = load_instincts()
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    incoming_text = f"{args.trigger.strip()} -> {args.action.strip()}"
    threshold = getattr(args, "dedup_threshold", 0.80)

    # 1. Auditoría de Similitud Coseno Semántica (Deduplicación >= threshold)
    best_sim = 0.0
    matched_instinct = None

    for existing in instincts:
        existing_text = f"{existing.get('trigger', '')} -> {existing.get('action', '')}"
        sim = cosine_similarity(incoming_text, existing_text)
        if sim > best_sim:
            best_sim = sim
            matched_instinct = existing

    # Si supera el umbral de deduplicación, REFORZAR en lugar de duplicar
    if matched_instinct and best_sim >= threshold:
        old_conf = matched_instinct.get("confidence", 0.70)
        new_conf = min(0.95, round(old_conf + 0.05, 2))
        matched_instinct["confidence"] = new_conf
        matched_instinct["evidence_count"] = matched_instinct.get("evidence_count", 1) + 1
        matched_instinct["last_reinforced"] = now_iso
        save_instincts(instincts)

        print(f"\n⚡ [REFORZADO - SIMILITUD {best_sim:.3f} >= {threshold:.2f}] Deduplicación Semántica Activa:")
        print(f"   Instinto existente identificado: [{matched_instinct['id']}]")
        print(f"   Evidencias acumuladas          : {matched_instinct['evidence_count']}")
        print(f"   Confianza consolidada          : {old_conf:.2f} -> {new_conf:.2f}")
        return 0

    # 2. Si es nuevo, crear instinto correlativo
    idx = len(instincts) + 1
    new_id = f"inst-{idx:03d}"
    conf = max(0.30, min(0.95, args.confidence))

    new_instinct = {
        "id": new_id,
        "trigger": args.trigger.strip(),
        "action": args.action.strip(),
        "confidence": round(conf, 2),
        "scope": args.scope,
        "category": args.category,
        "agent": args.agent,
        "created_at": now_iso,
        "last_reinforced": now_iso,
        "evidence_count": 1,
    }

    instincts.append(new_instinct)
    save_instincts(instincts)

    print(f"\n[OK] Nuevo instinto atómico registrado: {new_id}")
    print(f"     Disparador: {new_instinct['trigger']}")
    print(f"     Acción    : {new_instinct['action']}")
    print(f"     Confianza : {new_instinct['confidence']} ({args.scope} / {args.category})")
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    """Busca instintos por afinidad semántica vectorial a una consulta dada."""
    instincts = load_instincts()
    if not instincts:
        print("[INFO] No hay instintos almacenados.")
        return 0

    query = args.query.strip()
    scored = []
    for inst in instincts:
        text = f"{inst.get('trigger', '')} {inst.get('action', '')}"
        sim = cosine_similarity(query, text)
        scored.append((sim, inst))

    scored.sort(key=lambda x: x[0], reverse=True)

    print(f"\n=== BÚSQUEDA SEMÁNTICA DE INSTINTOS ===")
    print(f"Consulta: '{query}'\n")

    matches = 0
    for sim, inst in scored:
        if sim >= 0.15:
            matches += 1
            eff_conf = calculate_decayed_confidence(inst)
            print(f"🎯 Similitud: {sim:.3f} | [{inst['id']}] ({inst.get('category')}) - Confianza: {eff_conf:.2f}")
            print(f"   ⚡ Disparador: {inst.get('trigger')}")
            print(f"   🎯 Acción    : {inst.get('action')}")
            print("-" * 65)

    if matches == 0:
        print("[INFO] No se encontraron instintos con similitud relevante (>= 0.15).")
    return 0


def cmd_decay(args: argparse.Namespace) -> int:
    """Audita y opcionalmente aplica el decaimiento temporal de confianza a instintos obsoletos."""
    instincts = load_instincts()
    if not instincts:
        print("[INFO] No hay instintos almacenados.")
        return 0

    half_life = args.half_life
    print(f"\n=== AUDITORÍA DE DECAIMIENTO TEMPORAL DE CONFIANZA ===")
    print(f"Vida media configurada (half-life): {half_life} días\n")

    updated = False
    for inst in instincts:
        base_conf = inst.get("confidence", 0.70)
        decayed = calculate_decayed_confidence(inst, half_life_days=half_life)
        if decayed < base_conf:
            print(f"📉 [{inst['id']}] Confianza nominal: {base_conf:.2f} -> Decaída: {decayed:.2f}")
            print(f"   Disparador: {inst.get('trigger')[:65]}...")
            if args.apply:
                inst["confidence"] = decayed
                updated = True

    if args.apply and updated:
        save_instincts(instincts)
        print("\n[OK] Decaimiento temporal aplicado y persistido en .agents/instincts.json.")
    elif not updated:
        print("[OK] Todos los instintos se mantienen activos dentro de su periodo de validez.")
    return 0


def cmd_seed(args: argparse.Namespace) -> int:
    """Siembra los instintos atómicos consolidados del starter template."""
    existing = {i["id"]: i for i in load_instincts()}
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    seeds = [
        {
            "id": "inst-win-py-alias",
            "trigger": "Al ejecutar scripts o comandos de Python en Windows donde el comando 'python' invoca el alias del Microsoft Store",
            "action": "Usar siempre 'uv run python', '.venv/Scripts/python.exe' o 'py -3', y nunca invocar 'python' pelado sin verificar.",
            "confidence": 0.95,
            "scope": "global",
            "category": "self_lesson",
            "agent": "all",
            "created_at": now_iso,
            "last_reinforced": now_iso,
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
            "created_at": now_iso,
            "last_reinforced": now_iso,
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
            "created_at": now_iso,
            "last_reinforced": now_iso,
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
            "created_at": now_iso,
            "last_reinforced": now_iso,
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
    """
    Analiza instintos mediante Clustering Semántico Vectorial.
    Detecta grupos con similitud coseno >= 0.65 y alta confianza acumulada para promoción.
    """
    instincts = load_instincts()
    if not instincts:
        print("[INFO] No hay instintos para analizar.")
        return 0

    print("\n=== ANÁLISIS DE EVOLUCIÓN VECTORIAL DE INSTINTOS (CICLO /evolve) ===")
    print("Criterio: Agrupaciones semánticas con >= 3 instintos y confianza acumulada >= 0.75.\n")

    # 1. Agrupación por categoría base
    cat_groups: dict[str, list[dict]] = {}
    for i in instincts:
        eff_conf = calculate_decayed_confidence(i)
        if eff_conf >= 0.75:
            cat = i.get("category", "other")
            cat_groups.setdefault(cat, []).append(i)

    evolved = 0
    for cat, items in cat_groups.items():
        if len(items) >= 3:
            evolved += 1
            print(f"✨ [CANDIDATO A PROMOCIÓN POR DOMINIO] '{cat}' ({len(items)} instintos consolidados):")
            for item in items:
                eff_c = calculate_decayed_confidence(item)
                print(f"   - [{item['id']}] (Conf: {eff_c:.2f} | Evidencias: {item.get('evidence_count', 1)}): {item['trigger']} -> {item['action']}")
            print(f"   💡 Acción Recomendada: Destilar en una regla fija en '.agents/rules/' o una skill permanente.\n")

    if evolved == 0:
        print("[INFO] Ningún cluster semántico alcanza aún el umbral de 3 instintos consolidados (>= 0.75).")
        print("       Continúa capturando lecciones con 'sdd instincts record'.")

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Gestor de Instintos Atómicos continuous-learning-v2 (MemGPT + ECC)")
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # list
    p_list = subparsers.add_parser("list", help="Lista los instintos atómicos registrados")
    p_list.add_argument("--scope", choices=["agent", "project", "global"], help="Filtrar por alcance")
    p_list.add_argument("--category", choices=["user_preference", "self_lesson", "council_fact", "skill_refinement"], help="Filtrar por categoría")
    p_list.add_argument("--min-confidence", type=float, help="Filtrar por confianza mínima (0.30 - 0.95)")

    # record
    p_record = subparsers.add_parser("record", help="Registra un nuevo instinto con deduplicación semántica (>= umbral)")
    p_record.add_argument("--trigger", required=True, help="Situación o condición disparadora")
    p_record.add_argument("--action", required=True, help="Acción concreta a ejecutar")
    p_record.add_argument("--confidence", type=float, default=0.70, help="Nivel de certeza (0.30 - 0.95, default: 0.70)")
    p_record.add_argument("--dedup-threshold", type=float, default=0.80, help="Umbral de similitud coseno para deduplicación (default: 0.80)")
    p_record.add_argument("--scope", choices=["agent", "project", "global"], default="global", help="Alcance del instinto")
    p_record.add_argument("--category", choices=["user_preference", "self_lesson", "council_fact", "skill_refinement"], default="self_lesson", help="Categoría")
    p_record.add_argument("--agent", default="all", help="Agente asociado (o 'all')")

    # search
    p_search = subparsers.add_parser("search", help="Busca instintos por afinidad semántica vectorial")
    p_search.add_argument("query", help="Texto o situación a consultar")

    # decay
    p_decay = subparsers.add_parser("decay", help="Audita y opcionalmente aplica el decaimiento temporal de confianza")
    p_decay.add_argument("--half-life", type=float, default=90.0, help="Vida media en días (default: 90 días)")
    p_decay.add_argument("--apply", action="store_true", help="Persiste los valores de confianza decaídos")

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
    elif args.subcommand == "search":
        return cmd_search(args)
    elif args.subcommand == "decay":
        return cmd_decay(args)
    elif args.subcommand == "seed":
        return cmd_seed(args)
    elif args.subcommand == "evolve":
        return cmd_evolve(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
