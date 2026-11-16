# Plan de Tareas (DAG): `FWK-010` Endurecimiento Nivel L5 (10/10)

- **ID:** `FWK-010-l5-perfection-hardening`
- **Gate 3 Sign-off:** `[x] Gate 3 Approved (Authorized by PO on 2026-11-15T00:40:33+01:00)`

## Grafo DAG
- [x] `T10.1` [`@back-engineer`] `[PARALLEL: BLOCK_F1]`: Implementar `scripts/sdd_gate_seal.py` (`<= 280L`), integrar verificación de sellos SHA-256 en `.agents/scripts/sdd_code_gate_guard.py` (`<= 495L`) y exponer `approve-gate` / `verify-gates` en `scripts/sdd_cli.py`.
  - *Archivos exactos*: `scripts/sdd_gate_seal.py`, `.agents/scripts/sdd_code_gate_guard.py`, `scripts/sdd_cli.py`
  - *Comando de verificación DoD*: `uv run python scripts/sdd_gate_seal.py --help`
- [x] `T10.2` [`@back-engineer`] `[PARALLEL: BLOCK_F1]`: Implementar analizador políglota `check_polyglot_imports` (`.ts`, `.tsx`, `.js`, `.jsx`, `.cs`, `.go`, `.rs`, `.java`, `.kt`) en `.agents/scripts/verify_architecture_boundaries.py` (`<= 460L`).
  - *Archivos exactos*: `.agents/scripts/verify_architecture_boundaries.py`
  - *Comando de verificación DoD*: `uv run python .agents/scripts/verify_architecture_boundaries.py`
- [x] `T10.3` [`@back-engineer`] `[PARALLEL: BLOCK_F1]`: Implementar `DagWriteSetCollisionError`, extracción de `target_paths` y validación/partición de colisiones de escritura en olas paralelas en `scripts/sdd_dag.py` (`<= 495L`).
  - *Archivos exactos*: `scripts/sdd_dag.py`
  - *Comando de verificación DoD*: `uv run python scripts/sdd_dag.py --verify .sdd/framework/work-items/FWK-010-l5-perfection-hardening/03-tasks.md`
- [x] `T10.4` [`@qa-tester`] `[SEQUENTIAL: AFTER BLOCK_F1]`: Actualizar `.github/workflows/ci.yml` (step `sdd_dag.py --verify` + umbral `>= 120` tests) y crear suite determinista `tests/test_sdd_l5_perfection.py` (`<= 450L`) + actualizar `tests/test_sdd_sync_and_modularity.py`.
  - *Archivos exactos*: `.github/workflows/ci.yml`, `tests/test_sdd_l5_perfection.py`, `tests/test_sdd_sync_and_modularity.py`
  - *Comando de verificación DoD*: `uv run python -m unittest discover -s tests -q`
- [x] `T10.5` [`@documentator`] `[SEQUENTIAL: AFTER T10.4]`: Actualizar documentación 0DD (`docs/knowledge/`, `docs/traceability/TRACEABILITY-MATRIX.md`, `docs/es/`, `docs/en/`) y cerrar `FWK-010` en `Done`.
  - *Archivos exactos*: `docs/knowledge/API_CATALOG.md`, `docs/knowledge/DATA_MODELS.md`, `docs/knowledge/SYSTEM_TOPOLOGY.md`, `docs/knowledge/ADRS.md`, `docs/traceability/TRACEABILITY-MATRIX.md`
  - *Comando de verificación DoD*: `uv run python .agents/scripts/sdd_healthcheck.py`

<!-- sdd:gate-seal gate=3 sha256=348689a0a3ff5af3e2a63b23f415e1df95ff98d63b3e26c835ebaa5bdba7c84b -->
