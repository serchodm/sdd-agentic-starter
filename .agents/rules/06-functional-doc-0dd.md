# Regla 06: Estándar Zero Document Debt (0DD) y Cierre Documental Bilingüe (Gate 5)

> **ESTÁNDAR NORMATIVO:** El código sin documentación viva es deuda técnica inmediata. Ninguna funcionalidad puede marcarse como `Done` en el backlog sin la validación y firma del `@documentator` en Gate 5.
> *(Para la norma exhaustiva de estilo y estructura, consulta [`docs/standards/FUNCTIONAL_DOCUMENTATION_STANDARD.md`](file:///c:/Projects/sdd-agentic-starter/docs/standards/FUNCTIONAL_DOCUMENTATION_STANDARD.md)).*

---

## 1. Principio Fundamental de Deuda Cero (0DD)
Ninguna Feature (`FEAT-XXX`), Change Request (`CR-XXX`) o Bug (`BUG-XXX`) se considera completada sin actualizar concurrentemente los artefactos de documentación viva antes del cierre de la compuerta.

---

## 2. Artefactos Obligatorios de Gate 5

1. **Documentación Funcional Bilingüe (`docs/es/` y `docs/en/`):**
   - Manuales y guías de usuario que describen el comportamiento del incremento en español (ES-ES) e inglés (EN-GB), sin jerga técnica innecesaria.
2. **Catálogo de APIs (`docs/knowledge/API_CATALOG.md`):**
   - Endpoints, métodos HTTP, cabeceras requeridas, contratos DTO de petición/respuesta y códigos de retorno.
3. **Modelos de Datos (`docs/knowledge/DATA_MODELS.md`):**
   - Diccionario de entidades, tipos de datos, relaciones de claves foráneas y restricciones de integridad.
4. **Topología del Sistema (`docs/knowledge/SYSTEM_TOPOLOGY.md`):**
   - Mapa de contenedores, puertos, servicios y dependencias de infraestructura.
5. **Matriz de Trazabilidad (`docs/traceability/TRACEABILITY-MATRIX.md`):**
   - Matriz biunívoca que enlaza cada Requisito EARS (`RF-###`) con su contrato técnico, sus ficheros fuente implementados y sus pruebas unitarias/integración de verificación.

---

## 3. Cierre y Sincronización Remota (`RN-SDD-BRANCH-SYNC`)
Una vez completado Gate 5 por el `@documentator`:
- La Feature pasa a estado `Done` en `specs/BACKLOG.md` y su carpeta queda convertida en **Línea Base Inmutable** (`RN-SDD-IMMUTABLE-DONE`).
- Se ejecuta la sincronización Git obligatoria en la rama de trabajo (`git add`, `git commit`, `git push origin <rama-activa>`) previa a la creación/fusión de la Pull Request hacia `develop`. Prohibido el push directo a `main`.
