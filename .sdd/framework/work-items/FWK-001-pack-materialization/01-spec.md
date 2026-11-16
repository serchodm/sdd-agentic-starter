# Especificación Funcional: Materialización y Activación Fiables de Packs

- **ID de la Feature (Work Item del Framework)**: `FWK-001-pack-materialization`
- **RFC de Origen**: [`RFC-001` v2 (Aceptado)](../../rfcs/RFC-001-ui-ux-pro-max.md)
- **Estado**: `Aprobado` (Gate 1 aprobado por el usuario el 2026-11-10)
- **Analista Funcional / Tech Lead**: `@orchestrator` (actuando sobre mandato de `RFC-001`)
- **Fecha de Creación**: 2026-11-10
- **Última Actualización**: 2026-11-10

---

## 1. Resumen, Contexto y Claridad Epistémica (`morluto/rea`)
- **Problema y Valor de Negocio**: El generador actual de escuadrones (`scripts/sdd_agent_generator.py`) selecciona packs aplicando expresiones regulares sobre todo el texto de `specs/STACK.md` (incluidos ejemplos de plantilla), ignora `skills/`, `rules/` y `workflows/` de los packs, copia ficheros sin marca de procedencia ni hash SHA-256 y no limpia artefactos cuando un pack se desactiva. Por su parte, el importador (`scripts/sdd_catalog_import.py`) declara `workflows` en `pack.json` pero nunca los descarga. Como consecuencia, la plantilla base llega contaminada con 11 packs activos con Gate 00 sin aprobar y carece de un mecanismo determinista y seguro (*fail-closed*) para materializar capacidades opcionales (precondición bloqueante de `FWK-002`).
- **Hechos Observados (Observations)**:
  - `scripts/sdd_agent_generator.py` (`L220-L273`): `parse_stack_specs()` busca subcadenas regex en todo `specs/STACK.md`; `L276-L345`: `materialize_squad()` solo copia `agents/` de cada pack (`L327-L340`), sin cabecera `GENERATED` ni hashes por fichero en `.agents/squad.lock.json` (`L290-L298`), y no limpia ficheros de packs desactivados.
  - `scripts/sdd_catalog_import.py` (`L291-L351`): `import_packs()` escribe `"workflows": meta["workflows"]` en `pack.json` (`L312`), descarga `rules`, `specialists` y `skills` (`L317-L349`), pero no descarga `workflows`. Las 18 carpetas de packs en `.sdd/catalog/packs/` tienen 0 workflows descargados en disco.
  - `specs/STACK.md` (`L3`): `[ ] Gate 00 Approved (Human Sign-off)` y actualmente no contiene el bloque ```` ```yaml sdd:stack-config ````.
  - `.agents/squad.lock.json` (`L1-L52`): registra 11 `active_packs`, 2 `builders` y 20 `specialists` pese a que Gate 00 está sin aprobar; `.agents/agents/` contiene 42 ficheros (6 core, 2 builders, 20 especialistas de catálogo y 14 agentes de pack como `java-reviewer.md`, `go-reviewer.md`, `csharp-reviewer.md`, `vue-reviewer.md`). `.agent-inbox/` contiene 42 subdirectorios homónimos.
  - `.agents/skills/`: contiene 16 skills locales del starter; dos de ellas (`fastapi-patterns/SKILL.md` con 2.133 B y `postgres-patterns/SKILL.md` con 1.835 B) comparten exactamente el slug con las homónimas de `.sdd/catalog/packs/framework-fastapi/skills/fastapi-patterns/SKILL.md` (16.160 B) y `.sdd/catalog/packs/capability-database/skills/postgres-patterns/SKILL.md` (4.062 B), con contenido distinto y sin cabecera `GENERATED`.
  - `tests/`: contiene 18 tests unitarios (`test_sdd_governance.py`: 8; `test_sdd_token_usage.py`: 10); ninguno cubre `sdd_agent_generator.py` ni `sdd_catalog_import.py`.
- **Restricciones Derivadas (Derivations)**:
  - `RN-SDD-SELECTIVE-CONTEXT` (`AGENTS.md` §4): las reglas materializadas de un pack NO pueden convertirse en reglas globales *always-on* cargadas en toda sesión; su destino concreto se decidirá en Gate 2.
  - `RN-SDD-FAIL-CLOSED` (`AGENTS.md` §1.6): cualquier conflicto de ficheros modificados manualmente, colisión entre packs o manifiesto inválido debe abortar la ejecución antes de corromper estado.
  - `RFC-001` D5 / `.sdd/framework/README.md`: los cambios de framework se gestionan en `.sdd/framework/` en rama `feat/fwk-001-*` desde `develop`, sin tocar `src/` ni `specs/BACKLOG.md`.
  - Ejecución en Windows y Linux mediante Python 3.12+ (`uv run python`), sin dependencias externas fuera de la librería estándar salvo que se apruebe en Gate 2.

---

## 1.1. Fuentes Registradas y Trazabilidad (`SRC-###`)

