# Especificación Funcional: Stop-the-Line P0 Seguridad y Guardias Fail-Closed (`FWK-005`)

- **ID:** `FWK-005-p0-security-hardening`
- **RFC:** [`RFC-003`](../../rfcs/RFC-003-audit-remediation-and-hardening.md) (`Aceptado`)
- **Estado:** `In Progress`
- **Gate 1 Sign-off:** `[x] Gate 1 Approved (Pre-authorized by PO on 2026-11-14T16:05:46+01:00)`

## Requisitos Funcionales (EARS)
- `RF-501` (`AUD-007`): `.agents/hooks.json` deberá almacenarse sin BOM UTF-8 y apuntar a `.agents/scripts/{sdd_immutable_feature_guard,sdd_code_gate_guard}.py`.
- `RF-502` (`AUD-008`, `AUD-023`): Los guardias pre-tool (`sdd_code_gate_guard.py`, `sdd_immutable_feature_guard.py`, `sdd_stack_gate_guard.py`) y Git hooks (`sdd_hooks.py`, `.githooks/*`) deberán operar en modo *fail-closed* ante JSON vacío/corrupto o errores de E/S/`git`, normalizar prefijos Win32 `\\?\`, resolver symlinks/junctions con `resolve(strict=False)`, proteger `tests/`, `.agents/`, `specs/STACK.md`, y eliminar el bypass `SDD_FORCE_MAIN_PUSH`.
- `RF-503` (`AUD-009`, `AUD-024`): El control de Gate 1..3 deberá verificar las casillas `- [x] Gate 1 Approved`, `- [x] Gate 2 Approved`, `- [x] Gate 3 Approved` y contenido no vacío en `01-spec.md`, `02-tech-spec.md` y `03-tasks.md` del work item activo, detectar mutaciones ya comprometidas en features `Done` via `git diff`, normalizar la fila plantilla `FEAT-001` en `specs/BACKLOG.md` y evaluar estados `Draft`/`Proposed` únicamente en la columna `Status`.
- `RF-504` (`AUD-010`, `AUD-022`): `sdd_trim_exec.py` ejecutará comandos con `shell=False` / `argv` (sin concatenación de shell), `sdd_healthcheck.py` validará riesgos de inyección, y `sdd.cmd` eliminará `echo %FIRST_ARG% | findstr`.
- `RF-505` (`AUD-021`, `AUD-011`): `WorktreeManager.remove` deberá bloquear eliminación fuera de `worktrees_root`, y `.agents/skills/` del starter vacío no contendrá `fastapi-patterns`, `postgres-patterns` ni `react-performance-and-patterns`.
