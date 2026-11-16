# RFC-005: Portabilidad POSIX de Guards Win32 y Determinismo Temporal en Tests CI

- **ID:** `RFC-005`
- **Estado:** `Implementado / Done` *(Autorización explícita PO: `2026-11-16T00:56:38+01:00`; Gate 5 cerrado con `123/123` tests en verde)*
- **Rama base:** `develop`
- **Alcance origen:** Fallo del job `SDD Continuous Integration / SDD Governance & Architecture Audit` en `develop` (runs `43652299164`, `43656797048`, `43657539091` en `ubuntu-latest`) y fallo temporal reproducible localmente en `tests/test_sdd_governance.py`.

## 1. Motivación y Solución Propuesta (`FWK-011`)

1. **Portabilidad POSIX en `resolve_repo_relative_path` / `resolve_target_context` (`RF-1101`):**
   - `strip_win32_extended_prefix(r"\\?\C:\outside\evil.py")` devuelve `r"C:\outside\evil.py"`. En Linux (`os.name != "nt"`), `pathlib.Path("C:/outside/evil.py").is_absolute()` evalúa a `False`, por lo que `resolve_repo_relative_path` la resolvía como ruta relativa dentro del repositorio y el guard devolvía `allow` en lugar de `deny` en `ubuntu-latest`.
   - En `os.name != "nt"`, `resolve_repo_relative_path` y la rama `artifactDirectoryPath` de `resolve_target_context` deben rechazar explícitamente cualquier ruta con unidad Windows (`^[A-Za-z]:`) lanzando `ValueError` (*fail-closed*).
2. **Determinismo temporal en `test_sdd_instincts_temporal_decay` (`RF-1102`):**
   - `tests/test_sdd_governance.py` fijaba `"last_reinforced": "2026-11-09T00:00:00+00:00"`. A los 7 días (`2026-11-16`), `calculate_decayed_confidence` devuelve `0.85`, cuya diferencia IEEE-754 frente a `0.90` (`0.050000000000000044`) rompe `delta=0.05`.
   - Sustituir las fechas fijas por fechas relativas a `datetime.datetime.now(datetime.timezone.utc)` (`-1` día y `-365` días).
3. **Regresión POSIX verificable también desde Windows (`RF-1103`):**
   - Cubrir en `tests/test_sdd_security_guards.py` el rechazo de rutas `C:\outside\evil.py` y `\\?\C:\outside\evil.py` cuando `os.name == "posix"` manteniendo todos los `.py` en `<= 500` líneas.
