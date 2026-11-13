---
description: Ejecuta el pipeline desatendido completo de una Feature (FEAT-XXX) o Change Request (CR-XXX) aprobada a través de los agentes especialistas, culminando en la auditoría holística de regresión.
---

# Workflow: `/pipeline-run` (Migrado a `.agents/skills/pipeline-run/SKILL.md`)

Ejecuta el ciclo de vida de desarrollo de forma totalmente autónoma y desatendida para una **Feature** (`specs/features/FEAT-XXX-*`) o **Change Request** (`specs/changes/CR-XXX-*`) aprobada, delegando sucesivamente entre los agentes especialistas y culminando en la verificación de regresión global.

## Parámetros Esperados
- `$ARGUMENTS`: `<work-item-id>` (ej. `FEAT-001-scaffolding` o `CR-004-avatar-engine-dual-representation`)

## Verificación Previa de Gobernanza (Obligatoria)
1. Resolver carpeta `<spec-dir>`:
   - `FEAT-*` $\rightarrow$ `specs/features/<work-item-id>/`
   - `CR-*` $\rightarrow$ `specs/changes/<work-item-id>/`
   - `BUG-*` $\rightarrow$ `specs/bugs/<work-item-id>/`
2. Si `<work-item-id>` es una `FEAT-*` que ya figura como `Done` en `specs/BACKLOG.md`, **ABORTAR INMEDIATAMENTE** (`RN-SDD-IMMUTABLE-DONE`) y exigir un `CR-XXX` en `specs/changes/`.

---

## Bloques de Ejecución en Cascada (DAG)

`@orchestrator` orquestará los bloques técnicos y tareas de manera secuencial leyendo `<spec-dir>/03-tasks.md`:

1. `db-specialist`: DDL, índices y seeds en `DDBB/scripts`
2. `back-domain`: Entidades, Dominio y Casos de Uso
3. `back-infra`: Repositorios, MCP y Runners
4. `back-api`: Endpoints REST, WebSockets y DTOs
5. `audio-voice`: Adaptadores TTS y Web Audio API
6. `back-test`: pytest tests unitarios e integración
7. `front-logic`: Types espejo, TanStack Query, Zustand y Adaptadores
8. `front-ui`: Componentes UI, 3D Canvas, `@paco/avatar-engine`
9. `front-test`: Vitest, RTL, Typecheck, Linter
10. `devops`: Docker Compose, Despliegue, Healthchecks
11. `documentator`: Documentación viva y guías en `docs/`
12. `Full Regression`: Auditoría Global DoD y actualización de estado en `specs/BACKLOG.md`
