# Regla 04: Orquestación Multi-Agente y Grafo de Tareas (DAG)

## 1. Desacoplamiento de Roles
El desarrollo se realiza mediante agentes especializados con límites claros de responsabilidad:
- El `@orchestrator` nunca programa directamente.
- El `@architect` define contratos pero no implementa lógica interna.
- Los ingenieros de código (`@back-engineer`, `@front-engineer`) implementan estrictamente lo contratado sin inventar alcance.
- El `@qa-tester` audita con criterio independiente.

## 2. Estructura de Bloques en `03-tasks.md`
Las tareas deben organizarse para maximizar el paralelismo seguro y minimizar colisiones:
- `[PARALLEL: BLOCK_1]`: Tareas independientes que pueden ejecutarse simultáneamente (ej: backend DTOs y frontend mock UI).
- `[SEQUENTIAL: AFTER_BLOCK_1]`: Tareas que dependen estrictamente de que el bloque previo haya finalizado con éxito.