| ID Fuente | Tipología / Origen | Fecha | Notificado por | Descripción / Contenido Facilitado |
|---|---|---|---|---|
| `SRC-001` | RFC Aceptado (`RFC-001` v2) | 2026-11-10 | Usuario Humano | Aprobación de `RFC-001` v2 (§2 Hallazgos H1-H7, §7 `sdd:stack-config`, §9 Plan `FWK-001`, §10 Escenarios 1-6). |
| `SRC-002` | Chat / Orden directa + Inspección de workspace | 2026-11-10 | Usuario / `@orchestrator` | Solicitud de iniciar `FWK-001` y verificación empírica del estado actual de scripts, catálogo, `.agents/` y `tests/`. |

---

## 1.2. Registro de Ambigüedades y Cuestiones Pendientes (`AMB-###`)
> Aplicar Stop-the-Line (`RN-SDD-FAIL-CLOSED`) antes de autorizar Gate 1 y pasar a Gate 2:

| ID | Descripción de la Ambigüedad / Conflicto | Requisitos Afectados | Pregunta Directa para el Usuario | Impacto Funcional | Estado |
|---|---|---|---|---|---|
| `AMB-001` | `RFC-001` §9 indica *"Sin Gate 00 aprobado: solo core + builders; packs únicamente vía `--packs` explícito"*, mientras §2 H2/H4 y `.agents/workflows/harness-audit.md` consideran los 20 especialistas universales (`.sdd/catalog/specialists/`) como parte base de `.agents/agents/`. | `RF-002`, `RF-010` | **Resolución (Opción A)**: Los 20 especialistas universales de `.sdd/catalog/specialists/` siguen materializándose como baseline (con cabecera `GENERATED` y hash en lock), dejando la plantilla libre únicamente de packs no seleccionados. | Contenido exacto de `.agents/agents/`, `.agent-inbox/` y `squad.lock.json` en la plantilla limpia. | `Resolved` |
| `AMB-002` | `.agents/skills/fastapi-patterns/` y `.agents/skills/postgres-patterns/` ya existen como skills artesanales del starter (sin cabecera `GENERATED`) con el mismo slug que las skills de `framework-fastapi` y `capability-database` en `.sdd/catalog/packs/`. | `RF-006` | **Resolución (Opción A)**: Cualquier destino existente no gestionado en `squad.lock.json` se trata como colisión explícita (*fail-closed*), evitando sobrescribir ficheros artesanales. | Activación de `framework-fastapi` y `capability-database` en proyectos nuevos. | `Resolved` |
| `AMB-003` | `specs/STACK.md` actual no contiene todavía el bloque ```` ```yaml sdd:stack-config ```` (el cambio de `00-stack.template.md` estaba listado en `FWK-002` en `RFC-001` §9). | `RF-001`, `RF-010` | **Resolución (Opción A)**: Si falta el bloque: con Gate 00 sin aprobar se asume `packs: []` y `preset: compact`; con Gate 00 aprobado falla (*fail-closed*). Además, durante el saneamiento de `FWK-001` se añade el bloque inicial (`gate00_approved: false`, `preset: compact`, `packs: []`) a `specs/STACK.md`. | Compatibilidad de `STACK.md` sin bloque y estado inicial de la plantilla. | `Resolved` |
| `AMB-004` | Algunos `pack.json` declaran dependencias en `"requires"` (p. ej. `framework-fastapi` requiere `lang:python`; `framework-react` requiere `lang:typescript`). | `RF-001`, `RF-003` | **Resolución (Opción A)**: Fallar explícitamente (*fail-closed*) indicando las dependencias faltantes si se solicita un pack sin sus `requires` activos. | Validación y grafo de resolución de packs. | `Resolved` |

---

## 2. Historias de Usuario y Casos de Uso

### Historia 1: Activación determinista desde bloque estructurado
> **Como** desarrollador o agente `@orchestrator` que configura `specs/STACK.md`,
> **Quiero** que `sdd_agent_generator.py` lea únicamente el bloque estructurado `sdd:stack-config` y respete el bloqueo de Gate 00,
> **Para que** los textos de ejemplo o menciones en prosa nunca activen packs fantasma en `.agents/`.

### Historia 2: Materialización completa, trazable e idempotente de packs
> **Como** mantenedor del framework SDD,
> **Quiero** que cada pack activo materialice sus agentes, skills, rules (de carga perezosa) y workflows con procedencia (`GENERATED` + hash SHA-256 en `squad.lock.json`),
> **Para que** la ejecución repetida sea idempotente, se detecten colisiones antes de escribir y al desactivar un pack se eliminen únicamente ficheros generados sin ediciones manuales.

### Historia 3: Importación íntegra del catálogo sin pérdida de packs propios
> **Como** mantenedor del catálogo `.sdd/catalog/`,
> **Quiero** que `sdd_catalog_import.py` descargue también los `workflows` de `STACK_PACKS` sin tocar ni borrar packs ajenos a `STACK_PACKS`,
> **Para que** los workflows ECC estén disponibles para materializarse y los futuros packs propios (`capability-ui-design` en `FWK-002`) permanezcan íntegros.

---

## 3. Alcance (Scope)

### ✅ Dentro del Alcance (In-Scope)
- Selección de configuración y packs en `scripts/sdd_agent_generator.py` exclusivamente desde el bloque ```` ```yaml sdd:stack-config ```` de `specs/STACK.md` (y flag `--packs` cuando aplique).
- Control estricto de Gate 00 en el generador (`gate00_approved` + casilla `[x] Gate 00 Approved` en `specs/STACK.md`).
- Materialización de los 4 tipos de activos de un pack: `agents`, `skills`, `rules` (preservando la Matriz de Carga Perezosa) y `workflows`.
- Trazabilidad y procedencia en `.agents/squad.lock.json` (hashes SHA-256 por fichero materializado, origen `stack-config` vs `manual`) y cabecera `GENERATED` en ficheros generados compatibles.
- Limpieza segura (*fail-closed*) de ficheros y recursos al desactivar un pack o cambiar de configuración, bloqueando ante modificaciones manuales del usuario.
- Validación *fail-closed* de manifiestos `pack.json` inválidos y detección explícita de colisiones entre packs o contra destinos ocupados.
- Descarga de `workflows` en `scripts/sdd_catalog_import.py` manteniendo intactos los packs fuera de `STACK_PACKS`.
- Saneamiento de la plantilla del repositorio (`.agents/agents/`, `.agent-inbox/`, `.agents/squad.lock.json`) acorde a Gate 00 sin aprobar.
- Suite de tests unitarios offline deterministas en `tests/` cubriendo selección, Gate 00, idempotencia, limpieza, conflicto manual, colisión, manifiesto inválido e importador (preservación de packs externos y workflows).

