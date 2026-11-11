# Especificación Funcional: Pack `capability-ui-design` (UI UX Pro Max)

- **ID de la Feature (Work Item del Framework)**: `FWK-002-capability-ui-design`
- **RFC de Origen**: [`RFC-001` v2 (Aceptado)](../../rfcs/RFC-001-ui-ux-pro-max.md)
- **Estado**: `Aprobado` (Gate 1 aprobado por el usuario el 2026-11-11)
- **Analista Funcional / Tech Lead**: `@orchestrator` / `@functional-analyst` (actuando sobre mandato de `RFC-001` v2)
- **Fecha de Creación**: 2026-11-10
- **Última Actualización**: 2026-11-11

---

## 1. Resumen, Contexto y Claridad Epistémica (`morluto/rea`)
- **Problema y Valor de Negocio**: Tras completar `FWK-001` (`Done`), el framework SDD ya dispone de un motor determinista y *fail-closed* para validar `sdd:stack-config` y materializar `agents/`, `skills/`, `pack-rules/` y `workflows/` con lock v2. Sin embargo, los proyectos con interfaz web carecen todavía de un especialista de diseño UI/UX gobernado (`@ui-ux-designer`), de inteligencia de diseño vendorizada y offline (`ui-ux-pro-max`), de un flujo formal de Gate 2 con revisión de accesibilidad (`@a11y-architect`) y `[ ] Visual Sign-off (Human)`, de un ciclo de vida versionado (semver) para `docs/design-system/` compatible con `RN-SDD-IMMUTABLE-DONE`, y de integración guiada en `sdd-bootstrap`, plantillas y arquetipos frontend.
- **Hechos Observados (Observations)**:
  - `.sdd/framework/BACKLOG.md` (`L13-L14`): `FWK-001` figura como `Done` (Gates 1–5 aprobados), cumpliendo la precondición de `FWK-002`.
  - `.sdd/framework/rfcs/RFC-001-ui-ux-pro-max.md` (`L1-L284`): `RFC-001` v2 `Aceptado` el 2026-11-10; fija arquitectura del pack `capability-ui-design` (§3.1–§3.3), ciclo de vida semver de `docs/design-system/` (§4), contrato de `@ui-ux-designer` (§5), encaje SDD (§6), bloque `uiux` en `sdd:stack-config` (§7), decisiones cerradas D1–D5 (§8), alcance `FWK-002` (§9) y criterios `#6`–`#12` (§10).
  - `scripts/sdd_pack_registry.py` (`L45-L52`, `L327-L353`, `L363-L380`, `L448-L489`): `StackConfig` incluye ya el campo opaco opcional `uiux: dict[str, Any] | None = None` (`L51`) sin validación de esquema; `load_pack_manifest()` valida `id`, `family`, `description`, `requires`, `rules`, `specialists`, `skills`, `workflows` (`L374-L380`), sin procesar aún `targets`, `upstream` ni `vendor_lock`.
  - `scripts/sdd_agent_generator.py` (`L267-L279`, `L381-L421`): materializa packs activos desde `.sdd/catalog/packs/` y registra hashes SHA-256 en `.agents/squad.lock.json` v2; no verifica todavía manifiestos `VENDOR.lock.json`.
  - `scripts/sdd_catalog_import.py` (`L65-L456`): opera únicamente sobre `UNIVERSAL_SPECIALISTS` y `STACK_PACKS`; no existe `.sdd/catalog/packs/capability-ui-design/` todavía.
  - `.sdd/catalog/packs/capability-web-frontend/pack.json` (`L1-L34`): declara `id: "capability:web-frontend"`, `agents/a11y-architect.md`, `agents/seo-specialist.md` y las skills ECC `accessibility`, `frontend-a11y`, `design-system`, `browser-qa`, `make-interfaces-feel-better`, `motion-foundations`, `i18n-sync`.
  - `.agents/skills/sdd-bootstrap/SKILL.md` (`L1-L294`): wizard bilingüe ES-ES / EN-GB con poda dinámica (`L35-L47`), sin preguntas condicionales de `uiux`, sin plantilla de emisión del bloque `sdd:stack-config` y sin regla de alta automática de `Design System Foundation` en `specs/BACKLOG.md`.
  - `specs/templates/00-stack.template.md` (`L1-L163`): aún no contiene el bloque ```` ```yaml sdd:stack-config ````; `specs/STACK.md` (`L88-L92`) contiene solo el bloque mínimo añadido en `FWK-001` (`gate00_approved: false`, `preset: compact`, `packs: []`).
  - `specs/templates/02-technical-spec.template.md` (`L80-L101`): no contempla aún la subsección **"Diseño visual"** ni la casilla `[ ] Visual Sign-off (Human)`.
  - `.sdd/catalog/archetypes/` (`front-ui.archetype.md`, `front-engineer.archetype.md`, `tier-frontend.archetype.md`, `front-logic.archetype.md`, `front-test.archetype.md`): sus secciones `DoR` no exigen todavía `SCR-XXX`, `MASTER@versión`, `docs/design-system/pages/SCR-XXX.md` ni tokens.
  - `.agents/agents/orchestrator.md` (`L46-L51`): Gate 2 delega solo en `@architect`, sin protocolo de invocación a `@ui-ux-designer` ni revisión de `@a11y-architect` cuando hay pantallas (`SCR-###`).
  - `specs/BACKLOG.md` (`L11`): ya contiene `FEAT-001` (`Core Scaffolding & Healthcheck`, `In Progress`), por lo que el registro automático de la feature fundacional de Design System deberá asignar el siguiente ID secuencial disponible.
  - `docs/standards/FUNCTIONAL_DOCUMENTATION_STANDARD.md` (`§18`, `L901-L940`): regula el tránsito obligatorio de wireframe de baja fidelidad (`wireframe.excalidraw`, `screen-spec.md`) a alta fidelidad (`hi-fi/`).
