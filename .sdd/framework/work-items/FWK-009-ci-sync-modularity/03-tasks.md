# Plan de Tareas (DAG): `FWK-009` Sync, CI & Modularidad Global

- **ID:** `FWK-009-ci-sync-modularity`
- **Gate 3 Sign-off:** `[x] Gate 3 Approved (Pre-authorized by PO on 2026-11-14T16:05:46+01:00)`

## Grafo DAG
- `T9.1` `[PARALLEL: BLOCK_E1]`: Endurecer `scripts/sdd_sync.py` (sin rutas fijas, `--dry-run`, detección conflictos, rollback) + pruebas en `tests/test_sdd_sync_and_modularity.py`.
  - *DoD:* `uv run python -m unittest tests.test_sdd_sync_and_modularity -v`
- `T9.2` `[PARALLEL: BLOCK_E1]`: Dividir `.agents/scripts/sdd_token_usage.py` en módulos `<=500L` manteniendo tests verdes.
  - *DoD:* `uv run python -m unittest tests.test_sdd_token_usage -v`
- `T9.3` `[PARALLEL: BLOCK_E1]`: Dividir `.agents/scripts/sdd_repo_map.py` en módulos `<=500L` manteniendo CLI funcional.
  - *DoD:* `uv run python .agents/scripts/sdd_repo_map.py --help`
- `T9.4` `[PARALLEL: BLOCK_E1]`: Endurecer `.github/workflows/ci.yml`, crear `pyproject.toml` y añadir verificación global `<=500L` (sin exclusiones) en `tests/test_sdd_sync_and_modularity.py`.
  - *DoD:* comprobar YAML válido de `ci.yml`, TOML válido de `pyproject.toml` y CLI `--verify`.
