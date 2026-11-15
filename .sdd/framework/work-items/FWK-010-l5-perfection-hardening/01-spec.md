# Spec Funcional: Endurecimiento Nivel L5 — Sello SHA-256 de Gates, Fronteras Políglotas, Write-Set DAG y CI (`FWK-010`)

- **ID:** `FWK-010-l5-perfection-hardening`
- **RFC:** [`RFC-004`](../../rfcs/RFC-004-l5-perfection-hardening.md) (`Aceptado`)
- **Gate 1 Sign-off:** `[x] Gate 1 Approved (Authorized by PO on 2026-11-15T00:40:33+01:00)`

## Requisitos (EARS)
- `RF-1001` (**Sello Criptográfico SHA-256 de Gates**): Cuando se aprueben los artefactos `01-*`, `02-*` y `03-tasks.md` de un Work Item mediante `scripts/sdd_gate_seal.py` (`sdd approve-gate`), el sistema deberá registrar los hashes `sha256:<hex>` canónicos en `.agents/active_work_item.json` (`gate_seals`) y opcionalmente en comentarios HTML de sello de gate; si el contenido de un artefacto sellado cambia en un solo carácter tras su aprobación, `sdd_code_gate_guard.py` y `sdd verify-gates` deberán denegar (*fail-closed*) la edición de código hasta que el humano vuelva a sellar el Gate.
- `RF-1002` (**Escáner Políglota de `forbid_imports`**): Cuando `.agents/scripts/verify_architecture_boundaries.py` audite capas `Domain`/`Application` o zonas de `sdd:ownership-map` con `forbid_imports`, el sistema deberá detectar violaciones de imports prohibidos tanto en Python (`.py` vía AST) como en TypeScript/JavaScript (`.ts`, `.tsx`, `.js`, `.jsx`), C# (`.cs`), Go (`.go`), Rust (`.rs`), Java (`.java`) y Kotlin (`.kt`) ignorando comentarios de línea y bloque.
- `RF-1003` (**Detector de Colisión de Escritura `Write-Set Overlap` en Olas Paralelas DAG**): Cuando `scripts/sdd_dag.py` construya las olas de ejecución de `03-tasks.md`, el sistema deberá extraer las rutas/globs objetivo de cada tarea (`target_paths`) y lanzar `DagWriteSetCollisionError` si dos tareas asignadas a la misma ola paralela solapan rutas o globs (o separarlas en sub-olas secuenciales si se solicita `auto_split_waves=True` / `--auto-split`).
- `RF-1004` (**Verificación DAG y Suelo Mínimo de Tests en CI**): El pipeline `.github/workflows/ci.yml` deberá validar con `scripts/sdd_dag.py --verify` todos los ficheros `03-tasks.md` del repositorio y exigir en la ejecución de `unittest` un mínimo determinista de `>= 120` tests ejecutados con `0` fallos, manteniendo todos los archivos `.py` del repositorio en `<= 500` líneas.

<!-- sdd:gate-seal gate=1 sha256=4fd40e50b6365656e7114cef11a5af3e13f31fbd360a9081afa4cba46f8a011c -->
