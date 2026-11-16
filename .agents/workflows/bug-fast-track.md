---
description: Flujo fast-track para bugs e incidentes acotados (BUG-XXX) manteniendo triada documental, Gate S0 y firmas humanas Gate 1/2/3.
---

# Workflow `/bug-fast-track` — Resolución Ágil de Bugs (`BUG-XXX`)

Flujo optimizado de Spec-Driven Development para defectos reproducibles e incidentes acotados sin sacrificar trazabilidad, seguridad *fail-closed* ni aprobación humana.

---

## 1. Criterios de Elegibilidad y Escalado (*Fail-Closed*)

Usa `/bug-fast-track` (`specs/bugs/BUG-XXX-<slug>/`) **únicamente** cuando se cumplan todas estas condiciones:
1. El comportamiento esperado ya existía o está definido y hay una desviación reproducible (defecto funcional, regresión, validación o error de borde).
2. El cambio afecta a un único dominio o módulo acotado, sin alterar contratos públicos cross-feature ni introducir capacidades nuevas.
3. No requiere decisiones arquitectónicas mayores ni cambios destructivos de esquema de datos.

**Escalado obligatorio (Detener y redirigir si no cumple):**
- Requiere nueva funcionalidad o requisito de negocio nuevo -> crear `FEAT-XXX` en `specs/features/`.
- Evoluciona, rediseña o cambia el contrato de una feature ya `Done` (`RN-SDD-IMMUTABLE-DONE`) -> crear `CR-XXX` en `specs/changes/` (ver `.agents/skills/sdd-change-gate/SKILL.md`).
- Incidente crítico en producción fuera de ciclo normal -> aplicar protocolo de Hotfix (`specs/SDD_FRAMEWORK.md` §8.5) registrando igualmente la triada antes de cerrar.

---

## 2. Invariantes No Negociables

- **Gate S0 obligatorio (`RN-SDD-GATE-S0-STACK-LOCK`)**: `specs/STACK.md` debe tener `[x] Gate S0 Approved` (o alias legacy `Gate 00`) antes de tocar código en `src/`.
- **SSOT único en `specs/BACKLOG.md`**: Todo `BUG-XXX` y su estado (`Candidate` | `Backlog` | `In Progress` | `In Review` | `Done` | `Blocked`) se gestionan exclusivamente en `specs/BACKLOG.md` (sección `Historial de Bugs (BUG)`). Prohibido crear contadores paralelos o archivos de estado manuales.
- **Triada completa verificable**: Toda carpeta `specs/bugs/BUG-XXX-<slug>/` debe contener los 3 documentos no vacíos (`01-bug-report.md`, `02-fix-spec.md`, `03-tasks.md`) exigidos por `.agents/scripts/sdd_healthcheck.py`.
- **Firmas humanas Gate 1 / Gate 2 / Gate 3**: `.agents/scripts/sdd_code_gate_guard.py` bloquea la edición de código si faltan `[x] Gate 1 Approved`, `[x] Gate 2 Approved` o `[x] Gate 3 Approved` en los tres archivos de la triada.
- **Portabilidad y ejecución segura**: Ejecutar los scripts del framework mediante `uv run python .agents/scripts/...` y construir rutas de forma portable (`pathlib`), sin asumir separadores fijos ni `shell=True`.

---

## 3. Ejecución Paso a Paso (Gate 0 -> Gate 5)

### Paso 1 — Triage y Registro (`Gate 0` + `Gate 1`)
1. Consultar el último `BUG-XXX` en `specs/BACKLOG.md` y asignar el siguiente identificador consecutivo (`BUG-001`, `BUG-002`, ...).
2. Registrar la entrada en `specs/BACKLOG.md` con estado inicial `Backlog` (o `Candidate` si falta reproducción) y severidad (`S1` Crítico, `S2` Alto, `S3` Medio, `S4` Bajo).
3. Cargar contexto bajo demanda: leer **solo** `domains/<dominio>/overview.md` y `domains/<dominio>/decisions.md` del dominio afectado (si existen), más la fila pertinente de `docs/knowledge/SYSTEM_TOPOLOGY.md`.
4. Crear `specs/bugs/BUG-XXX-<slug>/` usando `specs/templates/05-bug-fast-track.template.md` (`01-bug-report.md`, `02-fix-spec.md`, `03-tasks.md` inicialmente en `Draft`) y completar `01-bug-report.md` con:
   - Pasos exactos de reproducción, resultado observado vs esperado y severidad.
   - Análisis de impacto acotado: `Affected Domains`, `Affected Specs` y `Unchanged Behavior`.
