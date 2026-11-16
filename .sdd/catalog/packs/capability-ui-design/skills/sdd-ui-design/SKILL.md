---
name: sdd-ui-design
description: "Adaptador metodológico SDD para ui-ux-pro-max offline. Gobierna la consulta al proveedor vendorizado, el esquema semver de docs/design-system/ (MASTER.md, design-tokens.json, CHANGELOG.md, pages/SCR-XXX.md), la generación hi-fi trazada a SCR-### y la evolución por CR sin --force."
---

# Skill: `sdd-ui-design` (Adaptador Metodológico UI/UX SDD)

Adapta el proveedor offline vendorizado `ui-ux-pro-max` (`2.15.0`, MIT) a las reglas de gobernanza SDD, el estándar [`FUNCTIONAL_DOCUMENTATION_STANDARD.md`](../../../../docs/standards/FUNCTIONAL_DOCUMENTATION_STANDARD.md) §18, `RN-SDD-IMMUTABLE-DONE` y `RN-SDD-1-TO-1-CR`.

---

## 1. Comando Canónico Offline y Reglas de Ejecución

### Consulta Canónica (100% Offline, Cero Red)

```bash
uv run python .agents/skills/ui-ux-pro-max/scripts/search.py "<query>" --design-system -p "<project>" --json
```

- **Fallbacks de intérprete**: si `uv` no está disponible, usa `python3` (Linux/macOS) o `py -3` (Windows).
- **Advertencia Windows**: **nunca** dependas del comando `python` sin `uv run` o `py -3` en Windows (puede invocar el alias stub de Microsoft Store).
- **Flags útiles soportadas por `search.py`**: `--domain`, `--stack`, `--format {ascii,markdown}`, `--variance`, `--motion`, `--density`, `--page`, `--persist --output-dir <temp_dir>` (alias `-o`).
- **Prohibición de `npx` y red**: queda terminantemente prohibido invocar `npx`, `npm` o realizar descargas externas durante diseño o materialización.

### Protección de `MASTER.md` Existente (`--persist` y `--force`)

- El script `search.py --persist` escribe siempre bajo `<output_dir>/design-system/<project-slug>/MASTER.md` y **no** emite `design-tokens.json` ni `CHANGELOG.md`.
- Si utilizas `--persist`, pasa **siempre** `--output-dir <temp_dir>` apuntando a un directorio temporal aislado fuera de `docs/design-system/`, inspecciona la salida y tradúcela de forma controlada al esquema normativo SDD.
- **PROHIBIDO** pasar `--force` sobre un `docs/design-system/MASTER.md` existente.

### Entornos Air-Gapped / Hosting Aislado

- Aunque `search.py` funciona 100% offline, su base de datos puede sugerir `@import` o `<link>` a Google Fonts (`fonts.googleapis.com`).
- Si `specs/STACK.md` declara un entorno **Air-Gapped / Aislado** (o sin acceso a CDNs externas), **advierte explícitamente** y sustituye cualquier URL externa de fuentes por ficheros `@font-face` locales autohospedados o pilas tipográficas nativas del sistema.

---

## 2. Esquema Normativo de `docs/design-system/`

*(El starter vacío no incluye `docs/design-system/`; esta estructura nace en el proyecto destino durante la feature fundacional `Design System Foundation`.)*

```text
docs/design-system/                     # Única fuente normativa visual (neutra de idioma)
├── MASTER.md                           # Sistema visual global con cabecera semver
├── design-tokens.json                  # Tokens estructurados 1:1 con MASTER.md
├── CHANGELOG.md                        # Historial semver (MAJOR / MINOR / PATCH)
└── pages/
    └── SCR-XXX.md                      # Overrides por pantalla trazados a FEAT-XXX y MASTER@1.x
```

### 2.1. `docs/design-system/MASTER.md`

Cabecera obligatoria al inicio del documento:

```yaml
---
design_system_version: "1.0.0"
owner_feature: "FEAT-XXX"
provider: "ui-ux-pro-max@2.15.0"
hifi_format: "html" # html | figma | html+figma
brand_constraints: "docs/design-system/BRAND.md" # o "none"
---
```

Contenido mínimo obligatorio: paleta semántica con ratios de contraste verificados (`>= 4.5:1` texto normal, `>= 3:1` texto grande y controles UI), tipografía, escala de espaciado, radios, sombras/elevación, motion (`prefers-reduced-motion`), breakpoints responsive, patrones de componentes base y antipatrones visuales.

### 2.2. `docs/design-system/design-tokens.json`

JSON estructurado sincronizado 1:1 con `MASTER.md`, con estas claves raíz obligatorias:

```json
{
  "version": "1.0.0",
  "meta": {
    "owner_feature": "FEAT-XXX",
    "provider": "ui-ux-pro-max@2.15.0",
    "hifi_format": "html",
    "brand_constraints": "none"
  },
  "colors": {},
  "typography": {},
  "spacing": {},
  "radii": {},
  "shadows": {},
  "motion": {},
  "breakpoints": {}
}
```

