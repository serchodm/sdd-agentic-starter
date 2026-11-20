---
name: sdd-execution-guardrails
description: Guardrails operativos promovidos de continuous-learning-v2 para entorno Python en Windows, aislamiento en Git Worktrees (.worktrees/), verificación de rama antes de commit/push y respeto de sign-off humano en Gates S0/1–3.
---

# Skill: `sdd-execution-guardrails`

Consolidación operativa de los instintos `inst-win-py-alias`, `inst-worktree-isolation`, `inst-branch-sync-main-lock` e `inst-anti-rubber-stamp` (sin duplicar las definiciones normativas de `AGENTS.md`):

1. **Python en Windows:** Al lanzar scripts o tests en Windows, usar siempre `uv run python`, `.venv/Scripts/python.exe` o `py -3`; nunca invocar `python` sin verificar (evita el alias del Microsoft Store).
2. **Aislamiento en Gate 4:** Al despachar tareas concurrentes o subagentes paralelos, aislar cada ejecución en un Git Worktree bajo `.worktrees/` con puertos y entorno de test independientes.
3. **Pre-Commit / Pre-Push (`RN-SDD-BRANCH-SYNC`):** Verificar la rama activa con `git branch --show-current` antes de comitear o pushear y bloquear cualquier operación directa sobre `main`.
4. **Anti Rubber-Stamping (`RN-SDD-HUMAN-GATE-OWNERSHIP`):** En Gate S0 y Gates 1–3, requerir confirmación humana explícita en el chat y jamás marcar casillas `[x]` por cuenta propia.
