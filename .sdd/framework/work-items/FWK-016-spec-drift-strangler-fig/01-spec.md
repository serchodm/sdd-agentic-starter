# Spec Funcional: Detector de *Spec Drift* (`sdd drift`), Zonas *Strangler Fig* y Baseline Retroactiva Ligera (`FWK-016`)

- **ID:** `FWK-016-spec-drift-strangler-fig`
- **RFC:** [`RFC-008`](../../rfcs/RFC-008-brownfield-adoption-and-spec-drift.md) (`Aceptado`)
- **Depende de:** `FWK-015` (`Done`)
- **Estado:** `Approved`
- **Gate 1 Sign-off:** `[x] Gate 1 Approved (Human Sign-off)` *(Aprobado explícitamente por el usuario en chat)*

## 1. Resumen y Alcance
Completar la hoja de ruta `v1.3.0` de [`RFC-008`](../../rfcs/RFC-008-brownfield-adoption-and-spec-drift.md) incorporando el soporte incremental *Strangler Fig*, la validación de baselines retroactivas minadas (`origin: brownfield-mined`) y el detector determinista offline de deriva entre código y especificaciones (`scripts/sdd_drift.py`, expuesto vía `./sdd drift` y conectado en `sdd ci-verify`).

- **Fuentes de Verdad (`SRC-###`):**
  - `SRC-001`: [`RFC-008`](../../rfcs/RFC-008-brownfield-adoption-and-spec-drift.md) §1.3, §1.4, §2.2, §2.3, §3 (`FWK-016`).
  - `SRC-002`: `scripts/sdd_ownership.py` (`OwnershipZone`, `OwnershipMapConfig`, `DEFAULT_CANDIDATE_ROOTS`, `parse_ownership_map`, `validate_repo_coverage`) y `.agents/scripts/sdd_code_gate_guard.py` (`is_protected_code_path`, `main`).
  - `SRC-003`: `.agents/scripts/sdd_healthcheck.py` (`check_spec_triads`) y `scripts/sdd_gate_seal.py` (`verify_work_item_gate_seals`, `seal_work_item_gates`).
  - `SRC-004`: `.agents/scripts/sdd_repo_map.py` (`collect_source_files`, `EXTENSION_PARSERS`), `scripts/sdd_ci.py` (`run_ci_verify`) y `scripts/sdd_cli.py` (`DISPATCH_MAP`).
- **In-Scope:**
  - Extensión de `yaml sdd:ownership-map` en `scripts/sdd_ownership.py` para soportar raíces de código personalizadas/brownfield y zonas *Strangler Fig* con propiedad `governance` (`governed` por defecto vs `legacy-readonly`).
  - Refuerzo *fail-closed* de `.agents/scripts/sdd_code_gate_guard.py` para proteger rutas declaradas en `sdd:ownership-map` (y raíces brownfield habituales) y bloquear ediciones en zonas `legacy-readonly`.
  - Soporte controlado de **Baseline Retroactiva Ligera** (`origin: brownfield-mined`: `01-spec.md` + `02-tech-spec.md` *as-built*, eximiendo `03-tasks.md` únicamente tras firma humana en Gate 1 y Gate 2) en `.agents/scripts/sdd_healthcheck.py` y `scripts/sdd_gate_seal.py`.
  - Motor determinista offline `scripts/sdd_drift.py` (stdlib-only, `<= 500L`), subcomando `drift` en `scripts/sdd_cli.py`, integración condicional en `scripts/sdd_ci.py` (`check_spec_drift`) y suite offline `tests/test_sdd_drift.py`.
- **Out-of-Scope:**
  - Auto-edición o refactorización automática del código fuente en zonas `legacy-readonly` o corrección automática de *Spec Drift*.
  - Auto-aprobación de `Gate S0` o `Gate 1..3` (`RN-SDD-HUMAN-GATE-OWNERSHIP`).

