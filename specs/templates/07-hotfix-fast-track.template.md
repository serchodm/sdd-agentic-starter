# Plantilla Fast-Track de Hotfix de Emergencia (`HOTFIX-XXX`)

> **Uso obligatorio:** Copiar las tres secciones siguientes en `specs/bugs/HOTFIX-XXX-<slug>/` como `01-bug-report.md`, `02-fix-spec.md` y `03-tasks.md` conforme a `specs/SDD_FRAMEWORK.md §8.5`. Los tres archivos deben existir sin estar vacíos para superar `.agents/scripts/sdd_healthcheck.py` y conservar sus checkboxes `[x] Gate N Approved` (tras aprobación humana) para superar `.agents/scripts/sdd_code_gate_guard.py`.
>
> **Estados válidos:**
> - En `specs/BACKLOG.md`: `Candidate` | `Backlog` | `In Progress` | `In Review` | `Done` | `Blocked`
> - Estado del documento: `Draft` | `In Review` | `Approved` | `Done`

---

## 1. Plantilla `01-bug-report.md` (Gate 1 — Reporte de Emergencia S1)

~~~~markdown
# HOTFIX-XXX: <Título corto de la incidencia crítica S1>

- **ID:** `HOTFIX-XXX`
- **Módulo / Dominio afectado:** `<dominio-o-modulo>`
- **Severidad:** `S1 (Crítico — Emergencia en Producción)`
- **Estado del Documento:** `Draft`
- **Entorno / Release / Commit en producción:** `<tag / release / commit afectado>`
- **Work Item relacionado:** `FEAT-XXX` | `CR-XXX` | `N/A`

## 1. Impacto en Producción y Reproducción Mínima
1. **Impacto operativo:** `<servicios caídos, pérdida de integridad, fallo de seguridad o bloqueo total>`
2. **Pasos mínimos de reproducción:**
   1. `<Paso 1>`
   2. `<Paso 2>`
3. **Resultado observado:** `<error exacto, código HTTP o stacktrace saneado sin secretos>`
4. **Resultado esperado:** `<comportamiento seguro y correcto según contrato vigente>`

## 2. Alcance Acotado de Emergencia
- **Affected Domains:** `<domains/dom-a/>`
- **Affected Specs:** `<FEAT-XXX / CR-XXX o Ninguna>`
- **Contención:** Parche estrictamente limitado a mitigar la incidencia S1 sin introducir requisitos funcionales nuevos ni alterar contratos adyacentes.

## 3. Aprobación Gate 1
- [ ] **Gate 1 Approved (Human Sign-off):** Incidencia S1 confirmada en producción, impacto acotado y elegible para protocolo Hotfix de emergencia (`SDD_FRAMEWORK.md §8.5`).
~~~~

---

## 2. Plantilla `02-fix-spec.md` (Gate 2 — Causa Raíz y Parche Quirúrgico Mínimo)

~~~~markdown
# Spec de Parche de Emergencia — HOTFIX-XXX: <Título corto>

- **ID:** `HOTFIX-XXX`
- **Estado del Documento:** `Draft`
- **Dominio:** `<domains/dominio/>`
- **Requiere Sub-Gate 2V (UI):** `No (N/A)` | `Sí`

## 1. Causa Raíz Verificada
- **Ubicación exacta:** `<ruta/al/archivo.ext>:<líneas>` (`<Símbolo / Función / Clase>`)
- **Mecanismo de fallo:** `<explicación técnica directa de la causa raíz verificada>`

## 2. Diseño del Parche Quirúrgico Mínimo
- **Archivos autorizados a modificar (`ALLOWED_FILES`):**
  - `<ruta/al/modulo>`
  - `<ruta/al/test_de_regresion>`
- **Parche propuesto:**
  - `<descripción mínima e indispensable del cambio con validación fail-closed>`
- **Mitigación, Seguridad y Rollback:**
  - `<confirmar ausencia de secretos o fallbacks silenciosos y detallar comando/estrategia de revert inmediato si el despliegue falla>`

## 3. Estrategia Test-First (Red -> Fix -> Green)
- **Test de reproducción (Red):** `<test unitario/integración que reproduce el fallo S1 antes del parche>`
- **Criterio de aceptación (Green):** `<aserción exacta que valida el parche sin relajar aserciones>`