- **Restricciones Derivadas (Derivations)**:
  - `RFC-001` §9 obliga a ejecutar un **Spike PoC en Gate 2** (directorio temporal aislado) con `npx ui-ux-pro-max-cli@<PIN> init --ai antigravity` para inventariar ficheros, confirmar soporte `--dry-run` / ruta de salida configurable, versión mínima de Python, licencia MIT y ausencia de telemetría o llamadas de red en ejecución, antes de congelar y aprobar el vendorizado.
  - `RFC-001` D1–D5: alcance inicial web (`targets: ["web"]`, `requires: ["capability:web-frontend"]`), hi-fi navegable HTML/CSS por defecto (`html | figma | html+figma`), sign-off visual bloqueante en Gate 2 solo si hay `SCR`, vendorización fijada con `VENDOR.lock.json` (`npx` confinado exclusivamente a `scripts/sdd_vendor_update.py` con revisión humana), y gobernanza de framework en `.sdd/framework/` (rama `feat/fwk-002-capability-ui-design` desde `develop`).
  - `RN-SDD-IMMUTABLE-DONE` + `RN-SDD-1-TO-1-CR`: `docs/design-system/MASTER.md` y `design-tokens.json` son propiedad de una feature fundacional `Design System Foundation`; tras su `Done`, cualquier evolución del sistema visual se tramita como **1 solo CR** sobre esa feature, y solo si altera comportamiento funcional de pantallas `Done` se abre CR adicional por cada feature consumidora afectada.
  - `RN-SDD-SELECTIVE-CONTEXT` y `RN-SDD-FAIL-CLOSED`: el pack no añade reglas *always-on* (`rules: []`); la activación sin UI (`api-only`, `cli`) o con `uiux.enabled: false` no materializa `@ui-ux-designer` ni el proveedor; cualquier incoherencia o alteración de checksum aborta antes de mutar el workspace.

---

## 1.1. Fuentes Registradas y Trazabilidad (`SRC-###`)

| ID Fuente | Tipología / Origen | Fecha | Notificado por | Descripción / Contenido Facilitado |
|---|---|---|---|---|
| `SRC-001` | RFC Aceptado (`RFC-001` v2) | 2026-11-10 | Usuario Humano | Mandato de `FWK-002` (§3–§11): pack `capability-ui-design`, ciclo semver `docs/design-system/`, contrato `@ui-ux-designer`, configuración `uiux` en `STACK.md`, `sdd_vendor_update.py`, `sdd-bootstrap`, plantillas, `orchestrator.md`, Spike PoC Gate 2 y escenarios `#6`–`#12`. |
| `SRC-002` | Chat / Orden directa + Inspección de workspace | 2026-11-10 | Usuario / `@orchestrator` | Orden *"iniciar FWK-002"* tras cierre de `FWK-001`; verificación empírica de `sdd_pack_registry.py`, `sdd_agent_generator.py`, `sdd-bootstrap`, plantillas, arquetipos frontend y `specs/BACKLOG.md`. |

---

## 1.2. Registro de Ambigüedades y Cuestiones Pendientes (`AMB-###`)
> Aplicar Stop-the-Line (`RN-SDD-FAIL-CLOSED`) antes de autorizar Gate 1 y pasar a Gate 2:

