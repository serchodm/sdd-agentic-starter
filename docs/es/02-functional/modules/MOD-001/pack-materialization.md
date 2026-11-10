<p align="right">
  <a href="../../../../en/02-functional/modules/MOD-001/pack-materialization.md">🇬🇧 English (EN-GB)</a> | <strong>🇪🇸 Español (ES-ES)</strong>
</p>

# `MOD-001`: Materialización y Activación Fiables de Packs

- **Identificador de Módulo:** `MOD-001`
- **Work Item / RFC de Origen:** `FWK-001-pack-materialization` ([`RFC-001` v2](../../../../../.sdd/framework/rfcs/RFC-001-ui-ux-pro-max.md))
- **Estado Funcional:** `Verified` (Confirmado y verificado por pruebas offline deterministas)
- **Índice Maestro:** [DOCUMENTATION-INDEX.md](../../../00-governance/DOCUMENTATION-INDEX.md)

---

## 1. Propósito y Alcance

### 1.1. Propósito (Confirmado)
Este módulo garantiza que los **Stack Packs** del catálogo inerte (`.sdd/catalog/packs/`) y el escuadrón agéntico base (`.agents/`) se seleccionen, materialicen, actualicen, limpien e importen de forma **determinista, trazable y segura (*fail-closed*)**.

Antes de `FWK-001`, el generador buscaba nombres de tecnologías en todo el texto de `specs/STACK.md` (activando packs fantasma por ejemplos de plantilla), ignoraba *skills*, *rules* y *workflows* de los packs, carecía de hashes por fichero y no limpiaba recursos desactivados. `MOD-001` elimina esas causas raíz.

### 1.2. Alcance Incluido (Confirmado)
- Selección exclusiva de configuración desde el bloque estructurado ```` ```yaml sdd:stack-config ```` en `specs/STACK.md`.
- Bloqueo estricto de packs del stack mientras **Gate 00** no esté aprobado, permitiendo únicamente activaciones manuales explícitas mediante `--packs`.
- Materialización completa e idempotente de los 4 tipos de activos de cada pack (`specialists`/`agents`, `skills`, `rules` y `workflows`), junto con builders y los 20 especialistas universales.
- Aislamiento de las reglas de pack en `.agents/pack-rules/<pack>/` para preservar la carga perezosa de contexto (`RN-SDD-SELECTIVE-CONTEXT`).
- Registro de procedencia (`GENERATED`) y hashes SHA-256 por fichero en `.agents/squad.lock.json` (`schema_version: 2`).
- Prevalidación atómica *fail-closed* antes de modificar disco: dependencias `requires`, manifiestos `pack.json`, rutas anti-*traversal*, colisiones intra-pack o contra ficheros artesanales existentes, y conflictos por edición manual.
- Limpieza segura de ficheros y buzones vacíos al desactivar un pack, preservando buzones que contengan tickets pendientes.
- Descarga de `workflows` en el importador del catálogo sin tocar ni borrar packs externos a `STACK_PACKS`, y protección de sincronización en `sdd_sync.py`.
- Saneamiento de la plantilla base del repositorio acorde a Gate 00 sin aprobar.

### 1.3. Excluido Explícitamente (Alcance Futuro)
- Creación o vendorización del pack `capability-ui-design`, `@ui-ux-designer`, `sdd_vendor_update.py` o preguntas `uiux` en `sdd-bootstrap` (corresponde a `FWK-002`).
- *Quality gates* visuales, contraste, capturas o cambios en `@a11y-architect` / `@qa-tester` (corresponde a `FWK-003`).
- Unificación global de terminología de Gates en `SDD_FRAMEWORK.md` / `BACKLOG.md` / `AGENTS.md` (corresponde a `FWK-004`).

---

## 2. Actores y Autoridad

| Actor | Responsabilidad | Restricción Principal |
| :--- | :--- | :--- |
| **Usuario Humano / Stakeholder** | Aprueba **Gate 00** en `specs/STACK.md` (`[x] Gate 00 Approved` + `gate00_approved: true`). | Ningún agente puede autoaprobar Gate 00 (`RN-SDD-HUMAN-GATE-OWNERSHIP`). |
| **Desarrollador / `@orchestrator`** | Configura el bloque `sdd:stack-config`, consulta el catálogo (`--list`) y ejecuta la materialización (`--materialize`) o activación manual (`--packs`). | No debe editar manualmente ficheros generados; las personalizaciones de builders van en `.agents/overrides/<builder>.md`. |
| **Mantenedor del Catálogo** | Ejecuta `scripts/sdd_catalog_import.py` para actualizar especialistas universales y packs `STACK_PACKS` desde `affaan-m/ecc`. | Los packs externos propios en `.sdd/catalog/packs/` permanecen intactos (`RN-05`). |

---

## 3. Reglas de Activación y Comportamiento del Sistema

### 3.1. Fuente Única de Activación (`RN-01`) y Doble Verificación Gate 00 (`RN-02`)
1. El sistema lee **únicamente** el bloque vallado ```` ```yaml sdd:stack-config ```` dentro de `specs/STACK.md`. Cualquier mención a lenguajes o frameworks en prosa, tablas o ejemplos de `specs/STACK.md` es ignorada por completo.
2. Debe existir como máximo **un** bloque `yaml sdd:stack-config` válido y cerrado; si hay más de uno, está sin cerrar o contiene sintaxis/valores inválidos (p. ej. tabuladores, claves duplicadas, `gate00_approved` no booleano o `preset` desconocido), la operación aborta con error sin tocar disco.
3. Para que los packs listados en `sdd:stack-config` se activen automáticamente, deben cumplirse **ambas** condiciones simultáneamente:
   - Firma humana en `specs/STACK.md`: `[x] Gate 00 Approved` (o `[X] Gate 00 Approved`).
   - Valor booleano `gate00_approved: true` dentro del bloque `sdd:stack-config`.
