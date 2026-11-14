# Tech Spec: Compilador de Ownership, Generador Transaccional y Motor DAG (`FWK-006`)

- **ID:** `FWK-006-compiler-dag-hardening`
- **Gate 2 Sign-off:** `[x] Gate 2 Approved (Pre-authorized by PO on 2026-11-14T16:05:46+01:00)`

## Arquitectura Modular (`<= 500` líneas por `.py`)
1. **`scripts/sdd_ownership.py`** (`<=500L`) + [verify_architecture_boundaries.py](../../../../.agents/scripts/verify_architecture_boundaries.py): parseo de bloque `yaml sdd:ownership-map` (`zones`, `forbid_imports`, `builder`), detección de solapamiento de globs y rutas huérfanas, compilación dinámica de `BuilderSpec` cuando exista en `STACK.md`, y validación AST de `forbid_imports` en `verify_architecture_boundaries.py`.
2. **`scripts/sdd_dag.py`** (`<=500L`) + enganche en [sdd_healthcheck.py](../../../../.agents/scripts/sdd_healthcheck.py): extracción de tareas (`T#`), bloques `[PARALLEL: ...]` / `[SEQUENTIAL: ...]`, validación de ciclos/dependencias inexistentes (error no-cero), e interfaz de transición `.agent-inbox/<agent>/` (`pending -> in_progress -> done/blocked`).
3. **`scripts/sdd_generator_tx.py`** (`<=500L`): transacción de filesystem staging/backup/rollback, escritura atómica via archivo temporal + `os.replace`, resolución DoD `verification_commands` de §2.5, drenaje/reasignación de inboxes obsoletos y verificación `--verify` (`CORE_AGENTS` incluidos, timestamps desacoplados del hash determinista).
4. **Integración en [sdd_pack_registry.py](../../../../scripts/sdd_pack_registry.py) (`<=500L`) y [sdd_agent_generator.py](../../../../scripts/sdd_agent_generator.py) (`<=500L`)** + [specs/STACK.md](../../../../specs/STACK.md) & [00-stack.template.md](../../../../specs/templates/00-stack.template.md).