| ID | Descripción de la Ambigüedad / Conflicto | Requisitos Afectados | Pregunta Directa para el Usuario | Impacto Funcional | Estado |
|---|---|---|---|---|---|
| `AMB-001` | `RFC-001` (§3.1, §7, §9) deja `<PIN_APROBADO>` como marcador pendiente de determinar durante el Spike PoC de Gate 2 con `ui-ux-pro-max-cli`. | `RF-001`, `RF-002`, `RF-004` | **Resolución (Opción A)**: El Spike PoC de Gate 2 inspecciona la última versión estable MIT publicada de `ui-ux-pro-max-cli`, verifica 0 llamadas de red/telemetría en ejecución y compatibilidad Python 3.12+ stdlib, y somete ese `<X.Y.Z>` exacto a aprobación en Gate 2 (abortando *Stop-the-Line* si detecta telemetría o dependencias bloqueantes). | Determina cómo se fija y valida la versión inicial del proveedor en Gate 2. | `Resolved` |
| `AMB-002` | `sdd_pack_registry.py` (`FWK-001`) activa packs únicamente desde `config.packs` y guarda `config.uiux` como diccionario opaco; no define qué ocurre si `uiux.enabled: true` no incluye `capability-ui-design` en `packs` (o viceversa). | `RF-003`, `RF-006`, `RF-007` | **Resolución (Opción A — Fail-Closed)**: Exigir coherencia explícita en `sdd:stack-config`: si `uiux.enabled: true`, debe figurar `capability-ui-design` en `packs` (y `capability-web-frontend` vía `requires`), y si `capability-ui-design` está en `packs`, `uiux.enabled` debe ser `true`; cualquier contradicción lanza `StackConfigError`. Si `uiux.enabled: false` (o ausente) con `capability-web-frontend` activo, operan únicamente las skills ECC sin `@ui-ux-designer`. | Evita activaciones fantasma y garantiza trazabilidad entre `packs` y `uiux`. | `Resolved` |
| `AMB-003` | `RFC-001` §10 Escenario `#10` exige que un fichero alterado en `vendor/` haga fallar la verificación de checksum, pero no fija si `VENDOR.lock.json` se verifica solo en `sdd_vendor_update.py` o también automáticamente al materializar con `sdd_agent_generator.py`. | `RF-002`, `RF-004` | **Resolución (Opción A)**: Verificar `VENDOR.lock.json` (SHA-256 exacto, sin ficheros faltantes ni extra no declarados) **tanto** en `scripts/sdd_vendor_update.py --verify` **como** automáticamente en `sdd_pack_registry.py` / `sdd_agent_generator.py --materialize` siempre que `capability-ui-design` esté activo (abortando *fail-closed* antes de materializar `.agents/`). | Impide que un asset vendorizado corrupto o manipulado se propague a `.agents/skills/`. | `Resolved` |
| `AMB-004` | `RFC-001` §6 introduce `[ ] Visual Sign-off (Human)` bloqueante en `02-tech-spec.md` solo cuando hay `SCR`, mientras `FWK-003` se reserva los *quality gates* visuales en `@qa-tester` / `@a11y-architect` / CI. `sdd_code_gate_guard.py` actualmente solo inspecciona `.agents/active_work_item.json`. | `RF-009`, `RF-010` | **Resolución (Opción A)**: Aplicar el bloqueo en Gate 2 mediante la subsección **"Diseño visual"** + `[ ] Visual Sign-off (Human)` en `specs/templates/02-technical-spec.template.md`, el checklist obligatorio de `.agents/agents/orchestrator.md` y el workflow `ui-design-review.md`, dejando los checks automáticos en hooks/CI para `FWK-003`. | Define la frontera exacta entre `FWK-002` (flujo y contratos) y `FWK-003` (quality gates automáticos). | `Resolved` |
| `AMB-005` | `RFC-001` §4.1 y §9 establecen que `sdd-bootstrap` registre automáticamente la feature fundacional `Design System Foundation` en `specs/BACKLOG.md` cuando `uiux.enabled` es `true`, y `specs/BACKLOG.md` ya contiene `FEAT-001`. | `RF-008` | **Resolución (Opción A)**: `sdd-bootstrap/SKILL.md` instruye a `@orchestrator` a registrar en `specs/BACKLOG.md` una fila `Design System Foundation` con el siguiente ID secuencial `FEAT-XXX` libre (Gate 0 `[x]`, Estado `Backlog`), sin crear carpetas de feature ni código hasta que se abra su propio hilo Gate 1–5. | Define cómo convive el alta automática con el backlog existente y `RN-SDD-SESSION-LIFECYCLE`. | `Resolved` |
| `AMB-006` | `specs/templates/00-stack.template.md` carece del bloque `sdd:stack-config`, mientras `specs/STACK.md` tiene el bloque mínimo de `FWK-001` (`packs: []`) sin `uiux`. Asimismo hay que fijar el detalle exacto de las preguntas `uiux` en `sdd-bootstrap`. | `RF-007`, `RF-008` | **Resolución (Opción A)**: Añadir en `00-stack.template.md` el bloque `sdd:stack-config` con `uiux` documentado, actualizar `specs/STACK.md` manteniendo la plantilla limpia (`gate00_approved: false`, `packs: []`, `uiux.enabled: false`), y añadir en `sdd-bootstrap/SKILL.md` (ES-ES/EN-GB, solo si hay UI) las 3 preguntas: (1) activar inteligencia de diseño (`ui-ux-pro-max` vs solo ECC), (2) `hifi_format` (`html` recomendado / `figma` / `html+figma`), (3) ruta opcional de `brand_constraints` (`docs/design-system/BRAND.md` o ninguna). | Mantiene Gate 00 ágil y diferido el diseño visual a `Design System Foundation`. | `Resolved` |
| `AMB-007` | Los arquetipos frontend en `.sdd/catalog/archetypes/` incluyen `front-ui`, `front-engineer`, `tier-frontend`, `front-logic` y `front-test`. Además hay que decidir dónde reside el esquema normativo de `MASTER.md`, `design-tokens.json`, `CHANGELOG.md` y `pages/SCR-XXX.md`. | `RF-005`, `RF-010`, `RF-011` | **Resolución (Opción A)**: Inyectar el DoR de Design System (`SCR-XXX`, `MASTER@versión`, `pages/SCR-XXX.md`, tokens) en `front-ui.archetype.md`, `front-engineer.archetype.md` y `tier-frontend.archetype.md` (sin acoplar `front-logic` ni anticipar `front-test` de `FWK-003`), y definir el esquema/formato canónico de los artefactos `docs/design-system/` dentro de `skills/sdd-ui-design/SKILL.md` (sin crear `docs/design-system/` en el starter vacío). | Evita contaminar proyectos sin UI con artefactos vacíos y acota el DoR a constructores de UI. | `Resolved` |

---

## 2. Historias de Usuario y Casos de Uso

### Historia 1: Pack independiente y vendorizado con integridad verificable
> **Como** mantenedor del framework SDD,
> **Quiero** disponer del pack `.sdd/catalog/packs/capability-ui-design/` con licencia/atribución (`NOTICE.md`), proveedor `ui-ux-pro-max` vendorizado bajo `VENDOR.lock.json` y un script explícito de actualización (`scripts/sdd_vendor_update.py`),
> **Para que** la materialización sea 100% offline, reproducible, auditable frente a alteraciones de checksum y protegida frente a `sdd_catalog_import.py`.

### Historia 2: Bootstrap condicional y activación limpia según topología UI
> **Como** arquitecto o Tech Lead que ejecuta Gate 00 (`sdd-bootstrap`),
> **Quiero** que las preguntas `uiux` solo aparezcan en proyectos con interfaz visual (poda automática en `api-only` / `CLI`) y que al habilitar `uiux.enabled` se registre automáticamente la feature fundacional `Design System Foundation` en `specs/BACKLOG.md`,
> **Para que** proyectos sin UI no reciban sobrecarga de contexto ni agentes innecesarios, y los proyectos con UI arranquen con su sistema visual gobernado desde el inicio.

### Historia 3: Diseño visual en Gate 2 con `@ui-ux-designer`, revisión a11y y evolución semver
> **Como** `@orchestrator` y `@architect` gobernando una feature con pantallas (`SCR-###`),
> **Quiero** que `@ui-ux-designer` produzca borradores hi-fi y propuestas de tokens solo tras aprobarse Gate 1 (wireframes), pase revisión obligatoria de `@a11y-architect` y obtenga `[ ] Visual Sign-off (Human)` en `02-tech-spec.md`, gestionando `docs/design-system/` mediante semver y CR único sobre la feature fundacional,
> **Para que** el diseño visual sea trazable a `RF`/`SCR`/tokens sin romper `RN-SDD-IMMUTABLE-DONE` ni `RN-SDD-1-TO-1-CR`.

