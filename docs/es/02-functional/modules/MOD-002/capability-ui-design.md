<p align="right">
  <a href="../../../../en/02-functional/modules/MOD-002/capability-ui-design.md">🇬🇧 English (EN-GB)</a> | <strong>🇪🇸 Español (ES-ES)</strong>
</p>

# `MOD-002`: Pack `capability-ui-design` y Gobernanza Visual SDD

- **Identificador de Módulo:** `MOD-002`
- **Work Item / RFC de Origen:** `FWK-002-capability-ui-design` y `FWK-003-conditional-visual-gates` ([`RFC-001` v2](../../../../../.sdd/framework/rfcs/RFC-001-ui-ux-pro-max.md))
- **Estado Funcional:** `Verified` (Confirmado y verificado por pruebas offline deterministas)
- **Índice Maestro:** [DOCUMENTATION-INDEX.md](../../../00-governance/DOCUMENTATION-INDEX.md)

---

## 1. Propósito y Alcance

### 1.1. Propósito (Confirmado)
Este módulo dota a los proyectos con interfaz web del framework SDD de una capacidad de diseño UI/UX **gobernada, 100% offline, accesible y compatible con `RN-SDD-IMMUTABLE-DONE` y `RN-SDD-1-TO-1-CR`**.

Para lograrlo, incorpora el pack independiente `.sdd/catalog/packs/capability-ui-design/`, la vendorización verificada por SHA-256 de `ui-ux-pro-max-cli@2.15.0` (MIT), el agente `@ui-ux-designer`, el adaptador `sdd-ui-design`, el flujo de revisión en Gate 2 (`/ui-design-review`), la configuración condicional en `sdd-bootstrap` y las reglas de evolución semver de `docs/design-system/`.

### 1.2. Alcance Incluido (Confirmado)
- Pack autónomo no-ECC `.sdd/catalog/packs/capability-ui-design/` (`id: "capability:ui-design"`, `requires: ["capability:web-frontend"]`, `targets: ["web"]`, `rules: []`) con `NOTICE.md` MIT y preservación byte a byte frente a `scripts/sdd_catalog_import.py`.
- Vendorización offline y verificable (`VENDOR.lock.json` SHA-256) de `ui-ux-pro-max@2.15.0` (`46` entradas: `45` ficheros runtime + `LICENSE` MIT), excluyendo las 6 skills hermanas y `scripts/tests/`, junto con `.gitattributes` (`text eol=lf`).
- Actualizador aislado `scripts/sdd_vendor_update.py` (único componente autorizado para invocar `npx` dentro de un directorio temporal, con diff previo a `--apply`) y verificación automática en `scripts/sdd_pack_registry.py` antes de materializar `.agents/`.
- Validación *fail-closed* del bloque `uiux` en `sdd:stack-config` y coherencia estricta `uiux.enabled` ↔ `capability-ui-design` tras Gate 00.
- Poda dinámica en `sdd-bootstrap` (ES-ES y EN-GB) para proyectos sin UI (`Solo Backend / API Only`, `CLI / Herramienta Local`), preguntas `uiux` condicionales en proyectos con UI y alta automática de `Design System Foundation` en `specs/BACKLOG.md` al aprobar Gate 00 con `uiux.enabled: true`.
- Contrato estricto de `@ui-ux-designer`, workflow `ui-design-review.md` en Gate 2 (`@ui-ux-designer` → `@a11y-architect` → `@architect` → `[ ] Visual Sign-off (Human)`), subsección §6.1 en `02-technical-spec.template.md`, orquestación en `.agents/agents/orchestrator.md` y DoR de tokens en arquetipos frontend (`front-ui`, `front-engineer`, `tier-frontend`).
- Esquema canónico semver para `docs/design-system/` (`MASTER.md`, `design-tokens.json`, `CHANGELOG.md`, `pages/SCR-XXX.md`) definido dentro de `skills/sdd-ui-design/SKILL.md`.
- Suite de Quality Gates visuales condicionales y validador determinista offline `scripts/sdd_tokens_validator.py` (Python 3.12 stdlib, `<= 500` líneas) para cotejo bidireccional JSON ↔ `MASTER.md`, escaneo estático de literales prohibidos (`--check-sources`), 4ª auditoría en `@qa-tester`, arquetipo `front-test.archetype.md` y gobernanza estricta de baselines (`INCONCLUSIVE` ante ausencias, prohibición de auto-actualización agéntica de snapshots) (`FWK-003`).

