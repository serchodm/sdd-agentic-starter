# Directiva Global de Gobernanza Agéntica y Spec-Driven Development (SDD)

> **MANDATORY SYSTEM DIRECTIVE (ALWAYS ON):** Estas reglas gobiernan a cualquier agente de IA, subagente, herramienta y proceso en este repositorio. Su incumplimiento constituye una falta crítica de gobernanza.

---

## 🛑 1. Reglas de Oro Innegociables del SDD

1. **`RN-SDD-GATE-S0-STACK-LOCK` (Bloqueo Inicial de Stack Tecnológico — Legacy: `RN-SDD-GATE00-STACK-LOCK`):**
   - Al clonar este repositorio, **el código de producción (`src/`) se encuentra estrictamente BLOQUEADO**.
   - Queda terminantemente prohibido crear o modificar ficheros de código hasta que `specs/STACK.md` haya sido completado por el `@orchestrator` y cuente con la firma explícita del usuario (`[x] Gate S0 Approved`, aceptándose `[x] Gate 00 Approved` como alias legacy).
2. **`RN-SDD-GATE2-CODE-LOCK` (Cero Código sin Gate 2 Aprobado):**
   - Superado el Gate S0, sigue rigiendo la regla de oro: es **estrictamente obligatorio** contar con `01-spec.md` (Gate 1), `02-tech-spec.md` (Gate 2) y `03-tasks.md` (Gate 3) con aprobación humana expresa antes de tocar código de producción o tests.
3. **`RN-SDD-IMMUTABLE-DONE` (Inmutabilidad de Features Completadas):**
   - Una vez que una Feature (`FEAT-XXX`) alcanza el estado `Done` / `Completado` (Gate 5 superado) en `specs/BACKLOG.md`, su carpeta `specs/features/FEAT-XXX-*/` se convierte en una **LÍNEA BASE HISTÓRICA INMUTABLE (SÓLO LECTURA)**.
   - Jamás se reescriben ni mutan especificaciones de features finalizadas. Cualquier cambio o evolución posterior requiere un Change Request independiente (`specs/changes/CR-XXX-*/`).
4. **`RN-SDD-1-TO-1-CR` (Cardinalidad Estricta 1:1 de Change Requests):**
   - Todo cambio posterior a una feature completada debe formalizarse como un Change Request independiente bajo `specs/changes/CR-<NUM>-<kebab-case>/`.
   - Si una petición impacta $N$ features completadas, se deben crear **$N$ Change Requests separados (1 CR por cada feature afectada)**.
5. **`RN-SDD-HUMAN-GATE-OWNERSHIP` (Autoridad Humana en Aprobación de Puertas):**
   - Los agentes de IA **nunca deben autoaprobar** Gate S0, Gate 1, Gate 2 o Gate 3, ni marcar casillas `[x]` de sign-off humano sin el consentimiento explícito del usuario en el chat.
6. **`RN-SDD-FAIL-CLOSED` (Parada Inmediata ante Ambigüedad):**
   - Ante cualquier ambigüedad en el alcance, contratos no tipados, conflictos lógicos o fallos de verificación, el agente debe detenerse inmediatamente (*Stop-the-Line*) y consultar al usuario. Queda prohibido inventar o asumir comportamientos.
7. **`RN-SDD-0DD` (Deuda Cero de Documentación & Gate 5 Sign-Off):**
   - Ninguna funcionalidad puede declararse `Done` sin que el `@documentator` actualice la documentación funcional viva (`docs/es/` y `docs/en/`), la base de conocimiento (`docs/knowledge/`) y la matriz de trazabilidad (`docs/traceability/TRACEABILITY-MATRIX.md`).
8. **`RN-SDD-ORCHESTRATOR-SUBAGENTS` (Orquestación DAG y Desacoplamiento de Roles):**
   - El `@orchestrator` (Tech Lead) **tiene terminantemente prohibido programar código directamente** en el hilo principal.
   - Su labor es estructurar el grafo de tareas (DAG) y despachar cada tarea a su especialista correspondiente (`@architect`, `@back-engineer`, `@front-engineer`, `@qa-tester`, `@documentator`).
