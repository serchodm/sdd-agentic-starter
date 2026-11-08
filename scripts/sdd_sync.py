#!/usr/bin/env python3
"""
SDD Framework Bi-Directional Synchronizer (sdd_sync.py)
Permite mantener sincronizado el framework agéntico (reglas, skills, scripts, estándares, agentes, contextos)
entre proyectos derivados y el repositorio plantilla (sdd-agentic-starter).
"""

import argparse
import filecmp
import os
import pathlib
import shutil
import sys

# Compatibilidad UTF-8 en Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Componentes exactos que forman el "Core Agéntico"
FRAMEWORK_PATHS = [
    ".agents/agents",
    ".agents/contexts",
    ".agents/rules",
    ".agents/scripts",
    ".agents/skills",
    ".agents/workflows",
    ".agents/hooks.json",
    "docs/standards",
    "specs/templates",
    "specs/SDD_FRAMEWORK.md",
]

# Archivos específicos de proyecto a excluir de la sincronización de plantilla
EXCLUDE_RELATIVE_FILES = {
    ".agents/agents/jarvis.md",
    ".agents/agents/audio-voice.md",
    ".agents/ACTIVE_STATE.md",
    ".agents/active_work_item.json",
}

DEFAULT_TEMPLATE_PATH = pathlib.Path("C:/Projects/sdd-agentic-starter")


def get_all_relative_files(base_dir: pathlib.Path, rel_subpaths: list[str]) -> set[str]:
    files = set()
    for sub in rel_subpaths:
        p = base_dir / sub
        if not p.exists():
            continue
        if p.is_file():
            rel = sub.replace("\\", "/")
            if rel not in EXCLUDE_RELATIVE_FILES:
                files.add(rel)
        elif p.is_dir():
            for item in p.rglob("*"):
                if item.is_file() and not item.name.endswith(".pyc") and "__pycache__" not in str(item):
                    rel = item.relative_to(base_dir).as_posix()
                    if rel not in EXCLUDE_RELATIVE_FILES:
                        files.add(rel)
    return files


def compare_framework(source_root: pathlib.Path, template_root: pathlib.Path):
    src_files = get_all_relative_files(source_root, FRAMEWORK_PATHS)
    tpl_files = get_all_relative_files(template_root, FRAMEWORK_PATHS)
    all_files = sorted(src_files | tpl_files)

    identical = []
    modified = []
    only_in_source = []
    only_in_template = []

    for rel in all_files:
        f_src = source_root / rel
        f_tpl = template_root / rel

        if f_src.exists() and f_tpl.exists():
            if filecmp.cmp(f_src, f_tpl, shallow=False):
                identical.append(rel)
            else:
                modified.append(rel)
        elif f_src.exists() and not f_tpl.exists():
            only_in_source.append(rel)
        elif not f_src.exists() and f_tpl.exists():
            only_in_template.append(rel)

    print("=== ESTADO DE SINCRONIZACIÓN DEL FRAMEWORK SDD ===")
    print(f"Origen (Proyecto Actual): {source_root}")
    print(f"Destino (Plantilla SDD) : {template_root}\n")

    if modified:
        print("[MODIFICADOS / DIVERGENTES]:")
        for f in modified:
            print(f"  * {f}")
        print()

    if only_in_source:
        print("[NUEVOS EN ESTE PROYECTO (Candidatos para subir a la plantilla)]:")
        for f in only_in_source:
            print(f"  + {f}")
        print()

    if only_in_template:
        print("[SOLO EN LA PLANTILLA (Candidatos para incorporar al proyecto)]:")
        for f in only_in_template:
            print(f"  - {f}")
        print()

    if not modified and not only_in_source and not only_in_template:
        print("[OK] Todos los componentes del framework estan 100% sincronizados.\n")
    else:
        print(
            f"Total: {len(identical)} identicos, {len(modified)} modificados, "
            f"{len(only_in_source)} solo en proyecto, {len(only_in_template)} solo en plantilla.\n"
        )


def push_to_template(source_root: pathlib.Path, template_root: pathlib.Path):
    print(f"Sincronizando mejoras del Framework: {source_root} -> {template_root}")
    src_files = get_all_relative_files(source_root, FRAMEWORK_PATHS)
    copied = 0

    for rel in sorted(src_files):
        src_file = source_root / rel
        dst_file = template_root / rel
        dst_file.parent.mkdir(parents=True, exist_ok=True)

        content = src_file.read_bytes()
        try:
            text = content.decode("utf-8")
            sanitized = (
                text.replace("P.A.C.O.", "Project")
                .replace("PACO", "Project")
                .replace("@jarvis", "@orchestrator")
                .replace("c:/Projects/P.A.C.O", "c:/Projects/sdd-agentic-starter")
                .replace("C:/Projects/P.A.C.O", "C:/Projects/sdd-agentic-starter")
                .replace("c:\\Projects\\P.A.C.O", "c:\\Projects\\sdd-agentic-starter")
                .replace("C:\\Projects\\P.A.C.O", "C:\\Projects\\sdd-agentic-starter")
            )
            content = sanitized.encode("utf-8")
        except UnicodeDecodeError:
            pass

        if not dst_file.exists() or dst_file.read_bytes() != content:
            dst_file.write_bytes(content)
            copied += 1
            print(f"  -> Exportado: {rel}")

    print(f"\n[OK] Sincronizacion completada: {copied} fichero(s) actualizados en la plantilla.")
    print("Recuerda entrar a la plantilla, revisar git diff y hacer git commit / push si procede.")


def pull_from_template(source_root: pathlib.Path, template_root: pathlib.Path):
    print(f"Incorporando mejoras de la Plantilla al Proyecto: {template_root} -> {source_root}")
    tpl_files = get_all_relative_files(template_root, FRAMEWORK_PATHS)
    copied = 0

    for rel in sorted(tpl_files):
        src_file = template_root / rel
        dst_file = source_root / rel
        dst_file.parent.mkdir(parents=True, exist_ok=True)

        content = src_file.read_bytes()
        if not dst_file.exists() or dst_file.read_bytes() != content:
            dst_file.write_bytes(content)
            copied += 1
            print(f"  <- Incorporado: {rel}")

    print(f"\n[OK] Actualizacion completada: {copied} fichero(s) incorporados desde la plantilla.")


def main():
    parser = argparse.ArgumentParser(description="SDD Framework Bi-Directional Synchronizer")
    parser.add_argument(
        "--template-dir",
        type=str,
        default=str(DEFAULT_TEMPLATE_PATH),
        help="Ruta a la carpeta local del repositorio plantilla sdd-agentic-starter",
    )
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument(
        "--status", action="store_true", help="Compara el framework entre el proyecto y la plantilla (por defecto)"
    )
    group.add_argument(
        "--push-to-template", action="store_true", help="Copia mejoras del framework del proyecto hacia la plantilla"
    )
    group.add_argument(
        "--pull-from-template", action="store_true", help="Trae actualizaciones de la plantilla hacia este proyecto"
    )

    args = parser.parse_args()

    project_root = pathlib.Path(__file__).resolve().parent.parent
    template_root = pathlib.Path(args.template_dir).resolve()

    if not template_root.exists():
        print(f"[ERROR] No se encontro la carpeta de la plantilla en: {template_root}", file=sys.stderr)
        sys.exit(1)

    if args.push_to_template:
        push_to_template(project_root, template_root)
    elif args.pull_from_template:
        pull_from_template(project_root, template_root)
    else:
        compare_framework(project_root, template_root)


if __name__ == "__main__":
    main()