5. Solicitar al usuario la revisión y aprobación de **Gate 1** (`[x] Gate 1 Approved`).

### Paso 2 — Causa Raíz y Plan Test-First (`Gate 2` + `Gate 3`)
1. Completar `02-fix-spec.md`:
   - Causa raíz verificada (archivo, símbolo y mecanismo de fallo; nunca hipótesis sin evidencia).
   - Archivos exactos a modificar dentro del Ownership Map aplicable, estrategia mínima de corrección, impacto en datos/seguridad y estado de `Sub-Gate 2V` (`N/A` si no hay cambios visuales).
   - Estrategia de prueba **Red -> Fix -> Green**.
2. Completar `03-tasks.md` con tareas atómicas y ordenadas:
   - `T1` (`@qa-tester` o especialista según `STACK.md`): escribir test unitario/integración que reproduce el defecto y **falla (Red)**.
   - `T2` (`@back-engineer` / `@front-engineer` según ownership): implementar el fix mínimo haciendo pasar el test (**Green**), manteniendo modularidad (`<= 500` líneas objetivo en `src/`).
   - `T3`: ejecutar pruebas de regresión acotadas y validación arquitectónica.
   - Cada tarea debe incluir su campo explícito `- *Comando de verificación DoD*: <comando exacto>`.
3. Solicitar aprobación humana de **Gate 2** (`[x] Gate 2 Approved`) y **Gate 3** (`[x] Gate 3 Approved`).
   > En bugs acotados `S2..S4`, el usuario puede revisar `01`, `02` y `03` en un bloque consolidado, autorizando marcar explícitamente cada checkbox Gate 1/2/3 una vez leído el diagnóstico.

### Paso 3 — Implementación Test-First y Guardias (`Gate 4`)
1. Actualizar el estado en `specs/BACKLOG.md` a `In Progress` y activar el work item si corresponde (`uv run python scripts/sdd_cli.py work-item set BUG-XXX` o actualizar `.agents/ACTIVE_STATE.md`).
2. Ejecutar `T1` y confirmar el fallo esperado (**Red**).
3. Implementar `T2` (sin `catch` silenciosos ni fallbacks ocultos) y confirmar que `T1` pasa (**Green**).
4. Ejecutar `T3` y las verificaciones obligatorias antes de pasar a `In Review`:
   ```bash
   uv run python .agents/scripts/sdd_healthcheck.py
   uv run python .agents/scripts/verify_architecture_boundaries.py
   ```
   Además, ejecutar el comando de test acotado congelado en `specs/STACK.md` §2.5.

### Paso 4 — Cierre 0DD Ligero (`Gate 5`)
1. Actualizar `specs/BACKLOG.md` a `In Review` y delegar cierre a `@documentator` (o `/gate5` si es la única tarea final):
   - Añadir fila `BUG-XXX` en `docs/traceability/TRACEABILITY-MATRIX.md`.
   - Actualizar `domains/<dominio>/overview.md` o `decisions.md` **únicamente** si el fix reveló un invariante nuevo, una restricción legacy (`LC-##`) o una decisión local (`DOM-<dom>.D-##`).
   - Marcar `01-bug-report.md`, `02-fix-spec.md` y `03-tasks.md` con estado documental `Done`.
   - Actualizar `specs/BACKLOG.md` a `Done` incluyendo el resumen de causa raíz verificada.
2. Comitear en rama de trabajo `fix/BUG-XXX-<slug>` (`fix(BUG-XXX): ...`) y sincronizar con el remoto; nunca comitear directo en `main`.
