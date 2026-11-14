# Regla 06: Zero Document Debt (0DD) y Cierre Bilingüe (Gate 5)

> Ninguna `FEAT-XXX`, `CR-XXX` o `BUG-XXX` pasa a `Done` sin validación de `@documentator` en Gate 5 (`RN-SDD-0DD`). Ver norma en [`docs/standards/FUNCTIONAL_DOCUMENTATION_STANDARD.md`](file:///c:/Projects/sdd-agentic-starter/docs/standards/FUNCTIONAL_DOCUMENTATION_STANDARD.md).

## 1. Artefactos Obligatorios en Gate 5
1. **Docs Funcionales Bilingües (`docs/es/` y `docs/en/`):** Comportamiento de usuario en ES-ES y EN-GB sin jerga interna.
2. **Catálogo de APIs (`docs/knowledge/API_CATALOG.md`):** Endpoints, métodos, cabeceras, DTOs y códigos.
3. **Modelos de Datos (`docs/knowledge/DATA_MODELS.md`):** Entidades, tipos, FKs e integridad.
4. **Topología (`docs/knowledge/SYSTEM_TOPOLOGY.md`):** Contenedores, puertos, servicios y dependencias.
5. **Matriz de Trazabilidad (`docs/traceability/TRACEABILITY-MATRIX.md`):** Enlace 1:1 `RF-###` $\leftrightarrow$ contrato $\leftrightarrow$ código $\leftrightarrow$ tests.

## 2. Cierre y Sync (`RN-SDD-BRANCH-SYNC`)
- Al aprobar Gate 5, la feature pasa a `Done` en `specs/BACKLOG.md` y queda inmutable (`RN-SDD-IMMUTABLE-DONE`).
- Ejecutar `git add`, `git commit` y `git push origin <rama-activa>` hacia la rama de trabajo o `develop` (prohibido push directo a `main`).
