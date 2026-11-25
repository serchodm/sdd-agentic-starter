---
name: search-first
description: Flujo obligatorio Research-Before-You-Code (affaan-m/ECC) para consultar docs/knowledge/ y reutilizar contratos/servicios antes de escribir código nuevo.
---

# Skill: `search-first` (*Research-Before-You-Code*)

Protocolo obligatorio en **Gate 0 / Pre-Spec** antes de diseñar `02-tech-spec.md` o implementar código (`RN-SDD-SELECTIVE-CONTEXT`):

> **Referencia (carga bajo demanda):** [references/reuse-vs-build-matrix.md](references/reuse-vs-build-matrix.md) (orden en `docs/knowledge/`, matriz *Reutilizar -> Extender -> Adoptar -> Construir* y validación `STACK.md`).

1. **Consultar `docs/knowledge/` Primero:** Revisar en orden `SYSTEM_TOPOLOGY.md` (módulos), `API_CATALOG.md` (endpoints/DTOs), `DATA_MODELS.md` (entidades/PII) y `ADRS.md` (decisiones vigentes).
2. **Inspeccionar Contratos y `specs/STACK.md`:** Verificar esquemas backend, tipos compartidos y librerías aprobadas para evitar duplicación y alucinación de paquetes.
3. **Cascada Reutilizar -> Extender -> Adoptar -> Construir:**
   - **Reutilizar (`>= 90%`):** Si ya existe $\rightarrow$ importar directamente.
   - **Extender (`60%–89%`):** Si cubre el mismo dominio $\rightarrow$ ampliar de forma retrocompatible.
   - **Adoptar librería aprobada:** Usar stdlib o paquete autorizado en `specs/STACK.md` (licencia permisiva, mantenimiento activo).
   - **Construir:** Solo cuando la capacidad es genuinamente nueva y diferenciadora.
