---
name: research
description: Contexto de Exploración Pre-Spec (search-first, Gate 0) de affaan-m/ECC en solo lectura antes de diseñar arquitectura.
---

# Contexto: `research.md` (Gate 0 / Gates 1–3)

- **Foco:** Comprender topología existente, reutilizar `docs/knowledge/` y extraer invariantes antes de redactar `01-spec.md` o `02-tech-spec.md`.
- **Reglas:**
  1. Solo lectura sobre código de producción (`RN-SDD-GATE2-CODE-LOCK`).
  2. Consultar `docs/knowledge/{SYSTEM_TOPOLOGY,API_CATALOG,DATA_MODELS,ADRS}.md` antes de buscar en código (`RN-SDD-SELECTIVE-CONTEXT`).
  3. Documentar hallazgos citando ruta física y líneas exactas.
  4. Roles habituales: `@functional-analyst`, `@architect` (y especialistas opt-in de descubrimiento si se activan).
