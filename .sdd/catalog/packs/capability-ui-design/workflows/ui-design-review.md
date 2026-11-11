---
description: "Flujo de revisión y aprobación de diseño UI/UX en Gate 2 para features con pantallas (SCR-###): DoR Gate 1, diseño offline con sdd-ui-design, revisión WCAG 2.2 AA por @a11y-architect, validación por @architect, control Stop-the-Line y Visual Sign-off humano."
---

# Workflow: `/ui-design-review` (Revisión Visual Gate 2 con `capability-ui-design`)

Secuencia obligatoria de **6 pasos** en **Gate 2** para toda feature (o Change Request activo) que incorpore o modifique pantallas `SCR-###` cuando `capability-ui-design` y `uiux.enabled: true` están activos en `specs/STACK.md`.

> Si la feature **no** toca pantallas `SCR-###`, `@orchestrator` y `@architect` marcan la subsección §6.1 (*Diseño Visual*) y `[ ] Visual Sign-off (Human)` como `N/A` y este flujo no bloquea Gate 2.

---

## Secuencia Obligatoria (6 Pasos)

### Paso 1: Validación DoR (Gate 1 + Wireframes §18 + Design System)
- **Responsables**: `@orchestrator` y `@ui-ux-designer`.
- **Verificaciones bloqueantes**:
  1. `specs/STACK.md` tiene `[x] Gate 00 Approved` (`gate00_approved: true`), `capability-ui-design` en `packs` y `uiux.enabled: true`.
  2. `01-spec.md` de la feature tiene `[x] Gate 1 Aprobado` y wireframes de baja fidelidad validados conforme a `FUNCTIONAL_DOCUMENTATION_STANDARD.md` §18 (`wireframe.excalidraw` + `screen-spec.md`).
  3. `docs/design-system/MASTER.md` y `design-tokens.json` están vigentes, **o** la feature activa es `Design System Foundation` (o un `CR-XXX` sobre ella).
- **Si falla cualquier punto**: `@ui-ux-designer` emite `.agent-inbox/ui-ux-designer/BLOCKED_DOR_<FEAT-ID>.md` y aplica *Stop-the-Line*.

### Paso 2: Consulta Offline `ui-ux-pro-max` + Tokens / Overrides / Hi-Fi (`sdd-ui-design`)
- **Responsable**: `@ui-ux-designer` utilizando la skill `sdd-ui-design`.
- **Acciones**:
  - Ejecutar offline `uv run python .agents/skills/ui-ux-pro-max/scripts/search.py "<query>" --design-system -p "<project>" --json` (sin `npx`, sin `--force` sobre un `MASTER.md` existente; usar `--output-dir <temp_dir>` si se usa `--persist`).
  - Aplicar `uiux.brand_constraints` y respetar `uiux.hifi_format` (`html`, `figma` o `html+figma`), emitiendo aviso si `STACK.md` declara entorno Air-Gapped y se sugieren Google Fonts.
  - Producir propuesta de tokens/diff semver (`MASTER.md`, `design-tokens.json`, `CHANGELOG.md` solo vía `Design System Foundation` o su CR), overrides en `docs/design-system/pages/SCR-XXX.md` (exclusivamente con tokens, cero literales sin token) y borradores en `specs/features/<feat>/ux/SCR-XXX/hi-fi/` con trazabilidad `RF-###` -> `SCR-###` -> token, etiquetas `Confirmado` / `Propuesto` / `Pendiente`, estados UI (`default`, `loading`, `empty`, `error`) y responsive.

### Paso 3: Revisión Independiente de Accesibilidad WCAG 2.2 AA
- **Responsable**: `@a11y-architect` (del pack requerido `capability-web-frontend`) usando la skill `accessibility`.
- **Acciones**:
  - Auditar de forma independiente los tokens propuestos, `pages/SCR-XXX.md` y el prototipo hi-fi frente a WCAG 2.2 AA: ratios de contraste (`4.5:1` texto normal / `3:1` texto grande y controles UI), semántica HTML/WAI-ARIA, orden e indicador de foco visible (`SC 2.4.11`), tamaño mínimo de objetivo (`24x24` / `44x44`), navegación por teclado y regiones `aria-live` para estados dinámicos/errores.
  - Si existen hallazgos bloqueantes de accesibilidad, `@ui-ux-designer` los corrige antes de continuar al Paso 4.

### Paso 4: Validación de Arquitectura, `MASTER@versión` y Contratos
- **Responsable**: `@architect`.
- **Acciones**:
  - Verificar la coherencia de estados UI (`loading`, `empty`, `error`, `default`), DTOs y arquitectura frontend en `02-tech-spec.md`.
  - Cumplimentar la subsección **§6.1 Diseño Visual (`SCR-###` & Design System)** en `02-tech-spec.md` declarando `design-system: MASTER@<versión>` (rango semver compatible, p. ej. `MASTER@1.x`), la tabla `SCR-XXX` -> `docs/design-system/pages/SCR-XXX.md` -> `ux/SCR-XXX/hi-fi/` -> tokens clave -> referencia al dictamen de `@a11y-architect`.

### Paso 5: Verificación *Stop-the-Line* de Cero Cambio Funcional No Aprobado
- **Responsables**: `@ui-ux-designer`, `@architect` y `@orchestrator` (Fase E de `FUNCTIONAL_DOCUMENTATION_STANDARD.md` §18).
- **Acciones**:
  - Confirmar que el diseño hi-fi no añade, elimina ni altera controles, campos, validaciones, flujos de navegación ni reglas funcionales fuera de `01-spec.md` aprobado.
  - Si existe cualquier cambio funcional no aprobado -> *Stop-the-Line* (`RN-SDD-FAIL-CLOSED`) y devolución a Gate 1.
  - Si el expediente evoluciona tokens tras el `Done` de `Design System Foundation`, confirmar la regla de cardinalidad (`RN-07`): **1 único CR** sobre `Design System Foundation` para re-skins puros (sin mutar `specs/features/` en `Done`) y **1 CR por cada feature `Done`** solo si cambia el comportamiento funcional de sus pantallas.

### Paso 6: Sign-off Humano Explícito `[x] Visual Sign-off (Human)` + Gate 2
- **Responsable**: Stakeholder Humano (presentado por `@orchestrator`).
- **Acciones**:
  - El usuario revisa los prototipos hi-fi, la evidencia WCAG 2.2 AA de `@a11y-architect` y `02-tech-spec.md` §6.1.
  - Solo tras aprobación expresa del usuario en el chat se marcan `[x] Visual Sign-off (Human)` y `[x] Gate 2 Aprobado por el Usuario` en `02-tech-spec.md` §8 (`RN-SDD-HUMAN-GATE-OWNERSHIP`).
  - Desbloqueado Gate 2, `@orchestrator` puede avanzar a Gate 3 propagando `SCR-XXX`, `MASTER@versión`, `pages/SCR-XXX.md` y tokens al DoR de las tareas frontend.
