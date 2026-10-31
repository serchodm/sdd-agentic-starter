#!/usr/bin/env python3
"""
Guardia de Inmutabilidad de Features Finalizadas (RN-SDD-IMMUTABLE-DONE)
Impide editar cualquier fichero dentro de specs/features/FEAT-XXX-*/ si la feature está marcada como Done.
"""
import pathlib
import re
import sys

def get_done_features(repo_root: pathlib.Path) -> set[str]:
    backlog = repo_root / "specs" / "BACKLOG.md"
    if not backlog.exists():
        return set()
    content = backlog.read_text(encoding="utf-8", errors="ignore")
    done_features = set()
    # Buscar patrones | FEAT-XXX | ... | Done / Completado |
    for line in content.splitlines():
        match = re.search(r"\|\s*(FEAT-\d+)\s*\|.*?\|\s*(Done|Completado)\s*\|", line, re.IGNORECASE)
        if match:
            done_features.add(match.group(1).upper())
    return done_features

def main():
    repo_root = pathlib.Path(__file__).resolve().parent.parent.parent
    done_features = get_done_features(repo_root)
    # Puede ser invocado con rutas de argumentos
    if len(sys.argv) > 1:
        target = sys.argv[1].replace("\\", "/")
        for feat in done_features:
            if f"specs/features/{feat.lower()}" in target.lower():
                print(f"\033[91m[IMMUTABLE GUARD] Error: {feat} está finalizada (Done) y es de SOLO LECTURA. Usa un Change Request (CR).\033[0m", file=sys.stderr)
                sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()