9. **`RN-SDD-SESSION-LIFECYCLE` (Límites Estrictos de Sesión y Control de Contexto):**
   - Un único hilo de conversación **NUNCA DEBE** abarcar múltiples Features (`FEAT-XXX`), Change Requests (`CR-XXX`) o Bugs (`BUG-XXX`).
   - El ciclo de vida máximo de un hilo del `@orchestrator` es de estrictamente **1 Work Item**. Una vez completado el Gate 5 (`git push`), el hilo finaliza y se abre uno nuevo.
   - **División de Fases de Sesión (Session Phase Splitting):**
     - **Sesión A (Arquitectura & Specs — Gates 0 a 3):** Usar modelos de alto razonamiento exclusivamente para redactar y validar `01-spec.md`, `02-tech-spec.md` y `03-tasks.md`.
     - **Sesión B (Ejecución & Cierre — Gates 4 y 5):** Abrir un hilo nuevo y limpio cargando sólo `02-tech-spec.md`, `03-tasks.md` y `docs/knowledge/` para despachar subagentes y ejecutar `@documentator` (Gate 5) con modelos rápidos y coste-eficientes.
10. **`RN-SDD-SELECTIVE-CONTEXT` (Cero Exploración Ciega y Lecturas Acotadas):**
    - Antes de ejecutar comandos de búsqueda masiva (`grep` / exploraciones recursivas), los agentes **DEBEN** consultar `docs/knowledge/SYSTEM_TOPOLOGY.md`, `API_CATALOG.md` y `DATA_MODELS.md` para localizar los ficheros objetivo exactos.
    - Al actualizar `TRACEABILITY-MATRIX.md` o ficheros en `docs/knowledge/*` durante Gate 5, usar lecturas y ediciones acotadas por rangos en lugar de volcar ficheros completos al contexto si superan las 200 líneas.
11. **`RN-SDD-BRANCH-SYNC` (Sincronización y Protección de Ramas Git):**
    - **Protección Estricta de `main`**: Queda terminantemente prohibido comitear o pushear código de desarrollo directamente a la rama `main`.
    - Cada vez que una Feature (`FEAT-XXX`), Change Request (`CR-XXX`), Bug (`BUG-XXX`) sea validada, **ejecutar siempre `git add`, `git commit` (Conventional Commits) y `git push origin <rama-activa>`** en su rama de trabajo (`feat/*`, `change/*`, `fix/*`).
    - Las actualizaciones globales de gobernanza y framework se integran en la rama `develop`.
    - La rama `main` se actualiza exclusivamente mediante Pull Request de Release (`release/*`) o Hotfix (`hotfix/*`) con aprobación humana explícita.
12. **`RN-SDD-CONTEXT-SEMAPHORE & AUTO-HANDOFF` (Higiene de Sesión y Gobernanza de Tokens):**
    - El `@orchestrator` **DEBE** incluir obligatoriamente el pie de telemetría de contexto al final de cada respuesta con el formato exacto:
      ```markdown
      ---
      🟢/🟡/🔴 **Context Health:** Turn X/15 | Blocks: Y/2 | Gate: Z<br>
      &emsp;&emsp;↳ **Tokens (Last Turn):** In X.Xk · Out X.Xk · Cache X.Xk<br>
      &emsp;&emsp;↳ **Tokens (Session Total):** In X.Xk · Out X.Xk · Cache X.Xk (Hit: XX.X%)
      ```
    - El `@orchestrator` **DEBE** actualizar automáticamente `.agents/ACTIVE_STATE.md` al: (a) aprobar Gate 3 (sign-off de `03-tasks.md`), (b) completar cualquier bloque de ejecución en Gate 4, o (c) alcanzar los umbrales Amarillo (`Turno >= 11` o `Bloques == 2`) o Rojo (`Turno >= 15` o `Bloques >= 3`).
    - Al pasar de Gate 3 (Diseño/Specs) a Gate 4 (Implementación), o de Gate 4 a Gate 5 (`@documentator`), el `@orchestrator` **DEBE** actualizar `.agents/ACTIVE_STATE.md` e instruir al usuario a abrir una sesión nueva con `/continue` o `/gate5` para cambiar de modelos de alto razonamiento a modelos rápidos de ejecución.
    - Al alcanzar el umbral Rojo (🔴), el `@orchestrator` **DEBE** aplicar un *Stop-the-Line* estricto, actualizar `.agents/ACTIVE_STATE.md` y negarse a despachar más subagentes hasta que el usuario ejecute `/continue` en un hilo limpio.

