# Plan de Tareas (DAG): `FWK-008` Concurrencia `sdd_git` (`<=500L`)

- **ID:** `FWK-008-git-concurrency`
- **Gate 3 Sign-off:** `[x] Gate 3 Approved (Pre-authorized by PO on 2026-11-14T16:05:46+01:00)`

## Grafo DAG
- `T8.1` `[PARALLEL: BLOCK_D1]`: Extraer `scripts/sdd_git_state.py` (`deepcopy`, estado por worktree, auto-sync `ACTIVE_STATE.md`) y `scripts/sdd_git_worktree.py` (puertos sin colisión, base/remote dinámicos, contención `worktrees_root`) manteniendo ambos `<=500L`.
  - *DoD:* `uv run python -m py_compile scripts/sdd_git_state.py scripts/sdd_git_worktree.py`
- `T8.2` `[SEQUENTIAL: AFTER_T8.1]`: Refactorizar `scripts/sdd_git.py` (`<=500L`) re-exportando API pública e integrar CLI.
  - *DoD:* `uv run python scripts/sdd_git.py status`
- `T8.3` `[SEQUENTIAL: AFTER_T8.2]` (`@qa-tester`): Crear `tests/test_sdd_git_concurrency.py` (`<=500L`) y validar `tests/test_sdd_governance.py`.
  - *DoD:* `uv run python -m unittest tests.test_sdd_governance tests.test_sdd_git_concurrency -v`
