# Topología Física y Lógica del Sistema

## 1. Topología del Framework SDD y Materialización de Packs (`FWK-001` & `FWK-002`)

```mermaid
flowchart TD
    STACK["specs/STACK.md (bloque yaml sdd:stack-config + uiux + Gate 00)"] --> REG["scripts/sdd_pack_registry.py (parser YAML, uiux, pack.json, requires, rutas seguras)"]
    CAT[".sdd/catalog/ (19 arquetipos, 20 especialistas, 19 packs)"] --> REG
    REG -->|verify_vendor_lock SHA-256| VENDOR["scripts/sdd_vendor_update.py (VENDOR.lock.json & staging aislado)"]
    OVR[".agents/overrides/*.md (personalizacion de builders)"] --> GEN["scripts/sdd_agent_generator.py (planificacion, prevalidacion fail-closed, mutacion)"]
    REG --> GEN

    GEN -->|builders, especialistas y agentes de pack| AGENTS[".agents/agents/*.md (28 base en plantilla)"]
    GEN -->|skills de packs activos| SKILLS[".agents/skills/"]
    GEN -->|carga perezosa aislada| PACKRULES[".agents/pack-rules/"]
    GEN -->|workflows de packs activos| WF[".agents/workflows/*.md"]
    GEN -->|buzones gestionados| INBOX[".agent-inbox/"]
    GEN -->|estado y hashes SHA-256| LOCK[".agents/squad.lock.json (schema_version: 2)"]

    UPSTREAM["affaan-m/ecc (raw GitHub)"] -->|sdd_catalog_import.py 18 STACK_PACKS| CAT
    UIUP["ui-ux-pro-max-cli@2.15.0 (MIT, npx aislado)"] -->|sdd_vendor_update.py --apply| CAT
    LOCK -->|excluye rutas gestionadas| SYNC["scripts/sdd_sync.py (sincronizacion proyecto-plantilla)"]
```

### Inventario de Componentes del Framework

| Componente / Ruta | Responsabilidad | Límites y Aislamiento |
| :--- | :--- | :--- |
| `scripts/sdd_pack_registry.py` | Parsea el bloque `yaml sdd:stack-config` de `specs/STACK.md`, valida Gate 00, el esquema estricto `uiux` y su coherencia con `packs`, carga `pack.json` (`targets`, `upstream`), comprueba `requires`, delega `verify_vendor_lock()` y resuelve rutas seguras anti-*path-traversal*. | Solo librería estándar Python 3.12+ (sin PyYAML); *fail-closed* ante errores de esquema, incompatibilidad `api-only`, discrepancia `uiux` ↔ `packs` o fallo de lock (`<= 500` líneas). |
| `scripts/sdd_agent_generator.py` | Construye el plan de materialización, valida colisiones intra-plan, destinos artesanales no gestionados y conflictos SHA-256 contra disco antes de mutar `.agents/` y `.agent-inbox/`, y persiste `squad.lock.json` v2. | No modifica `.agents/rules/` ni `.sdd/catalog/`; conserva buzones desactivados si tienen tickets pendientes (`<= 500` líneas). |
| `scripts/sdd_vendor_update.py` | Verifica `VENDOR.lock.json` (`verify_vendor_lock()`) y ejecuta actualizaciones explícitas de `ui-ux-pro-max-cli@<X.Y.Z>` en `tempfile.TemporaryDirectory()`, validando `validate_data.py`, excluyendo skills hermanas/tests, normalizando EOL a LF y mostrando diff previo a `--apply`. | Único módulo autorizado para invocar `npx` en staging temporal; nunca escribe sin `--apply` (`<= 500` líneas). |
| `scripts/sdd_catalog_import.py` | Importa `UNIVERSAL_SPECIALISTS` (20) y `STACK_PACKS` (18) desde `affaan-m/ecc` (incluidos `workflows/`), normaliza *frontmatter* y admite `fetcher` inyectable para pruebas offline. | Nunca modifica ni borra directorios de packs en `.sdd/catalog/packs/` ajenos a `STACK_PACKS`, preservando `capability-ui-design` byte a byte (`RN-05`, `RF-012`). |
| `scripts/sdd_sync.py` | Sincroniza bidireccionalmente artefactos core del framework entre proyectos derivados y plantilla. | Excluye `.agents/overrides/`, `.agents/squad.lock.json`, cualquier ruta en `squad.lock.json["files"]` y archivos con marcador `GENERATED` (primeros 4096 caracteres). |
| `.sdd/catalog/packs/capability-ui-design/` | Pack no-ECC (`id: "capability:ui-design"`, `requires: ["capability:web-frontend"]`, `targets: ["web"]`, `rules: []`) con `NOTICE.md` (MIT), `@ui-ux-designer`, skill `sdd-ui-design`, workflow `ui-design-review.md` y `vendor/ui-ux-pro-max/` (`46` entradas en `VENDOR.lock.json`: `45` runtime + `LICENSE` MIT). | Opera 100% offline con stdlib Python (`search.py`, `validate_data.py`); excluye 6 skills hermanas y `scripts/tests/`; nunca añade reglas *always-on*. |
| `.gitattributes` | Fija `text eol=lf` para `.sdd/catalog/packs/capability-ui-design/**` y `.agents/**`. | Evita discrepancias CRLF/LF en Windows frente a hashes SHA-256 de `VENDOR.lock.json` y `squad.lock.json`. |
| `.agents/pack-rules/<pack>/` | Aloja reglas específicas de packs activos (p. ej. `coding-style.md`) fuera de `.agents/rules/00-..07-`. | Cumple `RN-SDD-SELECTIVE-CONTEXT`; se poda automáticamente al desactivar el pack si no hay ediciones manuales. |
| `.agents/squad.lock.json` | Fuente de verdad de estado materializado (`schema_version: 2`, `active_packs`, `files` con `sha256`/`owner`/`kind`). | No se sincroniza en `sdd_sync.py`; en plantilla base con Gate 00 sin aprobar mantiene `active_packs: []` y 22 ficheros base (2 builders + 20 especialistas). |
| `tests/test_sdd_pack_materialization.py` & `tests/test_sdd_ui_design.py` | Suites unitarias y de aceptación 100% offline (`37` tests totales en `tests/`, cubriendo `FWK-001` y los 7 grupos / Escenarios 1–7 de `FWK-002`, ambos `<= 500` líneas). | Usan `tempfile.TemporaryDirectory`, *fetcher* y *runner* mockeados con `0` llamadas de red reales. |

