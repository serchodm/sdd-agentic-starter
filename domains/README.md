# Dominios del Proyecto (`domains/`)

Índice ligero de contexto por **Bounded Context / Dominio** diseñado para carga bajo demanda (*On-Demand Context Loading*). Evita inflar las reglas globales siempre activas (`.agents/rules/`) concentrando el conocimiento vivo de cada área de negocio en dos archivos compactos por dominio.

---

## 1. Cuándo Usar `domains/` y Qué NO Reemplaza

| Artefacto | Responsabilidad | Cuándo se consulta |
| :--- | :--- | :--- |
| **`domains/<slug>/overview.md`** | Mapa funcional del dominio: propósito, componentes clave, integraciones, puntos de extensión (`EP-##`) y restricciones (`DC-##`, `LC-##`, `AS-##`). | Bajo demanda en **Gate 0 / 1 / 2** (`FEAT-XXX`, `CR-XXX`, `BUG-XXX`) solo para los `Affected Domains`. |
| **`domains/<slug>/decisions.md`** | Registro ligero de decisiones locales del dominio (`DOM-<slug>.D-01`) en formato MADR. | Bajo demanda en **Gate 2** y antes de proponer cambios de diseño locales. |
| `specs/STACK.md` | Contrato tecnológico único y Ownership Map (**Gate S0**). | Siempre en Bootstrap y compilación de agentes. |
| `specs/BACKLOG.md` | Fuente única de verdad (SSOT) de work items y estados. | En todo cambio de estado o planificación. |
| `docs/knowledge/*` | Catálogo técnico transversal (`SYSTEM_TOPOLOGY.md`, `API_CATALOG.md`, `DATA_MODELS.md`, `ADRS.md`). | Consulta cruzada entre dominios y cierre **Gate 5**. |

> **Regla de Oro:** Los documentos en `domains/` enlazan hacia `docs/knowledge/` y `specs/` pero **no duplican** schemas completos, payloads API ni criterios EARS.

---

## 2. Estructura de Carpetas y Ciclo de Vida

```text
domains/
├── README.md                  # Este índice y registro de dominios activos
├── _template/                 # Plantilla base (no editar directamente)
│   ├── overview.md
│   └── decisions.md
└── <domain-slug>/             # Ej: billing, auth, catalog (kebab-case)
    ├── overview.md
    └── decisions.md
```

### Ciclo de actualización
1. **Alta inicial (Gate 1/2 o Gate 5):** Cuando nace una feature o dominio nuevo, copiar `domains/_template/` a `domains/<domain-slug>/` y añadir la fila en el registro inferior.
2. **Lectura acotada (Gate 1/2 y `/bug-fast-track`):** Leer únicamente `domains/<dom>/{overview,decisions}.md` de los dominios impactados antes de diseñar tareas o modificar código.
3. **Sincronización 0DD (Gate 5 — `@documentator`):** Si una `FEAT-XXX`, `CR-XXX` o `BUG-XXX` altera componentes, invariantes, extensiones o decisiones del dominio, `@documentator` actualiza `domains/<dom>/` como parte del cierre Gate 5.

---

## 3. Registro de Dominios Activos

| Dominio (`slug`) | Estado | Propósito Breve | Owner Role | Archivos |
| :--- | :--- | :--- | :--- | :--- |
| `_template` | `Template` | Plantilla estándar para nuevos dominios | `@documentator` | [overview](_template/overview.md) · [decisions](_template/decisions.md) |
