# Plantilla Fast-Track de Bug (`BUG-XXX`)

> **Uso obligatorio:** Copiar las tres secciones siguientes en `specs/bugs/BUG-XXX-<slug>/` como `01-bug-report.md`, `02-fix-spec.md` y `03-tasks.md`. Los tres archivos deben existir sin estar vacíos para superar `.agents/scripts/sdd_healthcheck.py`, y conservar sus checkboxes `[x] Gate N Approved` (tras aprobación humana) para superar `.agents/scripts/sdd_code_gate_guard.py`.
>
> **Estados válidos:**
> - En `specs/BACKLOG.md`: `Candidate` | `Backlog` | `In Progress` | `In Review` | `Done` | `Blocked`
> - Estado del documento: `Draft` | `In Review` | `Approved` | `Done`

---

## 1. Plantilla `01-bug-report.md` (Gate 1)

~~~~markdown
# BUG-XXX: <Título corto y descriptivo del defecto>

- **ID:** BUG-XXX
- **Módulo / Dominio afectado:** `<dominio-o-modulo>`
- **Severidad:** `S1 (Crítico)` | `S2 (Alto)` | `S3 (Medio)` | `S4 (Bajo)`
- **Estado del Documento:** `Draft`
- **Entorno / Versión / Commit:** `<branch / entorno / commit>`
- **Work Item relacionado:** `FEAT-XXX` | `CR-XXX` | `N/A`

## 1. Síntoma y Pasos de Reproducción
1. **Precondiciones:** `<estado inicial, usuario, datos o configuración>`
2. **Pasos:**
   1. `<Paso 1>`
   2. `<Paso 2>`
3. **Resultado observado:** `<error exacto, stacktrace, código HTTP o comportamiento incorrecto>`
4. **Resultado esperado:** `<comportamiento correcto según especificación existente>`
5. **Evidencia / Logs:** `<referencia a log, test fallido o captura sin secretos>`

## 2. Análisis de Impacto y Criterio Fast-Track
- **Affected Domains:** `<domains/dom-a/>` (indicar si existe `overview.md`)
- **Affected Specs:** `<FEAT-XXX / CR-XXX o Ninguna>`
- **Unchanged Behavior:** `<qué contratos o flujos adyacentes NO deben cambiar>`
- **Confirmación de alcance:** No introduce requisitos funcionales nuevos ni rompe contratos de features `Done`; en caso contrario, escalar a `FEAT-XXX` o `CR-XXX`.

## 3. Aprobación Gate 1
- [ ] **Gate 1 Approved (Human Sign-off):** Bug reproducido, severidad confirmada, impacto acotado y elegible para `/bug-fast-track`.
~~~~

---

## 2. Plantilla `02-fix-spec.md` (Gate 2)

~~~~markdown
# Spec de Corrección — BUG-XXX: <Título corto>

- **ID:** BUG-XXX
- **Estado del Documento:** `Draft`
- **Dominio:** `<domains/dominio/>`
- **Requiere Sub-Gate 2V (UI):** `No (N/A)` | `Sí`

## 1. Causa Raíz Verificada
- **Ubicación exacta:** `<ruta/al/archivo.ext>:<líneas>` (`<Símbolo / Función / Clase>`)
- **Mecanismo de fallo:** `<explicación técnica precisa y verificada del porqué ocurre el bug>`
- **Por qué no saltó antes:** `<hueco en validación, edge case o ausencia de cobertura>`

## 2. Diseño del Fix Mínimo
- **Archivos autorizados a modificar (`ALLOWED_FILES`):**
  - `<ruta/al/modulo>`
  - `<ruta/al/test_de_regresion>`
- **Cambio técnico propuesto:**
  - `<descripción concreta del cambio, validación fail-closed y preservación de invariantes>`
- **Riesgos / Seguridad / Migración:**
  - `<confirmar que no introduce fallbacks silenciosos, secretos ni regresiones de autorización>`

## 3. Estrategia Test-First (Red -> Fix -> Green)
- **Test de reproducción (Red):** `<nombre del test unitario/integración que falla antes del fix>`
- **Criterio de aceptación (Green):** `<aserción exacta que pasa tras el fix sin relajar aserciones>`
- **Regresión mínima:** `<suite o módulo acotado a verificar>`

## 4. Aprobación Gate 2
- [ ] **Gate 2 Approved (Human Sign-off):** Causa raíz verificada, alcance mínimo del fix y estrategia Test-First aprobados.
- [ ] **Gate 2 Visual Sign-off (Human):** N/A (sin cambios de UI) o evidencia visual aprobada.
~~~~

---

## 3. Plantilla `03-tasks.md` (Gate 3)

~~~~markdown
# Tareas de Ejecución — BUG-XXX: <Título corto>

- **ID:** BUG-XXX
- **Estado del Documento:** `Draft`
- **Rama objetivo:** `fix/BUG-XXX-<slug>`

## Plan DAG Atómico

### T1 — Test de reproducción que falla (Red)
- **Agente asignado:** `@qa-tester` (o especialista designado en `specs/STACK.md`)
- **Dependencias:** `Ninguna`
- **ALLOWED_FILES:** `<ruta/al/test_de_regresion>`
- **Descripción:** Añadir test reproducible que demuestre el defecto descrito en `01-bug-report.md` y falle antes de aplicar el fix.
- *Comando de verificación DoD*: `uv run python -m unittest <modulo_test> -v` (confirmar fallo esperado Red)

### T2 — Implementación del fix mínimo (Green)
- **Agente asignado:** `@back-engineer` | `@front-engineer` (según Ownership Map de `specs/STACK.md`)
- **Dependencias:** `T1`
- **ALLOWED_FILES:** `<ruta/al/modulo>`
- **Descripción:** Aplicar la corrección especificada en `02-fix-spec.md` respetando fail-closed engineering y techo de modularidad.
- *Comando de verificación DoD*: `uv run python -m unittest <modulo_test> -v` (confirmar pase Green)

### T3 — Verificación integral y cierre SDD
- **Agente asignado:** `@qa-tester` + `@documentator`
- **Dependencias:** `T2`
- **ALLOWED_FILES:** `docs/traceability/TRACEABILITY-MATRIX.md`, `specs/BACKLOG.md`, `domains/<dominio>/` (si aplica)
- **Descripción:** Verificar límites arquitectónicos, healthcheck del framework, regresión acotada y cierre 0DD ligero.
- *Comando de verificación DoD*: `uv run python .agents/scripts/sdd_healthcheck.py && uv run python .agents/scripts/verify_architecture_boundaries.py`

## Aprobación Gate 3
- [ ] **Gate 3 Approved (Human Sign-off):** Plan de tareas Test-First, `ALLOWED_FILES` y comandos DoD aprobados para implementación.
~~~~