### 🚫 Fuera del Alcance (Out-of-Scope)
- Creación o vendorización del pack `capability-ui-design`, `@ui-ux-designer`, `sdd_vendor_update.py` o preguntas `uiux` en `sdd-bootstrap` (corresponde a `FWK-002`).
- Quality gates visuales, contraste, capturas o cambios en `@a11y-architect` / `@qa-tester` (corresponde a `FWK-003`).
- Unificación global de terminología de Gates en `SDD_FRAMEWORK.md` / `BACKLOG.md` / `AGENTS.md` (corresponde a `FWK-004`).
- Modificación de `src/` o `specs/BACKLOG.md` del proyecto usuario.

---

## 4. Requisitos del Sistema bajo Protocolo EARS

| ID Requisito | Fuente | Patrón EARS | Cláusula EARS (Sintaxis Formal Canónica) | Componente Afectado |
|---|---|---|---|---|
| `RF-001` | `SRC-001` | `Ubiquitous` | `El sistema sdd_agent_generator deberá determinar los packs activos de configuración exclusivamente a partir del bloque estructurado yaml sdd:stack-config en specs/STACK.md, ignorando cualquier prosa o ejemplo fuera de dicho bloque.` | `scripts/sdd_agent_generator.py` |
| `RF-002` | `SRC-001` | `State-driven` | `MIENTRAS specs/STACK.md no cuente con Gate 00 aprobado (casilla [x] Gate 00 Approved y gate00_approved: true), el sistema sdd_agent_generator deberá omitir los packs del stack y permitir únicamente la activación explícita de packs solicitados mediante --packs, registrándolos en .agents/squad.lock.json con origen manual.` | `scripts/sdd_agent_generator.py`, `.agents/squad.lock.json` |
| `RF-003` | `SRC-001` | `Event-driven` | `CUANDO se ejecute la materialización con packs activos válidos, el sistema sdd_agent_generator deberá materializar los ficheros de agents, skills, rules y workflows declarados por cada pack, ubicando las rules fuera del ámbito global always-on para cumplir la Matriz de Carga Perezosa.` | `scripts/sdd_agent_generator.py`, `.agents/` |
| `RF-004` | `SRC-001` | `Ubiquitous` | `El sistema sdd_agent_generator deberá añadir una cabecera de procedencia GENERATED en cada fichero Markdown materializado (builders, especialistas, agentes, rules y workflows de pack, y skills) y registrar la ruta relativa, el pack propietario y el hash SHA-256 de todos los ficheros materializados en .agents/squad.lock.json.` | `scripts/sdd_agent_generator.py`, `.agents/squad.lock.json` |
| `RF-005` | `SRC-001` | `Complex` | `CUANDO un pack o recurso previamente registrado en .agents/squad.lock.json deje de estar activo, SI el hash SHA-256 actual del fichero en disco coincide con el hash del lock anterior, ENTONCES el sistema sdd_agent_generator deberá eliminar el fichero y limpiar su buzón vacío asociado; SI el hash difiere por modificación manual, ENTONCES deberá abortar con error explícito sin eliminar ni sobrescribir el fichero.` | `scripts/sdd_agent_generator.py` |
| `RF-006` | `SRC-001` | `Unwanted` | `SI dos packs activos declaran el mismo destino o slug de skill, agente, rule o workflow, ENTONCES el sistema sdd_agent_generator deberá rechazar la materialización con un error explícito antes de escribir cambios en .agents/.` | `scripts/sdd_agent_generator.py` |
| `RF-007` | `SRC-001` | `Event-driven` | `CUANDO se ejecute --materialize dos o más veces consecutivas sin cambios en specs/STACK.md ni en el catálogo, el sistema sdd_agent_generator deberá producir exactamente el mismo conjunto de ficheros en disco y los mismos hashes SHA-256 sin duplicar entradas.` | `scripts/sdd_agent_generator.py` |
| `RF-008` | `SRC-001` | `Unwanted` | `SI un pack activo no existe en el catálogo, contiene un pack.json malformado, carece de campos obligatorios o referencia rutas inexistentes o fuera de la carpeta del pack, ENTONCES el sistema sdd_agent_generator deberá detenerse con error explícito y código de salida distinto de cero.` | `scripts/sdd_agent_generator.py` |
| `RF-009` | `SRC-001` | `Event-driven` | `CUANDO se ejecute scripts/sdd_catalog_import.py, el sistema deberá descargar los workflows declarados en STACK_PACKS además de specialists, rules y skills, sin modificar ni eliminar directorios de packs en .sdd/catalog/packs/ que no pertenezcan a STACK_PACKS.` | `scripts/sdd_catalog_import.py`, `.sdd/catalog/packs/` |
| `RF-010` | `SRC-001`, `SRC-002` | `Event-driven` | `CUANDO se cierre FWK-001 en la plantilla base del repositorio (con Gate 00 sin aprobar), el repositorio deberá quedar saneado con .agents/agents/, .agent-inbox/ y .agents/squad.lock.json libres de packs no seleccionados.` | `.agents/agents/`, `.agent-inbox/`, `.agents/squad.lock.json` |

