# Spec Funcional: Sync Seguro, Hardening CI/0DD y Modularidad Global (`FWK-009`)

- **ID:** `FWK-009-ci-sync-modularity`
- **RFC:** [`RFC-003`](../../rfcs/RFC-003-audit-remediation-and-hardening.md) (`Aceptado`)
- **Gate 1 Sign-off:** `[x] Gate 1 Approved (Pre-authorized by PO on 2026-11-14T16:05:46+01:00)`

## Requisitos (EARS)
- `RF-901` (`AUD-006`): `scripts/sdd_sync.py` deberá eliminar rutas hardcodeadas (`C:/Projects/...`), exigir ruta explícita o variable de entorno verificada, soportar `--dry-run`, detectar conflictos por divergencia local/destino y ejecutar staging con rollback ante fallos.
- `RF-902` (`AUD-014`, `AUD-018`): `.github/workflows/ci.yml` validará `--verify` del generador, integridad de `.agents/hooks.json` (sin BOM + scripts existentes), cumplimiento 0DD (`docs/` + `TRACEABILITY-MATRIX.md`) y ausencia de mutaciones comprometidas en features `Done`.
- `RF-903` (`AUD-019`, `AUD-025`): Incorporar `pyproject.toml` mínimo para `uv`/tooling, dividir `.agents/scripts/sdd_token_usage.py` (`901L`) y `.agents/scripts/sdd_repo_map.py` (`681L`) en módulos `<= 500` líneas preservando sus CLIs, y añadir test global de modularidad `<= 500L` cubriendo TODOS los `.py` de `scripts/`, `.agents/scripts/` y `tests/`.