### 1.3. Excluido Explícitamente (Alcance Futuro)
- **No** se crea una carpeta `docs/design-system/` vacía en el repositorio starter; dicha estructura nace únicamente en el proyecto usuario al ejecutar la feature fundacional `Design System Foundation`.

- Unificación global de terminología de Gates en `SDD_FRAMEWORK.md`, `BACKLOG.md` y `AGENTS.md`: corresponde a **`FWK-004`**.
- Soporte operativo para `targets` distintos de `web` (solo preparado a nivel de metadato en `pack.json`).

---

## 2. Actores y Autoridad

| Actor | Responsabilidad | Restricción Principal |
| :--- | :--- | :--- |
| **Usuario Humano / Stakeholder** | Decide en `sdd-bootstrap` si activa `uiux` y aprueba Gate 00, Gate 1 (wireframes), `[x] Visual Sign-off (Human)` y Gate 2. | Ningún agente puede marcar `[x] Visual Sign-off (Human)` ni Gate 00/1/2 por su cuenta (`RN-SDD-HUMAN-GATE-OWNERSHIP`). |
| **`@orchestrator`** | Ejecuta `sdd-bootstrap`, registra `Design System Foundation` tras Gate 00 si `uiux.enabled: true`, coordina `/ui-design-review` en Gate 2 y propaga `SCR-XXX`, `MASTER@versión` y tokens al DoR de Gate 3. | Si una feature no toca `SCR-###`, marca §6.1 y `Visual Sign-off (Human)` como `N/A`. |
| **`@ui-ux-designer`** | Consulta `search.py --json` offline (`sdd-ui-design`), redacta propuestas de tokens (`Design System Foundation` o su CR), overrides `pages/SCR-XXX.md` y prototipos hi-fi trazados a `RF-###` / `SCR-###` / tokens. | Bloqueado sin Gate 1 + wireframes §18; prohibido `src/**`, `tests/**`, `01-spec.md`, features `Done`, `npx` o `--force` sobre `MASTER.md`. |
| **`@a11y-architect`** | Ejecuta revisión independiente WCAG 2.2 AA sobre tokens, `pages/SCR-XXX.md` e hi-fi usando la skill `accessibility`. | Permanece activo incluso cuando `uiux.enabled: false` si `capability-web-frontend` está activo (`RN-03`). |
| **`@architect`** | Valida estados UI, contratos y rangos `MASTER@versión` cumplimentando `02-tech-spec.md` §6.1. | Aplica *Stop-the-Line* si detecta cambio funcional no aprobado en Gate 1. |
| **Constructores UI (`@front-ui`, `@front-engineer`, `tier-frontend`)** | Implementan componentes y vistas en código durante Gate 4 usando tokens de `docs/design-system/design-tokens.json`. | Exigen `SCR-XXX`, `MASTER@versión`, `pages/SCR-XXX.md` y tokens en su DoR; prohibido hardcodear valores literales cuando exista token. |
| **Mantenedor del Framework** | Verifica o actualiza el proveedor vendorizado con `scripts/sdd_vendor_update.py`. | Debe revisar el diff antes de aplicar `--apply` y jamás usar `npx` fuera de este script. |

---

## 3. Reglas de Negocio y Comportamiento del Sistema