---

## 4.1. Reglas de Negocio Vinculantes (`RN-###`)
1. **RN-01 (Fuente Única de Activación)**: Ninguna palabra clave fuera del bloque `sdd:stack-config` en `specs/STACK.md` puede activar un pack.
2. **RN-02 (Doble Verificación Gate 00)**: La activación automática desde `sdd:stack-config` exige simultáneamente la firma humana `[x] Gate 00 Approved` en `specs/STACK.md` y `gate00_approved: true` en el bloque estructurado; si cualquiera falta, el estado se trata como Gate 00 no aprobado (*fail-closed*).
3. **RN-03 (Propiedad y Protección de Ediciones Manuales)**: Un fichero en `.agents/` solo puede ser sobrescrito o eliminado automáticamente por el generador si consta bajo gestión en `.agents/squad.lock.json` y su SHA-256 actual coincide con el último SHA-256 emitido por el generador (salvo mecanismo explícito de `.agents/overrides/` para builders).
4. **RN-04 (Atomicidad Ante Errores de Prevalidación)**: Las validaciones de `sdd:stack-config`, Gate 00, manifiestos `pack.json`, colisiones y conflictos de hash deben ejecutarse **antes** de aplicar borrados o escrituras sobre `.agents/`, evitando estados parcialmente materializados.
5. **RN-05 (Preservación de Packs Externos a ECC)**: `sdd_catalog_import.py` opera únicamente sobre `UNIVERSAL_SPECIALISTS` y las claves de `STACK_PACKS`; cualquier otro directorio en `.sdd/catalog/packs/` es intocable.

