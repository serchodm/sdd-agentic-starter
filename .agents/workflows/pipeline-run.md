---
description: Ejecuta el pipeline SDD completo de una FEAT-XXX o CR-XXX aprobada por bloques DAG (ver skill pipeline-run).
---

# Workflow `/pipeline-run` -> `.agents/skills/pipeline-run/SKILL.md`

- **Parámetros:** `$ARGUMENTS` = `<work-item-id>` (ej. `FEAT-001-scaffolding` o `CR-002-checkout-flow`).
- **Ejecución:** Sigue `.agents/skills/pipeline-run/SKILL.md`: verifica `RN-SDD-GATE2-CODE-LOCK` y `RN-SDD-IMMUTABLE-DONE`, orquesta por bloques DAG los roles activos en `specs/STACK.md` (sin escribir código directo), ejecuta las 3 auditorías QA + `sdd_healthcheck.py` + `verify_architecture_boundaries.py` y cierra en Gate 5 con `@documentator`.
