<p align="right">
  <a href="../../en/00-governance/DOCUMENTATION-INDEX.md">🇬🇧 English (EN-GB)</a> | <strong>🇪🇸 Español (ES-ES)</strong>
</p>

# Índice de Documentación Funcional (`00-governance`)

## Información del Producto
- **Producto:** `sdd-agentic-starter` (Plantilla Agéntica bajo Spec-Driven Development)
- **Descripción breve:** Plantilla multi-stack gobernada por puertas SDD (Gate 00 a Gate 5), con catálogo inerte de arquetipos, especialistas universales y packs de tecnología activables de forma determinista y *fail-closed*, incluyendo gobernanza UI/UX offline (`capability-ui-design`).
- **Versión / Baseline funcional vigente:** `FWK-001` + `FWK-002` (`RFC-001` v2 — Materialización Fiable de Packs y Pack `capability-ui-design`)
- **Estado global:** `Verified` (para `FWK-001` y `FWK-002`); aplicación de usuario pendiente de Gate 00
- **Responsable funcional:** `@documentator` (supervisado por `@orchestrator`)

---

## Cómo Utilizar Esta Documentación

1. Esta documentación sigue la norma modular de [`FUNCTIONAL_DOCUMENTATION_STANDARD.md`](../../standards/FUNCTIONAL_DOCUMENTATION_STANDARD.md): únicamente contiene los artefactos con contenido real confirmado; no se crean carpetas vacías (como `docs/design-system/` en el starter) ni plantillas sin respaldo.
2. Cada documento distingue explícitamente entre hechos **Confirmados** (respaldados por especificaciones aprobadas y verificados mediante pruebas) y alcance futuro **Excluido / Diferido** (`FWK-003`, `FWK-004` y features del proyecto tras Gate 00).
3. Toda la literatura funcional mantiene equivalencia **1:1** entre [`docs/es/`](../README.md) y [`docs/en/`](../../en/README.md).

---

## 1. Funcionalidad (`02-functional`)
- [**`MOD-001`: Materialización y Activación Fiables de Packs**](../02-functional/modules/MOD-001/pack-materialization.md) (`Verified` — cubre `FWK-001`: `RF-001`..`RF-010`, `RN-01`..`RN-05`, flujos operativos y criterios de aceptación BDD 1–7).
- [**`MOD-002`: Pack `capability-ui-design` y Gobernanza Visual SDD**](../02-functional/modules/MOD-002/capability-ui-design.md) (`Verified` — cubre `FWK-002`: `RF-001`..`RF-012`, `RN-01`..`RN-07`, `REL-VENDOR-INTEGRITY-01`, `PERF-FWK-TESTS-01`, flujos Gate 2 / semver y criterios BDD 1–7).

## 2. Trazabilidad y Conocimiento Técnico (`06-traceability` / `knowledge`)
- [**Matriz de Trazabilidad Bidireccional (0DD)**](../../traceability/TRACEABILITY-MATRIX.md)
- [**Registro de Decisiones de Arquitectura (`ADRS.md`)**](../../knowledge/ADRS.md) *(incluye `ADR-001`, `ADR-002` y `ADR-003`)*
- [**Topología del Sistema (`SYSTEM_TOPOLOGY.md`)**](../../knowledge/SYSTEM_TOPOLOGY.md)
- [**Modelos de Datos (`DATA_MODELS.md`)**](../../knowledge/DATA_MODELS.md)
- [**Catálogo de Interfaces y CLI (`API_CATALOG.md`)**](../../knowledge/API_CATALOG.md)

---

## Estado y Riesgos

| Aspecto | Situación Actual (Confirmada) |
| :--- | :--- |
| **Artefactos aprobados y verificados** | `MOD-001` (`FWK-001`) y `MOD-002` (`FWK-002`: `RF-001`..`RF-012`, `RN-01`..`RN-07`, Escenarios BDD 1–7; `37` tests offline en `tests/`). |
| **Decisiones abiertas** | Ninguna en `FWK-001` ni en `FWK-002` (`AMB-001`..`AMB-007` resueltas en Gate 1; `<PIN_APROBADO> = "2.15.0"` validado tras Spike PoC en Gate 2). |
| **Riesgos mitigados en esta baseline** | Activación accidental por prosa (`FWK-001` `RN-01`), contaminación *always-on* (`ADR-002`), sobrescritura de skills artesanales, pérdida de ediciones manuales, colisión ECC `design-system` / ejecución `npx` en diseño (`ADR-003`), corrupción SHA-256 en Windows (`VENDOR.lock.json` + `.gitattributes`), hi-fi sin Gate 1 (`RN-04`) y ruptura de `RN-SDD-IMMUTABLE-DONE` (`RN-07`). |
| **Próximos pasos (fuera de esta baseline)** | `FWK-003` (quality gates visuales), `FWK-004` (unificación terminológica de Gates) y Gate 00 del proyecto usuario en `specs/STACK.md`. |