---

## 4.2. Example Mapping (Datos Concretos de Entrada / Salida)

| Regla Asociada | Caso de Ejemplo | Datos de Entrada (Input Real) | Estado / Precondición | Salida Esperada (Output Verificable) |
|---|---|---|---|---|
| `RN-01` | Éxito Nominal (`RF-001`) | `STACK.md` con ejemplos `"React / Vue / Java / TypeScript"` en §2 y bloque `sdd:stack-config` con `gate00_approved: true`, `packs: [lang-python]` | `[x] Gate 00 Approved` en `STACK.md` | Solo se activa `lang-python`; no se activan `lang-java`, `framework-react`, `framework-vue` ni `capability-web-frontend`. |
| `RN-02` | Gate 00 sin aprobar (`RF-002`) | `STACK.md` con `[ ] Gate 00 Approved`, `packs: [lang-python]`, comando `--materialize` sin `--packs` | Plantilla inicial | `active_packs: []` en `squad.lock.json`; ningún fichero de pack en `.agents/`. |
| `RN-02` | Activación manual pre-Gate 00 (`RF-002`) | `--materialize --packs lang-python` | `[ ] Gate 00 Approved` | Se materializa `lang-python`; `squad.lock.json` registra origen `manual` para `lang-python`. |
| `RN-03` | Conflicto de edición manual (`RF-005`) | Usuario edita `.agents/agents/python-reviewer.md` tras materializar; luego quita `lang-python` de `sdd:stack-config` y ejecuta `--materialize` | `python-reviewer.md` tiene hash distinto al de `squad.lock.json` | Código de salida != 0; mensaje indicando conflicto y ruta exacta; `python-reviewer.md` NO es eliminado ni sobrescrito. |
| `RN-04` | Colisión entre packs (`RF-006`) | Pack A y Pack B declaran skill `skills/shared-skill` | Ambos packs solicitados | Código de salida != 0; mensaje indicando colisión de slug y packs implicados; disco sin cambios parciales. |
| `RN-05` | Importador preserva externos (`RF-009`) | `.sdd/catalog/packs/capability-ui-design/pack.json` presente + red mockeada en test | `capability-ui-design` no está en `STACK_PACKS` | Workflows de `STACK_PACKS` descargados en `pack/workflows/`; `capability-ui-design` permanece byte a byte idéntico. |

---

## 4.3. Requisitos No Funcionales y SLAs Cuantitativos (Planguage)

