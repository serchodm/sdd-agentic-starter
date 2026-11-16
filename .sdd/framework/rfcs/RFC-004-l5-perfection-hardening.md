# RFC-004: Endurecimiento Nivel L5 (10/10) — Sello Criptográfico de Gates, Fronteras AST Políglotas, Write-Set DAG y Auditoría CI

- **ID:** `RFC-004`
- **Estado:** `Implementado / Done` *(Autorización explícita PO: `2026-11-15T00:40:33+01:00` — "Implementar estos ultimos 0.5"; Gate 5 cerrado en `develop` con `FWK-010` `Done` y `123/123` tests en verde)*
- **Rama base:** `develop` (prohibido tocar `main` directamente)
- **Alcance origen:** Auditoría Independiente de Madurez de Plataforma (`2026-11-15`, evolución de `9.4/10` Nivel `4.6/5` a `10.0/10` Nivel `5.0/5` en capacidades deterministas del repositorio).

## 1. Motivación y Pilares Técnicos (`FWK-010`)

Para alcanzar el techo técnico `10.0 / 10.0` (Nivel L5 Optimizado) en las dimensiones gobernadas por código dentro del repositorio, se aprueban cuatro mejoras deterministas sin romper el límite modular de `<= 500` líneas por archivo Python:

1. **Sello Criptográfico SHA-256 de Aprobación de Gates (`RF-1001` — `scripts/sdd_gate_seal.py` + `sdd approve-gate` / `sdd verify-gates` + `sdd_code_gate_guard.py`):**
   - Calcular y registrar la huella `sha256:<hex>` normalizada (`LF`, ignorando la línea de comentario `<!-- sdd:gate-seal ... -->`) de `01-spec.md`/`01-bug-report.md`, `02-tech-spec.md`/`02-fix-spec.md` y `03-tasks.md` en `.agents/active_work_item.json` (`gate_seals`) y/o como comentario inline `<!-- sdd:gate-seal gate=N sha256=<hex> -->`.
   - Invalidar automáticamente la apertura de código en `sdd_code_gate_guard.py` (*fail-closed*) si cualquier especificación sellada sufre una mutación post-aprobación sin re-sellar.
2. **Escáner Políglota de `forbid_imports` en Fronteras Arquitectónicas (`RF-1002` — `.agents/scripts/verify_architecture_boundaries.py`):**
   - Extender la verificación estática de imports prohibidos (tanto en capas `Domain`/`Application` por defecto como en zonas `sdd:ownership-map` con `forbid_imports`) a `.ts`, `.tsx`, `.js`, `.jsx`, `.cs`, `.go`, `.rs`, `.java` y `.kt` mediante analizadores léxicos libres de falsos positivos por comentarios (`//` y `/* ... */`).
3. **Detección de Colisión de Escritura (`Write-Set Overlap`) en Olas Paralelas DAG (`RF-1003` — `scripts/sdd_dag.py`):**
   - Parsear las rutas/globs objetivo declaradas en cada tarea (`- *Archivos exactos*:`, `- *Rutas objetivo*:`, `- *Target paths*:`, `- *Files*:`, `- *Write-set*:`) dentro de `DagTask.target_paths`.
   - En `build_and_validate_dag`, rechazar de forma *fail-closed* (`DagWriteSetCollisionError`) cualquier ola paralela donde dos tareas sin dependencia mutua solapen sus archivos o globs objetivo (o separarlas automáticamente en sub-olas secuenciales cuando se invoque con `auto_split_waves=True` / `--auto-split`).
4. **Verificación DAG Global y Suelo Mínimo de Tests en CI (`RF-1004` — `.github/workflows/ci.yml`):**
   - Añadir un paso explícito en `.github/workflows/ci.yml` que ejecute `sdd_dag.py --verify` sobre todos los `03-tasks.md` del repositorio y verifique en el paso de pruebas unitarias que el número de tests ejecutados sea `>= 120` con `0` fallos.
