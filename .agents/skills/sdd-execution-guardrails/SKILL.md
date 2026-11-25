---
name: sdd-execution-guardrails
description: Guardrails operativos promovidos de continuous-learning-v2 para entorno Python en Windows, aislamiento en Git Worktrees (.worktrees/), verificación de rama antes de commit/push y respeto de sign-off humano en Gates S0/1–3.
---

# Skill: `sdd-execution-guardrails`

Consolidación operativa de `inst-win-py-alias`, `inst-worktree-isolation`, `inst-branch-sync-main-lock` e `inst-anti-rubber-stamp` (sin duplicar `AGENTS.md`):

> **Referencia (carga bajo demanda):** [references/worktree-lifecycle.md](references/worktree-lifecycle.md) (ciclo Windows/POSIX en `.worktrees/`, `ports_registry.json`, `.env.test` sin secretos y poda).

1. **Python Determinista:** Ejecutar scripts y tests con `uv run python`, `.venv` (`.venv/Scripts/python.exe` o `.venv/bin/python`), `python3` o `py -3`; nunca invocar `python` sin verificar en Windows (evita el alias del Microsoft Store).
2. **Aislamiento en Gate 4:** Aislar ejecuciones paralelas en Git Worktrees bajo `.worktrees/` (`sdd git worktree-create` / `worktree-remove`) con puertos y `.env.test` independientes.
3. **Pre-Commit / Pre-Push (`RN-SDD-BRANCH-SYNC`):** Verificar la rama activa con `git branch --show-current` antes de comitear o pushear y bloquear cualquier operación directa sobre `main`.
4. **Anti Rubber-Stamping (`RN-SDD-HUMAN-GATE-OWNERSHIP`):** En Gate S0 y Gates 1–3, requerir confirmación humana explícita en el chat y jamás marcar casillas `[x]` por cuenta propia.
