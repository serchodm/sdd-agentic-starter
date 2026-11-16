# Spec Funcional: Portabilidad POSIX de Guards Win32 y Determinismo Temporal (`FWK-011`)

- **ID:** `FWK-011-ci-posix-time-determinism`
- **RFC:** [`RFC-005`](../../rfcs/RFC-005-ci-posix-time-determinism.md) (`Aceptado`)
- **Gate 1 Sign-off:** `[x] Gate 1 Approved (Authorized by PO on 2026-11-16T00:56:38+01:00)`

## Requisitos (EARS)
- `RF-1101` (**Rechazo POSIX de rutas con unidad Windows**): Cuando `.agents/scripts/sdd_immutable_feature_guard.py` ejecute `resolve_repo_relative_path` o `resolve_target_context` bajo un sistema no Windows (`os.name != "nt"`) y reciba una ruta cuya forma normalizada comience por una letra de unidad Windows (`^[A-Za-z]:`, incluyendo rutas resultantes de `strip_win32_extended_prefix` sobre `\\?\C:\...`), el sistema deberá lanzar `ValueError` para denegar (*fail-closed*) la operación en `sdd_code_gate_guard.py` y `sdd_immutable_feature_guard.py`, manteniendo intacto el comportamiento de `is_protected_code_path`.
- `RF-1102` (**Determinismo temporal en `test_sdd_instincts_temporal_decay`**): En `tests/test_sdd_governance.py`, `test_sdd_instincts_temporal_decay` deberá construir los timestamps `last_reinforced` de forma relativa a `datetime.datetime.now(datetime.timezone.utc)` (`timedelta(days=1)` para instinto reciente y `timedelta(days=365)` para instinto antiguo) para garantizar determinismo en cualquier fecha futura.
- `RF-1103` (**Prueba de regresión multiplataforma en `<= 500` líneas**): `tests/test_sdd_security_guards.py` deberá verificar mediante mock de `os.name == "posix"` que `resolve_repo_relative_path` rechaza rutas `\\?\C:\outside\evil.py` y `C:\outside\evil.py`, manteniendo todos los ficheros Python del proyecto en `<= 500` líneas.

<!-- sdd:gate-seal gate=1 sha256=af307454832123cb20bdcf2d1f5fe5f588d55cea9b2698d593d66b4f9add036f -->