### Historia 4: Degradación segura a skills ECC cuando el proveedor está desactivado
> **Como** equipo de producto con frontend (`spa-only` / `Fullstack`) que decide no activar `ui-ux-pro-max`,
> **Quiero** activar `capability-web-frontend` con `uiux.enabled: false`,
> **Para que** `@a11y-architect` y las skills ECC (`design-system`, `accessibility`, `browser-qa`) sigan operativos sin materializar `@ui-ux-designer` ni el proveedor externo.

---

## 3. Alcance (Scope)

### ✅ Dentro del Alcance (In-Scope)
- Creación del pack no-ECC `.sdd/catalog/packs/capability-ui-design/`:
  - `pack.json` (con `id: "capability:ui-design"`, `family: "capability"`, `requires: ["capability:web-frontend"]`, `targets: ["web"]`, `upstream` + `vendor_lock`, `specialists`, `skills`, `workflows`, `rules: []`).
  - `NOTICE.md` con atribución explícita a `nextlevelbuilder/ui-ux-pro-max-skill` (MIT) y separación de procedencia respecto a `affaan-m/ecc`.
  - `agents/ui-ux-designer.md` con contrato estricto de fronteras (Gate 2, escritura acotada a `docs/design-system/**` y `specs/features/<activa>/ux/**`, prohibición de `src/**`/`tests/**`/`01-spec.md`/features `Done`/`npx`/`--force`, escalado *Stop-the-Line* si introduce cambio funcional).
  - `skills/sdd-ui-design/SKILL.md` como adaptador metodológico entre el proveedor, el estándar `docs/standards/FUNCTIONAL_DOCUMENTATION_STANDARD.md` §18, el formato canónico `docs/design-system/` (`MASTER.md` semver, `design-tokens.json`, `CHANGELOG.md`, `pages/SCR-XXX.md`) y la regla de no ejecutar `--force` sobre `MASTER.md` existente.
  - `workflows/ui-design-review.md` con la secuencia diseño (`@ui-ux-designer`) → revisión a11y (`@a11y-architect`) → validación técnica (`@architect`) → `[ ] Visual Sign-off (Human)`.
  - `vendor/ui-ux-pro-max/` congelado tras superar el Spike PoC de Gate 2, con `LICENSE` y `VENDOR.lock.json` (versión, fecha, SHA-256 por fichero).
- Creación de `scripts/sdd_vendor_update.py` para verificación de integridad (`--verify`) y actualización explícita en directorio temporal aislado con revisión de diff (único lugar autorizado para invocar `npx ui-ux-pro-max-cli@<version>`).
- Extensión mínima y retrocompatible de `scripts/sdd_pack_registry.py` (y `scripts/sdd_agent_generator.py` si aplica) para validar esquema `uiux`, coherencia `uiux` ↔ `packs`, metadatos `targets` / `upstream` / `vendor_lock` en `pack.json`, y verificación de checksums `VENDOR.lock.json`.
- Actualización de `.agents/skills/sdd-bootstrap/SKILL.md` (ES-ES y EN-GB): preguntas `uiux` condicionadas a proyectos con UI, emisión de `sdd:stack-config` y alta automática de `Design System Foundation` en `specs/BACKLOG.md`.
- Actualización de plantillas y arquetipos:
  - `specs/templates/00-stack.template.md` (y bloque inicial coherente en `specs/STACK.md` manteniendo `gate00_approved: false` y `packs: []`).
  - `specs/templates/02-technical-spec.template.md` (subsección **"Diseño visual"** + rango `MASTER@1.x` + casilla `[ ] Visual Sign-off (Human)`).
  - `.sdd/catalog/archetypes/` (`front-ui.archetype.md`, `front-engineer.archetype.md`, `tier-frontend.archetype.md`) incorporando referencias a `SCR-XXX`, `MASTER@versión`, `pages/SCR-XXX.md` y tokens en el `DoR`.
- Actualización de `.agents/agents/orchestrator.md` para incorporar el flujo condicional de Gate 2 con `@ui-ux-designer` y `@a11y-architect` cuando la feature toca pantallas (`SCR-###`).
- Batería de pruebas offline deterministas en `tests/` cubriendo los escenarios de `FWK-002` (`RFC-001` §10 `#6`–`#12` aplicables en código/config/contratos + tests de `sdd_vendor_update.py`, `uiux` config y verificación de `VENDOR.lock.json`).

### 🚫 Fuera del Alcance (Out-of-Scope)
- Quality gates visuales automáticos en `@qa-tester`, `@a11y-architect` y CI/CD (contraste, teclado, responsive, coherencia automática de tokens con código, regresiones de capturas con baseline humana): corresponde a **`FWK-003`**.
- Unificación global de terminología de Gates en `SDD_FRAMEWORK.md`, `BACKLOG.md` y `AGENTS.md`: corresponde a **`FWK-004`**.
- Ejecución de una feature de proyecto real `Design System Foundation` o creación de `docs/design-system/MASTER.md` propio para este starter vacío.
- Soportes `targets` distintos de `web` (mobile/desktop nativos quedan preparados a nivel de metadato en `pack.json`, no implementados en `FWK-002`).
- Modificación de `src/` o `specs/BACKLOG.md` del proyecto plantilla (salvo la instrucción de cómo `sdd-bootstrap` registrará la feature cuando un proyecto humano ejecute Gate 00).

---

## 4. Requisitos del Sistema bajo Protocolo EARS

