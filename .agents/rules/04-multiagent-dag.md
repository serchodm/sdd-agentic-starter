# Regla 04: Orquestación Multi-Agente, DAG y Ownership Map

> Protocolo de despacho y sincronización en Gate 3 y Gate 4. Ver especificación extendida en [`docs/standards/MULTIAGENT_ORCHESTRATION_STANDARD.md`](file:///c:/Projects/sdd-agentic-starter/docs/standards/MULTIAGENT_ORCHESTRATION_STANDARD.md).

## 1. Fronteras de Rol (`RN-SDD-ORCHESTRATOR-SUBAGENTS`)
- **`@orchestrator`:** Prohibido escribir código en `src/` o `tests/`. Lidera planificación DAG, despacho y puertas.
- **`@architect`:** Diseña contratos (OpenAPI, DTOs, schemas, ADRs) sin implementar lógica de negocio.
- **Constructores:** Implementan **solo dentro de su zona del Ownership Map** (`specs/STACK.md`).
- **`@qa-tester` y especialistas:** Auditan calidad, pruebas y seguridad con criterio independiente.

## 2. Bloques DAG en `03-tasks.md` y DoR Estricta
- `[PARALLEL: BLOCK_X]`: tareas ortogonales en zonas disjuntas ejecutables concurrentemente.
- `[SEQUENTIAL: AFTER_BLOCK_X]`: barrera dependiente del éxito previo.
- **DoR obligatoria por tarea:** (1) agente asignado (`owner`), (2) rutas físicas exactas, (3) sección/contrato exacto en `02-tech-spec.md`, (4) comando DoD determinista pre-probado (ej. `pytest tests/unit/domain -q`).

## 3. Despacho y Sincronización
- Depositar tickets en `.agent-inbox/<agente>/` vía `opsx-delegate` e invocar con `invoke_subagent` / `runSubAgent`.
- En `[PARALLEL]`, despachar concurrentemente y esperar reactivamente (sin polling) a que todos terminen en verde antes de abrir el bloque `[SEQUENTIAL]`.
