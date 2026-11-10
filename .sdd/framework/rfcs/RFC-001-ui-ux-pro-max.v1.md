# Propuesta técnica — UI UX Pro Max en `sdd-agentic-starter`

**Estado:** RFC / propuesta para debate; **sin aprobación de Gates** y **sin modificar el repositorio original**.

**Base examinada:** ZIP `sdd-agentic-starter-main.zip` aportado el 09/11/2026; repositorio externo `nextlevelbuilder/ui-ux-pro-max-skill` consultado en GitHub.

## 1. Decisión propuesta

Incorporar **UI UX Pro Max como proveedor opcional de inteligencia de diseño**, no como sustituto de las reglas SDD, de la documentación funcional, ni del `design-system` ya existente. Introducir un especialista `@ui-ux-designer` de análisis/diseño con revisión humana, sin propiedad sobre código de producción.

La integración se incorporará **por extensión del pack existente** `capability-web-frontend`. Se evitará copiar directamente el motor o cambiar los agentes constructores. La dependencia externa deberá ser instalable y versionable, con un modo sin conexión/alternativo documentado.

## 2. Activos existentes que hay que reutilizar

| Activo de la plantilla | Reutilización |
|---|---|
| `.sdd/catalog/packs/capability-web-frontend/` | Punto de extensión frontend, sin reescribir el contenido upstream ECC. |
| `.../skills/design-system/SKILL.md` | Extracción de tokens, auditoría, previsualización de UI existente; no sustituir. |
| `.../skills/browser-qa/SKILL.md` | Revisiones en navegador. |
| `.../skills/accessibility/` y `.../skills/frontend-a11y/` | Evaluación de accesibilidad. |
| `.agents/agents/a11y-architect.md` | Especialista revisor independiente. |
| `.agents/archetypes/front-ui.archetype.md` | Implementador en modalidad granular. |
| `.agents/agents/front-engineer.md` / arquetipo `tier-frontend` | Implementador en modalidad compacta. |
| `docs/standards/FUNCTIONAL_DOCUMENTATION_STANDARD.md` | Fuente de verdad sobre `SCR-###`, wireframes, fichas de pantalla, alta fidelidad. |
| `specs/templates/01-functional-spec.template.md` y `02-technical-spec.template.md` | Contratos Gate 1 y Gate 2. |
| `.agents/skills/sdd-bootstrap/SKILL.md` | Decidir si habilitar la capacidad en Gate 00. |
| `scripts/sdd_agent_generator.py` | Activación/materialización y lock. |
| `scripts/sdd_catalog_import.py` | Importador ECC: respetar sus límites; no perder extensiones locales. |
| `scripts/sdd_sync.py` | Sincronizar definiciones reutilizables sin incorporar artefactos específicos del proyecto. |

## 3. Correcciones previas necesarias (confirmadas en el ZIP)

1. **Materialización incompleta**: `materialize_squad` copia builders, agentes core y agentes especialistas de packs, pero no instala las skills, rules ni workflows contenidos en esos packs. Incorporar materialización idempotente, seguimiento de origen, control de colisiones y limpieza segura.
2. **Detección poco fiable del stack**: `parse_stack_specs` aplica expresiones regulares a **todo** `specs/STACK.md`; incluso las opciones de ejemplo pueden activar packs irrelevantes. El `squad.lock.json` proporcionado contiene simultáneamente React, Vue, Java, C#, Go, Python, etc., mientras Gate 00 no está aprobado. Sustituir por lectura de decisiones estructuradas y efectivamente aprobadas; si falta aprobación, no activar extensiones de forma automática.
3. **Reimportaciones con sobrescritura**: `sdd_catalog_import.py` reescribe `pack.json` para los packs definidos en `STACK_PACKS`. Una integración escrita únicamente en ese manifiesto se perdería. Usar overlay de extensión propio o un merge explícito protegido por tests.
4. **No atribuir nuevas reglas a ECC**: mantener la procedencia y licencia de UI UX Pro Max separadas de las del código ECC. Verificar versión, checksums/licencias y política de actualización.

## 4. Estructura objetivo — extensión sin duplicar el pack

```text
.sdd/catalog/packs/capability-web-frontend/
├── pack.json                            # ECC: no adulterar en importación
├── agents/...
├── rules/...
├── skills/
│   ├── design-system/SKILL.md          # Existente; queda intacta
│   └── ...
└── extensions/                         # NUEVO punto extensible
    └── ui-ux-pro-max/
        ├── extension.json              # Activación, versión y procedencia
        ├── agents/ui-ux-designer.md     # Especialista read-only
        ├── skills/sdd-ui-design/SKILL.md # Adaptador metodológico SDD
        └── workflows/ui-design-review.md

.agents/agents/ui-ux-designer.md         # MATERIALIZADO solo si se activa
.agents/skills/sdd-ui-design/SKILL.md   # MATERIALIZADO solo si se activa
.agents/skills/ui-ux-pro-max/           # INSTALACIÓN externa de la CLI
.agent-inbox/ui-ux-designer/             # Buzón del especialista

design-system/<project-slug>/           # Solo en proyectos que usan UI
├── MASTER.md                           # Design System global aprobado
├── design-tokens.json                  # Tokens estructurados/verificables
└── pages/<screen-slug>.md              # Overrides controlados
```

