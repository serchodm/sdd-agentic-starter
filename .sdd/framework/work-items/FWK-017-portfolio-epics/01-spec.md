# Spec Funcional: Portfolio, Épicas (`EPIC-XXX`), Roadmap y Dependencias entre Features (`FWK-017`)

- **ID:** `FWK-017-portfolio-epics`
- **RFC:** [`RFC-009`](../../rfcs/RFC-009-portfolio-finops-multiservice.md) (`Aceptado`)
- **Estado:** `Approved`
- **Gate 1 Sign-off:** `[x] Gate 1 Approved (Authorized by PO on 2026-11-21T01:17:55+01:00 — "Perfecto")`

## 1. Resumen, Fuentes y Alcance

Materializar la capa Pre-Gate-0 descrita conceptualmente en `specs/SDD_FRAMEWORK.md §2.1` mediante un motor determinista 100% offline (`scripts/sdd_portfolio.py`, CLI `./sdd portfolio`) y una plantilla oficial fuera de `.agents/` (`specs/templates/09-epic-roadmap.template.md`), permitiendo gestionar Épicas (`EPIC-XXX`), priorización (*MoSCoW* / *RICE*), dependencias entre features (`depends_on`), detección de ciclos y cálculo de progreso/ruta crítica sin romper proyectos existentes que aún no utilicen Épicas.

### Fuentes (`SRC-###`) y Ambigüedades (`AMB-###`)
- `SRC-001`: Directriz PO (`2026-11-16` / `2026-11-21` — confirmación de los 3 bloques de `v1.4.0` / `RFC-009`, siendo `FWK-017` el Bloque 1: Épicas `EPIC-XXX`, Roadmap, grafo de dependencias entre features y priorización *MoSCoW* / *RICE*).
- `AMB-001` *(Resolved)*: Almacenamiento de Épicas y dependencias sin romper `specs/BACKLOG.md` ni el techo de `499L` en `sdd_healthcheck.py`. Resolución: las Épicas residen en `specs/epics/EPIC-XXX-<slug>.md` (basadas en `09-epic-roadmap.template.md` con bloque `yaml sdd:epic` o tabla normalizada) y/o columnas opcionales `Épica` / `Prioridad` / `Depende de` en `specs/BACKLOG.md`; toda la lógica de validación vive en `scripts/sdd_portfolio.py` (`<= 500L`).

- **In-Scope:**
  - Plantilla `specs/templates/09-epic-roadmap.template.md` (`0` bytes en `.agents/`) y actualización de estructura documental en `specs/SDD_FRAMEWORK.md §3` (`specs/epics/` y `09-epic-roadmap.template.md`).
  - Motor stdlib-only `scripts/sdd_portfolio.py` (`<= 500L`) con validación *fail-closed* de rutas (`is_link_or_junction`, `strip_win32_extended_prefix`), parser de `specs/epics/EPIC-*.md` + `specs/BACKLOG.md`, cálculo de *rollup* de progreso por Épica, prioridad (*MoSCoW* `Must`/`Should`/`Could`/`Wont` y puntuación *RICE*), orden topológico y ruta crítica entre `FEAT-XXX`.
  - Subcomandos `./sdd portfolio init|status|graph|validate` registrados en `DISPATCH_MAP` y `print_help()` de `scripts/sdd_cli.py`, con salida `--format text|json`.
  - Integración no intrusiva en `scripts/sdd_ci.py` (`check_portfolio`, devolviendo `SKIPPED_NO_APPLICABLE` cuando no existan Épicas ni dependencias declaradas).
  - Suite offline `tests/test_sdd_portfolio.py` (`<= 500L`).
- **Out-of-Scope:**
  - Contabilidad FinOps de tokens/coste y presupuestos por Work Item/Épica (diferido a `FWK-018`).
  - Gobierno multi-servicio/monorepo y verificación de contratos compartidos (diferido a `FWK-019`).
  - Mutación automática de `specs/BACKLOG.md` o autoaprobación de Gates `1..3` o `Gate S0`.

## 2. Requisitos (EARS)