### 3.1. Procedencia Offline Exclusiva e Integridad del Proveedor (`RN-01`, `RF-001`, `RF-002`, `RF-004`, `RF-012`)
1. `capability-ui-design` es un pack independiente fuera de `STACK_PACKS` en `scripts/sdd_catalog_import.py`: ejecutar el importador ECC deja su directorio **intacto byte a byte**.
2. Sus activos vendorizados en `vendor/ui-ux-pro-max/` proceden exclusivamente de `ui-ux-pro-max-cli@2.15.0` (MIT, atribución explícita en `NOTICE.md` separada de `affaan-m/ecc`).
3. Durante la extracción se conservan **únicamente** los `45` ficheros runtime de `ui-ux-pro-max` más `LICENSE` (`46` entradas en `VENDOR.lock.json`), descartando las 6 skills hermanas (`banner-design`, `brand`, `design`, `design-system` —que colisionaría con `capability-web-frontend/skills/design-system`—, `slides` y `ui-styling` Apache 2.0) y `scripts/tests/`.
4. Cada fichero vendorizado se verifica por longitud en `bytes` y digest `sha256` contra `VENDOR.lock.json` tanto mediante `scripts/sdd_vendor_update.py --verify` como automáticamente durante `sdd_pack_registry.resolve_pack_assets()` / `sdd_agent_generator.py --materialize`. Ante cualquier fichero faltante, alterado (incluso 1 byte) o no declarado, el sistema aborta *fail-closed* antes de mutar `.agents/`.
5. `.gitattributes` fija `text eol=lf` para `.sdd/catalog/packs/capability-ui-design/**` y `.agents/**`, garantizando determinismo de SHA-256 entre Windows y POSIX.

### 3.2. Poda UI-Only, Configuración `uiux` y Degradación Segura (`RN-02`, `RN-03`, `RF-003`, `RF-006`, `RF-007`, `RF-008`)
1. **Poda en `sdd-bootstrap` (ES-ES y EN-GB):** en proyectos `Solo Backend / API Only` o `CLI / Herramienta Local`, el asistente omite por completo las 3 preguntas `uiux` y no añade `capability-ui-design`. En proyectos con UI (`Fullstack` o `Solo Frontend`), pregunta: (a) activar inteligencia `ui-ux-pro-max` vs solo skills ECC, (b) `uiux.hifi_format` (`html` recomendado / `figma` / `html+figma`), y (c) `uiux.brand_constraints` opcional.
2. **Validación estricta de `uiux` en `sdd:stack-config`:** solo admite las claves `enabled` (`bool` obligatorio), `provider` (`"ui-ux-pro-max"` cuando `enabled: true`), `version`, `hifi_format` (`html` | `figma` | `html+figma`) y `brand_constraints` (`null` o ruta relativa segura). Rechaza `uiux.enabled: true` con `preset: api-only`.
3. **Coherencia `uiux.enabled` ↔ `packs`:** cuando Gate 00 está aprobado, `uiux.enabled: true` exige `capability-ui-design` (y su dependencia `capability:web-frontend`) en `packs`, e incluir `capability-ui-design` exige `uiux.enabled: true`.
4. **Materialización con proveedor activo:** `sdd_agent_generator.py --materialize` genera `.agents/agents/ui-ux-designer.md` (con cabecera `GENERATED`), `.agent-inbox/ui-ux-designer/.gitkeep`, `.agents/skills/sdd-ui-design/`, `.agents/skills/ui-ux-pro-max/` (con `scripts/search.py` y datasets) y `.agents/workflows/ui-design-review.md`, protegidos contra sincronización inversa por `squad.lock.json` v2 y `sdd_sync.py`.
5. **Degradación sin proveedor (`RN-03`):** con `capability-web-frontend` activo y `uiux.enabled: false`, el proyecto conserva intactos `@a11y-architect` y las skills ECC (`design-system`, `accessibility`, `browser-qa`, `frontend-a11y`, `make-interfaces-feel-better`, `motion-foundations`, `i18n-sync`), sin materializar `@ui-ux-designer` ni `ui-ux-pro-max`.
6. **Alta automática en `specs/BACKLOG.md` (`RF-008`):** únicamente cuando Gate 00 se aprueba con `uiux.enabled: true`, `sdd-bootstrap` instruye a `@orchestrator` a registrar una fila **`Design System Foundation`** en `specs/BACKLOG.md` con el siguiente ID `FEAT-XXX` secuencial disponible, `Gate 0 (Intake)` = `[x]` y estado `Backlog` (sin crear carpetas ni código hasta abrir su sesión dedicada Gate 1–5).

