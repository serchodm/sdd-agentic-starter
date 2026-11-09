---
description: Recoge la tarea pendiente (FEAT-XXX, CR-XXX o BUG-XXX) del buzón del agente, audita la Definition of Ready (DoR), implementa el código y valida la Definition of Done (DoD).
---

# Workflow: `/opsx-pickup` (Migrado a `.agents/skills/opsx-pickup/SKILL.md`)

Este comando es ejecutado por cualquier especialista del equipo de desarrollo para procesar el ticket asignado en su buzón.

## Pasos de Ejecución:

1. **Localizar Buzón**:
   - Inspecciona `.agent-inbox/{mi-nombre-de-agente}/` y localiza `<work-item-id>.md` (`FEAT-*`, `CR-*` o `BUG-*`).
   - Resuelve `<spec-dir>` (`specs/features/<work-item-id>/`, `specs/changes/<work-item-id>/` o `specs/bugs/<work-item-id>/`).
2. **🛑 Auditoría Obligatoria de Definition of Ready (DoR)**:
   - ¿Están definidos los archivos exactos a modificar o crear?
   - ¿Están detallados los campos, tipos o contratos sin ambigüedad?
   - ¿Pertenece 100% a mi ámbito permitido?
   - ¿Está claro el comando de validación?
   - ¿El `<work-item-id>` respeta `RN-SDD-IMMUTABLE-DONE` (no edita una `FEAT-*` ya cerrada en `Done`)?
   - *Si alguna respuesta es NO*: Detente de inmediato y genera `BLOCKED_DOR_{work-item-id}.md` en tu buzón.
3. **Implementación en Aislamiento**:
   - Si existe un worktree activo asignado en `.agents/active_work_item.json`, opera dentro de `.worktrees/<slug>/`.
   - Codifica exclusivamente dentro de tu ámbito permitido en el Ownership Map.
4. **Validación Automática de Definition of Done (DoD)**: Ejecuta el comando de validación asignado a tu rol.
5. **Comprobación de Incongruencias**: Si surge una contradicción no resoluble, genera `BLOCKED_{work-item-id}.md` y detén la ejecución.
6. **Cierre de Tarea**: Marca con `[x]` las tareas completadas en `<spec-dir>/03-tasks.md`, elimina el ticket del buzón y reporta éxito a `@orchestrator`.