- **Tag**: `REL-GEN-DETERMINISM-01`
  - **Ambition**: Materialización y verificación completamente deterministas y reproducibles en entornos locales y CI.
  - **Scale**: Porcentaje de ficheros y hashes SHA-256 idénticos entre dos ejecuciones consecutivas (`--materialize` ×2) sin cambios externos.
  - **Meter**: Test unitario automatizado comparando árbol de rutas y diccionario de hashes SHA-256 en `squad.lock.json`.
  - **Baseline**: Inexistente (0% de hashes registrados por fichero en `squad.lock.json`).
  - **Target**: `100%` de identidad en rutas y hashes SHA-256 entre ejecución 1 y ejecución 2.
  - **Constraint**: `< 100%` (cualquier divergencia o duplicación en ejecuciones repetidas invalida el requisito).

- **Tag**: `PERF-TEST-OFFLINE-01`
  - **Ambition**: Suite de pruebas unitarias rápida y ejecutable sin red ni dependencias externas.
  - **Scale**: Tiempo de ejecución de la suite completa de tests unitarios (en segundos) y número de peticiones de red reales.
  - **Meter**: `uv run python -m unittest discover tests -v` con mocks de transporte HTTP para `sdd_catalog_import.py`.
  - **Baseline**: 18 tests existentes en `0.088s`, 0 tests de generador/importador.
  - **Target**: `< 2.0s` para toda la suite en `tests/` con `0` llamadas de red reales.
  - **Constraint**: `> 5.0s` o cualquier dependencia de conectividad externa en tests unitarios.

---

## 5. Criterios de Aceptación (BDD / Given-When-Then)

### Escenario 1: Selección estricta desde `sdd:stack-config` (RFC-001 §10 #1)
- **Dado que** `specs/STACK.md` contiene `[x] Gate 00 Approved`, menciones a React, Vue y Java en los textos de ejemplo y un bloque `sdd:stack-config` con `gate00_approved: true` y `packs: [lang-python]`
- **Cuando** se ejecuta `sdd_agent_generator.py --materialize`
- **Entonces** únicamente el pack `lang-python` queda activo en `.agents/squad.lock.json`
- **Y** se materializan su agente, sus skills, sus rules (en destino de carga perezosa) y sus workflows, sin activar packs de React, Vue o Java.

### Escenario 2: Bloqueo con Gate 00 sin aprobar y modo `--packs` manual (RFC-001 §10 #2)
- **Dado que** `specs/STACK.md` tiene `[ ] Gate 00 Approved`
- **Cuando** se ejecuta `sdd_agent_generator.py --materialize` sin `--packs`
- **Entonces** ningún pack queda activado y `.agents/squad.lock.json` refleja `active_packs: []`
- **Y cuando** se ejecuta `--materialize --packs lang-python` con Gate 00 sin aprobar
- **Entonces** solo se activa `lang-python` y el lock lo registra con origen `manual`.

### Escenario 3: Idempotencia en ejecuciones repetidas (RFC-001 §10 #3)
- **Dado que** una configuración válida de packs ha sido materializada una primera vez
- **Cuando** se vuelve a ejecutar `sdd_agent_generator.py --materialize` sin cambios en `specs/STACK.md` ni en `.sdd/catalog/`
- **Entonces** el conjunto de ficheros materializados y sus hashes SHA-256 en `.agents/squad.lock.json` son exactamente idénticos sin duplicados.

### Escenario 4: Limpieza segura y bloqueo ante edición manual (RFC-001 §10 #4)
- **Dado que** `lang-python` está materializado y registrado en `.agents/squad.lock.json`
- **Cuando** se desactiva `lang-python` en `sdd:stack-config` sin modificar sus ficheros y se ejecuta `--materialize`
- **Entonces** los ficheros pertenecientes a `lang-python` desaparecen del workspace y del lock
- **Pero si** uno de esos ficheros fue editado manualmente por el usuario antes de desactivar el pack
- **Entonces** `--materialize` falla explícitamente reportando el conflicto y no borra el fichero modificado.

### Escenario 5: Colisión de slugs entre packs (RFC-001 §10 #5)
- **Dado que** dos packs activos en un catálogo de prueba declaran el mismo slug de skill o agente
- **Cuando** se intenta materializar ambos packs simultáneamente
- **Entonces** el generador aborta con error explícito indicando la colisión y no deja ficheros parcialmente escritos.

### Escenario 6: Manifiesto `pack.json` inválido o con rutas inválidas
- **Dado que** un pack solicitado tiene `pack.json` corrupto, sin campo `id` o con una ruta declarada inexistente o fuera del pack
- **Cuando** se ejecuta `--materialize`
- **Entonces** el generador aborta con error explícito y código de salida distinto de cero antes de modificar `.agents/`.

