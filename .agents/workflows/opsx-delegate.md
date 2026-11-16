---
description: Delega tareas DoR-verificadas de FEAT-XXX, CR-XXX o BUG-XXX a .agent-inbox/ (ver skill opsx-delegate).
---

# Workflow `/opsx-delegate` -> `.agents/skills/opsx-delegate/SKILL.md`

- **Parámetros:** `$ARGUMENTS` = `<agente> <work-item-id>` (ej. `/opsx-delegate back-engineer FEAT-001-scaffolding`).
- **Ejecución:** Sigue íntegramente `.agents/skills/opsx-delegate/SKILL.md`: valida `<spec-dir>` y `RN-SDD-IMMUTABLE-DONE`, prepara worktree (`python scripts/sdd_git.py worktree-create --spec <work-item-id>` si aplica), filtra tareas `- [ ]` con DoR completa y escribe `.agent-inbox/<agente>/<work-item-id>.md`.
