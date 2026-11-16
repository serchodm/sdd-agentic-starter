# Especificación Funcional: Quality Gates Visuales Condicionales

- **ID de la Feature (Work Item del Framework)**: `FWK-003-conditional-visual-gates`
- **RFC de Origen**: [`RFC-001` v2 (Aceptado)](../../rfcs/RFC-001-ui-ux-pro-max.md)
- **Estado**: `Aprobado` (Gate 1 aprobado por el usuario el 2026-11-13)
- **Analista Funcional / Tech Lead**: `@orchestrator` / `@qa-tester` / `@a11y-architect` (actuando sobre mandato de `RFC-001` v2)
- **Fecha de Creación**: 2026-11-12
- **Última Actualización**: 2026-11-12

---

## 1. Resumen, Contexto y Claridad Epistémica (`morluto/rea`)
- **Problema y Valor de Negocio**: Tras completar `FWK-001` (materialización fiable de packs y lock v2) y `FWK-002` (pack `capability-ui-design`, especialista `@ui-ux-designer`, workflow `ui-design-review.md`, DoR en arquetipos y ciclo semver de `docs/design-system/`), el framework cuenta con especificación de diseño visual en Gate 2. Sin embargo, en **Gate 4 (Implementación y QA)** y en **CI/CD**, no existen *Quality Gates* formales, deterministas y automatizados para verificar que la implementación visual respete el diseño aprobado:
  1. **Deriva de Tokens (`design-tokens.json` vs código vs `MASTER.md`)**: No existe una herramienta determinista y offline que compruebe que los tokens definidos en `design-tokens.json` y la normativa visual de `MASTER.md` permanezcan 100% sincronizados, ni que detecte el uso de valores literales de estilo (colores hexadecimales hardcodeados, espaciados o fuentes arbitrarias) en el código de componentes cuando existen tokens oficiales.
  2. **Verificaciones de Accesibilidad (WCAG 2.2 AA) y Navegación**: En Gate 4, `@qa-tester` carece de una cláusula operativa para exigir pruebas de contraste de color (mínimo `4.5:1` texto normal / `3:1` texto grande y controles) y navegación por teclado (foco visible, ausencia de trampas de teclado).
  3. **Comprobación Responsive**: No está formalizada la verificación de renderizado en los 3 viewports canónicos (`375px` móvil, `768px` tablet, `1440px` escritorio) para evitar desbordamientos horizontales inesperados.
  4. **Gobernanza de Baselines Visuales (Visual Regression)**: Existe un riesgo crítico de **falsos verdes ("silent pass")** cuando un test visual carece de captura de referencia previa, o de que un agente de IA auto-apruebe silenciosamente una regresión visual alterando los baselines sin supervisión humana.
  5. **Condicionalidad y Cero Overhead**: Los proyectos sin interfaz visual (`api-only`, CLI) no deben sufrir penalizaciones de tiempo ni dependencias innecesarias, y los entornos sin navegadores instalados deben degradar elegantemente sin romper la verificación offline de tokens.

- **Hechos Observados (Observations)**:
  - `.sdd/framework/BACKLOG.md` (`L15`): `FWK-003` figura como dependiente de `FWK-002` (actualmente `Done`), habilitando su apertura.
  - `.sdd/framework/rfcs/RFC-001-ui-ux-pro-max.md`:
    - §6 (Gate 4, `L176`): *"El DoD de las tareas UI incluye comprobaciones visuales verificables (`@qa-tester`): navegador, responsive, teclado, contraste, estados, coherencia con tokens. Cambios de baseline de capturas requieren revisión humana. Nunca un score subjetivo como único quality gate."*
    - §9 (`L239-L242`): `FWK-003` mandate: *"Comprobaciones condicionales en qa-tester, a11y-architect y CI (solo con herramientas realmente instaladas): contraste, teclado, responsive, coherencia de tokens, baselines de capturas con revisión humana."*
    - §10 Escenario `#13` (`L265`): *"Errores de contraste/teclado y regresiones de captura producen resultado verificable y bloqueante."*
    - §11 (`L276`): *"Deriva entre MASTER.md y design-tokens.json -> Verificación de coherencia en QA (FWK-003)."*
  - `.agents/agents/qa-tester.md` (`L49-L72`): Contempla únicamente 3 auditorías obligatorias (`sdd-silent-failure-audit`, `sdd-test-quality-audit`, `sdd-spec-compliance-audit`). No incluye directrices para auditoría visual ni coherencia de tokens.
  - `.agents/agents/a11y-architect.md`: Contempla checklist WCAG 2.2 AA pero está enfocado al diseño y arquitectura, sin protocolo formal de auditoría de pruebas en Gate 4.
  - `.sdd/catalog/archetypes/front-test.archetype.md` (`L38-L44`): Su DoR solo pide Criterios de Aceptación y componentes listos; su DoD solo exige `{{FRONTEND_TEST_CMD}}` sin mencionar tokens, accesibilidad ni regresión visual.
  - `specs/templates/02-technical-spec.template.md` (`L101-L107`): Sección 7 lista únicamente tests unitarios, `verify_architecture_boundaries.py` y perturbación semántica; no menciona quality gates visuales.
  - `specs/templates/03-tasks.template.md` (`L31-L34`, `L108-L113`): Bloque D contiene tareas de testing, pero sin especificación de comandos ni DoD para quality gates visuales.
  - `.github/workflows/ci.yml` (`L31-L58`): Ejecuta scripts de gobernanza en Python y tests unitarios, pero no dispone de verificación determinista de tokens ni ejecución condicional de auditoría visual/accesibilidad.
  - `scripts/`: No existe actualmente un validador determinista de design tokens (`sdd_tokens_validator.py` o equivalente) que opere 100% offline con la librería estándar de Python.