## 2. Requisitos (EARS)
- `RF-1601` (**Zonas *Strangler Fig* y raíces personalizadas en `sdd:ownership-map` y guardias**): `scripts/sdd_ownership.py` deberá admitir el atributo opcional `governance` (`governed` por defecto o `legacy-readonly`) en las zonas de `yaml sdd:ownership-map` y derivar raíces candidatas personalizadas desde `zone.paths` para `validate_repo_coverage`; CUANDO un agente intente escribir o editar un fichero bajo una ruta protegida (incluidas raíces declaradas en `sdd:ownership-map`), `.agents/scripts/sdd_code_gate_guard.py` deberá aplicar `RN-SDD-GATE2-CODE-LOCK` de forma *fail-closed* y, SI el fichero pertenece a una zona `legacy-readonly`, ENTONCES deberá denegar la modificación bloqueando ediciones directas sobre código legado congelado.
- `RF-1602` (**Baseline Retroactiva Ligera `origin: brownfield-mined`**): CUANDO una feature `FEAT-XXX` contenga el marcador estructurado `Origin: brownfield-mined` (o `Origen: brownfield-mined`) en `01-spec.md` fuera de comentarios HTML o bloques de código, `.agents/scripts/sdd_healthcheck.py` y `scripts/sdd_gate_seal.py` deberán validar y sellar `01-spec.md` y `02-tech-spec.md` (*as-built*) eximiendo `03-tasks.md` únicamente SI ambos documentos existen, tienen contenido sustantivo y exhiben `[x] Gate 1 Approved` y `[x] Gate 2 Approved` válidos; SI falta `03-tasks.md` sin marcador `brownfield-mined` válido o sin ambos sign-offs humanos, ENTONCES ambos scripts deberán fallar en modo *fail-closed*.
- `RF-1603` (**Detector determinista offline de *Spec Drift* `scripts/sdd_drift.py`**): CUANDO se ejecute `scripts/sdd_drift.py` (o `./sdd drift`), el sistema deberá cruzar de forma determinista y 100% offline las citas `SRC-###` (`path::symbol` y `<sha>` opcional) de `specs/features/FEAT-*/01-spec.md` y `docs/traceability/TRACEABILITY-MATRIX.md` contra el mapa AST de `.agents/scripts/sdd_repo_map.py`, las zonas `governed` de `sdd:ownership-map` y `git diff`/`git status` para detectar: (a) ficheros en zonas `governed` sin cobertura `FEAT-XXX`, (b) ficheros o símbolos `SRC-###` desaparecidos o renombrados sin `CR-XXX` vinculado, y (c) modificaciones sobre ficheros vinculados a features `Done` / baseline sin `CR-XXX`, `BUG-XXX` o `HOTFIX-XXX` vinculado, emitiendo salida `text` o `json` y fallando con código `!= 0` ante hallazgos `error` (o cualquier hallazgo bajo `--strict`).
- `RF-1604` (**Integración CLI `sdd drift`, CI `sdd_ci.py` y límites de modularidad**): `scripts/sdd_cli.py` deberá registrar `drift` en `DISPATCH_MAP` y `print_help()`, y `scripts/sdd_ci.py` deberá ejecutar `check_spec_drift` en modo `project` (omitiéndolo limpiamente como `SKIPPED_NO_APPLICABLE` en modo `framework`), manteniendo todos los `.py` bajo `scripts/`, `.agents/scripts/` y `tests/` en `<= 500` líneas y el presupuesto activo de `.agents/` por debajo de `25k` tokens.

