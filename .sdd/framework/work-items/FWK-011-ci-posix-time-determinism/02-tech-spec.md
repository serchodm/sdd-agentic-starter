# Tech Spec: Portabilidad POSIX de Guards Win32 y Determinismo Temporal (`FWK-011`)

- **ID:** `FWK-011-ci-posix-time-determinism`
- **Gate 2 Sign-off:** `[x] Gate 2 Approved (Authorized by PO on 2026-11-16T00:56:38+01:00)`

## Arquitectura Modular (`<= 500` líneas por `.py`)
1. **`.agents/scripts/sdd_immutable_feature_guard.py` (actual `348L`, objetivo `<= 365L`):**
   - Añadir validación en `resolve_repo_relative_path(target_path, repo_root)`: tras `cleaned = strip_win32_extended_prefix(target_path.strip()).replace("\\", "/")`, si `os.name != "nt"` y `re.match(r"^[A-Za-z]:", cleaned)`, lanzar `ValueError(f"Windows drive paths are disallowed on POSIX: {target_path!r}")`.
   - En `resolve_target_context`, aplicar la misma guarda sobre `cand_art` antes de evaluar `cand_art.is_absolute()` cuando `os.name != "nt"`.
   - Mantener `strip_win32_extended_prefix` sin rechazar `C:\...` para preservar `code_guard.is_protected_code_path(r"\\?\C:\repo\src\evil.py", r"C:\repo") == "src/evil.py"`.
2. **`tests/test_sdd_governance.py` (actual `176L`, objetivo `<= 185L`):**
   - Importar `datetime` y reemplazar las fechas fijas `"2026-11-09T00:00:00+00:00"` / `"2025-11-09T00:00:00+00:00"` en `test_sdd_instincts_temporal_decay` por `(now - datetime.timedelta(days=1)).isoformat()` y `(now - datetime.timedelta(days=365)).isoformat()`.
3. **`tests/test_sdd_security_guards.py` (actual `486L`, objetivo `<= 498L`):**
   - En `test_code_gate_protects_perimeter_traversal_and_win32_extended_paths`, añadir un bloque `with mock.patch.object(imm_guard.os, "name", "posix"):` verificando que `imm_guard.resolve_repo_relative_path(p, repo)` lanza `ValueError` para `r"\\?\C:\outside\evil.py"` y `r"C:\outside\evil.py"`.
4. **Cierre 0DD (`docs/traceability/TRACEABILITY-MATRIX.md` + `docs/knowledge/SYSTEM_TOPOLOGY.md`):**
   - Registrar `FWK-011` tras completar los 123+ tests en verde y las auditorías SDD.

<!-- sdd:gate-seal gate=2 sha256=60f5dd1b982b8e9896dda5a62cee30f9dbb12afb2487f6ddb1484b3c5d0205b3 -->