> La ruta `.agents/skills/ui-ux-pro-max/` es la publicada por el instalador para Antigravity/universal. El contenido generado por el instalador debe validarse mediante `--dry-run` antes de cualquier operación de escritura.

**Alternativa:** convertir el proveedor en un pack independiente `capability-ui-ux` si se necesita activarlo también para aplicaciones nativas. Para el primer alcance web, la extensión del pack actual es la menor intervención.

## 5. Contrato de `@ui-ux-designer`

**Responsabilidades**:
- Leer especificación EARS, escenarios BDD, fichas `SCR-###`, mapa de navegación y stack aprobado.
- Ejecutar búsquedas orientadas a producto, estilo, color, tipografía, UX y stack usando UI UX Pro Max.
- Proponer variantes justificadas con trazabilidad a los requisitos de cada pantalla.
- Proponer Design System coherente, componentes, tokens, estados, responsive y antipatrones.
- Validar alineación con wireframes funcionales aprobados y con el estándar documental existente.
- Solicitar revisión de `@a11y-architect`; registrar discrepancias/alternativas y elevar al humano cuando corresponda.

**No puede**: editar código productivo, reescribir requisitos aprobados, instalar dependencias del sistema sin autorización, marcar Gates como aprobados ni modificar artefactos inmutables. Para persistir propuestas, el coordinador delega la edición documental al agente propietario de la ruta dentro del Ownership Map.

**Entradas mínimas**: feature ID, `01-spec.md`, fichas `SCR`, estado de aprobación, `STACK.md` aprobado, design system vigente y restricciones de marca.

**Salidas**: propuestas con etiquetas `Confirmado/Propuesto/Pendiente`, vínculos a `SCR`/`RF`, cambios sugeridos sobre `MASTER.md` y `pages/`, tokens y evidencia de revisión de accesibilidad. No se aprueban automáticamente.

## 6. Encaje preciso con el proceso SDD

### Gate 00 — Bootstrap

- Solo en proyectos con UI: selector `uiux.enabled`, `uiux.provider`, versión fijada y preferencias iniciales de diseño.
- En API-only/CLI, omitir las preguntas y no activar el proveedor ni el agente.
- Generar configuración estructurada y validar explícitamente el estado de aprobación de Gate 00.

### Gate 1 — Especificación funcional

- `@functional-analyst` documenta `RF`, `SCR`, acciones, datos, validaciones, mensajes y estados.
- Wireframe de baja fidelidad editable y exportado, siguiendo `FUNCTIONAL_DOCUMENTATION_STANDARD.md`.
- Aprobación humana del comportamiento. El agente de diseño puede asesorar, pero no sustituye la aceptación funcional.

### Gate 2 — Diseño técnico y visual

- Ejecutar `@ui-ux-designer` sobre los requisitos aprobados para proponer Design System y alta fidelidad.
- `@architect` valida encaje con stack y contratos; `@a11y-architect` revisa accesibilidad.
- Registrar decisiones en la documentación existente y enlazar al `02-tech-spec.md` sin duplicar fichas de pantalla.
- Pedir aprobación humana del diseño junto con Gate 2. Los cambios funcionales regresan a revisión de requisitos.

### Gate 3 — Plan de implementación

- Desglosar tareas `front-ui` o `front-engineer` con referencias explícitas a `SCR`, `MASTER.md`, overrides y tokens.
- Mantener el Ownership Map: solo un constructor edita una zona de código en cada bloque DAG.

### Gate 4 — Verificación

- Tests de navegador, capturas baseline, responsive, teclado, accesibilidad, estados vacío/error/loading y coherencia con tokens.
- Evidencia reproducible por pantalla y por requisito. No usar un score subjetivo como único quality gate.
- Los cambios de capturas de referencia requieren revisión humana (evitar aceptar automáticamente regresiones).

### Gate 5 — Living docs

- `@documentator` sincroniza el catálogo de pantallas, fichas, enlaces al Design System, decisiones y matriz `RF` → `SCR` → tarea → prueba → evidencia.
- Prohibido editar la carpeta de una Feature `Done` directamente: seguir Change Request `CR-XXX`.

## 7. Reutilizar el Design System existente en lugar de duplicarlo

UI UX Pro Max genera un `design-system/<slug>/MASTER.md` y posibles overrides por página. La skill ECC `design-system` puede producir `DESIGN.md`, `design-tokens.json` y una previsualización. Establecer:

- **Fuente normativa visual única:** `design-system/<slug>/MASTER.md` y su versión aprobada.
- **Fuente estructurada:** `design-tokens.json` generado/revisado y coherente con el master.
- **Evidencias y vistas:** previews y capturas; no constituir otra fuente normativa independiente.
- **Documentación funcional:** fichas SCR en la estructura prevista por el estándar; enlazan al master.
- **Actualización:** persistencia no destructiva; proponer cambios en diff/CR y nunca `--force` sobre una aprobación existente sin autorización.

## 8. Cambios de código concretos (pendientes de aprobación)

| Prioridad | Archivo/área | Acción |
|---|---|---|
| P0 | `scripts/sdd_agent_generator.py` | Parseo declarativo de packs aprobados; materializador de skills/rules/workflows y extensiones; desactivación limpia; lock fiable. |
| P0 | `scripts/sdd_catalog_import.py` | Hacer persistentes las extensiones locales en `extensions/` sin conflictos de reimportación. |
| P0 | `tests/test_sdd_governance.py` y nuevas pruebas | Tests de selección frontend/backend, lock, idempotencia, manifest invalido y reglas de colisión. |
| P1 | `.sdd/catalog/packs/capability-web-frontend/extensions/ui-ux-pro-max/` | Nuevo manifiesto, agente y adaptador metodológico. |
| P1 | `.agents/skills/sdd-bootstrap/SKILL.md` | Nueva configuración opcional Gate 00 y poda dinámica. |
| P1 | `specs/STACK.md` y plantilla `00-stack.template.md` | Persistir configuración explícita y versionada; sin activar nada basado en texto de ejemplo. |
| P1 | `specs/templates/02-technical-spec.template.md` | Referencia a sistema visual aprobado y evidencias, sin plantilla funcional duplicada. |
| P1 | `.agents/agents/orchestrator.md` | Delegación del diseño en Gate 2 y aprobación humana. |
| P1 | Arquetipos y/o `front-engineer` | DoR con vínculo a SCR y Design System aprobado. |
| P2 | `qa-tester`, `a11y-architect`, CI | Introducir quality gates visuales condicionales al tipo de proyecto y herramientas realmente instaladas. |
| P2 | `scripts/sdd_sync.py`, `README.md`, notices | Sincronización, trazabilidad, procedencia de tercero y documentación de actualización. |

## 9. PoC de instalación (NO ejecutada)

Desde una copia o worktree aislado del proyecto:

```bash
# Inspección segura de qué archivos crearía la CLI
npx ui-ux-pro-max-cli init --ai antigravity --dry-run

# Solo tras revisar el plan de cambios, autorizar explícitamente
# una versión concreta y verificar las rutas de destino:
# npx ui-ux-pro-max-cli@VERSION_APROBADA init --ai antigravity
```

El proveedor requiere Python 3 para su motor de búsqueda local. No instalar software del sistema de forma automática. Evaluar degradación controlada si la CLI/Python no está disponible: el workflow SDD sigue funcionando con la skill `design-system` local.

## 10. Pruebas de aceptación propuestas

1. Proyecto `api-only`, Gate 00 aprobado: sin especialista UI ni proveedor instalado.
2. Proyecto `spa-only` con proveedor habilitado: agente, inbox, skill y workflows disponibles sin duplicados.
3. Proyecto `spa-only` sin proveedor: siguen funcionando los agentes y la skill de diseño ECC existentes.
4. `--materialize` ejecutado dos veces: mismos archivos lógicos, sin duplicar skills ni alterar artefactos aprobados.
5. `sdd_catalog_import.py` ejecutado: la extensión local permanece íntegra.
6. `sdd_sync.py`: sincroniza la definición de la extensión, no un Design System específico de otro proyecto.
7. Selector Stack: las palabras React/Vue/Java en ejemplos de plantilla no activan packs no seleccionados.
8. Gate 1 aún no aprobado: no permitir tratar una propuesta de alta fidelidad como diseño final.
9. Cambio sobre feature `Done`: registrar CR y no modificar el baseline directamente.
10. Quality gates visuales: errores de contraste/teclado y regresiones relevantes producen resultado verificable.

## 11. Decisiones por debatir

- ¿Incorporar inicialmente únicamente web (extensión de `capability-web-frontend`) o cubrir también mobile/desktop con un nuevo pack transversal?
- ¿El mockup de alta fidelidad será HTML/CSS navegable, Figma, Excalidraw o una combinación, según el stack?
- ¿Cuándo se hace sign-off visual: como subsección explícita de Gate 2 o como actividad adicional no bloqueante según criticidad?
- ¿Versión de UI UX Pro Max fijada en repositorio o resuelta al generar cada proyecto (recomendación: fijada)?

**Recomendación de implantación:** corregir materialización/activación (P0), integrar un caso vertical SPA de referencia (P1) y extender QA automatizada (P2). No alterar todas las etapas del starter de una sola vez.