### Escenario 7: Importador de workflows y preservación de packs ajenos a `STACK_PACKS` (RFC-001 §10 #6)
- **Dado que** existe un pack externo fuera de `STACK_PACKS` en `.sdd/catalog/packs/` y un transporte HTTP simulado para `affaan-m/ecc`
- **Cuando** se ejecuta `sdd_catalog_import.py`
- **Entonces** los `workflows` declarados en `STACK_PACKS` quedan descargados dentro de `<pack>/workflows/`
- **Y** el pack externo permanece completamente intacto.

---

## 6. Pre-Mortem Inverso (Anticipación de Puntos Ciegos y Fallos)

1. **Escenario de Fallo Catastrófico 1**: Un usuario activa `lang-python` en la plantilla recién saneada y `sdd_agent_generator` sobrescribe silenciosamente skills artesanales del proyecto (como `fastapi-patterns` o `postgres-patterns`) o borra ficheros propios de `.agents/agents/`.
   - **Causa Oculta**: Ausencia de verificación previa contra ficheros existentes no presentes en `squad.lock.json` o sin cabecera `GENERATED`.
   - **Mitigación Preventiva en Gate 1**: Regla `RN-03` y `RN-04` exigiendo prevalidación fail-closed antes de mutar disco, y resolución explícita de `AMB-002`.
2. **Escenario de Fallo Catastrófico 2**: Al materializar `rules/` de un pack directamente en `.agents/rules/`, el IDE/agente carga automáticamente decenas de reglas de múltiples lenguajes en cada turno, destruyendo el presupuesto de contexto.
   - **Causa Oculta**: Tratar `.agents/rules/` como destino genérico sin diferenciar reglas core always-on de reglas condicionales de pack.
   - **Mitigación Preventiva en Gate 1**: `RF-003` prohíbe explícitamente ubicar las rules de pack como always-on y difiere el diseño exacto de ruta perezosa a Gate 2 (`02-tech-spec.md`).
3. **Escenario de Fallo Catastrófico 3**: Una skill futura o con scripts (`.py`, `.json`, `.csv`, `.sh`) recibe una cabecera HTML `<!-- GENERATED ... -->` que rompe el parser de Python o JSON.
   - **Causa Oculta**: Inyectar comentarios Markdown/HTML de forma indiscriminada en ficheros no Markdown.
   - **Mitigación Preventiva en Gate 1**: `RF-004` acota la cabecera textual `GENERATED` a ficheros Markdown compatibles y basa la trazabilidad universal de todos los ficheros en ruta + SHA-256 en `.agents/squad.lock.json`.

---

## 7. Incógnitas y Decisiones Pendientes (`NOT_ENOUGH_INFO` — Tarjetas Rojas / Stop-the-Line)
- [x] **`AMB-001`**: Resuelto (Opción A) — mantener los 20 especialistas universales materializados con cabecera `GENERATED` y hash en lock incluso antes de Gate 00.
- [x] **`AMB-002`**: Resuelto (Opción A) — tratar cualquier destino existente no gestionado en `squad.lock.json` como colisión explícita (*fail-closed*).
- [x] **`AMB-003`**: Resuelto (Opción A) — fallback sin packs si Gate 00 no está aprobado, fail-closed si Gate 00 está aprobado sin bloque `sdd:stack-config`, e incorporar bloque inicial en `specs/STACK.md` durante el saneamiento.
- [x] **`AMB-004`**: Resuelto (Opción A) — fallar explícitamente (*fail-closed*) cuando falte una dependencia declarada en `requires`.

---

## 8. Aprobación Formal Gate 1 (`RN-SDD-HUMAN-GATE-OWNERSHIP`)
> ⚠️ **Exclusivo para el Stakeholder Humano** (Los agentes de IA tienen prohibido marcar esta casilla por su cuenta):
- [x] **Gate 1 Aprobado por el Usuario**: El alcance funcional, requisitos EARS, ejemplos concretos, métricas Planguage, criterios BDD y resolución de `AMB-001`..`AMB-004` han sido revisados y validados (aprobación expresa en chat 2026-11-10: *"Me fio de tus recomendaciones, prosigue"*).