## 4. Aprobación Gate 2
- [ ] **Gate 2 Approved (Human Sign-off):** Causa raíz verificada, parche quirúrgico mínimo, estrategia de rollback y plan Test-First aprobados.
- [ ] **Gate 2 Visual Sign-off (Human):** N/A (sin cambios de UI) o evidencia visual aprobada.
~~~~

---

## 3. Plantilla `03-tasks.md` (Gate 3 — Red -> Fix -> Green y Checklist Obligatorio <= 24h)

~~~~markdown
# Tareas de Ejecución — HOTFIX-XXX: <Título corto>

- **ID:** `HOTFIX-XXX`
- **Estado del Documento:** `Draft`
- **Rama objetivo:** `hotfix/HOTFIX-XXX-<slug>` (integración mediante PR hacia `main` y backport a `develop` según `RN-SDD-BRANCH-SYNC`)

## Plan DAG Atómico

### T1 — Test de reproducción que falla (Red)
- **Agente asignado:** `@qa-tester` (o especialista designado en `specs/STACK.md`)
- **Dependencias:** `Ninguna`
- **ALLOWED_FILES:** `<ruta/al/test_de_regresion>`
- **Descripción:** Añadir test mínimo reproducible del fallo S1 descrito en `01-bug-report.md` y confirmar fallo antes del parche.
- *Comando de verificación DoD*: `uv run python -m unittest <modulo_test> -v` (confirmar fallo esperado Red)

### T2 — Aplicación del parche quirúrgico mínimo (Green)
- **Agente asignado:** `@back-engineer` | `@front-engineer` (según Ownership Map de `specs/STACK.md`)
- **Dependencias:** `T1`
- **ALLOWED_FILES:** `<ruta/al/modulo>`
- **Descripción:** Aplicar exclusivamente el parche mínimo definido en `02-fix-spec.md`, preservando invariantes y comportamiento fail-closed.
- *Comando de verificación DoD*: `uv run python -m unittest <modulo_test> -v` (confirmar pase Green)

### T3 — Verificación de despliegue y PR de emergencia
- **Agente asignado:** `@qa-tester` + `@orchestrator`
- **Dependencias:** `T2`
- **ALLOWED_FILES:** `N/A (validación y PR hacia rama protegida)`
- **Descripción:** Verificar build/lint/tests críticos y abrir PR desde `hotfix/HOTFIX-XXX-<slug>` hacia `main` (sin push directo a `main`).
- *Comando de verificación DoD*: `uv run python .agents/scripts/verify_architecture_boundaries.py`

### T4 — Cierre obligatorio <= 24h post-despliegue (Regresión y 0DD)
- **Agente asignado:** `@qa-tester` + `@documentator`
- **Dependencias:** `T3`
- **ALLOWED_FILES:** `docs/traceability/TRACEABILITY-MATRIX.md`, `docs/es/`, `docs/en/`, `docs/knowledge/`, `specs/BACKLOG.md`, `<tests_de_regresion_ampliados>`
- **Descripción:** Dentro de las **24 horas posteriores** al despliegue (`SDD_FRAMEWORK.md §8.5`), completar la documentación detallada 0DD, actualizar las suites de regresión para cubrir casos de borde adyacentes y ejecutar el healthcheck completo.
- *Checklist post-despliegue <= 24h*:
  - [ ] Suite de regresión ampliada y ejecutada en verde.
  - [ ] Documentación funcional (`docs/es/`, `docs/en/`) y `docs/knowledge/*` actualizadas si aplica.
  - [ ] `docs/traceability/TRACEABILITY-MATRIX.md` y `specs/BACKLOG.md` actualizados (`Done`).
  - [ ] Backport / sincronización confirmada con `develop`.
- *Comando de verificación DoD*: `uv run python .agents/scripts/sdd_healthcheck.py && uv run python -m unittest discover -s tests -v`

## Aprobación Gate 3
- [ ] **Gate 3 Approved (Human Sign-off):** Plan de emergencia Test-First, `ALLOWED_FILES`, comandos DoD y compromiso de cierre <= 24h aprobados.
~~~~
