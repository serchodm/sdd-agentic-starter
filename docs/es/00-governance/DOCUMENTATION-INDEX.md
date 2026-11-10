<p align="right">
  <a href="../../en/00-governance/DOCUMENTATION-INDEX.md">🇬🇧 English (EN-GB)</a> | <strong>🇪🇸 Español (ES-ES)</strong>
</p>

# Índice de Documentación Funcional (`00-governance`)

## Información del Producto
- **Producto:** `sdd-agentic-starter` (Plantilla Agéntica bajo Spec-Driven Development)
- **Descripción breve:** Plantilla multi-stack gobernada por puertas SDD (Gate 00 a Gate 5), con catálogo inerte de arquetipos, especialistas universales y packs de tecnología activables de forma determinista y *fail-closed*.
- **Versión / Baseline funcional vigente:** `FWK-001` (`RFC-001` v2 — Materialización y Activación Fiables de Packs)
- **Estado global:** `Verified` (para `FWK-001`); aplicación de usuario pendiente de Gate 00
- **Responsable funcional:** `@documentator` (supervisado por `@orchestrator`)

---

## Cómo Utilizar Esta Documentación

1. Esta documentación sigue la norma modular de [`FUNCTIONAL_DOCUMENTATION_STANDARD.md`](../../standards/FUNCTIONAL_DOCUMENTATION_STANDARD.md): únicamente contiene los artefactos con contenido real confirmado; no se crean carpetas vacías ni plantillas sin respaldo.
2. Cada documento distingue explícitamente entre hechos **Confirmados** (respaldados por especificaciones aprobadas y verificados mediante pruebas) y alcance futuro **Excluido / Diferido** (`FWK-002`, `FWK-003`, `FWK-004` y features del proyecto tras Gate 00).
3. Toda la literatura funcional mantiene equivalencia **1:1** entre [`docs/es/`](../README.md) y [`docs/en/`](../../en/README.md).

---

## 1. Funcionalidad (`02-functional`)
- [**`MOD-001`: Materialización y Activación Fiables de Packs**](../02-functional/modules/MOD-001/pack-materialization.md) (`Verified` — cubre `RF-001`..`RF-010`, `RN-01`..`RN-05`, flujos operativos y criterios de aceptación BDD 1–7).

## 2. Trazabilidad y Conocimiento Técnico (`06-traceability` / `knowledge`)
- [**Matriz de Trazabilidad Bidireccional (0DD)**](../../traceability/TRACEABILITY-MATRIX.md)
- [**Registro de Decisiones de Arquitectura (`ADRS.md`)**](../../knowledge/ADRS.md) *(incluye `ADR-001` y `ADR-002`)*
- [**Topología del Sistema (`SYSTEM_TOPOLOGY.md`)**](../../knowledge/SYSTEM_TOPOLOGY.md)
- [**Modelos de Datos (`DATA_MODELS.md`)**](../../knowledge/DATA_MODELS.md)
- [**Catálogo de Interfaces y CLI (`API_CATALOG.md`)**](../../knowledge/API_CATALOG.md)

---

## Estado y Riesgos

| Aspecto | Situación Actual (Confirmada) |
| :--- | :--- |
| **Artefactos aprobados y verificados** | `MOD-001` (`FWK-001`: `RF-001`..`RF-010`, `RN-01`..`RN-05`, Escenarios BDD 1–7). |
| **Decisiones abiertas** | Ninguna en `FWK-001` (`AMB-001`..`AMB-004` resueltas en Gate 1). |
| **Riesgos mitigados en esta baseline** | Activación accidental por prosa (`RN-01`), contaminación de reglas globales *always-on* (`ADR-002`), sobrescritura de skills artesanales como `fastapi-patterns`/`postgres-patterns` (`AMB-002`), pérdida de ediciones manuales (`RN-03`) y borrado de packs externos (`RN-05`). |
| **Próximos pasos (fuera de esta baseline)** | `FWK-002` (pack `capability-ui-design`), `FWK-003` (quality gates visuales), `FWK-004` (unificación terminológica de Gates) y Gate 00 del proyecto usuario en `specs/STACK.md`. |