### 1.1. Flujo Condicional de Diseño Visual en Gate 2 (`FWK-002`)

Cuando `capability-ui-design` y `uiux.enabled: true` están activos y una feature (o `CR-XXX`) afecta al menos a una pantalla `SCR-###`:

```mermaid
flowchart LR
    G1["Gate 1 Aprobado + Wireframes §18"] --> ORCH["@orchestrator (Gate 2 con SCR-###)"]
    ORCH --> UIUX["@ui-ux-designer (sdd-ui-design + search.py --json offline)"]
    UIUX --> A11Y["@a11y-architect (revisión WCAG 2.2 AA)"]
    A11Y --> ARCH["@architect (02-tech-spec.md §6.1 MASTER@versión)"]
    ARCH --> SIGN["[ ] Visual Sign-off (Human) en §8"]
    SIGN --> G3["Gate 3 DoR -> front-ui / front-engineer / tier-frontend"]
```

- **Poda UI-Only:** En proyectos `api-only` o CLI, `sdd-bootstrap` poda las preguntas `uiux` y no activa `capability-ui-design`; con `capability-web-frontend` y `uiux.enabled: false`, permanecen activos `@a11y-architect` y las skills ECC (`design-system`, `accessibility`, `browser-qa`) sin `@ui-ux-designer`.
- **Plantilla Base Limpia:** El repositorio starter **no** crea `docs/design-system/` vacío; dicha carpeta nace únicamente en el proyecto usuario durante la feature fundacional `Design System Foundation` (registrada en `specs/BACKLOG.md` tras Gate 00 cuando `uiux.enabled: true`).

---

## 2. Topología de la Aplicación del Proyecto *(Plantilla Base — Pendiente de Gate 00)*

```mermaid
graph TD
    Client["Cliente / Frontend"] -->|HTTP / WebSocket| API["API Backend"]
    API -->|Persistencia| DB[("Base de Datos")]
```

*(Actualizar esta sección con los servicios reales definidos en `specs/STACK.md` tras aprobar Gate 00).*
