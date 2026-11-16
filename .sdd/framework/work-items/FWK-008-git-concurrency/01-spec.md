# Spec Funcional: Concurrencia Multi-Worktree en `sdd_git` (`FWK-008`)

- **ID:** `FWK-008-git-concurrency`
- **RFC:** [`RFC-003`](../../rfcs/RFC-003-audit-remediation-and-hardening.md) (`Aceptado`)
- **Gate 1 Sign-off:** `[x] Gate 1 Approved (Pre-authorized by PO on 2026-11-14T16:05:46+01:00)`

## Requisitos (EARS)
- `RF-801` (`AUD-016`): La creación/gestión de worktrees deberá asignar puertos sin colisiones entre worktrees activos, almacenar el estado activo por worktree (`active_work_item` aislado por worktree, sin pisar el singleton global), y resolver dinámicamente la rama base y URL de `origin`.
- `RF-802` (`AUD-003`, `AUD-019`): `load_git_governance()` utilizará `copy.deepcopy(DEFAULT_GOVERNANCE)` evitando mutación compartida de estado global, y las operaciones de cambio/cierre en `sdd_git` sincronizarán automáticamente `.agents/ACTIVE_STATE.md`.
- `RF-803` (`AUD-025`): Dividir `scripts/sdd_git.py` (`743` líneas) en módulos cohesivos todos `<= 500` líneas preservando las firmas CLI/Python de [`DISPATCH_MAP`](../../../../scripts/sdd_cli.py) y `tests/test_sdd_governance.py`.