- **Restricciones Derivadas (Derivations)**:
  - `RN-SDD-HUMAN-GATE-OWNERSHIP`: La creación o actualización de baselines visuales requiere revisión y sign-off humano explícito; los agentes de IA tienen estrictamente prohibido actualizar snapshots de forma autónoma.
  - `RN-SDD-SELECTIVE-CONTEXT` & `RN-SDD-FAIL-CLOSED`: Los quality gates visuales solo aplican a features que tocan pantallas (`SCR-###`) con `capability-ui-design` o interfaz web activa. En proyectos `api-only` o CLI, el coste en tiempo y tokens debe ser cero.
  - **Ejecución Offline y Ligera**: El starter debe contar con un validador en Python stdlib (`scripts/sdd_tokens_validator.py`) para verificar la coherencia de tokens y ausencia de literales sin requerir `npm`, Node.js ni navegadores pesados en las pruebas base del starter.

---

## 1.1. Fuentes Registradas y Trazabilidad (`SRC-###`)

| ID Fuente | Tipología / Origen | Fecha | Notificado por | Descripción / Contenido Facilitado |
|---|---|---|---|---|
| `SRC-001` | RFC Aceptado (`RFC-001` v2) | 2026-11-10 | Usuario Humano | Mandatos para `FWK-003` (§6 Gate 4, §9 Alcance, §10 Escenario `#13`, §11 Riesgo de deriva de tokens). |
| `SRC-002` | Chat / Orden directa + Inspección de workspace | 2026-11-12 | Usuario / `@orchestrator` | Orden *"iniciar FWK-003"* tras merge de `FWK-002` en `develop`; verificación de tests verdes (37/37) y estado del workspace. |
| `SRC-003` | Estándar Funcional (`FUNCTIONAL_DOCUMENTATION_STANDARD.md`) | 2026-10-31 | Repositorio | §18 (Fase E: Verificación y coherencia entre wireframe de baja fidelidad, prototipo hi-fi e implementación). |
| `SRC-004` | Catálogo y Arquetipos Frontend | 2026-11-11 | Starter | Arquetipos `front-ui`, `front-engineer`, `tier-frontend` (actualizados en FWK-002) y `front-test` (pendiente de actualización). |

---

## 1.2. Registro de Ambigüedades y Cuestiones Pendientes (`AMB-###`)
> Aplicar Stop-the-Line (`RN-SDD-FAIL-CLOSED`) antes de autorizar Gate 1 y pasar a Gate 2:

