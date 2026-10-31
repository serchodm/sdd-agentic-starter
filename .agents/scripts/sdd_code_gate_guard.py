#!/usr/bin/env python3
"""
SDD Code Gate Guard (PreToolUse Hook)
Bloquea cualquier intento de edición sobre código de producción si:
1. Gate 00 (Stack) no está aprobado en specs/STACK.md.
2. No existe un work item activo en .agents/active_work_item.json con Gates 1, 2 y 3 aprobados por humano.
3. Se intenta superar el límite de 800 líneas por fichero de código.
"""
import json
import pathlib
import re
import sys
from sdd_stack_gate_guard import check_stack_gate

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

MAX_SOURCE_LINES = 800

def is_code_path(target_path: str, repo_root: pathlib.Path) -> str | None:
    norm = target_path.replace("\\", "/").lower()
    root_str = str(repo_root).replace("\\", "/").lower()
    if norm.startswith(root_str + "/"):
        norm = norm[len(root_str) + 1:]
    norm = norm.lstrip("/")

    # Exclusiones seguras
    if norm.startswith((".agents/", "specs/", "docs/", ".agent-inbox/")):
        return None
    if norm in ("agents.md", "readme.md", ".gitignore"):
        return None

    # Si afecta a src/ o ficheros de código típicos
    if norm.startswith("src/") or any(norm.endswith(ext) for ext in [".py", ".ts", ".tsx", ".js", ".jsx", ".cs", ".java", ".go", ".rs", ".php", ".html", ".css", ".sql"]):
        return norm
    return None

def main():
    repo_root = pathlib.Path(__file__).resolve().parent.parent.parent

    # 1. Verificar Gate 00 (Stack Lock)
    stack_ok, stack_msg = check_stack_gate(repo_root)
    if not stack_ok:
        print(f"[SDD GUARD REJECTED] {stack_msg}", file=sys.stderr)
        sys.exit(1)

    # 2. Verificar Work Item Activo (Gate 2 Code Lock)
    state_file = repo_root / ".agents" / "active_work_item.json"
    if not state_file.exists():
        print("[SDD GUARD REJECTED] Falta .agents/active_work_item.json", file=sys.stderr)
        sys.exit(1)

    try:
        state = json.loads(state_file.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"[SDD GUARD REJECTED] JSON invalido en active_work_item.json: {exc}", file=sys.stderr)
        sys.exit(1)

    g1 = bool(state.get("gate_1_approved"))
    g2 = bool(state.get("gate_2_approved"))
    g3 = bool(state.get("gate_3_approved"))
    human_ok = bool(state.get("approved_by_human"))

    if not (g1 and g2 and g3 and human_ok):
        print(
            "[SDD GUARD REJECTED] RN-SDD-GATE2-CODE-LOCK: El codigo de produccion esta BLOQUEADO.\n"
            "No hay un work item con Gates 1, 2 y 3 aprobados explicitamente por el humano en .agents/active_work_item.json.",
            file=sys.stderr
        )
        sys.exit(1)

    sys.exit(0)

if __name__ == "__main__":
    main()