### 2.3. `docs/design-system/CHANGELOG.md` y Política Semver

Cada cambio publicado tras la línea base inicial actualiza `design_system_version`, `design-tokens.json["version"]` y añade entrada en `CHANGELOG.md` referenciando el `FEAT-XXX` o `CR-XXX`:

- **`MAJOR` (`X.0.0`)**: eliminación, renombrado o cambio incompatible de contrato de tokens o componentes. **Obligatorio** incluir análisis de impacto con la lista explícita de todos los `SCR-###` afectados.
- **`MINOR` (`0.X.0`)**: incorporación de nuevos tokens, variantes o componentes retrocompatibles.
- **`PATCH` (`0.0.X`)**: ajuste de valor de token existente sin ruptura de contrato ni renombrado.

### 2.4. `docs/design-system/pages/SCR-XXX.md`

- Nombrado siempre por ID `SCR-XXX` (nunca por slug libre).
- Cabecera obligatoria: `screen_id: SCR-XXX`, `owner_feature: FEAT-XXX`, `design_system: MASTER@1.x` (rango semver compatible).
- **Prohibición estricta de literales sin token**: todo color, fuente, tamaño, espaciado, radio o sombra en `pages/SCR-XXX.md` debe referenciar un token definido en `design-tokens.json` / `MASTER.md`; nunca valores `#hex`, `rgb(...)` ni `px` arbitrarios sin token asociado.
- Pertenece a la feature dueña del `SCR-XXX`; tras su `Done`, modificarlo requiere un CR sobre esa feature.

---

## 3. Gobernanza de Evolución (`RN-SDD-IMMUTABLE-DONE` & `RN-SDD-1-TO-1-CR`)

1. **Feature fundacional**: `Design System Foundation` (registrada al activar `uiux.enabled: true` en Gate S0) produce `MASTER.md` v`1.0.0`, `design-tokens.json` y `CHANGELOG.md`.
2. **Evolución centralizada (1 CR sobre la fundacional)**: tras el `Done` de `Design System Foundation`, cualquier cambio de tokens o reglas globales en `MASTER.md` / `design-tokens.json` se canaliza como **1 único Change Request (`CR-XXX`) sobre `Design System Foundation`**, incrementando semver y actualizando `CHANGELOG.md`.
3. **Re-skins puros vs impacto funcional**:
   - **Re-skin puro por tokens** (sin cambio de flujos, controles ni reglas): **no** abre CRs en las features consumidoras que estén en `Done`; sus carpetas `specs/features/` permanecen intactas (solo lectura).
   - **Cambio de comportamiento funcional**: si la evolución altera el comportamiento funcional de pantallas `SCR-###` en features `Done`, **sí** debe abrirse **1 CR independiente por cada feature `Done` afectada** (retornando a Gate 1 si introduce requisitos nuevos).
4. **Consolidación bilingüe en Gate 5**: `docs/{es,en}/03-ux-ui/screens/SCR-XXX/screen-spec.md` enlaza hacia `docs/design-system/` (`MASTER@versión`), sin duplicar tokens ni crear copias paralelas.

---

## 4. Reglas de Alta Fidelidad (`specs/features/<feat>/ux/SCR-XXX/hi-fi/`)

1. **Tránsito §18 obligatorio**: solo generar hi-fi tras Gate 1 aprobado con `wireframe.excalidraw` y `screen-spec.md` validados (`FUNCTIONAL_DOCUMENTATION_STANDARD.md` §18 Fase C -> D -> E). Si introduce cambios funcionales, **Stop-the-Line** hacia Gate 1.
2. **Restricciones de marca (`brand_constraints`)**: si `specs/STACK.md` define `uiux.brand_constraints` (p. ej. `docs/design-system/BRAND.md`), léelo y aplícalo antes de consultar o elegir paletas y tipografías.
3. **Formatos soportados (`uiux.hifi_format`)**:
   - **`html`** (por defecto): prototipo navegable autocontenido (`index.html` + hoja CSS con variables derivadas de `docs/design-system/design-tokens.json`), verificable en navegador/`browser-qa`, cubriendo estados `default`, `loading`, `empty`, `error` y breakpoints responsive.
   - **`figma`**: especificación trazada a `SCR-XXX` + enlace Figma versionado junto al mapeo de tokens de `design-tokens.json`.
   - **`html+figma`**: ambos artefactos sincronizados bajo el mismo `SCR-XXX` y `MASTER@versión`.
4. **Separación de ECC `design-system`**: las vistas previas generadas por la skill ECC `design-system` son evidencias auxiliares de auditoría; nunca sustituyen ni duplican la autoridad normativa de `docs/design-system/MASTER.md`.