| ID | Descripción de la Ambigüedad / Conflicto | Requisitos Afectados | Propuesta de Resolución para el Usuario | Impacto Funcional | Estado |
|---|---|---|---|---|---|
| `AMB-001` | `RFC-001` (§9, §11) exige verificar la coherencia entre `MASTER.md`, `design-tokens.json` y el código fuente, pero no especifica la tecnología de dicha validación. | `RF-001`, `RF-002`, `RF-003` | **Resolución (Opción A — Recomendada)**: Desarrollar `scripts/sdd_tokens_validator.py` en Python 3.12 stdlib (sin dependencias externas). Este script valida: (a) coherencia interna bidireccional entre `design-tokens.json` y `MASTER.md`, (b) formato de tokens (colores hex/rgba, tipografía, espaciado), y (c) `--check-sources <dir>` para detectar uso de literales de color/estilo donde existan tokens normativos. 100% offline y determinista. | Garantiza verificación reproducible y ligera en cualquier entorno sin dependencias Node. | `Resolved` |
| `AMB-002` | `RFC-001` §9 prescribe que las comprobaciones en QA y CI apliquen *"solo con herramientas realmente instaladas"*. ¿Cómo se gestionan entornos sin Playwright/axe-core instalado? | `RF-004`, `RF-006` | **Resolución (Opción A — Modelo Bi-Nivel)**: <br>1. **Nivel Estático (Obligatorio y Bloqueante)**: Validación de coherencia de tokens (`sdd_tokens_validator.py`) y linters estáticos de código. Siempre falla si hay incoherencia.<br>2. **Nivel Dinámico (Condicional a Disponibilidad)**: Pruebas de navegador (contraste, teclado, responsive y capturas). Si el comando de test E2E/navegador está configurado en `STACK.md` y las herramientas están presentes, se ejecutan de forma bloqueante. Si la herramienta no está disponible, `@qa-tester` emite aviso explícito `SKIPPED_UNAVAILABLE_TOOL` (nunca aprobado falso) y exige verificación visual manual al desarrollador. | Evita bloqueos en máquinas sin navegadores instalados sin generar falsos aprobados. | `Resolved` |
| `AMB-003` | ¿Cómo se evita el falso verde (*silent pass*) cuando no existe baseline previo de captura de pantalla, y cómo se gobierna la actualización de baselines? | `RF-004`, `RF-005` | **Resolución (Opción A — Bloqueo Inconclusive + Sign-off Humano)**: Si no existe captura de referencia previa, el test devuelve estado **`INCONCLUSIVE`** y bloquea Gate 4 hasta que el baseline se genere y sea revisado. Queda **estrictamente prohibido** que un agente de IA ejecute flags tipo `--update-snapshots` o sobreescriba baselines visuales sin autorización humana expresa en el chat. | Elimina la autocomplacencia agéntica en regresiones visuales. | `Resolved` |
| `AMB-004` | Articulación de roles entre `@qa-tester` y `@a11y-architect` en Gate 4. | `RF-007`, `RF-008` | **Resolución (Opción A)**: `@qa-tester` ejecuta y certifica la suite técnica global de Gate 4 (incluyendo la 4ª auditoría: *Quality Gate Visual y Coherencia de Tokens*). Si se detectan fallos complejos de accesibilidad WCAG 2.2 AA (foco, ARIA), `@qa-tester` invoca a `@a11y-architect` para diagnosticar la solución y certificar el dictamen de accesibilidad. | Claridad de responsabilidades y división del trabajo sin solapamientos. | `Resolved` |
| `AMB-005` | Integración en `.github/workflows/ci.yml` del starter base frente a proyectos de usuario con UI. | `RF-009`, `RF-010` | **Resolución (Opción A)**: En el CI del starter, añadir la comprobación offline de tokens sobre el catálogo y plantillas (`scripts/sdd_tokens_validator.py`). Para proyectos generados con frontend, documentar el step condicional en la plantilla de CI que ejecuta los tests visuales solo si `uiux.enabled: true` y existen ficheros en `frontend/`. | Mantiene el CI del starter ultrarrápido y provee la receta completa para proyectos reales. | `Resolved` |

---

## 2. Historias de Usuario y Casos de Uso

### Historia 1: Prevención Determinista de Deriva de Tokens de Diseño
> **Como** Tech Lead y auditor de calidad del proyecto,
> **Quiero** ejecutar una validación automática y offline de coherencia de design tokens,
> **Para que** ningún componente frontend use colores hexadecimales hardcodeados o tokens inexistentes, y para asegurar que `MASTER.md` y `design-tokens.json` nunca diverjan.

### Historia 2: Quality Gate Visual Condicional en `@qa-tester` y `front-test`
> **Como** ingeniero de pruebas (`@qa-tester` / `front-test`),
> **Quiero** disponer de un protocolo claro de verificación visual en Gate 4 (contraste WCAG 2.2 AA, navegación por teclado, renderizado en 3 viewports y estados UI),
> **Para que** ninguna pantalla (`SCR-###`) pase a producción con defectos visuales o de accesibilidad cuando las herramientas estén disponibles en el stack.