### 3.3. Gate 1 Previo, Cadena de Revisión Visual en Gate 2 y Stop-the-Line (`RN-04`, `RN-05`, `RN-06`, `RF-009`, `RF-010`)
1. **DoR bloqueante de `@ui-ux-designer`:** exige simultáneamente (1) Gate 00 aprobado con `uiux.enabled: true`, (2) `01-spec.md` de la feature con `[x] Gate 1 Aprobado` y wireframes §18 validados (`wireframe.excalidraw` + `screen-spec.md`), y (3) `docs/design-system/MASTER.md` vigente (o que la feature activa sea `Design System Foundation` o un CR sobre ella). Si falta cualquiera, emite `.agent-inbox/ui-ux-designer/BLOCKED_DOR_<FEAT-ID>.md` y se detiene.
2. **Consulta offline segura:** ejecuta `uv run python .agents/skills/ui-ux-pro-max/scripts/search.py "<query>" --design-system -p "<project>" --json` (fallbacks `python3` / `py -3`, nunca `npx` ni `--force` sobre `MASTER.md`; si usa `--persist`, emplea siempre `--output-dir <temp_dir>`). En entornos Air-Gapped emite advertencia si el proveedor sugiere URLs de Google Fonts.
3. **No invasión funcional (`RN-04`):** si un ajuste visual introduce o altera controles, campos, validaciones o flujos no aprobados en `01-spec.md`, se registra `BLOCKED_<FEAT-ID>.md` y se devuelve el expediente a Gate 1 (*Stop-the-Line*).
4. **Cadena obligatoria en Gate 2 (`RN-05`):** toda feature con `SCR-###` atraviesa `@ui-ux-designer` (trazabilidad `RF-###` → `SCR-###` → token, estados `Confirmado` / `Propuesto` / `Pendiente`, estados UI `default`/`loading`/`empty`/`error` y responsive) → `@a11y-architect` (WCAG 2.2 AA) → `@architect` (`02-tech-spec.md` §6.1 `MASTER@versión`) → `[ ] Visual Sign-off (Human)` (§8).
5. **Frontera de escritura (`RN-06`):** `@ui-ux-designer` solo escribe en `docs/design-system/**` (vía `Design System Foundation` o su CR, y `pages/SCR-XXX.md` de la feature activa) y `specs/features/<activa>/ux/**`; tiene prohibido tocar `src/**`, `tests/**`, `01-spec.md`, features `Done` o casillas `[x]` de sign-off.

### 3.4. Esquema Canónico de `docs/design-system/`, Semver y Cardinalidad de CRs (`RN-07`, `RF-011`)
- La skill `sdd-ui-design` fija la estructura neutra de idioma para proyectos destino (`MASTER.md`, `design-tokens.json`, `CHANGELOG.md`, `pages/SCR-XXX.md`), exigiendo referencias a tokens (prohibidos `#hex`/`px` literales sin token) y separando las vistas auxiliares de la skill ECC `design-system` frente a la autoridad de `MASTER.md`.
- Los arquetipos `front-ui`, `front-engineer` y `tier-frontend` incorporan en su `DoR` y `DoD` la exigencia de `SCR-XXX`, `MASTER@versión`, `docs/design-system/pages/SCR-XXX.md`, prototipo `hi-fi` y tokens de `design-tokens.json`.
- **Evolución post-`Done` (`RN-07`):** tras completar `Design System Foundation`, los cambios de tokens o reglas globales se canalizan como **1 único `CR-XXX` sobre `Design System Foundation`** con bump semver (`MAJOR` con lista explícita de `SCR-###` impactados, `MINOR` retrocompatible o `PATCH` de valor) y entrada en `CHANGELOG.md`:
  - **Re-skin puro por tokens:** no abre CRs sobre features consumidoras en estado `Done` (sus carpetas `specs/features/` permanecen intactas).
  - **Cambio de comportamiento funcional:** sí exige **1 CR independiente por cada feature `Done` afectada** (`RN-SDD-1-TO-1-CR`).

