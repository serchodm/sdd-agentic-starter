# Tech Spec: Sync Seguro, CI/0DD y Modularidad Global (`FWK-009`)

- **ID:** `FWK-009-ci-sync-modularity`
- **Gate 2 Sign-off:** `[x] Gate 2 Approved (Pre-authorized by PO on 2026-11-14T16:05:46+01:00)`

## Arquitectura Modular (`<= 500` líneas por `.py`)
1. **`scripts/sdd_sync.py` (`<=500L`):** resolver plantilla vía `--template-dir` / `SDD_TEMPLATE_DIR` sin defaults `C:/Projects/...`, añadir `--dry-run`, `--force` explícito para conflictos, snapshot staging temporal y rollback transaccional si falla copia parcial.
2. **`.agents/scripts/sdd_token_usage.py` (`901L` -> `<=450L`):** extraer parsers por IDE / agregación / renderizador de telemetría a `.agents/scripts/sdd_token_parsers.py` y `.agents/scripts/sdd_token_report.py`, preservando API pública y CLI en `sdd_token_usage.py` + `tests/test_sdd_token_usage.py`.
3. **`.agents/scripts/sdd_repo_map.py` (`681L` -> `<=450L`):** extraer extractores AST / lenguajes a `.agents/scripts/sdd_repo_map_parsers.py`, preservando CLI e interfaz en `sdd_repo_map.py`.
4. **`.github/workflows/ci.yml` + `pyproject.toml` + `tests/test_sdd_sync_and_modularity.py`:** verificar `--verify`, `hooks.json` (no BOM + targets existen), docs 0DD, `TRACEABILITY-MATRIX` y aserción global `<= 500` líneas sobre **todos** los `.py` en `scripts/`, `.agents/scripts/` y `tests/`.