| ID Requisito | Fuente | Patrón EARS | Cláusula EARS (Sintaxis Formal Canónica) | Componente Afectado |
|---|---|---|---|---|
| `RF-001` | `SRC-001` | `Ubiquitous` | `El sistema de catálogo del framework deberá incluir el pack .sdd/catalog/packs/capability-ui-design/ con pack.json válido (id capability:ui-design, requires capability:web-frontend, targets web, rules vacío, upstream y vendor_lock), NOTICE.md de atribución MIT y activos vendorizados fijados en vendor/ui-ux-pro-max/ sin modificar packs ECC existentes.` | `.sdd/catalog/packs/capability-ui-design/` |
| `RF-002` | `SRC-001` | `Ubiquitous` | `El sistema vendor/ui-ux-pro-max deberá mantener un manifiesto VENDOR.lock.json con versión fijada, fecha y hash SHA-256 por cada fichero vendorizado, sin ejecutar llamadas npx ni peticiones de red durante la materialización o la operación de diseño.` | `vendor/ui-ux-pro-max/VENDOR.lock.json`, `scripts/sdd_pack_registry.py` |
| `RF-003` | `SRC-001` | `Event-driven` | `CUANDO se ejecute sdd_agent_generator.py --materialize con Gate 00 aprobado, capability-ui-design en packs y uiux.enabled en true, el sistema deberá materializar .agents/agents/ui-ux-designer.md (con cabecera GENERATED), .agents/skills/sdd-ui-design/, .agents/skills/ui-ux-pro-max/, .agents/workflows/ui-design-review.md y .agent-inbox/ui-ux-designer/.` | `scripts/sdd_agent_generator.py`, `.agents/` |
| `RF-004` | `SRC-001` | `Unwanted` | `SI algún fichero bajo vendor/ui-ux-pro-max/ falta, no está declarado en VENDOR.lock.json o presenta un hash SHA-256 distinto al registrado en VENDOR.lock.json, ENTONCES el sistema deberá abortar la verificación y la materialización con error explícito y código de salida distinto de cero antes de modificar .agents/.` | `scripts/sdd_vendor_update.py`, `scripts/sdd_pack_registry.py` |
| `RF-005` | `SRC-001` | `Event-driven` | `CUANDO un mantenedor ejecute scripts/sdd_vendor_update.py para actualizar el proveedor vendorizado, el sistema deberá ejecutar la instalación únicamente en un directorio temporal aislado, validar licencia/estructura/exclusiones, generar un resumen o diff para revisión humana y actualizar vendor/ui-ux-pro-max/ junto con VENDOR.lock.json solo tras validación.` | `scripts/sdd_vendor_update.py` |
| `RF-006` | `SRC-001` | `State-driven` | `MIENTRAS specs/STACK.md declare un proyecto sin interfaz web (preset api-only o uiux.enabled: false sin capability-ui-design), el sistema sdd_agent_generator deberá omitir @ui-ux-designer, sdd-ui-design, ui-ux-pro-max y ui-design-review.md, manteniendo operativas las skills ECC de capability-web-frontend cuando dicho pack esté activo.` | `scripts/sdd_pack_registry.py`, `scripts/sdd_agent_generator.py` |
| `RF-007` | `SRC-001` | `Optional` | `DONDE el proyecto definido en sdd-bootstrap (ES-ES o EN-GB) incluya interfaz visual (Fullstack o Solo Frontend), el asistente sdd-bootstrap deberá formular las preguntas de configuración uiux (activación del proveedor, hifi_format y brand_constraints opcional), omitiéndolas en proyectos Solo Backend o CLI.` | `.agents/skills/sdd-bootstrap/SKILL.md`, `specs/templates/00-stack.template.md` |
| `RF-008` | `SRC-001` | `Event-driven` | `CUANDO el usuario apruebe Gate 00 en sdd-bootstrap con uiux.enabled: true, el asistente deberá instruir y registrar la feature fundacional Design System Foundation en specs/BACKLOG.md con el siguiente ID FEAT-XXX secuencial disponible, Gate 0 [x] y estado Backlog.` | `.agents/skills/sdd-bootstrap/SKILL.md` |
| `RF-009` | `SRC-001` | `State-driven` | `MIENTRAS una feature toque al menos una pantalla (SCR-###) con capability-ui-design activo, el sistema de gobernanza (@orchestrator y 02-technical-spec.template.md) deberá exigir la delegación de diseño en Gate 2 a @ui-ux-designer, la revisión independiente de @a11y-architect, la validación técnica de @architect y la casilla bloqueante [ ] Visual Sign-off (Human) en 02-tech-spec.md.` | `.agents/agents/orchestrator.md`, `specs/templates/02-technical-spec.template.md`, `workflows/ui-design-review.md` |
| `RF-010` | `SRC-001` | `Unwanted` | `SI una feature tiene Gate 1 sin aprobar (o carece de wireframes funcionales aprobados), O SI un diseño propuesto introduce o altera comportamiento funcional, ENTONCES @ui-ux-designer deberá rechazar la generación de hi-fi y activar Stop-the-Line para retornar a Gate 1 sin modificar src/, tests/, 01-spec.md ni features en estado Done.` | `.sdd/catalog/packs/capability-ui-design/agents/ui-ux-designer.md`, `skills/sdd-ui-design/SKILL.md` |
| `RF-011` | `SRC-001` | `Ubiquitous` | `La skill adaptadora sdd-ui-design y los arquetipos frontend actualizados deberán gobernar docs/design-system/ bajo versionado semver (MASTER.md, design-tokens.json, CHANGELOG.md, pages/SCR-XXX.md), prohibiendo usar --force sobre un MASTER.md existente, exigiendo referencias a tokens (nunca valores literales) y canalizando cambios posteriores al Done de la fundacional mediante un único CR sobre la feature fundacional (y CR adicional solo si cambia comportamiento funcional de pantallas Done).` | `skills/sdd-ui-design/SKILL.md`, `.sdd/catalog/archetypes/front-*.archetype.md`, `.sdd/catalog/archetypes/tier-frontend.archetype.md` |
| `RF-012` | `SRC-001` | `Event-driven` | `CUANDO se ejecute scripts/sdd_catalog_import.py sobre el catálogo con capability-ui-design presente en .sdd/catalog/packs/, el importador deberá dejar intacto byte a byte el directorio capability-ui-design.` | `scripts/sdd_catalog_import.py`, `tests/` |