- `RF-1701` (**Plantilla y creación segura de Épicas `EPIC-XXX`**): CUANDO se ejecute `./sdd portfolio init --id EPIC-XXX --title "<título>"` sobre un repositorio válido, el sistema deberá crear de forma atómica `specs/epics/EPIC-XXX-<slug>.md` a partir de `specs/templates/09-epic-roadmap.template.md` con estado inicial `Draft`, sin sobrescribir ficheros existentes salvo `--force`, rechazando IDs inválidos, symlinks/junctions y escapes de ruta, y manteniendo `0` bytes añadidos en `.agents/`.
- `RF-1702` (**Modelo de Épicas, Priorización *MoSCoW*/*RICE* y *Rollup* de Progreso**): CUANDO existan expedientes `specs/epics/EPIC-*.md` y/o vínculos a Épicas en `specs/BACKLOG.md`, `scripts/sdd_portfolio.py` deberá agregar de forma determinista y 100% offline las features asociadas (`FEAT-XXX`), validar prioridades *MoSCoW* (`Must`, `Should`, `Could`, `Wont`) y/o *RICE* (`reach`, `impact`, `confidence`, `effort` con `effort > 0` y puntuación `RICE = (reach * impact * confidence) / effort`), y calcular por cada Épica `total_features`, `done_features`, `in_progress_features`, `blocked_features`, `progress_pct` y `ready_features` (features cuyas dependencias ya están `Done`).
- `RF-1703` (**Grafo de Dependencias entre Features, Detección de Ciclos y Ruta Crítica**): CUANDO existan dependencias declaradas (`depends_on` / columna `Depende de` entre `FEAT-XXX`), `./sdd portfolio graph` y `./sdd portfolio validate` deberán construir el DAG de features, calcular las olas topológicas y la cadena más larga de dependencias pendientes (*critical path*), detectar en modo *fail-closed* cualquier ciclo (`CYCLE_DETECTED`) o dependencia inexistente (`UNKNOWN_DEPENDENCY`), y emitir advertencia explícita (`PRIORITY_INVERSION`) si una feature `Must` depende de una `Could` o `Wont`.
- `RF-1704` (**Integración CLI `sdd portfolio`, Retrocompatibilidad CI y Restricciones Modulares**): `scripts/sdd_cli.py` deberá exponer `portfolio` en `DISPATCH_MAP` y `print_help()`, y `scripts/sdd_ci.py` deberá ejecutar `check_portfolio` devolviendo `SKIPPED_NO_APPLICABLE` cuando el repositorio no declare `specs/epics/EPIC-*` ni dependencias/épicas en `BACKLOG.md`, `PASS` cuando el grafo y las Épicas sean válidos, y `FAIL` ante errores estructurales o ciclos; todo módulo `.py` afectado deberá mantenerse en `<= 500` líneas y `.agents/` bajo `< 25k` tokens.

## 3. Criterios de Aceptación (BDD / Given-When-Then)

1. **Escenario `CA-1701` (Creación determinista `portfolio init` sin sobrescritura accidental):**
   - **Dado** un repositorio temporal sin `specs/epics/`
   - **Cuando** se ejecuta `scripts/sdd_cli.py portfolio init --repo-root <repo> --id EPIC-001 --title "Core Billing"`
   - **Entonces** crea `specs/epics/EPIC-001-core-billing.md` con bloque `yaml sdd:epic` válido, `status: Draft`, sin marcas `[x]` de aprobación de Gates; una segunda ejecución sin `--force` falla de forma controlada (`!= 0`) sin alterar el fichero, y un `--repo-root` o `specs/epics` apuntando a symlink es rechazado.
2. **Escenario `CA-1702` (*Rollup* de progreso, prioridad *MoSCoW*/*RICE* y `ready_features`):**
   - **Dado** un `EPIC-001` que agrupa `FEAT-001` (`Done`, `Must`), `FEAT-002` (`In Progress`, `Must`, `depends_on: [FEAT-001]`) y `FEAT-003` (`Backlog`, `Should`, `depends_on: [FEAT-002]`, `RICE: reach=100, impact=2, confidence=0.8, effort=4`)
   - **Cuando** se ejecuta `portfolio status --repo-root <repo> --format json`
   - **Entonces** reporta `progress_pct: 33.3`, `done_features: 1`, `total_features: 3`, `rice_score: 40.0` en `FEAT-003`, `ready_features` excluye a `FEAT-003` por tener pendiente `FEAT-002`, y `FEAT-002` aparece desbloqueada respecto a `FEAT-001`.
3. **Escenario `CA-1703` (Detección *fail-closed* de ciclos, dependencias huérfanas e inversión de prioridad):**
   - **Dado** un portfolio con ciclo `FEAT-010 -> FEAT-011 -> FEAT-010` (o referencia `depends_on: [FEAT-999]` inexistente, o `Must` dependiendo de `Wont`)
   - **Cuando** se ejecuta `portfolio validate --repo-root <repo> --format json`
   - **Entonces** ante ciclo o dependencia huérfana retorna código `!= 0` con hallazgo `CYCLE_DETECTED` o `UNKNOWN_DEPENDENCY`, y ante inversión de prioridad reporta `PRIORITY_INVERSION` como advertencia verificable.
4. **Escenario `CA-1704` (Integración CI retrocompatible, CLI `graph` y límites modulares):**
   - **Dado** el repositorio starter sin `specs/epics/EPIC-*` frente a un proyecto derivado con Épicas válidas y ruta crítica `FEAT-001 -> FEAT-002 -> FEAT-003`
   - **Cuando** se ejecutan `sdd_ci.py` (`check_portfolio`) y `portfolio graph --format json`
   - **Entonces** en el starter sin Épicas `check_portfolio` devuelve `SKIPPED_NO_APPLICABLE`, en el proyecto con Épicas devuelve `PASS` y `graph` expone las olas topológicas y `critical_path`, y todos los `.py` en `scripts/`, `.agents/scripts/` y `tests/` cumplen `<= 500` líneas con `.agents/` `< 25k` tokens.

## 4. Aprobación Formal Gate 1 (`RN-SDD-HUMAN-GATE-OWNERSHIP`)
- [x] **Gate 1 Approved (Human Sign-off):** Revisado y validado por Stakeholder Humano (`2026-11-21T01:17:55+01:00`).

<!-- sdd:gate-seal gate=1 sha256=e9ccde8c7cc9a06a4fe6fcc11c51316290bc5be752e67955c57a974d590cc055 -->