## 3. Criterios de Aceptación (BDD / Given-When-Then)
1. **Escenario `CA-1601` (Zonas *Strangler Fig* `governed` vs `legacy-readonly` y raíces brownfield):**
   - **Dado** un repositorio con `specs/STACK.md` (`Gate S0` aprobado) declarando una zona `legacy-billing` (`paths: ["app/legacy/**"]`, `governance: legacy-readonly`) y una zona `new-billing` (`paths: ["app/billing/**"]`, `governance: governed`), junto con un work item activo aprobado (`Gate 1..3`)
   - **Cuando** se valida cobertura con `sdd_ownership.py` y se evalúa `.agents/scripts/sdd_code_gate_guard.py` sobre `app/legacy/invoice.py` y `app/billing/service.py`
   - **Entonces** `sdd_ownership.py` valida la cobertura de las raíces `app/legacy` y `app/billing` sin errores, el guard deniega la edición de `app/legacy/invoice.py` por pertenecer a `legacy-readonly`, y permite la edición de `app/billing/service.py` bajo el work item aprobado.
2. **Escenario `CA-1602` (Baseline retroactiva ligera `brownfield-mined` con sign-off obligatorio):**
   - **Dado** una feature `specs/features/FEAT-001-auth/` marcada `Done` con `01-spec.md` (`Origin: brownfield-mined`, `[x] Gate 1 Approved`) y `02-tech-spec.md` (`[x] Gate 2 Approved`) sin `03-tasks.md`, y otra feature normal `FEAT-002-orders` en `Done` sin `03-tasks.md`
   - **Cuando** se ejecutan `check_spec_triads` (`sdd_healthcheck.py`) y `verify_work_item_gate_seals` (`sdd_gate_seal.py`)
   - **Entonces** `FEAT-001-auth` pasa las validaciones y sellado de Gates 1..2 sin requerir `03-tasks.md`, mientras `FEAT-002-orders` (o una feature `brownfield-mined` sin `[x] Gate 2 Approved`) falla de forma *fail-closed*.
3. **Escenario `CA-1603` (Detección de cobertura, símbolos `SRC-###` desaparecidos y cambios sin `CR-XXX`):**
   - **Dado** un repositorio Git temporal con `FEAT-001-orders` (`Done`) citando `SRC-001` (`app/orders/service.py::create_order`) y una zona `governed` (`app/orders/**`)
   - **Cuando** (a) se añade `app/orders/orphan.py` sin cita en ninguna `FEAT-*`, (b) se renombra `create_order` a `submit_order` sin `CR-XXX`, o (c) se modifica `app/orders/service.py` sin `CR-XXX`/`BUG-XXX`/`HOTFIX-XXX`
   - **Entonces** `scripts/sdd_cli.py drift --repo-root <repo> --format json` reporta los hallazgos exactos (`UNCOVERED_FILE`, `MISSING_SYMBOL`, `UNLINKED_CODE_DRIFT`), retorna código `!= 0` ante errores (y bajo `--strict` ante `UNCOVERED_FILE`), retorna `0` cuando los cambios están respaldados por un `CR-XXX` vinculado (y no genera falsos positivos en futuras features una vez cerrado dicho `CR-XXX` como `Done` con sus citas actualizadas, aunque sí detectará un cambio posterior sin nuevo `CR-XXX`).
4. **Escenario `CA-1604` (Integración en `sdd_ci.py`, presupuesto `< 25k` y techo `<= 500L`):**
   - **Dado** la implementación completa de `FWK-016`
   - **Cuando** se ejecuta `sdd ci-verify --mode framework --format json` y la verificación en un proyecto temporal con drift
   - **Entonces** en modo `framework` el check `spec_drift` devuelve `SKIPPED_NO_APPLICABLE` sin falsos fallos, en modo `project` con deriva devuelve `FAIL`, todos los `.py` del framework cumplen `<= 500` líneas, `.agents/` se mantiene `< 25k` tokens y la suite completa `unittest` pasa 100% offline.

## 4. Aprobación Formal Gate 1 (`RN-SDD-HUMAN-GATE-OWNERSHIP`)
- [x] **Gate 1 Approved (Human Sign-off):** Revisado y validado por Stakeholder Humano.