4. **Si Gate 00 NO está aprobado:**
   - Si falta el bloque `sdd:stack-config` y no hay firma humana `[x]`, el sistema asume de forma segura `preset: compact` y `packs: []`.
   - Cualquier pack declarado dentro de `sdd:stack-config` se **ignora**.
   - Solo pueden activarse packs explícitamente mediante `--packs <nombre...>` en línea de comandos, quedando registrados en `.agents/squad.lock.json` con `"source": "manual"`.
5. **Si hay firma humana `[x]` pero falta el bloque `sdd:stack-config`:** el sistema falla explícitamente (*fail-closed*).
6. **Si Gate 00 SÍ está aprobado:** se activan los packs de `sdd:stack-config` con `"source": "stack-config"` y, si además se pasa `--packs`, se añaden los no presentes con `"source": "manual"`.

### 3.2. Destinos de Materialización y Aislamiento de Contexto
En toda materialización válida (incluso con `active_packs: []` antes de Gate 00) se materializan los *builders* del preset elegido (`compact`, `granular`, `api-only` o `spa-only`) y los **20 especialistas universales** de `.sdd/catalog/specialists/` (`AMB-001`).

Para cada pack activo (identificado por nombre de carpeta, p. ej. `lang-python`, o por `id`, p. ej. `lang:python`):

| Tipo de Activo en `pack.json` | Destino Materializado | Comportamiento Especial |
| :--- | :--- | :--- |
| **`specialists` (agentes de pack)** | `.agents/agents/<fichero>.md` + `.agent-inbox/<agente>/.gitkeep` | Recibe cabecera `GENERATED` tras el YAML frontmatter; el buzón se crea automáticamente. |
| **`skills`** | `.agents/skills/<slug>/<ruta_relativa>` | Copia recursiva completa (Markdown y archivos auxiliares `.py`, `.json`, etc.); toda skill debe contener `SKILL.md`. |
| **`rules`** | `.agents/pack-rules/<pack>/<fichero>.md` | **Nunca** se copian en `.agents/rules/`, protegiendo la carga perezosa (`RN-SDD-SELECTIVE-CONTEXT`) y evitando colisiones de nombres idénticos como `coding-style.md` entre packs. |
| **`workflows`** | `.agents/workflows/<fichero>.md` | Recibe cabecera `GENERATED` tras el YAML frontmatter si aplica. |

### 3.3. Procedencia (`GENERATED`) y Lock v2
- Todo fichero Markdown materializado incorpora el marcador `<!-- GENERATED by sdd_agent_generator (<owner>). Do not edit directly. -->`:
  - Si comienza por YAML frontmatter (`--- ... ---`), el marcador se inserta **inmediatamente después** del cierre `---` para no romper la detección de frontmatter de los IDEs.
  - Si no tiene frontmatter, se inserta en la línea 1.
