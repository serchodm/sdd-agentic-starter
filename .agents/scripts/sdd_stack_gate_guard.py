#!/usr/bin/env python3
"""
Guardia de Gate 00: Bloqueo de Stack Tecnológico
Comprueba que specs/STACK.md exista y contenga el sign-off humano formal.
"""
import pathlib
import sys

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

def check_stack_gate(repo_root: pathlib.Path) -> tuple[bool, str]:
    stack_file = repo_root / "specs" / "STACK.md"
    if not stack_file.exists():
        return False, "Gate 00 LOCKED: Falta el fichero specs/STACK.md."
    
    content = stack_file.read_text(encoding="utf-8", errors="ignore")
    if "[x] Gate 00 Approved" not in content and "[X] Gate 00 Approved" not in content:
        return False, (
            "Gate 00 LOCKED: specs/STACK.md no cuenta con la firma de aprobacion humana ([x] Gate 00 Approved).\n"
            "Define el stack tecnico con el @orchestrator y solicita la aprobacion del usuario antes de crear codigo."
        )
    return True, "Gate 00 OK"

if __name__ == "__main__":
    root = pathlib.Path(__file__).resolve().parent.parent.parent
    ok, msg = check_stack_gate(root)
    if not ok:
        print(f"[BLOQUEO GATE 00] {msg}", file=sys.stderr)
        sys.exit(1)
    print(f"[OK] {msg}")
    sys.exit(0)
