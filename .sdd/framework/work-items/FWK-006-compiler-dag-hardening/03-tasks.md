# Plan de Tareas (DAG): `FWK-006` Compiler, Registry & DAG Engine

- **ID:** `FWK-006-compiler-dag-hardening`
- **Gate 3 Sign-off:** `[x] Gate 3 Approved (Pre-authorized by PO on 2026-11-14T16:05:46+01:00)`

## Grafo DAG
- `T6.1` `[PARALLEL: BLOCK_B1]`: Crear `scripts/sdd_ownership.py` y conectar `forbid_imports` en `.agents/scripts/verify_architecture_boundaries.py`.
  - *DoD:* `uv run python .agents/scripts/verify_architecture_boundaries.py`
- `T6.2` `[PARALLEL: BLOCK_B1]`: Crear `scripts/sdd_dag.py` y conectar validación DAG en `.agents/scripts/sdd_healthcheck.py`.
  - *DoD:* `uv run python .agents/scripts/sdd_healthcheck.py`
- `T6.3` `[PARALLEL: BLOCK_B1]`: Crear `scripts/sdd_generator_tx.py` (transacción rollback, DoD §2.5, `CORE_AGENTS` hash, orden/hash determinista, `--verify` & drain inbox).
  - *DoD:* `uv run python -m py_compile scripts/sdd_generator_tx.py`
- `T6.4` `[SEQUENTIAL: AFTER_BLOCK_B1]`: Cablear `sdd_pack_registry.py`, `sdd_agent_generator.py`, `specs/STACK.md` y `specs/templates/00-stack.template.md` respetando `<=500L`.
  - *DoD:* `uv run python scripts/sdd_agent_generator.py --list`
- `T6.5` `[SEQUENTIAL: AFTER_T6.4]`: Actualizar `tests/test_sdd_pack_materialization.py` y crear `tests/test_sdd_ownership_dag.py` (`<=500L`).
  - *DoD:* `uv run python -m unittest tests.test_sdd_pack_materialization tests.test_sdd_ownership_dag -v`
