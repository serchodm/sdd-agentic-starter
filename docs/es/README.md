<p align="right">
  <a href="../en/README.md">🇬🇧 English (EN-GB)</a> | <strong>🇪🇸 Español (ES-ES)</strong>
</p>

# Documentación Funcional Viva (`docs/es/`)

Bienvenido a la documentación funcional viva del repositorio **`sdd-agentic-starter`**, mantenida bajo el estándar **Zero Document Debt (0DD)** en equivalencia **1:1** entre español (ES-ES) e inglés británico (EN-GB).

---

## Baseline Activa

- **Work Item de Framework Completado:** `FWK-001` — *Materialización y Activación Fiables de Packs* (`RFC-001` v2, estado `Verified` / `Done`).
- **Aplicación de Proyecto:** Pendiente de definición tecnológica y firma humana en **Gate 00** (`specs/STACK.md`). Hasta entonces, esta documentación cubre la funcionalidad operativa del motor de materialización, activación de packs y sincronización del catálogo del starter.

---

## Mapa de Lectura

| Bloque / Recurso | Contenido | Enlace |
| :--- | :--- | :--- |
| **Índice Maestro (`00-governance`)** | Punto de entrada normativo, estado de artefactos y alcance documental vigente. | [DOCUMENTATION-INDEX.md](./00-governance/DOCUMENTATION-INDEX.md) |
| **Módulo `MOD-001` (`02-functional`)** | Guía funcional y operativa de materialización de packs (`sdd:stack-config`, Gate 00, carga perezosa, limpieza *fail-closed* e importación de catálogo). | [pack-materialization.md](./02-functional/modules/MOD-001/pack-materialization.md) |
| **Base de Conocimiento (`docs/knowledge/`)** | Decisiones de arquitectura (`ADR-001`, `ADR-002`), topología, modelos de datos y catálogo CLI/APIs. | [ADRS.md](../knowledge/ADRS.md) · [SYSTEM_TOPOLOGY.md](../knowledge/SYSTEM_TOPOLOGY.md) · [DATA_MODELS.md](../knowledge/DATA_MODELS.md) · [API_CATALOG.md](../knowledge/API_CATALOG.md) |
| **Matriz de Trazabilidad (0DD)** | Trazabilidad bidireccional desde requisitos EARS (`RF-001`..`RF-010`) y reglas (`RN-01`..`RN-05`) hasta código, pruebas offline y documentación. | [TRACEABILITY-MATRIX.md](../traceability/TRACEABILITY-MATRIX.md) |