---

## 🧭 2. Árbol de Decisión Pre-Edición (Ejecutar Antes de Editar Ficheros)

```text
[ Petición del Usuario ]
         │
         ▼
¿Está aprobado el Gate S0 en specs/STACK.md?
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

---

## 🏛️ 4. Matriz de Carga Perezosa de Reglas (Conditional Lazy-Loading Matrix)

**DIRECTIVA CRÍTICA DE AHORRO DE TOKENS & GOBERNANZA DE CONTEXTO:** PROHIBIDO cargar globalmente todos los archivos de `.agents/rules/*` simultáneamente en el contexto. El `@orchestrator` y los subagentes solo deben cargar en memoria las reglas listadas explícitamente en `Mandatory Context Files` de `.agents/ACTIVE_STATE.md` o las que correspondan estrictamente a su Gate activo o capa técnica:

- **Gate S0 (`specs/STACK.md`):** Leer únicamente `.agents/rules/00-stack-lock.md`.
- **Gate 0 (`specs/BACKLOG.md`):** Leer únicamente `.agents/rules/01-sdd-lifecycle.md`.
- **Gate 1 (`01-spec.md`):** Leer únicamente `.agents/rules/03-ears-requirements.md` y `.agents/rules/01-sdd-lifecycle.md`.
- **Gates 2 y 3 (`02-tech-spec.md` y `03-tasks.md`):** Leer únicamente `.agents/rules/04-multiagent-dag.md` + las directivas técnicas fijadas en `specs/STACK.md`.
- **Gate 4 (Subagentes de Código):** Cada especialista lee exclusivamente su contrato de `02-tech-spec.md`, su regla de rol (`.agents/agents/<agente>.md`), `.agents/rules/05-security-and-secrets.md`, `.agents/rules/07-engineering-baseline.md` y las reglas del stack pack activo que le correspondan.
- **Gate 5 (`@documentator`):** Leer únicamente `.agents/rules/06-functional-doc-0dd.md`.
- **Change Management (CR-XXX):** Leer `.agents/rules/02-change-management.md`.

---

## ⚡ 5. Comandos Deterministas de Verificación DoD (Zero Discovery Overhead)

Queda terminantemente prohibido que los subagentes ejecuten comandos exploratorios, inspeccionen archivos de configuración a ciegas o ejecuten suites completas de tests sin necesidad.

1. **Definición en Gate S0:** En la Sección 2.5 de `specs/STACK.md` se congelan los comandos exactos y pre-probados del proyecto para:
   - **Lint & Typecheck**
   - **Prueba Unitaria Acotada** (en memoria, mocks, sin BD/red externa — ejecución < 1s)
   - **Prueba de Integración** (con servicios auxiliares levantados)
   - **Build de Producción**
   - **Verificación de Entorno / Infraestructura**
2. **Asignación en Gate 3:** Cada tarea atómica en `03-tasks.md` DEBE incluir su campo `- *Comando de verificación DoD*: <comando exacto>`, garantizando cero overhead de descubrimiento y cero tokens malgastados en fallos de ejecución.
