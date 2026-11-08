---
description: Delega una tarea específica de una Feature (FEAT-XXX), Change Request (CR-XXX) o Bug (BUG-XXX) a un agente especialista escribiendo en su buzón de .agent-inbox/ cumpliendo con Definition of Ready (DoR).
---

# Workflow: `/opsx-delegate` (Migrado a `.agents/skills/opsx-delegate/SKILL.md`)

Este comando es utilizado por `@orchestrator` (Tech Lead) para preparar y depositar una orden de trabajo en el buzón de un agente especialista del proyecto.

## Parámetros Esperados
- `$ARGUMENTS`: `<agente> <work-item-id>` (ej. `/opsx-delegate front-ui CR-004-avatar-engine-dual-representation` o `/opsx-delegate back-domain FEAT-001-scaffolding`)

## Pasos de Ejecución:

1. **Validar existencia de especificaciones e inmutabilidad**:
   - Resolver `<spec-dir>`: `specs/features/<work-item-id>/` (`FEAT-*`), `specs/changes/<work-item-id>/` (`CR-*`), o `specs/bugs/<work-item-id>/` (`BUG-*`).
   - Comprobar que existen `<spec-dir>/01-spec.md`, `02-tech-spec.md` y `03-tasks.md`.
   - Verificar que si es `FEAT-*`, NO esté en estado `Done` en `specs/BACKLOG.md` (`RN-SDD-IMMUTABLE-DONE`).
2. **Filtrar tareas del especialista** en `<spec-dir>/03-tasks.md` (`- [ ]`).
3. **Garantizar Definition of Ready (DoR) en el Ticket**.
4. **Generar Ticket en Buzón** `.agent-inbox/<agente>/<work-item-id>.md`.
5. **Confirmación**: Notificar que el ticket está listo para ser recogido por el especialista.
