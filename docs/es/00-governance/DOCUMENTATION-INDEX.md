<p align="right">
  <a href="../../en/00-governance/DOCUMENTATION-INDEX.md">🇬🇧 English (EN-GB)</a> | <strong>🇪🇸 Español (ES-ES)</strong>
</p>

# Índice de Documentación Funcional (`00-governance`)

## Información del Producto
- **Producto:** `sdd-agentic-starter` (Plantilla Agéntica bajo Spec-Driven Development)
- **Descripción breve:** Plantilla multi-stack gobernada por compuertas SDD (Gate S0, Gate 0 a Gate 5), con catálogo inerte de arquetipos, especialistas universales y packs de tecnología activables de forma determinista y *fail-closed*, incluyendo gobernanza UI/UX offline (`capability-ui-design`) y orquestación unificada DAG.
- **Versión / Baseline funcional vigente:** `FWK-001` + `FWK-002` + `FWK-003` + `FWK-004` (`RFC-001` v2 y `RFC-002` — Materialización Fiable de Packs, Pack `capability-ui-design`, Quality Gates Visuales Condicionales y Unificación de Terminología de Gates)
- **Estado global:** `Verified` (para `FWK-001`, `FWK-002`, `FWK-003` y `FWK-004`); aplicación de usuario pendiente de Gate S0
- **Responsable funcional:** `@documentator` (supervisado por `@orchestrator`)

---

## Cómo Utilizar Esta Documentación

1. Esta documentación sigue la norma modular de [`FUNCTIONAL_DOCUMENTATION_STANDARD.md`](../../standards/FUNCTIONAL_DOCUMENTATION_STANDARD.md): únicamente contiene los artefactos con contenido real confirmado; no se crean carpetas vacías (como `docs/design-system/` en el starter) ni plantillas sin respaldo.
2. Cada documento distingue explícitamente entre hechos **Confirmados** (respaldados por especificaciones aprobadas y verificados mediante pruebas) y alcance futuro **Excluido / Diferido** (features del proyecto tras Gate S0).
3. Toda la literatura funcional mantiene equivalencia **1:1** entre [`docs/es/`](../README.md) y [`docs/en/`](../../en/README.md).

---

## 1. Funcionalidad (`02-functional`)
- [**`MOD-001`: Materialización y Activación Fiables de Packs**](../02-functional/modules/MOD-001/pack-materialization.md) (`Verified` — cubre `FWK-001`: `RF-001`..`RF-010`, `RN-01`..`RN-05`, flujos operativos y criterios de aceptación BDD 1–7).
- [**`MOD-002`: Pack `capability-ui-design`, Gobernanza Visual y Quality Gates SDD**](../02-functional/modules/MOD-002/capability-ui-design.md) (`Verified` — cubre `FWK-002` y `FWK-003`: `RF-001`..`RF-012`, `RN-01`..`RN-07` de FWK-002; `RF-001`..`RF-010`, `RN-01`..`RN-05` de FWK-003, validador `sdd_tokens_validator.py`, flujos bi-nivel de Gate 4 y suite de 45 tests offline).
- [**`MOD-003`: Unificación de Terminología de Gates, Estados y Grafo DAG**](../02-functional/modules/MOD-003/gate-terminology-unification.md) (`Verified` — cubre `FWK-004`: `RF-001`..`RF-007`, canonización de `Gate S0` / `Gate 0..5`, `Block`, `Session Phase`, soporte dual-accept fail-closed en scripts/guardias y suite de 22 tests unitarios en `tests/test_sdd_terminology_unification.py`).

## 2. Trazabilidad y Conocimiento Técnico (`06-traceability` / `knowledge`)
- [**Matriz de Trazabilidad Bidireccional (0DD)**](../../traceability/TRACEABILITY-MATRIX.md)
- [**Registro de Decisiones de Arquitectura (`ADRS.md`)**](../../knowledge/ADRS.md) *(incluye `ADR-001` a `ADR-005`)*
- [**Topología del Sistema (`SYSTEM_TOPOLOGY.md`)**](../../knowledge/SYSTEM_TOPOLOGY.md)
- [**Modelos de Datos (`DATA_MODELS.md`)**](../../knowledge/DATA_MODELS.md)
- [**Catálogo de Interfaces y CLI (`API_CATALOG.md`)**](../../knowledge/API_CATALOG.md)

---

## Estado y Riesgos

| Aspecto | Situación Actual (Confirmada) |
| :--- | :--- |
| **Artefactos aprobados y verificados** | `MOD-001` (`FWK-001`), `MOD-002` (`FWK-002` y `FWK-003`) y `MOD-003` (`FWK-004`: `RF-001`..`RF-007`, `67` tests offline en `tests/`). |
| **Decisiones abiertas** | Ninguna en `FWK-001`..`FWK-004` (`RFC-001` y `RFC-002` plenamente aceptados e implementados). |
| **Riesgos mitigados en esta baseline** | Activación accidental por prosa (`FWK-001`), contaminación *always-on* (`ADR-002`), colisión ECC `design-system` / ejecución `npx` (`ADR-003`), corrupción SHA-256 en Windows, deriva de tokens y baselines visuales (`ADR-004`), colisión numérica `Gate 00` vs `Gate 0`, ambigüedad del término Fase vs Gate vs Block, divergencias de estados bilingües y plantillas CR redundantes (`ADR-005`). |
| **Próximos pasos (fuera de esta baseline)** | Gate S0 del proyecto usuario en `specs/STACK.md`. |