### Historia 3: Gobernanza Estricta de Regresiones Visuales sin Falsos Verdes
> **Como** mantenedor del proyecto,
> **Quiero** que la ausencia de capturas baseline devuelva `INCONCLUSIVE` y que cualquier alteración de snapshots requiera sign-off humano explícito,
> **Para que** los agentes de IA no puedan enmascarar regresiones visuales auto-aprobando capturas rotas.

### Historia 4: Cero Sobrecarga en Proyectos sin UI
> **Como** desarrollador de proyectos Solo Backend (`api-only`) o CLI,
> **Quiero** que los quality gates visuales se omitan de forma totalmente transparente,
> **Para que** no se consuman tokens innecesarios ni se exijan dependencias gráficas donde no existen pantallas.

---

## 3. Alcance del Work Item (In-Scope / Out-of-Scope)

### 🎯 Dentro del Alcance (In-Scope)
- **Script Validador de Tokens (`scripts/sdd_tokens_validator.py`)**:
  - Implementación en Python 3.12 stdlib (100% determinista y offline, sin dependencias externas).
  - Verificación de esquema JSON de `design-tokens.json` (colores válidos, escala tipográfica, espaciado).
  - Verificación de coherencia bidireccional entre `docs/design-system/MASTER.md` y `docs/design-system/design-tokens.json`.
  - Opción `--check-sources <directorio>` para escanear componentes/archivos de diseño en busca de literales prohibidos (ej. `#ffffff`, `#000000`, valores de color arbitrarios) donde existen tokens normativos declarados.
- **Auditoría de Calidad en `@qa-tester` (`.agents/agents/qa-tester.md`)**:
  - Incorporación de la **4ª Auditoría Obligatoria**: *"Quality Gate Visual y Coherencia de Tokens"*.
  - Protocolo de 5 comprobaciones visuales: (1) tokens sin literales hardcodeados, (2) contraste WCAG 2.2 AA (`4.5:1` / `3:1`), (3) navegación por teclado e indicadores visibles, (4) responsive en 375px/768px/1440px sin overflow horizontal, y (5) baselines de capturas con regla de revisión humana.
- **Actualización de Arquetipos Frontend (`.sdd/catalog/archetypes/front-test.archetype.md`)**:
  - Inyección en DoR de las referencias a pantallas `SCR-XXX`, tokens y prototipos hi-fi aprobados en Gate 2.
  - Inyección en DoD de los checks visuales y la ejecución de `sdd_tokens_validator.py`.
- **Actualización de `@a11y-architect`**:
  - Incorporación de pautas de auditoría técnica en Gate 4 como soporte especializado a `@qa-tester`.
- **Actualización de Plantillas de Especificación**:
  - `specs/templates/02-technical-spec.template.md` (Sección 7): Añadir cláusula de Quality Gates Visuales condicionales.
  - `specs/templates/03-tasks.template.md` (Bloque D): Añadir tarea estándar para el Quality Gate Visual cuando aplique.
- **Integración en CI (`.github/workflows/ci.yml`)**:
  - Inclusión del paso de validación offline de tokens.
  - Documentación del patrón condicional de visual testing para proyectos derivados.
- **Batería de Pruebas Offline Deterministas (`tests/test_sdd_visual_gates.py`)**:
  - Cobertura completa de los escenarios de validación de tokens, deriva, literales, ausencia de baseline, degradación de herramientas y proyectos sin UI.

### 🚫 Fuera del Alcance (Out-of-Scope)
- `FWK-004` (Unificación de terminología de Gates en `SDD_FRAMEWORK.md`, `BACKLOG.md` y `AGENTS.md`).
- Instalación de navegadores pesados (Chromium, Firefox, WebKit) o dependencias de Node.js en el starter base.
- Implementación de pantallas o lógica de producción en `src/` (el starter permanece limpio con `src/` bloqueado según `RN-SDD-GATE00-STACK-LOCK`).
- Modificación de `specs/BACKLOG.md` del proyecto plantilla (solo se gestiona `.sdd/framework/BACKLOG.md`).

---

## 4. Requisitos del Sistema bajo Protocolo EARS