---

## 4.1. Reglas de Negocio Vinculantes (`RN-###`)
1. **RN-01 (Procedencia Exclusiva y Offline del Proveedor)**: `capability-ui-design` es un pack propio fuera de `STACK_PACKS`; sus activos provienen únicamente de `vendor/ui-ux-pro-max/` verificados por `VENDOR.lock.json` (`SHA-256`). Ningún agente ni `--materialize` puede invocar `npx` ni descargar recursos en tiempo de diseño.
2. **RN-02 (Poda UI-Only en Gate 00)**: Los proyectos sin UI (`api-only`, `CLI`) nunca muestran preguntas `uiux` ni activan `@ui-ux-designer`; en proyectos con UI, activar `uiux.enabled: true` exige `capability-web-frontend` (`requires`) y registra `Design System Foundation` en `specs/BACKLOG.md`.
3. **RN-03 (Degradación Sin Proveedor)**: Con `capability-web-frontend` activo y `uiux.enabled: false`, el proyecto conserva intactas las capacidades ECC (`@a11y-architect`, `design-system`, `accessibility`, `browser-qa`) sin `@ui-ux-designer` ni skills de `ui-ux-pro-max`.
4. **RN-04 (Gate 1 Previo y No Invasión Funcional)**: `@ui-ux-designer` tiene Gate 1 aprobado (con wireframes §18) como DoR bloqueante. Si el diseño altera flujos, controles o reglas funcionales, se dispara *Stop-the-Line* (`RN-SDD-FAIL-CLOSED`) hacia Gate 1.
5. **RN-05 (Cadena de Revisión y Sign-Off Visual en Gate 2)**: Todo diseño visual en features con `SCR-###` atraviesa `@ui-ux-designer` → `@a11y-architect` → `@architect` → `[ ] Visual Sign-off (Human)` en `02-tech-spec.md`. En features sin `SCR-###`, la subsección se marca `N/A` y no bloquea Gate 2.
6. **RN-06 (Frontera de Escritura y Prohibición de `--force`)**: `@ui-ux-designer` solo escribe en `docs/design-system/**` (vía `Design System Foundation` o CR sobre ella, y `pages/SCR-XXX.md` de la feature activa) y `specs/features/<activa>/ux/**`. Nunca escribe en `src/**`, `tests/**`, `01-spec.md`, features `Done` ni sobrescribe `MASTER.md` con `--force`.
7. **RN-07 (Semver y Cardinalidad 1:1 en Evolución de Tokens)**: Los cambios tras el `Done` de `Design System Foundation` incrementan semver (`patch`/`minor`/`major`) y actualizan `CHANGELOG.md` mediante **1 CR sobre la feature fundacional**; los re-skins puros por tokens no abren CRs sobre features consumidoras `Done`, mientras que cambios de comportamiento funcional en `SCR` `Done` sí exigen 1 CR por cada feature afectada.

---

## 4.2. Example Mapping (Datos Concretos de Entrada / Salida)

| Regla Asociada | Caso de Ejemplo | Datos de Entrada (Input Real) | Estado / Precondición | Salida Esperada (Output Verificable) |
|---|---|---|---|---|
| `RN-01` | Verificación de `VENDOR.lock.json` limpia | `capability-ui-design/vendor/ui-ux-pro-max/` íntegro + `sdd_agent_generator.py --materialize` | `gate00_approved: true`, `packs: [capability-web-frontend, capability-ui-design]`, `uiux.enabled: true` | Exit code `0`; `.agents/agents/ui-ux-designer.md`, `.agents/skills/sdd-ui-design/`, `.agents/skills/ui-ux-pro-max/`, `.agents/workflows/ui-design-review.md` y `.agent-inbox/ui-ux-designer/` creados. |
| `RN-01` | Vendor alterado (Escenario `#10`) | 1 byte modificado en un fichero de `vendor/ui-ux-pro-max/` sin actualizar `VENDOR.lock.json` | Pack `capability-ui-design` activo | `sdd_vendor_update.py --verify` y `--materialize` fallan con exit code `!= 0`, identificando la ruta y mismatch SHA-256; `.agents/` sin cambios parciales. |
| `RN-02` | Proyecto `api-only` (Escenario `#7`) | `STACK.md` con `gate00_approved: true`, `preset: api-only`, `packs: [lang-python, framework-fastapi]` | Sin bloque `uiux` ni `capability-ui-design` | `@ui-ux-designer`, `sdd-ui-design` y `ui-ux-pro-max` ausentes de `.agents/` y `squad.lock.json`. |
| `RN-03` | `spa-only` sin proveedor (Escenario `#9`) | `STACK.md` con `gate00_approved: true`, `preset: spa-only`, `packs: [lang-typescript, framework-react, capability-web-frontend]`, `uiux: {enabled: false}` | `capability-web-frontend` presente | `@a11y-architect` y skills ECC (`design-system`, `accessibility`, `browser-qa`) materializados; `@ui-ux-designer` y `ui-ux-pro-max` ausentes. |
| `RN-04` | Gate 1 sin aprobar (Escenario `#11`) | Solicitud a `@ui-ux-designer` sobre `FEAT-003` cuyo `01-spec.md` tiene `[ ] Gate 1 Aprobado` | Pack activo | `@ui-ux-designer` rechaza generar hi-fi y emite bloqueo DoR (`BLOCKED_DOR_FEAT-003.md` / Stop-the-Line). |
| `RN-07` | Cambio de token post-`Done` (Escenario `#12`) | Cambio de valor de token primario tras `Done` de `FEAT-002` (`Design System Foundation`), con `FEAT-003` (`SCR-001`) `Done` | Re-skin puro sin cambio funcional de `SCR-001` | 1 único `CR-001` sobre `FEAT-002` con bump `patch`/`minor` en `MASTER.md` + `CHANGELOG.md`; `specs/features/FEAT-002*/` y `FEAT-003*/` intocadas. |

