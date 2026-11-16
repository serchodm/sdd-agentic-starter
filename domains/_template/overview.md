---
domain: <domain-slug>
status: Draft | Active | Deprecated
last_updated: YYYY-MM-DD
owner_zone: src/<domain-slug>/
related_specs:
  - FEAT-XXX
---

# Dominio: <Nombre del Dominio> (`<domain-slug>`)

## 1. Propósito y Alcance
- **Qué resuelve:** `<resumen de 2-3 líneas sobre la responsabilidad de negocio del dominio>`
- **Límites (Out of Scope):** `<qué responsabilidades pertenecen explícitamente a otros dominios>`

## 2. Componentes Clave y Mapa de Archivos

| Componente | Archivo / Entrypoint | Responsabilidad | Rol Responsable |
| :--- | :--- | :--- | :--- |
| `<Nombre>` | `<ruta/relativa/modulo>` | `<responsabilidad acotada>` | `@back-engineer` / `@front-engineer` |

## 3. Patrones, Integraciones y Puntos de Extensión

### Patrones e Integraciones
- **Dependencias entrantes (consumidores):** `<quién invoca a este dominio>`
- **Dependencias salientes (proveedores / puertos):** `<servicios externos u otros dominios>`
- **Invariantes críticos:** `<reglas de consistencia, seguridad o transacciones que nunca deben romperse>`

### Puntos de Extensión (`EP-##`)
- **`EP-01` `<Nombre>`:** `<cómo se extiende de forma segura sin romper el núcleo (ej. strategy, adapter, hook)>`

## 4. Restricciones y Supuestos

- **Design Constraints (`DC-##`):**
  - `DC-01`: `<restricción intencional de diseño (ej. idempotencia, aislamiento multi-tenant)>`
- **Legacy / Operational Constraints (`LC-##`):**
  - `LC-01`: `<deuda técnica conocida, límite de latencia o restricción heredada>`
- **Assumptions (`AS-##`):**
  - `AS-01`: `<supuesto asumido sobre entradas, volumen o entorno>`

## 5. Referencias Cruzadas (Sin Duplicación)
- **Modelos de datos:** Ver sección `<dominio>` en `docs/knowledge/DATA_MODELS.md`.
- **Contratos / API:** Ver sección `<dominio>` en `docs/knowledge/API_CATALOG.md`.
- **Topología y eventos:** Ver `docs/knowledge/SYSTEM_TOPOLOGY.md`.
- **Decisiones locales:** Ver [`decisions.md`](decisions.md).