| ID Requisito | Fuente | Patrón EARS | Cláusula EARS (Sintaxis Formal Canónica) | Componente Afectado |
|---|---|---|---|---|
| `RF-001` | `SRC-001` | `Ubiquitous` | `El framework deberá proveer el script determinista scripts/sdd_tokens_validator.py basado exclusivamente en Python 3.12 stdlib, capaz de verificar la sintaxis, completitud y coherencia bidireccional entre docs/design-system/design-tokens.json y docs/design-system/MASTER.md sin llamadas de red ni dependencias externas.` | `scripts/sdd_tokens_validator.py` |
| `RF-002` | `SRC-001` | `Unwanted` | `SI scripts/sdd_tokens_validator.py detecta una divergencia de nombres o valores entre design-tokens.json y MASTER.md, O SI detecta el uso de literales de color/estilo hardcodeados en los ficheros analizados existiendo tokens normativos, ENTONCES el script deberá abortar con código de salida distinto de cero (fail-closed) detallando el fichero, la línea y la discrepancia encontrada.` | `scripts/sdd_tokens_validator.py` |
| `RF-003` | `SRC-001` | `State-driven` | `MIENTRAS una feature incorpore o modifique pantallas (SCR-###) con interfaz web activa, el agente @qa-tester y el arquetipo front-test deberán exigir en Gate 4 la certificación formal de la 4ª Auditoría de Calidad ("Quality Gate Visual y Coherencia de Tokens") antes de autorizar el paso a Gate 5.` | `.agents/agents/qa-tester.md`, `.sdd/catalog/archetypes/front-test.archetype.md` |
| `RF-004` | `SRC-001` | `Unwanted` | `SI una suite de pruebas visuales carece de captura de referencia previa (baseline) para una pantalla o componente, ENTONCES el resultado de la prueba deberá ser INCONCLUSIVE y bloquear la aprobación de Gate 4 hasta que el baseline sea generado y aprobado formalmente por un humano.` | `.agents/agents/qa-tester.md`, `specs/templates/02-technical-spec.template.md` |
| `RF-005` | `SRC-001` | `Event-driven` | `CUANDO se detecte una regresión visual respecto al baseline aprobado, el sistema de pruebas deberá fallar de forma bloqueante, quedando terminantemente prohibido que los agentes de IA ejecuten comandos de auto-actualización de capturas o sobrescriban baselines sin autorización humana explícita en el chat.` | `.agents/agents/qa-tester.md`, `specs/templates/03-tasks.template.md` |
| `RF-006` | `SRC-001` | `State-driven` | `MIENTRAS las herramientas de navegador dinámico (Playwright / axe-core) no estén instaladas o configuradas en el entorno local o CI, el sistema deberá ejecutar obligatoriamente la validación estática de tokens y degradar las pruebas dinámicas emitiendo aviso informativo SKIPPED_UNAVAILABLE_TOOL sin generar un aprobado falso.` | `scripts/sdd_tokens_validator.py`, `.agents/agents/qa-tester.md` |
| `RF-007` | `SRC-001` | `State-driven` | `MIENTRAS specs/STACK.md declare un proyecto sin interfaz visual (preset api-only, CLI o uiux.enabled: false), el sistema de calidad y el CI deberán omitir la ejecución de los quality gates visuales con coste cero en tiempo y sin emitir errores.` | `.agents/agents/qa-tester.md`, `.github/workflows/ci.yml` |
| `RF-008` | `SRC-001` | `Ubiquitous` | `El arquetipo .sdd/catalog/archetypes/front-test.archetype.md deberá incluir en su DoR la referencia a pantallas SCR-XXX, tokens normativos y prototipos hi-fi de Gate 2, y en su DoD la ejecución limpia de sdd_tokens_validator.py y las comprobaciones de contraste, teclado y responsive.` | `.sdd/catalog/archetypes/front-test.archetype.md` |
| `RF-009` | `SRC-001` | `Ubiquitous` | `Las plantillas specs/templates/02-technical-spec.template.md y specs/templates/03-tasks.template.md deberán incorporar secciones explícitas para registrar los comandos y criterios de aceptación del Quality Gate Visual en el Bloque D de tareas.` | `specs/templates/02-technical-spec.template.md`, `specs/templates/03-tasks.template.md` |
| `RF-010` | `SRC-001` | `Event-driven` | `CUANDO se ejecute el flujo de CI en .github/workflows/ci.yml, el pipeline deberá ejecutar la validación determinista de scripts/sdd_tokens_validator.py para certificar la integridad de los tokens del repositorio.` | `.github/workflows/ci.yml` |

---

## 4.1. Reglas de Negocio Vinculantes (`RN-###`)

1. **`RN-01` (Cero Falsos Verdes en Regresiones Visuales)**:
   La falta de baseline visual nunca se interpreta como éxito; genera dictamen `INCONCLUSIVE`. La actualización o recreación de snapshots es potestad exclusiva del usuario humano; los agentes tienen prohibido auto-aceptar diferencias visuales.
