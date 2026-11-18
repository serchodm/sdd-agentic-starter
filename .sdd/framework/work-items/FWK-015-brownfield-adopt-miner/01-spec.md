# Spec Funcional: Motor de Adopción Brownfield (`sdd adopt`) y Workflow `@spec-miner` (`FWK-015`)

- **ID:** `FWK-015-brownfield-adopt-miner`
- **RFC:** [`RFC-008`](../../rfcs/RFC-008-brownfield-adoption-and-spec-drift.md) (`Aceptado`)
- **Estado:** `Approved`
- **Gate 1 Sign-off:** `[x] Gate 1 Approved (Authorized by PO on 2026-11-17T17:25:03+01:00 — "Aprobados")`

## 1. Resumen y Alcance
Proveer un motor determinista 100% offline (`scripts/sdd_brownfield.py`, expuesto vía `./sdd adopt`) y un workflow operativo compacto (`.agents/workflows/brownfield-adopt.md`) para incorporar repositorios con código existente (*brownfield*) al flujo SDD sin sobrescribir código ni configuraciones previas y preservando la autoridad humana en `Gate S0` y `Gate 1`.

- **In-Scope:**
  - `scripts/sdd_brownfield.py` (stdlib-only, `<= 500L`): descubrimiento offline de manifiestos (`pyproject.toml`, `package.json`, `go.mod`, `Cargo.toml`, `pom.xml`, `*.csproj`, etc.), frameworks, ficheros CI/infraestructura, raíces de código y comandos candidatos para `yaml sdd:verification-commands`.
  - Inferencia determinista de `packs`, `preset` (`compact` vs `granular`) y zonas candidatas para `yaml sdd:ownership-map` (soportando raíces habituales brownfield como `src/`, `app/`, `lib/`, `backend/`, `frontend/`, `api/`, `web/`, `services/`, `packages/`, `cmd/`, `internal/`).
  - Modo `--dry-run` por defecto y `--apply` explícito no destructivo para generar un borrador de `specs/STACK.md` (`[ ] Gate S0 Approved`, `stack_approved: false`), `docs/knowledge/BROWNFIELD_INVENTORY.md` y `specs/BACKLOG.md` (solo si faltan).
  - Registro de `adopt` en `DISPATCH_MAP` y `print_help()` de `scripts/sdd_cli.py`.
  - Workflow `.agents/workflows/brownfield-adopt.md` (`<= 25L`) conectando `sdd adopt` -> `Gate S0` -> `sdd repo-map` -> `@spec-miner` (`.sdd/catalog/specialists-optin/spec-miner.md`).
  - Suite de pruebas offline `tests/test_sdd_brownfield.py`.
- **Out-of-Scope:**
  - Motor `sdd drift`, extensión de `sdd_ownership.py` / `sdd_code_gate_guard.py` para zonas *Strangler Fig* y soporte `brownfield-mined` en `sdd_healthcheck.py` (diferidos a `FWK-016`).
  - Ejecución automática de `npm install`, `uv sync`, linters o comandos descubiertos durante `sdd adopt`.

