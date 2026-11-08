---
name: research
description: Modo de contexto de Exploración y Descubrimiento Pre-Spec (search-first, Fase 0) de affaan-m/ECC en solo lectura antes de diseñar arquitectura.
---

# Contexto Operativo: `research.md` (Modo Exploración y Arquitectura — Fase 0 / Gates 1-3)

- **Modo**: Investigación, Trazado de Flujos y Diseño de Especificaciones (`search-first`).
- **Foco Principal**: Comprender la topología existente, reutilizar capacidades de `docs/knowledge/` y extraer invariantes antes de proponer cambios en `01-spec.md` o `02-tech-spec.md`.

## Comportamiento en Modo `research`
1. **Solo Lectura sobre Código de Producción**: No modificar archivos en `backend/`, `frontend/` ni `DDBB/` mientras se investiga (`RN-SDD-GATE2-CODE-LOCK`).
2. **Consulta Prioritaria de Knowledge Base**: Empezar siempre por `docs/knowledge/SYSTEM_TOPOLOGY.md`, `API_CATALOG.md`, `DATA_MODELS.md` y `ADRS.md` (`RN-SDD-SELECTIVE-CONTEXT`).
3. **Evidencia con Enlaces Exactos**: Documentar cada hallazgo citando la ruta física y el rango de líneas correspondiente.
4. **Agentes Activos Preferentes**: `@code-explorer`, `@spec-miner`, `@code-architect`, `@functional-analyst`, `@ai-architect`.
