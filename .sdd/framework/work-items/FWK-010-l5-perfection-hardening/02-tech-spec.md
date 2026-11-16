# Tech Spec: Endurecimiento Nivel L5 — Sello SHA-256, Fronteras Políglotas, Write-Set DAG y CI (`FWK-010`)

- **ID:** `FWK-010-l5-perfection-hardening`
- **Gate 2 Sign-off:** `[x] Gate 2 Approved (Authorized by PO on 2026-11-15T00:40:33+01:00)`

## Arquitectura Modular (`<= 500` líneas por `.py`)
1. **`scripts/sdd_gate_seal.py` (`<= 280L`) + `scripts/sdd_cli.py` + `.agents/scripts/sdd_code_gate_guard.py` (`<= 495L`):**
   - `compute_gate_doc_sha256(text: str) -> str`: normaliza CRLF->LF, elimina líneas de comentario de sello y devuelve `sha256:<64-hex>`.
   - `seal_work_item_gates(repo_root, work_item_id=None, gates=(1, 2, 3), embed_inline=False) -> dict[str, str]`: verifica que `01-*`, `02-*`, `03-tasks.md` tengan `[x] Gate N Approved` válido y persiste `"gate_seals": {"1": "sha256:...", "2": "sha256:...", "3": "sha256:..."}` en `.agents/active_work_item.json` (y en el estado del worktree activo si existe), insertando opcionalmente el comentario HTML de sello de gate.
   - `verify_work_item_gate_seals(repo_root, state=None, spec_dir=None, require_seals=False) -> tuple[bool, str]`: valida los sellos presentes en `state["gate_seals"]`, `state["gate_{1,2,3}_sha256"]` o el comentario inline (y falla cerrado si `require_seals=True` o `state.get("enforce_gate_seals") is True` y falta algún sello, o si cualquier hash difiere del documento actual).
   - `sdd_code_gate_guard.py` invoca `verify_work_item_gate_seals` dentro de `validate_active_work_item`. `sdd_cli.py` expone `approve-gate` y `verify-gates`.
2. **`.agents/scripts/verify_architecture_boundaries.py` (`<= 460L`):**
   - Añadir `check_polyglot_imports(code_file: pathlib.Path, forbidden_roots: set[str], layer_name: str, display_path: str | None = None) -> tuple[list[str], list[str]]` para `.ts`, `.tsx`, `.js`, `.jsx`, `.cs`, `.go`, `.rs`, `.java`, `.kt`.
   - Eliminar comentarios `/* ... */` y `// ...` preservando saltos de línea para reportar el número de línea exacto (`label:lineno`).
   - Escanear todos los archivos `_CODE_EXTENSIONS` tanto en `_run_ownership_audit` (zonas con `forbid_imports`) como en `run_boundary_audit` (`domain_dirs` y `app_dirs`).
3. **`scripts/sdd_dag.py` (`<= 495L`):**
   - Añadir `DagWriteSetCollisionError(DagError)` y el campo `target_paths: tuple[str, ...] = ()` en `DagTask`.
   - Extraer rutas/globs desde sub-bullets `- *Archivos exactos*:`, `- *Archivos*:`, `- *Ficheros exactos*:`, `- *Rutas objetivo*:`, `- *Target paths*:`, `- *Files*:`, `- *Write-set*:`.
   - En `build_and_validate_dag(tasks, *, auto_split_waves: bool = False)`: verificar pares de tareas dentro de cada ola paralela; si sus `target_paths` colisionan (igualdad, prefijo padre/hijo o intersección de globs), lanzar `DagWriteSetCollisionError` (o dividir la ola en sub-olas sin colisión si `auto_split_waves=True` / CLI `--auto-split`).
4. **`.github/workflows/ci.yml` + `tests/test_sdd_l5_perfection.py` (`<= 450L`):**
   - Añadir paso `Verify Task DAG Specifications (sdd_dag.py --verify)` en `.github/workflows/ci.yml` y verificación de `>= 120` tests ejecutados en el paso de tests unitarios.
   - Crear `tests/test_sdd_l5_perfection.py` cubriendo `RF-1001`..`RF-1004` y actualizar `tests/test_sdd_sync_and_modularity.py` si es necesario.

<!-- sdd:gate-seal gate=2 sha256=5f697cef89fc1a0f5de8003f2e5b4bd78f2bd1cb0832540ceaf5b818142e5db5 -->
