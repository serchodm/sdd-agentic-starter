---
name: search-first
description: Flujo obligatorio Research-Before-You-Code (affaan-m/ECC) para consultar docs/knowledge/ y reutilizar contratos/servicios antes de escribir código nuevo.
---

# Skill: `search-first` (*Research-Before-You-Code*)

Protocolo obligatorio en **Gate 0 / Pre-Spec** antes de diseñar `02-tech-spec.md` o implementar código (`RN-SDD-SELECTIVE-CONTEXT`):

1. **Consultar `docs/knowledge/` Primero:** Revisar `SYSTEM_TOPOLOGY.md` (módulos), `API_CATALOG.md` y `DATA_MODELS.md` (endpoints/DTOs/entidades existentes) y `ADRS.md` (decisiones vigentes).
2. **Inspeccionar Contratos Existentes:** Verificar esquemas backend y tipos frontend existentes para evitar duplicación.
3. **Decisión Reutilizar vs. Extender vs. Construir:**
   - **Reutilizar:** Si ya existe $\rightarrow$ importar directamente.
   - **Extender:** Si cubre ~80% $\rightarrow$ ampliar de forma retrocompatible.
   - **Construir:** Solo cuando la capacidad es genuinamente nueva con responsabilidad diferenciada.
