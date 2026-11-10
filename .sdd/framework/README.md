# Evolución del Framework SDD (`.sdd/framework/`)

Canal de gobernanza para cambios **del propio starter** (scripts, catálogo, agentes core, reglas, plantillas). Se separa de `specs/BACKLOG.md`, que pertenece al **proyecto** que se construya a partir de la plantilla.

## Estructura

```text
.sdd/framework/
├── README.md        # Este documento (proceso)
├── BACKLOG.md       # Registro de RFCs y work items FWK-XXX
├── rfcs/            # Propuestas de diseño (RFC-XXX-<slug>.md)
└── work-items/      # Especificaciones por item: FWK-XXX-<slug>/{01-spec,02-tech-spec,03-tasks}.md
```

## Proceso

1. **RFC** (`Propuesto` → `Aceptado` / `Rechazado`): decisión de diseño. Solo un humano marca `Aceptado`.
2. **Work item `FWK-XXX`**: cada RFC aceptado se divide en items. Cada item sigue los Gates 1-5 del SDD reutilizando las plantillas de `specs/templates/`, con aprobación humana en cada Gate.
3. **Sesiones**: 1 work item por hilo (`RN-SDD-SESSION-LIFECYCLE`).
4. **Git**: rama `feat/fwk-XXX-<slug>` desde `develop` → PR a `develop`. `main` solo vía `release/*`.
5. **Inmutabilidad**: un item `Done` es línea base; su evolución requiere un nuevo item o RFC.

## Prefijos

| Prefijo | Uso |
|---|---|
| `RFC-XXX` | Propuesta de diseño del framework |
| `FWK-XXX` | Work item del framework (no colisiona con `FEAT`/`CR`/`BUG` de proyecto) |

> `sdd_sync.py` solo sincroniza `.sdd/catalog`; este directorio no se propaga a proyectos existentes.
