# Referencia `santa-method`: Rúbricas Binarias SDD por Gate

Ambos revisores reciben **exactamente la misma rúbrica** del Gate activo (`PASS` / `FAIL`).

## Rúbrica A — `PRE_GATE_2` (`01-spec.md` + `02-tech-spec.md`)

| Criterio | Condición `PASS` | Señal `FAIL` (Bloqueante) |
| :--- | :--- | :--- |
| `ears-traceability` | Todo EARS y Given-When-Then de `01-spec.md` trazado en `02-tech-spec.md`. | Requisitos omitidos, BDD sin soporte técnico o alcance inventado. |
| `internal-contract-consistency` | Entidades, DTOs, BD, endpoints y UI en `02-tech-spec.md` 100% coherentes (tipos, nulabilidad, aliases). | Contradicciones entre secciones (ej. `snake_case`/tipo API vs modelo/UI sin adaptador). |
| `zero-hallucination-stack` | Librerías, APIs, tablas y rutas existen en `specs/STACK.md`, `docs/knowledge/` o repo. | Paquetes no aprobados en `STACK.md` o APIs/rutas inventadas. |
| `error-states-and-boundaries` | Fallos de red/BD/validación/auth modelados **fail-closed** con frontera única de normalización. | Errores sin modelar, fallbacks silenciosos o contratos sin tipar (`any`/`dict` opaco). |
| `cr-scope-and-cleanup` | En `CR-XXX`, plan explícito de borrado de código obsoleto; respeta `RN-SDD-IMMUTABLE-DONE` y `1-TO-1-CR`. | Wrappers zombis sin limpieza, mutación de `FEAT-XXX` `Done` o varias features en 1 CR. |
| `upstream-spec-integrity` | `01-spec.md` sin contradicciones ni ambigüedades bloqueantes. | Defecto real en `01-spec.md` aprobado $\rightarrow$ `upstream_spec_conflicts` + escalar humano. |

## Rúbrica B — `GATE_4` (Código + Tests, tras Capa 1 Determinista en verde)

| Criterio | Condición `PASS` | Señal `FAIL` (Bloqueante) |
| :--- | :--- | :--- |
| `spec-contract-parity` | Paridad 1:1 en disco con `02-tech-spec.md` (`sdd-spec-compliance-audit`); cero `any`, `as unknown as` o `# type: ignore` injustificado. | Campos divergentes backend $\leftrightarrow$ frontend o escapes de tipado no autorizados. |
| `producing-boundary-and-cleanup` | Payloads externos normalizados en 1 frontera productora; código obsoleto de `CR-XXX` borrado. | Consumidores adivinando formatos o wrappers/imports zombis sin eliminar. |
| `fail-closed-no-silent-failures` | Cero `except: pass`, `.catch(() => {})` o fallbacks silenciosos (`sdd-silent-failure-audit`); errores observables según `01-spec.md`. | Excepciones tragadas o retornos `None`/`{}`/`[]` enmascarando fallos inesperados. |
| `test-quality-and-bdd-coverage` | Cada Given-When-Then tiene aserciones reales de comportamiento y casos límite (`sdd-test-quality-audit`). | Tests verdes tautológicos (solo mocks), `assert True` o BDD/errores sin cubrir. |
| `completeness-no-placeholders` | Todos los entregables de `03-tasks.md` implementados de extremo a extremo. | `TODO`/`FIXME` bloqueantes, `NotImplementedError`, stubs o flujos truncados. |
| `security-and-secrets` | Cumple `05-security-and-secrets.md`: cero secretos literales, validación en fronteras, anti-inyección/XSS/path traversal. | Credenciales hardcodeadas, SQL/shell/HTML inseguro o endpoints sin autorización. |

## Rúbrica C — `GATE_5` (Living Docs 0DD & Trazabilidad)

| Criterio | Condición `PASS` | Señal `FAIL` (Bloqueante) |
| :--- | :--- | :--- |
| `knowledge-code-factual-parity` | `docs/knowledge/` (`API_CATALOG`, `DATA_MODELS`, `SYSTEM_TOPOLOGY`, `ADRS`) coincide con el código real. | Endpoints, parámetros, códigos HTTP o modelos que contradicen la implementación. |
| `bilingual-semantic-parity` | `docs/es/` y `docs/en/` cubren exactamente las mismas funciones, reglas y avisos. | Actualización en un solo idioma, divergencia semántica ES $\leftrightarrow$ EN o texto truncado. |
| `traceability-matrix-completeness` | `TRACEABILITY-MATRIX.md` y `specs/BACKLOG.md` alineados con ID, specs, código y tests reales. | Work Item sin trazar, estado inconsistente o IDs cruzados. |
| `zero-hallucinated-references` | Todos los enlaces, rutas, comandos CLI y símbolos citados existen en el repositorio. | Enlaces rotos, rutas inexistentes o flags/símbolos inventados. |

## Extensiones Opcionales de Dominio (si aplica)

- **Regulado / Financiero / Compliance:** `compliance-claims` (cero promesas no respaldadas, disclaimers presentes) · `audit-trail-and-pii` (trazabilidad crítica y cero PII en logs/errores).
- **API Pública / SDK:** `backward-compatibility` (cambios *breaking* versionados con guía de migración en `02-tech-spec.md` y `docs/`).