2. **`RN-02` (Anti-Deriva de Design Tokens)**:
   `design-tokens.json` y `MASTER.md` deben guardar correspondencia biunívoca en nombres y valores. Ningún archivo fuente frontend analizado puede declarar colores hexadecimales literales si existe un token semántico correspondiente.
3. **`RN-03` (Degradación Determinista Bi-Nivel)**:
   La validación estática de tokens es 100% obligatoria y offline en todo proyecto con Design System activo. Las comprobaciones dinámicas de navegador dependen de la disponibilidad de herramientas; su ausencia emite `SKIPPED_UNAVAILABLE_TOOL` y exige verificación manual sin falsos aprobados.
4. **`RN-04` (Poda Absoluta en Proyectos sin UI)**:
   En proyectos `api-only` o CLI, los quality gates visuales quedan deshabilitados en `@qa-tester`, plantillas y CI, garantizando cero overhead de ejecución.
5. **`RN-05` (Cuádruple Auditoría de Calidad en Gate 4)**:
   Para declarar completado el Gate 4 en features con UI, `@qa-tester` debe certificar:
   - 1. *Silent Failure Audit* (`sdd-silent-failure-audit`)
   - 2. *Test Quality Audit* (`sdd-test-quality-audit`)
   - 3. *Spec Compliance Audit* (`sdd-spec-compliance-audit`)
   - 4. *Visual Quality & Token Gate* (`sdd_tokens_validator.py` + checklist visual).

---

## 4.2. Example Mapping (Datos Concretos de Entrada / Salida)