- Los ficheros no Markdown dentro de una skill (p. ej. `.py`, `.json`, `.csv`, `.sh`) **no** reciben comentarios HTML; su trazabilidad e integridad quedan protegidas mediante ruta y hash **SHA-256** en `.agents/squad.lock.json` (`schema_version: 2`).
- **Idempotencia:** si dos ejecuciones consecutivas producen exactamente el mismo contenido y configuración, ningún fichero cambia en disco y `.agents/squad.lock.json` conserva intacto su `timestamp` sin reescribirse.

### 3.4. Validaciones *Fail-Closed* y Limpieza Segura (`RN-03`, `RN-04`)
Antes de escribir o borrar **un solo byte** en `.agents/` o `.agent-inbox/`, el sistema valida todo el plan:
1. **Dependencias (`requires`):** si un pack requiere otro (p. ej. `framework-fastapi` requiere `lang:python`) que no está activo en la misma ejecución, aborta indicando las dependencias faltantes.
2. **Integridad de `pack.json` y anti-*traversal*:** rechaza JSON corrupto, campos obligatorios ausentes (`id`, `family`, `description`, listas), IDs duplicados en el catálogo, rutas inexistentes, rutas absolutas o escapes con `..`.
3. **Colisiones intra-plan:** si dos packs activos intentan escribir el mismo destino (p. ej. dos packs con la misma skill o workflow), aborta identificando ambos propietarios y la ruta en conflicto.
4. **Protección de destinos artesanales no gestionados (`AMB-002`):** si un destino ya existe en disco pero **no** consta en `.agents/squad.lock.json` (como las skills locales artesanales `fastapi-patterns` o `postgres-patterns` del starter), aborta sin sobrescribirlo.
5. **Protección ante ediciones manuales (`RN-03`):** si un fichero gestionado fue modificado en disco (su SHA-256 actual difiere del último registrado en `squad.lock.json`), tanto la rematerialización como la desactivación del pack **abortan** sin borrar ni sobrescribir el trabajo manual.
6. **Limpieza segura al desactivar packs:** si los hashes coinciden sin ediciones manuales, los ficheros del pack desactivado se eliminan, podando directorios vacíos en `.agents/skills/` y `.agents/pack-rules/`. Los buzones `.agent-inbox/<agente>/` solo se eliminan si únicamente contienen `.gitkeep`; si hay tickets pendientes, el buzón se conserva y se emite un aviso `[WARN]`.

### 3.5. Importación del Catálogo y Sincronización (`RN-05`)
- `scripts/sdd_catalog_import.py` descarga especialistas universales y todos los recursos de `STACK_PACKS`, **incluidos sus `workflows`** (creando `<pack>/workflows/` solo cuando la lista de workflows no está vacía), adaptando el *frontmatter* de agentes y registrando advertencias `[WARN]` si falla alguna descarga sin abortar el resto.
- El importador actúa únicamente sobre los directorios declarados en `STACK_PACKS`: cualquier pack externo o propio presente en `.sdd/catalog/packs/` permanece **intacto byte a byte**.
- `scripts/sdd_sync.py` excluye automáticamente cualquier ruta presente en `squad.lock.json["files"]` y amplía la detección de la cabecera `GENERATED` a `4096` caracteres (cubriendo frontmatters extensos), evitando que artefactos generados contaminen la plantilla.

---

## 4. Flujos Operativos Paso a Paso

### Flujo 1: Consultar packs y presets disponibles
1. Ejecutar `uv run python scripts/sdd_agent_generator.py --list`.
2. El sistema inspecciona y valida los manifiestos del catálogo y muestra arquetipos, especialistas universales, stack packs disponibles (con su `id` y descripción) y presets (`compact`, `granular`, `api-only`, `spa-only`).

### Flujo 2: Probar o activar un pack manualmente antes de aprobar Gate 00
1. Con Gate 00 sin aprobar en `specs/STACK.md`, ejecutar por ejemplo:
   `uv run python scripts/sdd_agent_generator.py --materialize --packs lang-python`
2. El sistema ignora `packs:` de `sdd:stack-config` (por estar Gate 00 sin aprobar) y materializa únicamente `lang-python` junto al baseline (builders + 20 especialistas), marcando `"source": "manual"` en `.agents/squad.lock.json`.