---

## 4. Flujos Operativos Paso a Paso

### Flujo 1: Bootstrap de Proyecto con UI vs Sin UI (`sdd-bootstrap`)
1. El usuario inicia Gate 00 con `@orchestrator`.
2. Si elige `Solo Backend` o `CLI`, las preguntas `uiux` se podan automáticamente y `uiux.enabled` queda desactivado.
3. Si elige `Fullstack` o `Solo Frontend`, decide entre activar `ui-ux-pro-max` (`hifi_format`, `brand_constraints`) o usar únicamente las skills ECC de `capability-web-frontend`.
4. Tras la firma humana `[x] Gate 00 Approved`, `@orchestrator` materializa el escuadrón (`--materialize`) y, si `uiux.enabled: true`, da de alta `Design System Foundation` en `specs/BACKLOG.md`.

### Flujo 2: Verificación de Integridad y Materialización (`--verify` / `--materialize`)
1. Ejecutar `uv run python scripts/sdd_vendor_update.py --verify` para validar los `46` ficheros de `vendor/ui-ux-pro-max/` contra `VENDOR.lock.json`.
2. Al ejecutar `uv run python scripts/sdd_agent_generator.py --materialize` con `capability-ui-design` activo, `resolve_pack_assets()` ejecuta automáticamente la misma comprobación SHA-256 antes de escribir en `.agents/`.

### Flujo 3: Revisión Visual en Gate 2 (`/ui-design-review`)
1. Confirmar DoR (Gate 00 + Gate 1 `[x]` con wireframes §18 + `MASTER.md` o `Design System Foundation`).
2. `@ui-ux-designer` consulta `search.py --json` offline y genera tokens/overrides/hi-fi en `specs/features/<feat>/ux/SCR-XXX/hi-fi/`.
3. `@a11y-architect` audita WCAG 2.2 AA; `@architect` valida contratos y completa `02-tech-spec.md` §6.1 (`MASTER@versión`).
4. Tras verificar cero cambios funcionales no aprobados, el stakeholder humano revisa y autoriza `[x] Visual Sign-off (Human)` y Gate 2.

### Flujo 4: Evolución de Tokens Post-`Done`
1. Abrir **1 único `CR-XXX`** sobre `Design System Foundation`.
2. Actualizar `MASTER.md`, `design-tokens.json` y `CHANGELOG.md` con el incremento semver correspondiente.
3. Mantener intactas las features consumidoras `Done` salvo que exista cambio funcional en sus `SCR-###` (en cuyo caso se abre 1 CR por cada feature afectada).

### Flujo 5: Actualización Controlada del Proveedor por un Mantenedor (`sdd_vendor_update.py`)
1. Previsualizar diff en directorio temporal aislado (sin modificar el catálogo):
   `uv run python scripts/sdd_vendor_update.py --version <X.Y.Z>`
2. Revisar ficheros añadidos/modificados/eliminados y cambio de versión en `pack.json`.
3. Aplicar y regenerar `VENDOR.lock.json` solo tras revisión explícita:
   `uv run python scripts/sdd_vendor_update.py --version <X.Y.Z> --apply`

---

## 5. Estado Verificado en el Starter Base (Confirmado)