---

## 4.3. Requisitos No Funcionales y SLAs Cuantitativos (Planguage)

- **Tag**: `REL-VENDOR-INTEGRITY-01`
  - **Ambition**: Detección determinista de cualquier manipulación, borrado o fichero no declarado dentro de `vendor/ui-ux-pro-max/`.
  - **Scale**: Porcentaje de alteraciones (modificación de 1 byte, supresión o añadido no registrado) detectadas antes de materializar `.agents/`.
  - **Meter**: Test unitario offline de verificación SHA-256 contra `VENDOR.lock.json` ejecutado vía `uv run python -m unittest`.
  - **Baseline**: Inexistente (`0%` de verificación de activos externos vendorizados).
  - **Target**: `100%` de detecciones *fail-closed* con código de salida distinto de `0`.
  - **Constraint**: `< 100%` (cualquier alteración no detectada invalida el requisito).

- **Tag**: `PERF-FWK-TESTS-01`
  - **Ambition**: Mantener ejecución rápida y 100% offline de la suite completa de tests del framework.
  - **Scale**: Segundos de ejecución total de `uv run python -m unittest discover tests -v` y llamadas de red reales.
  - **Meter**: Ejecución directa en entorno local/CI sin acceso a npm ni GitHub (`fetch` / subprocesos mockeados en tests de `sdd_vendor_update.py` y `sdd_catalog_import.py`).
  - **Baseline**: Suite actual (`test_sdd_governance.py` + `test_sdd_pack_materialization.py` + `test_sdd_token_usage.py`) en `< 1.0s` con `0` llamadas de red reales.
  - **Target**: `< 3.0s` para toda la suite en `tests/` con `0` llamadas de red reales.
  - **Constraint**: `> 8.0s` o cualquier dependencia de red en tests unitarios.

---

## 5. Criterios de Aceptación (BDD / Given-When-Then)

### Escenario 1: Preservación de `capability-ui-design` en `sdd_catalog_import.py` (`RFC-001` §10 #6)
- **Dado que** `.sdd/catalog/packs/capability-ui-design/` existe en el catálogo con `pack.json`, `NOTICE.md`, `VENDOR.lock.json` y sus activos
- **Cuando** se ejecuta `scripts/sdd_catalog_import.py` con un fetcher simulado para `affaan-m/ecc`
- **Entonces** los packs de `STACK_PACKS` (incluidos sus workflows) se actualizan normalmente
- **Y** el contenido completo de `.sdd/catalog/packs/capability-ui-design/` permanece idéntico byte a byte.

### Escenario 2: Proyecto `api-only` con Gate 00 aprobado (`RFC-001` §10 #7)
- **Dado que** `specs/STACK.md` tiene `[x] Gate 00 Approved`, `gate00_approved: true`, `preset: api-only` y `packs: [lang-python, framework-fastapi]`
- **Cuando** se ejecuta `sdd_agent_generator.py --materialize`
- **Entonces** la materialización termina con éxito
- **Y** ni `.agents/agents/ui-ux-designer.md`, ni `.agents/skills/sdd-ui-design/`, ni `.agents/skills/ui-ux-pro-max/`, ni `.agents/workflows/ui-design-review.md` existen en el workspace ni en `.agents/squad.lock.json`.

### Escenario 3: Proyecto `spa-only` con `uiux.enabled: true` (`RFC-001` §10 #8)
- **Dado que** un proyecto se configura en `sdd-bootstrap` como `Solo Frontend` con `uiux.enabled: true` (`capability-web-frontend` + `capability-ui-design` y Gate 00 aprobado)
- **Cuando** se finaliza el bootstrap y se ejecuta `sdd_agent_generator.py --materialize`
- **Entonces** quedan disponibles `.agents/agents/ui-ux-designer.md` (con cabecera `GENERATED`), `.agent-inbox/ui-ux-designer/`, `.agents/skills/sdd-ui-design/`, `.agents/skills/ui-ux-pro-max/` y `.agents/workflows/ui-design-review.md`
- **Y** la especificación de `sdd-bootstrap` garantiza el registro de la feature fundacional `Design System Foundation` en `specs/BACKLOG.md`.

### Escenario 4: Proyecto `spa-only` sin proveedor externo (`RFC-001` §10 #9)
- **Dado que** `specs/STACK.md` tiene `[x] Gate 00 Approved`, `preset: spa-only`, `packs: [lang-typescript, framework-react, capability-web-frontend]` y `uiux.enabled: false`
- **Cuando** se ejecuta `sdd_agent_generator.py --materialize`
- **Entonces** se materializan `@a11y-architect` y las skills ECC `design-system`, `accessibility` y `browser-qa`
- **Y** no se materializan `@ui-ux-designer` ni las skills `sdd-ui-design` / `ui-ux-pro-max`.

### Escenario 5: Detección de alteración en `vendor/` (`RFC-001` §10 #10)
- **Dado que** un fichero dentro de `.sdd/catalog/packs/capability-ui-design/vendor/ui-ux-pro-max/` ha sido alterado, borrado o añadido sin corresponder con `VENDOR.lock.json`
- **Cuando** se ejecuta la verificación de `VENDOR.lock.json` (`sdd_vendor_update.py --verify` o `sdd_agent_generator.py --materialize` con el pack activo)
- **Entonces** la ejecución falla de forma explícita (*fail-closed*, código de salida distinto de `0`) indicando la ruta afectada
- **Y** no se materializa ningún fichero en `.agents/`.

