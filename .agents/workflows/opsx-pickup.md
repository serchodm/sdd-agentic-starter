---
description: Recoge ticket de .agent-inbox/, audita DoR, implementa en ámbito permitido y valida DoD (ver skill opsx-pickup).
---

# Workflow `/opsx-pickup` -> `.agents/skills/opsx-pickup/SKILL.md`

- **Ejecución:** Sigue `.agents/skills/opsx-pickup/SKILL.md`: localiza `.agent-inbox/{agente}/<work-item-id>.md`, audita DoR y `RN-SDD-IMMUTABLE-DONE` (si falla $\rightarrow$ `BLOCKED_DOR_{work-item-id}.md`), implementa en el worktree/zona de `.agents/active_work_item.json`, valida el comando DoD (si hay contradicción $\rightarrow$ `BLOCKED_{work-item-id}.md`), marca `[x]` en `03-tasks.md` y elimina el ticket.