En la plantilla limpia (con `[ ] Gate 00 Approved`):
- `specs/STACK.md` mantiene `gate00_approved: false`, `preset: compact`, `packs: []` y `uiux: {enabled: false}`.
- `specs/templates/00-stack.template.md` incluye el bloque completo `yaml sdd:stack-config` con `uiux` documentado (`provider: ui-ux-pro-max`, `version: "2.15.0"`, `hifi_format: html`).
- `specs/templates/02-technical-spec.template.md` incorpora la subsección `### 6.1. Diseño Visual` y la casilla `- [ ] **Visual Sign-off (Human)**` en §8.
- `docs/design-system/` **no existe** en el starter vacío.
- `.sdd/catalog/packs/capability-ui-design/` aloja el pack completo con `vendor/ui-ux-pro-max/` (`46` entradas verificadas en `VENDOR.lock.json`), preservado intacto ante `sdd_catalog_import.py`.
- `.agents/` mantiene únicamente los `28` agentes base y `22` entradas en `squad.lock.json` (`active_packs: []`), sin materializar `@ui-ux-designer` hasta que un proyecto apruebe Gate 00 con `uiux.enabled: true`.

---

## 6. Requisitos, Reglas y Criterios de Aceptación Verificados

| Referencia | Descripción Resumida | Estado |
| :--- | :--- | :--- |
| `RF-001`, `RF-002`, `RN-01` | Pack `capability-ui-design` (`NOTICE.md`, `pack.json`, `rules: []`) y `VENDOR.lock.json` SHA-256 (`46` entradas) 100% offline sin `npx`. | `Verified` |
| `RF-003`, `RF-006`, `RN-02`, `RN-03` | Activación y poda por topología (`api-only`, `spa-only` con `uiux.enabled: true` y degradación ECC con `uiux.enabled: false`) + validación estricta de `uiux`. | `Verified` |
| `RF-004`, `REL-VENDOR-INTEGRITY-01` | Aborto *fail-closed* en `--verify` y `--materialize` ante 1 byte modificado, fichero faltante o fichero extra en `vendor/`. | `Verified` |
| `RF-005` | Actualización aislada en `TemporaryDirectory` vía `sdd_vendor_update.py` con `validate_data.py`, exclusión de skills hermanas/tests, normalización LF y diff previo a `--apply`. | `Verified` |
| `RF-007`, `RF-008` | Preguntas condicionales ES-ES/EN-GB en `sdd-bootstrap`, bloque `sdd:stack-config` en plantillas y alta de `Design System Foundation` en `specs/BACKLOG.md`. | `Verified` |
| `RF-009`, `RF-010`, `RN-04`, `RN-05`, `RN-06` | DoR Gate 1 + wireframes §18 (`BLOCKED_DOR_`), Stop-the-Line funcional, cadena `@ui-ux-designer` → `@a11y-architect` → `@architect` → `[ ] Visual Sign-off (Human)` y fronteras de escritura. | `Verified` |
| `RF-011`, `RN-07` | Esquema semver `docs/design-system/`, prohibición `--force`, referencias a tokens en `SCR-XXX` / arquetipos frontend y cardinalidad 1:1 en CRs post-`Done`. | `Verified` |
| `RF-012` | Preservación byte a byte de `capability-ui-design` frente a `scripts/sdd_catalog_import.py`. | `Verified` |
| `FWK-003: RF-001`..`RF-010`, `RN-01`..`RN-05` | Validador determinista `sdd_tokens_validator.py`, anti-deriva estilística, 4ª auditoría en `@qa-tester`, baselines `INCONCLUSIVE` y poda en `api-only`. | `Verified` |
| `PERF-FWK-TESTS-01` / `03` | Suite completa offline en `tests/` (`45` tests totales, `0` llamadas de red reales, módulos `<= 500` líneas). | `Verified` |

*(Para la correspondencia exacta con ficheros fuente y métodos de prueba, véase [TRACEABILITY-MATRIX.md](../../../../traceability/TRACEABILITY-MATRIX.md)).*
