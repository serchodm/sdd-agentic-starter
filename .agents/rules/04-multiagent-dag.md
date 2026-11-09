# Regla 04: Orquestación Multi-Agente, Grafo de Tareas (DAG) y Ownership Map

> **ESTÁNDAR NORMATIVO:** Define el protocolo de descomposición atómica, sincronización paralela y despacho de subagentes en Gate 3 y Gate 4.
> *(Para la especificación extendida de orquestación, consulta [`docs/standards/MULTIAGENT_ORCHESTRATION_STANDARD.md`](file:///c:/Projects/sdd-agentic-starter/docs/standards/MULTIAGENT_ORCHESTRATION_STANDARD.md)).*

---

## 1. Desacoplamiento de Roles (`RN-SDD-ORCHESTRATOR-SUBAGENTS`)
El desarrollo se realiza mediante agentes especializados con límites claros de responsabilidad:
- El `@orchestrator` tiene **terminantemente prohibido programar código directo** en el hilo principal (`src/` o `tests/`). Su labor es de liderazgo técnico, planificación DAG, despacho de órdenes y verificación holística de compuertas.
- El `@architect` diseña contratos (OpenAPI, DTOs, schemas, ADRs) pero no programa la lógica de negocio interna.
- Los subagentes constructores implementan código **exclusivamente dentro de las rutas asignadas en el Ownership Map** de `specs/STACK.md`.
- El `@qa-tester` y los especialistas de revisión ECC auditan la calidad con criterio independiente.

---

## 2. Estructura de Bloques en `03-tasks.md`
Las tareas deben organizarse para maximizar el paralelismo seguro y erradicar colisiones:
- `[PARALLEL: BLOCK_X]`: Tareas ortogonales que tocan zonas disjuntas del Ownership Map y pueden ejecutarse concurrentemente (ej: DTOs backend y maquetación frontend).
- `[SEQUENTIAL: AFTER_BLOCK_X]`: Tareas que dependen estrictamente de que el bloque previo haya finalizado con éxito (barrera de sincronización).

---

## 3. Definition of Ready (DoR) Estricta por Tarea
Toda tarea atómica registrada en `03-tasks.md` DEBE incluir obligatoriamente:
1. **Agente asignado:** Debe corresponder al `owner` de la zona según el Ownership Map.
2. **Rutas físicas exactas:** Ficheros a crear o modificar dentro de la zona del agente.
3. **Contrato de referencia:** Sección o esquema exacto de `02-tech-spec.md`.
4. **Comando de verificación DoD:** Comando determinista pre-probado (ej: `pytest tests/unit/domain -q`) para cero sobrecarga de descubrimiento.

---

## 4. Despacho y Barreras de Sincronización
- El `@orchestrator` despacha las tareas depositando tickets formales en `.agent-inbox/<agente>/` mediante `opsx-delegate` e invocando `invoke_subagent` / `runSubAgent`.
- En bloques paralelos, despacha concurrentemente y espera reactivamente (sin polling) a que todos los subagentes notifiquen finalización antes de desbloquear el siguiente bloque secuencial.
