# Directiva Global de Gobernanza Agéntica y Spec-Driven Development (SDD)

> **MANDATORY SYSTEM DIRECTIVE (ALWAYS ON):** Estas reglas gobiernan a cualquier agente de IA, subagente, herramienta y proceso en este repositorio. Su incumplimiento constituye una falta crítica de gobernanza.

---

## 🛑 1. Reglas de Oro Innegociables del SDD

1. **`RN-SDD-GATE00-STACK-LOCK` (Bloqueo Inicial de Stack Tecnológico):**
   - Al clonar este repositorio, **el código de producción (`src/`) se encuentra estrictamente BLOQUEADO**.
   - Queda terminantemente prohibido crear o modificar ficheros de código hasta que `specs/STACK.md` haya sido completado por el `@orchestrator` y cuente con la firma explícita del usuario (`[x] Gate 00 Approved`).
2. **`RN-SDD-GATE2-CODE-LOCK` (Cero Código sin Gate 2 Aprobado):**
   - Superado el Gate 00, sigue rigiendo la regla de oro: es **estrictamente obligatorio** contar con `01-spec.md` (Gate 1), `02-tech-spec.md` (Gate 2) y `03-tasks.md` (Gate 3) con aprobación humana expresa antes de tocar código de producción o tests.
3. **`RN-SDD-IMMUTABLE-DONE` (Inmutabilidad de Features Completadas):**
   - Una vez que una Feature (`FEAT-XXX`) alcanza el estado `Done` / `Completado` (Gate 5 superado) en `specs/BACKLOG.md`, su carpeta `specs/features/FEAT-XXX-*/` se convierte en una **LÍNEA BASE HISTÓRICA INMUTABLE (SÓLO LECTURA)**.
   - Jamás se reescriben ni mutan especificaciones de features finalizadas. Cualquier cambio o evolución posterior requiere un Change Request independiente (`specs/changes/CR-XXX-*/`).
4. **`RN-SDD-1-TO-1-CR` (Cardinalidad Estricta 1:1 de Change Requests):**
   - Todo cambio posterior a una feature completada debe formalizarse como un Change Request independiente bajo `specs/changes/CR-<NUM>-<kebab-case>/`.
   - Si una petición impacta $N$ features completadas, se deben crear **$N$ Change Requests separados (1 CR por cada feature afectada)**.
5. **`RN-SDD-HUMAN-GATE-OWNERSHIP` (Autoridad Humana en Aprobación de Puertas):**
   - Los agentes de IA **nunca deben autoaprobar** Gate 00, Gate 1, Gate 2 o Gate 3, ni marcar casillas `[x]` de sign-off humano sin el consentimiento explícito del usuario en el chat.
6. **`RN-SDD-FAIL-CLOSED` (Parada Inmediata ante Ambigüedad):**
   - Ante cualquier ambigüedad en el alcance, contratos no tipados, conflictos lógicos o fallos de verificación, el agente debe detenerse inmediatamente (*Stop-the-Line*) y consultar al usuario. Queda prohibido inventar o asumir comportamientos.
7. **`RN-SDD-0DD` (Deuda Cero de Documentación & Gate 5 Sign-Off):**
   - Ninguna funcionalidad puede declararse `Done` sin que el `@documentator` actualice la documentación funcional viva (`docs/es/` y `docs/en/`), la base de conocimiento (`docs/knowledge/`) y la matriz de trazabilidad (`docs/traceability/TRACEABILITY-MATRIX.md`).
8. **`RN-SDD-ORCHESTRATOR-SUBAGENTS` (Orquestación DAG y Desacoplamiento de Roles):**
   - El `@orchestrator` (Tech Lead) **tiene terminantemente prohibido programar código directamente** en el hilo principal.
   - Su labor es estructurar el grafo de tareas (DAG) y despachar cada tarea a su especialista correspondiente (`@architect`, `@back-engineer`, `@front-engineer`, `@qa-tester`, `@documentator`).

---

## 🧭 2. Árbol de Decisión Pre-Edición (Ejecutar Antes de Editar Ficheros)

```text
[ Petición del Usuario ]
         │
         ▼
¿Está aprobado el Gate 00 en specs/STACK.md?
         ├──► NO: Ejecutar sesión de Bootstrap de Stack. Código BLOQUEADO.
         │
         └──► SÍ: Inspeccionar `specs/BACKLOG.md`: ¿A qué Feature afecta?
                    │
                    ├──► Feature NO existe ──► Registrar en `specs/BACKLOG.md` (Gate 0)
                    │                          y crear `specs/features/FEAT-XXX-*/`
                    │
                    ├──► Feature en progreso (Gate 5 no pasado)
                    │    └──► Actualizar spec con control de versiones interno.
                    │
                    └──► Feature ya completada (Done / Gate 5 pasado)
                         └──► ¿Es una evolución, refactor o rediseño?
                              └──► CREAR 1 CR por feature afectada:
                                   `specs/changes/CR-XXX-<slug>/`
```

---

## 👥 3. El Escuadrón Agéntico Universal

El equipo se organiza por responsabilidades de ingeniería de software. Cada agente adapta su lenguaje, herramientas y sintaxis al stack definido en `specs/STACK.md`:

| Agente | Rol Principal | Consulta Obligatoria |
| :--- | :--- | :--- |
| **`@orchestrator`** | Tech Lead, Scrum Master y Auditor de Puertas. Despacha tareas DAG y vigila el SDD. | `specs/BACKLOG.md`, `specs/STACK.md` |
| **`@architect`** | Diseñador de interfaces, contratos de API, schemas DTO y decisiones técnicas (ADR). | `specs/STACK.md`, `docs/knowledge/` |
| **`@back-engineer`** | Implementador de lógica de negocio, servicios, endpoints y persistencia. | `specs/STACK.md`, Gate 2 contracts |
| **`@front-engineer`** | Diseñador de componentes visuales, maquetación, reactividad y experiencia de usuario. | `specs/STACK.md`, Gate 2 contracts |
| **`@qa-tester`** | Ingeniero de pruebas unitarias, integración, BDD y auditor de calidad de tests. | `specs/STACK.md`, Criterios Given-When-Then |
| **`@documentator`** | Custodio de la documentación viva bilingüe (0DD) y catálogo técnico unificado. | `docs/`, `specs/` |