## 2. Requisitos (EARS)
- `RF-1501` (**Descubrimiento brownfield determinista y offline**): CUANDO se ejecute `scripts/sdd_brownfield.py` (o `./sdd adopt`) sobre un repositorio existente, el sistema deberá inspeccionar de forma determinista, 100% offline y sin ejecutar código ni comandos del proyecto los manifiestos, configuraciones CI/DB y directorios de código (ignorando `.git`, `.venv`, `node_modules`, `dist`, `build`, etc.) para inferir ecosistemas (`lang-*`, `framework-*`, `capability-*`), raíces de código candidatas, `preset` sugerido y bounded contexts preliminares, emitiendo salida legible (`--format text`) o estructurada (`--format json`).
- `RF-1502` (**Adopción no destructiva `--dry-run` por defecto y bloqueo `Gate S0`**): El sistema deberá operar en modo `--dry-run` por defecto sin escribir ningún fichero en disco; CUANDO se invoque con `--apply`, deberá crear únicamente los artefactos SDD ausentes (`specs/STACK.md` en borrador, `docs/knowledge/BROWNFIELD_INVENTORY.md` y `specs/BACKLOG.md` si no existen) sin sobrescribir ficheros existentes, manteniendo estrictamente `[ ] Gate S0 Approved (Human Sign-off)` y `stack_approved: false` (`RN-SDD-HUMAN-GATE-OWNERSHIP`). SI `specs/STACK.md` ya existe con `Gate S0` aprobado, ENTONCES el sistema deberá rechazar o omitir cualquier modificación sobre `specs/STACK.md`.
- `RF-1503` (**Sanitización *fail-closed* de rutas y comandos inferidos**): El sistema deberá validar `--repo-root` rechazando symlinks, junctions y rutas fuera del repositorio, y al inferir comandos DoD desde manifiestos (como `scripts` de `package.json`) deberá filtrar metacaracteres inseguros (`;`, `|`, `` ` ``, `$(`, `>`, `<`, saltos de línea, `&` simple) antes de volcar el bloque `yaml sdd:verification-commands`, registrando advertencias explícitas para los slots inseguros o ausentes.
- `RF-1504` (**Integración CLI `sdd adopt` y workflow `@spec-miner`**): `scripts/sdd_cli.py` deberá registrar `adopt` en `DISPATCH_MAP` y `print_help()`, y `.agents/workflows/brownfield-adopt.md` (`<= 25` líneas) deberá guiar el flujo `sdd adopt` -> revisión humana `Gate S0` -> `sdd generate --materialize` -> `sdd repo-map` -> `@spec-miner`, preservando el presupuesto activo de `.agents/` por debajo de `25k` tokens estimados.

## 3. Criterios de Aceptación (BDD / Given-When-Then)
1. **Escenario `CA-1501` (Descubrimiento multi-stack y salida JSON en `--dry-run`):**
   - **Dado** un repositorio temporal brownfield con `pyproject.toml` (FastAPI + pytest), `frontend/package.json` (React + scripts `lint`, `test`, `build`), `backend/app/main.py` y `frontend/src/App.tsx`
   - **Cuando** se ejecuta `scripts/sdd_cli.py adopt --repo-root <repo> --format json` (sin `--apply`)
   - **Entonces** retorna código `0`, no crea ni modifica ficheros en `<repo>`, y el JSON reporta `applied: false`, packs sugeridos incluyendo `lang-python`, `framework-fastapi`, `lang-typescript`, `framework-react`, `capability-web-frontend`, `preset: "granular"` y zonas candidatas para `backend/app` y `frontend/src`.
2. **Escenario `CA-1502` (Aplicación `--apply` no destructiva y preservación de `Gate S0`):**
   - **Dado** un repositorio temporal con `README.md` y código fuente en `app/service.py` sin `specs/STACK.md`
   - **Cuando** se ejecuta `adopt --repo-root <repo> --apply`
   - **Entonces** crea `specs/STACK.md`, `docs/knowledge/BROWNFIELD_INVENTORY.md` y `specs/BACKLOG.md`, conserva intacto `README.md` y el código fuente, y `specs/STACK.md` contiene `[ ] Gate S0 Approved (Human Sign-off)`, `stack_approved: false` y `gate00_approved: false`. Una segunda ejecución de `--apply` no sobrescribe `specs/STACK.md` ni `specs/BACKLOG.md`.
3. **Escenario `CA-1503` (Seguridad *fail-closed* en comandos de manifiesto y symlinks):**
   - **Dado** un `package.json` con un script malicioso `"lint": "eslint . && rm -rf /; echo pwn"` o un `--repo-root` que apunta a un symlink
   - **Cuando** se ejecuta `adopt`
   - **Entonces** rechaza el symlink con error controlado (`!= 0`), y ante el script malicioso lo descarta del bloque `yaml sdd:verification-commands` emitiendo una advertencia verificable en el reporte.
4. **Escenario `CA-1504` (Workflow compacto, presupuesto `< 25k` y techo modular `<= 500L`):**
   - **Dado** la implementación completa de `FWK-015`
   - **Cuando** se inspeccionan `.agents/workflows/brownfield-adopt.md`, el tamaño total de Markdown en `.agents/` y todos los `.py` en `scripts/`, `.agents/scripts/` y `tests/`
   - **Entonces** `brownfield-adopt.md` tiene `<= 25` líneas, `.agents/` permanece `< 25k` tokens estimados, todos los `.py` cumplen `<= 500` líneas y `tests/test_sdd_brownfield.py` pasa 100% offline.

## 4. Aprobación Formal Gate 1 (`RN-SDD-HUMAN-GATE-OWNERSHIP`)
- [x] **Gate 1 Approved (Human Sign-off):** Revisado y validado por Stakeholder Humano (`2026-11-17T17:25:03+01:00`).

<!-- sdd:gate-seal gate=1 sha256=5c86998134000b90ddf8d8d69857188a4f7d33afbcd3524188316bc4cc79bb7a -->
