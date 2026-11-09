#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SDD Git Hooks Validator (sdd_hooks.py)
======================================
Validador determinista multiplataforma para hooks nativos de Git (.githooks).
Asegura la gobernanza de ramas (RN-SDD-BRANCH-SYNC), límites de fichero y ausencia de secretos.
"""

import os
import pathlib
import re
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

# Patrones de secretos conocidos
SECRET_PATTERNS = [
    (re.compile(r"ghp_[A-Za-z0-9_]{36}"), "GitHub Personal Access Token (Classic)"),
    (re.compile(r"github_pat_[A-Za-z0-9_]{82}"), "GitHub Fine-Grained Token"),
    (re.compile(r"AKIA[0-9A-Z]{16}"), "AWS Access Key ID"),
    (re.compile(r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----"), "Private Key PEM block"),
]

# Marcadores de conflicto Git
CONFLICT_PATTERNS = [
    re.compile(r"^<<<<<<< ", re.MULTILINE),
    re.compile(r"^=======$", re.MULTILINE),
    re.compile(r"^>>>>>>> ", re.MULTILINE),
]


def get_staged_files() -> list[pathlib.Path]:
    """Retorna la lista de archivos preparados en el staging de Git."""
    res = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
        cwd=str(ROOT_DIR),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if res.returncode != 0:
        return []
    lines = [line.strip() for line in res.stdout.splitlines() if line.strip()]
    return [ROOT_DIR / line for line in lines]


def validate_pre_commit() -> int:
    """Ejecuta las validaciones previas al commit."""
    print("--- [HOOK SDD] Ejecutando pre-commit hook ---")
    staged_files = get_staged_files()
    if not staged_files:
        print("[HOOK SDD] No hay ficheros en staging.")
        return 0

    errors = 0

    for file_path in staged_files:
        if not file_path.exists() or file_path.is_dir():
            continue

        rel_path = file_path.relative_to(ROOT_DIR)

        # Omitir archivos binarios, imágenes, lockfiles pesados y logs
        if rel_path.suffix.lower() in [".png", ".jpg", ".jpeg", ".ico", ".pdf", ".lock", ".jsonl", ".pyc"]:
            continue

        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            print(f"[WARN] No se pudo leer {rel_path}: {e}")
            continue

        # 1. Verificar marcadores de conflicto Git
        for pat in CONFLICT_PATTERNS:
            if pat.search(content):
                print(f"[ERROR SDD] Marcador de conflicto Git detectado en: {rel_path}")
                errors += 1
                break

        # 2. Verificar secretos expuestos
        for pat, desc in SECRET_PATTERNS:
            if pat.search(content):
                print(f"[ERROR SDD] Posible secreto expuesto ({desc}) en: {rel_path}")
                errors += 1

        # 3. Verificar límite de 800 líneas en código fuente y especificaciones
        lines_count = len(content.splitlines())
        is_source_or_rule = (
            str(rel_path).startswith("src")
            or str(rel_path).startswith(".agents\\rules")
            or str(rel_path).startswith(".agents/rules")
            or str(rel_path).startswith(".agents\\agents")
            or str(rel_path).startswith(".agents/agents")
            or (str(rel_path).startswith("specs") and not str(rel_path).endswith("STACK.md"))
        )
        if is_source_or_rule and lines_count > 800:
            print(f"[ERROR SDD] {rel_path} supera el límite de 800 líneas ({lines_count} líneas). Divide la responsabilidad.")
            errors += 1

    # 4. Ejecutar Healthcheck de gobernanza SDD
    healthcheck_script = ROOT_DIR / ".agents" / "scripts" / "sdd_healthcheck.py"
    if healthcheck_script.exists():
        hc_res = subprocess.run([sys.executable, str(healthcheck_script)], cwd=str(ROOT_DIR))
        if hc_res.returncode != 0:
            print("[ERROR SDD] Healthcheck falló. Resuelve las advertencias o errores antes de comitear.")
            errors += 1

    if errors > 0:
        print(f"\n[RECHAZADO] Pre-commit cancelado por {errors} error(es) de gobernanza SDD.")
        return 1

    print("[APROBADO] Pre-commit validado con éxito.")
    return 0


def validate_pre_push(args: list[str]) -> int:
    """Ejecuta las validaciones previas al push (protección de main)."""
    print("--- [HOOK SDD] Ejecutando pre-push hook ---")
    
    # Permitir bypass de emergencia si se define explícitamente en el entorno
    if os.environ.get("SDD_FORCE_MAIN_PUSH") == "1":
        print("[WARN SDD] SDD_FORCE_MAIN_PUSH=1 detectado. Bypass de protección de main concedido.")
        return 0

    # Git pasa los refs a pushear por stdin en el formato:
    # <local_ref> <local_sha> <remote_ref> <remote_sha>
    stdin_content = sys.stdin.read()
    if not stdin_content.strip():
        # Push sin refs por stdin (por ejemplo, git push --delete)
        return 0

    lines = [line.strip() for line in stdin_content.splitlines() if line.strip()]
    blocked = False

    for line in lines:
        parts = line.split()
        if len(parts) >= 3:
            remote_ref = parts[2]
            # Detectar si el destino es la rama main
            if remote_ref in ["refs/heads/main", "refs/heads/master"]:
                print(f"\n🛑 [BLOQUEO DE GOBERNANZA SDD - RN-SDD-BRANCH-SYNC]")
                print(f"   Intento de push directo a '{remote_ref}' denegado.")
                print(f"   La rama principal de producción está protegida contra pushes directos.")
                print(f"   Para integrar cambios en producción:")
                print(f"     1. Crea una rama 'release/<version>' o 'hotfix/<bug>'")
                print(f"     2. Abre una Pull Request hacia 'main'")
                print(f"     3. Requiere sign-off humano explícito y CI verde.\n")
                blocked = True

    if blocked:
        return 1

    print("[APROBADO] Pre-push validado con éxito.")
    return 0


def main() -> int:
    if len(sys.argv) < 2:
        print("Uso: python sdd_hooks.py [pre-commit | pre-push]")
        return 1

    command = sys.argv[1].lower()
    if command == "pre-commit":
        return validate_pre_commit()
    elif command == "pre-push":
        return validate_pre_push(sys.argv[2:])
    else:
        print(f"[ERROR] Hook desconocido: {command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
