---
name: santa-method
description: Protocolo de doble verificación independiente convergente (Santa Method de affaan-m/ECC) que exige veredicto NICE unánime de dos revisores aislados antes de certificar un entregable.
---

# Skill: `santa-method` (Verificación Adversaria de Doble Lista: *Checking It Twice*)

El **Santa Method** de `affaan-m/ECC` elimina los puntos ciegos de una revisión simple mediante un bucle de verificación con **dos revisores independientes sin contexto compartido** que auditan el entregable contra una lista explícita de criterios (*The List*).

## 1. Flujo de las 5 Fases del Santa Loop

1. **Fase 1 — Construir *The List* (Criterios Explícitos)**:
   - Extraer de `01-spec.md`, `02-tech-spec.md` y `03-tasks.md` la lista cerrada de entregables físicos, invariantes de contrato y comandos DoD.
2. **Fase 2 — Ejecución del Trabajo**:
   - Los subagentes especialistas implementan las tareas asignadas y ejecutan sus pruebas locales.
3. **Fase 3 — Doble Revisión Independiente (*Checking It Twice*)**:
   - Se invocan dos agentes revisores con lentes complementarias (por ejemplo, `@fastapi-reviewer` / `@python-reviewer` + `@gan-evaluator` / `@silent-failure-hunter`) sin que ninguno vea el veredicto del otro:
     - **Revisor A (Lente de Especificación y Contratos)**: Verifica que no falte ningún archivo, campo de DTO o requisito EARS.
     - **Revisor B (Lente Adversaria y de Fallos Ocultos)**: Busca errores silenciados, regresiones, casos límite rotos o texto placeholder.
4. **Fase 4 — Puerta de Decisión (*NICE* vs *NAUGHTY*)**:
   - **`NICE + NICE`**: Ambos revisores emiten veredicto limpio con 0 defectos bloqueantes $\rightarrow$ **Certificación Aprobada**.
   - **Cualquier `NAUGHTY`**: Se consolidan todos los defectos detectados por ambos revisores en una lista única de remediación.
5. **Fase 5 — Corrección Quirúrgica y Re-Verificación**:
   - Se corrigen los defectos y se vuelve a ejecutar la Fase 3 desde cero hasta lograr unanimidad `NICE + NICE` (máximo 3 rondas antes de escalar al usuario).