### Escenario 6: Bloqueo DoR de `@ui-ux-designer` ante Gate 1 sin aprobar (`RFC-001` §10 #11)
- **Dado que** el pack `capability-ui-design` está activo pero una feature con pantalla `SCR-001` no tiene Gate 1 aprobado ni wireframes funcionales validados
- **Cuando** se solicita a `@ui-ux-designer` producir el diseño de alta fidelidad
- **Entonces** el contrato del agente y de `sdd-ui-design` le ordenan rechazar la generación de hi-fi, emitir el bloqueo DoR correspondiente y exigir la aprobación previa de Gate 1.

### Escenario 7: Evolución de tokens tras `Done` sin romper `RN-SDD-IMMUTABLE-DONE` (`RFC-001` §10 #12)
- **Dado que** la feature fundacional `Design System Foundation` y una feature consumidora con `SCR-001` están en estado `Done`
- **Cuando** se solicita ajustar o añadir tokens sin modificar el comportamiento funcional de `SCR-001`
- **Entonces** las reglas operativas de `sdd-ui-design` y `ui-design-review.md` canalizan el cambio mediante **1 único CR** sobre `Design System Foundation` con bump semver y entrada en `docs/design-system/CHANGELOG.md`, manteniendo intactas las carpetas `specs/features/` `Done`.

---

## 6. Pre-Mortem Inverso (Anticipación de Puntos Ciegos y Fallos)

1. **Escenario de Fallo Catastrófico 1**: Al ejecutar `npx ui-ux-pro-max-cli init --ai antigravity`, el instalador sobreescribe o contamina archivos de `.agents/` o intenta leer/escribir rutas relativas fuera de un sandbox, o sus scripts internos en Python importan paquetes externos o ejecutan telemetría HTTP en runtime.
   - **Causa Oculta**: Adoptar el CLI del proveedor sin ejecutar un Spike PoC auditado en directorio temporal aislado antes de definir el diseño de vendorización.
   - **Mitigación Preventiva en Gate 1**: El Spike PoC es precondición obligatoria de Gate 2 (`RFC-001` §9) con inventario completo de ficheros, comprobación de red/telemetría, versión mínima de Python y licencia MIT; además `npx` queda prohibido fuera de `scripts/sdd_vendor_update.py` en directorio temporal.
2. **Escenario de Fallo Catastrófico 2**: Un usuario activa `uiux.enabled: true` en `STACK.md` olvidando `capability-ui-design` o `capability-web-frontend` en `packs`, obteniendo un estado inconsistente donde cree tener el sistema de diseño activo pero `@ui-ux-designer` no existe.
   - **Causa Oculta**: Tratar `uiux` como un campo meramente informativo desconectado de `packs`.
   - **Mitigación Preventiva en Gate 1**: `AMB-002` propone validación *fail-closed* de coherencia entre `uiux.enabled` y `packs`, complementada con la comprobación existente de `requires: ["capability:web-frontend"]`.
3. **Escenario de Fallo Catastrófico 3**: Al ejecutar `sdd-ui-design` o `design-system` para una segunda feature o un CR, el script del proveedor sobrescribe `docs/design-system/MASTER.md` con `--force` borrando tokens aprobados y el historial semver.
   - **Causa Oculta**: El CLI o script por defecto escribe directamente en `design-system/MASTER.md` respecto al directorio de trabajo.
   - **Mitigación Preventiva en Gate 1**: Prohibición explícita de `--force` sobre un `MASTER.md` existente (`RN-06` y `RF-011`) y ejecución aislada en directorio temporal o ruta parametrizada cuando `MASTER.md` ya existe.

---

## 7. Incógnitas y Decisiones Pendientes (`NOT_ENOUGH_INFO` — Tarjetas Rojas / Stop-the-Line)
- [x] **`AMB-001`**: Resuelto (Opción A) — determinar y verificar `<PIN_APROBADO>` mediante el Spike PoC aislado en Gate 2 y someterlo a sign-off humano en Gate 2.
- [x] **`AMB-002`**: Resuelto (Opción A) — exigir coherencia estricta (*fail-closed*) entre `uiux.enabled` y `capability-ui-design` en `packs`.
- [x] **`AMB-003`**: Resuelto (Opción A) — verificar `VENDOR.lock.json` tanto en `sdd_vendor_update.py --verify` como automáticamente en `sdd_pack_registry.py` / `sdd_agent_generator.py --materialize`.
- [x] **`AMB-004`**: Resuelto (Opción A) — bloqueo `[ ] Visual Sign-off (Human)` en `02-technical-spec.template.md`, `orchestrator.md` y `ui-design-review.md`, dejando automatizaciones de QA/CI en hooks para `FWK-003`.
- [x] **`AMB-005`**: Resuelto (Opción A) — registro de `Design System Foundation` en `specs/BACKLOG.md` por `sdd-bootstrap` con el siguiente ID `FEAT-XXX` secuencial libre, Gate 0 `[x]` y estado `Backlog`.
- [x] **`AMB-006`**: Resuelto (Opción A) — 3 preguntas `uiux` condicionales (solo UI) en `sdd-bootstrap/SKILL.md`, bloque `sdd:stack-config` en `00-stack.template.md` y `specs/STACK.md` mantenido en estado bloqueado (`gate00_approved: false`, `packs: []`, `uiux.enabled: false`).
- [x] **`AMB-007`**: Resuelto (Opción A) — DoR de Design System en `front-ui`, `front-engineer` y `tier-frontend`, y esquema normativo `docs/design-system/` documentado en `skills/sdd-ui-design/SKILL.md`.

---

## 8. Aprobación Formal Gate 1 (`RN-SDD-HUMAN-GATE-OWNERSHIP`)
> ⚠️ **Exclusivo para el Stakeholder Humano** (Los agentes de IA tienen prohibido marcar esta casilla por su cuenta):
- [x] **Gate 1 Aprobado por el Usuario**: El alcance funcional, requisitos EARS, ejemplos concretos, métricas Planguage, criterios BDD y resolución de `AMB-001`..`AMB-007` han sido revisados y validados (aprobación expresa en chat 2026-11-11: *"De acuerdo y confirmo"*).