### Flujo 3: Activar el stack completo tras aprobar Gate 00
1. Completar `specs/STACK.md`, marcar `[x] Gate 00 Approved (Human Sign-off)` y configurar el bloque:
   ````yaml
   ```yaml sdd:stack-config
   gate00_approved: true
   preset: compact
   packs:
     - lang-python
     - capability-database
   ```
   ````
2. Ejecutar `uv run python scripts/sdd_agent_generator.py --materialize`.
3. Si alguna skill artesanal preexistente colisiona con una skill del pack (p. ej. `postgres-patterns`), el sistema se detendrá con error de colisión; el usuario decide explícitamente si conservar su versión artesanal o retirarla antes de materializar.

### Flujo 4: Desactivar un pack sin perder trabajo
1. Retirar el pack de `packs:` en `sdd:stack-config` (o ejecutar `--materialize` sin `--packs` si era manual).
2. Si ningún fichero generado del pack fue editado manualmente, sus agentes, skills, `pack-rules/<pack>/` y workflows desaparecen de `.agents/`.
3. Si algún fichero fue editado a mano, el sistema se detiene reportando la ruta exacta para que el usuario resuelva el conflicto de forma explícita.

### Flujo 5: Personalizar un builder de forma segura
1. Crear o editar `.agents/overrides/<builder>.md` (por ejemplo `.agents/overrides/back-engineer.md`).
2. Al ejecutar `--materialize`, el generador prioriza ese fichero frente al arquetipo base e inserta el marcador de override correspondiente.

---

## 5. Estado Inicial Verificado de la Plantilla Base (`RF-010`)

En la plantilla limpia (con `[ ] Gate 00 Approved`):
- `specs/STACK.md` incluye el bloque inicial `sdd:stack-config` (`gate00_approved: false`, `preset: compact`, `packs: []`).
- `.agents/agents/` contiene exactamente **28** agentes (6 core + 2 builders `back-engineer`/`front-engineer` + 20 especialistas universales) y **0** agentes de pack.
- `.agent-inbox/` contiene los **28** subdirectorios homónimos.
- `.agents/pack-rules/` no existe hasta que se active un pack con reglas.
- `.agents/squad.lock.json` usa `schema_version: 2`, `gate00_approved: false`, `active_packs: []` y **22** entradas verificadas por SHA-256 en `files` (2 builders + 20 especialistas).

---

## 6. Requisitos, Reglas y Criterios de Aceptación Verificados

| Referencia | Descripción Resumida | Estado |
| :--- | :--- | :--- |
| `RF-001`, `RN-01` | Selección exclusiva desde bloque `yaml sdd:stack-config`, ignorando prosa y ejemplos. | `Verified` |
| `RF-002`, `RN-02` | Bloqueo por doble verificación Gate 00 (`[x]` + `gate00_approved: true`) y modo `--packs` (`manual`). | `Verified` |
| `RF-003` | Materialización de los 4 tipos de activos y aislamiento perezoso en `.agents/pack-rules/<pack>/`. | `Verified` |
| `RF-004` | Cabecera `GENERATED` respetando YAML frontmatter y registro SHA-256 en `squad.lock.json` v2. | `Verified` |
| `RF-005`, `RN-03` | Limpieza segura al desactivar, preservación de buzones con tickets y bloqueo ante ediciones manuales. | `Verified` |
| `RF-006`, `RN-04` | Detección atómica pre-mutación de colisiones intra-pack y contra destinos artesanales no gestionados. | `Verified` |
| `RF-007`, `REL-GEN-DETERMINISM-01` | Idempotencia 100% en ejecuciones consecutivas (mismos hashes y preservación de `timestamp`). | `Verified` |
| `RF-008` | Validación *fail-closed* de `pack.json`, `requires` y rutas anti-*path-traversal*. | `Verified` |
| `RF-009`, `RN-05` | Descarga de `workflows` en `sdd_catalog_import.py` preservando packs externos intactos. | `Verified` |
| `RF-010` | Saneamiento completo de la plantilla base sin packs huérfanos. | `Verified` |
| `PERF-TEST-OFFLINE-01` | Suite de pruebas unitarias 100% offline (`< 2.0s`, `0` llamadas de red reales). | `Verified` |

*(Para la correspondencia exacta con ficheros fuente y métodos de prueba, véase [TRACEABILITY-MATRIX.md](../../../../traceability/TRACEABILITY-MATRIX.md)).*