| Regla Asociada | Caso de Ejemplo | Datos de Entrada (Input Real) | Estado / Precondición | Salida Esperada (Output Verificable) |
|---|---|---|---|---|
| `RN-02` | Tokens íntegros y sincronizados | `design-tokens.json` con `color.primary: #2563eb` y `MASTER.md` documentando `#2563eb` | Design System activo | Exit code `0`; mensaje `[OK] Design tokens and MASTER.md are 100% coherent`. |
| `RN-02` | Deriva de tokens (incoherencia) | `design-tokens.json` añade `color.accent: #f59e0b` ausente en `MASTER.md` | Ejecución de validador | Exit code `1`; error detallando `Token 'color.accent' declared in JSON but missing in MASTER.md`. |
| `RN-02` | Literal prohibido en código | Componente `Button.tsx` contiene `style={{ backgroundColor: "#2563eb" }}` existiendo `color.primary` | Validador con `--check-sources` | Exit code `1` o advertencia bloqueante: `Hardcoded color '#2563eb' detected in Button.tsx:12; use token 'color.primary'`. |
| `RN-01` | Falta de captura baseline (`RFC-001` §10 #13) | Test visual ejecuta suite de capturas en `375px` y no existe `baseline/SCR-001-mobile.png` | Suite E2E visual | Estado `INCONCLUSIVE`; Gate 4 bloqueado hasta revisión y guardado de baseline por el usuario. |
| `RN-01` | Regresión visual de píxeles (`RFC-001` §10 #13) | Botón desplazado 15px por fallo de CSS respecto a `baseline/SCR-001-desktop.png` | Test visual Playwright | Test falla con `Visual regression detected: 2.4% pixel mismatch > 0.1% threshold`; prohibido `--update-snapshots`. |
| `RN-03` | Entorno sin navegadores instalados | Proyecto con UI pero sin binarios de Chromium en CI | Ejecución de Gate 4 | Validador estático pasa; tests dinámicos emiten `SKIPPED_UNAVAILABLE_TOOL`; `@qa-tester` solicita verificación visual manual. |
| `RN-04` | Proyecto `api-only` | `specs/STACK.md` con `preset: api-only` y sin UI | Gate 4 de backend | Salida limpia; ninguna tarea ni check visual invocado. |

---

## 4.3. Requisitos No Funcionales y SLAs Cuantitativos (Planguage)

- **Tag**: `PERF-TOKENS-VALIDATOR-01`
  - **Ambition**: Validación ultrarrápida y 100% offline de la coherencia de tokens en repositorios con diseño.
  - **Scale**: Tiempo total de ejecución de `uv run python scripts/sdd_tokens_validator.py` sobre un sistema de diseño con más de 100 tokens y 50 archivos de pantalla.
  - **Meter**: Medición de tiempo de ejecución de proceso en entorno local estándar (Windows/Linux).
  - **Baseline**: Inexistente (0 validaciones automatizadas de coherencia de tokens).
  - **Target**: `< 0.3 segundos` para ejecución completa, sin llamadas de red.
  - **Constraint**: `> 1.0 segundo` invalida el requisito.

- **Tag**: `REL-VISUAL-NO-SILENT-PASS-01`
  - **Ambition**: Cero falsos positivos ("silent passes") ante ausencia de capturas de referencia o desajustes visuales.
  - **Scale**: Porcentaje de ausencias de baseline catalogadas como `INCONCLUSIVE`.
  - **Meter**: Batería de pruebas automatizadas en `tests/test_sdd_visual_gates.py`.
  - **Baseline**: `0%` (los arneses convencionales asumen pass o generan snapshots silenciosamente).
  - **Target**: `100%` de ausencias de baseline devuelven `INCONCLUSIVE` de forma bloqueante.
  - **Constraint**: `< 100%` invalida el requisito.

- **Tag**: `PERF-FWK-TESTS-03`
  - **Ambition**: Mantener la suite completa de tests unitarios del framework en tiempos óptimos de ejecución.
  - **Scale**: Tiempo de `uv run python -m unittest discover tests -v`.
  - **Meter**: Tiempo medido por unittest en la suite consolidada.
  - **Baseline**: `6.5 segundos` (37 tests existentes en develop).
  - **Target**: `< 8.0 segundos` para la suite total ampliada con los tests de `FWK-003`.
  - **Constraint**: `> 12.0 segundos` invalida el requisito.

---

## 5. Criterios de Aceptación (BDD / Given-When-Then)

### Escenario 1: Validación limpia de tokens y documentación coherente
- **Dado que** existen `docs/design-system/design-tokens.json` y `docs/design-system/MASTER.md` con los mismos identificadores y valores
- **Cuando** se ejecuta `scripts/sdd_tokens_validator.py --tokens docs/design-system/design-tokens.json --master docs/design-system/MASTER.md`
- **Entonces** el script finaliza con código de salida `0`
- **Y** reporta coherencia total sin discrepancias.

### Escenario 2: Detección de divergencia entre tokens y documentación normativa (`RFC-001` §11)
- **Dado que** se añade un nuevo token en `design-tokens.json` pero no se documenta en `MASTER.md`
- **Cuando** se ejecuta `scripts/sdd_tokens_validator.py`
- **Entonces** el script aborta con código de salida `1`
- **Y** emite un mensaje de error explícito indicando el token no sincronizado.

### Escenario 3: Detección de colores literales hardcodeados en código fuente
- **Dado que** un archivo de componente en `frontend/` utiliza un color literal `#3b82f6` que coincide con el token normativo `color.brand.primary`
- **Cuando** se ejecuta `scripts/sdd_tokens_validator.py --check-sources frontend/`
- **Entonces** el script detecta la ocurrencia, indica fichero y línea
- **Y** exige el uso del token en lugar del literal.

### Escenario 4: Bloqueo de Gate 4 ante ausencia de baseline visual (`RFC-001` §10 #13)
- **Dado que** una feature con pantallas `SCR-001` ejecuta su suite de pruebas visuales
- **Y** no existe ningún archivo de captura previa en el directorio de baselines
- **Cuando** `@qa-tester` evalúa el resultado de la prueba
- **Entonces** el veredicto es catalogado como `INCONCLUSIVE`
- **Y** Gate 4 queda bloqueado hasta que el usuario humano apruebe el baseline inicial.

### Escenario 5: Bloqueo de Gate 4 ante regresión visual sin auto-actualización agéntica (`RFC-001` §10 #13)
- **Dado que** un componente presenta una alteración visual que supera el umbral de tolerancia frente al baseline
- **Cuando** se ejecuta la prueba de regresión
- **Entonces** el test falla de forma verificable y bloqueante
- **Y** el agente tiene prohibido actualizar los baselines de forma autónoma.

### Escenario 6: Degradación elegante ante ausencia de herramientas de navegador dinámico
- **Dado que** el entorno de ejecución no dispone de binarios de Chromium o Playwright instalados
- **Cuando** se ejecuta la verificación de calidad en Gate 4
- **Entonces** la validación estática de tokens se ejecuta normalmente en verde
- **Y** las pruebas que requieren navegador emiten estado `SKIPPED_UNAVAILABLE_TOOL` solicitando verificación visual manual sin emitir un falso aprobado.

### Escenario 7: Cero overhead en proyectos sin interfaz visual (`api-only` / CLI)
- **Dado que** `specs/STACK.md` define un proyecto `api-only` o `CLI`
- **Cuando** se ejecuta el pipeline de CI o la verificación de Gate 4
- **Entonces** los quality gates visuales se omiten automáticamente sin errores ni demoras.

---

## 6. Pre-Mortem Inverso (Anticipación de Puntos Ciegos y Fallos)

1. **Escenario de Fallo Catastrófico 1**: Falsos positivos masivos en el escaneo de código (ej. commits hash de Git, identificadores alfanuméricos o selectores CSS que contienen secuencias de 6 caracteres interpretadas erróneamente como colores hexadecimales).
   - **Causa Oculta**: Regex simplistas sin contexto semántico de estilo (ej. buscar cualquier `#([0-9a-fA-F]{6})` en cualquier archivo).
   - **Mitigación Preventiva en Gate 1**: El validador `sdd_tokens_validator.py` solo evalúa literales de color en extensiones relevantes (`.css`, `.scss`, `.tsx`, `.jsx`, `.vue`, `.html`) y sobre propiedades de estilo (`color:`, `backgroundColor:`, `fill:`, `stroke:`, `border-color:`, etc.), permitiendo además directivas de exclusión inline (`/* sdd-token-ignore */`).
2. **Escenario de Fallo Catastrófico 2**: Introducir dependencias pesadas de Node/npm en el CI o en el hook de tests del starter que ralenticen o rompan la ejecución offline de Python.
   - **Causa Oculta**: Intentar ejecutar Playwright o axe-core dentro de los unit tests del propio repositorio del framework starter.
   - **Mitigación Preventiva en Gate 1**: El framework starter únicamente valida contratos, reglas de gobernanza y coherencia de tokens en Python 3.12 stdlib offline. Las herramientas pesadas de browser son prescritas para los proyectos derivados de usuario, operando condicionalmente según la disponibilidad de su stack.
3. **Escenario de Fallo Catastrófico 3**: Agentes de IA ejecutando silenciosamente comandos de actualización de baselines (ej. `npx playwright test --update-snapshots`) para "hacer pasar" los tests rotos.
   - **Causa Oculta**: Falta de prohibición contractual en el prompt de `@qa-tester` y en el arquetipo `front-test`.
   - **Mitigación Preventiva en Gate 1**: `RN-01`, `RF-005` y actualización explícita de `.agents/agents/qa-tester.md` catalogando la auto-actualización de snapshots como violación de gobernanza.

---

## 7. Incógnitas y Decisiones Pendientes (`NOT_ENOUGH_INFO` — Tarjetas Rojas / Stop-the-Line)
- [x] **`AMB-001`**: Validador CLI determinista `scripts/sdd_tokens_validator.py` en Python 3.12 stdlib (offline, sin dependencias externas). *(Resuelto: Opción A)*.
- [x] **`AMB-002`**: Modelo bi-nivel para pruebas visuales: Nivel 1 estático obligatorio (tokens) + Nivel 2 dinámico condicional a herramientas instaladas (`SKIPPED_UNAVAILABLE_TOOL`). *(Resuelto: Opción A)*.
- [x] **`AMB-003`**: Política de regresión visual: falta de baseline es `INCONCLUSIVE` y prohibición estricta de auto-actualización de snapshots por IA sin sign-off humano. *(Resuelto: Opción A)*.
- [x] **`AMB-004`**: `@qa-tester` asume la 4ª Auditoría Obligatoria de Calidad (*Quality Gate Visual y Coherencia de Tokens*) con soporte especializado de `@a11y-architect` para WCAG 2.2 AA. *(Resuelto: Opción A)*.
- [x] **`AMB-005`**: Integración en `.github/workflows/ci.yml` del paso de tokens offline en el starter y documentación condicional para proyectos. *(Resuelto: Opción A)*.

---

## 8. Aprobación Formal Gate 1 (`RN-SDD-HUMAN-GATE-OWNERSHIP`)
> ⚠️ **Exclusivo para el Stakeholder Humano** (Los agentes de IA tienen prohibido marcar esta casilla por su cuenta):
- [x] **Gate 1 Aprobado por el Usuario**: El alcance funcional, requisitos EARS, ejemplos concretos, métricas Planguage, criterios BDD y resolución de `AMB-001`..`AMB-005` han sido revisados y validados para `FWK-003` (Aprobado expresamente en chat por el usuario el 2026-11-13).
