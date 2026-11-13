---
name: search-first
description: Flujo obligatorio Research-Before-You-Code de affaan-m/ECC para consultar la Base de Conocimiento viva y reutilizar contratos/servicios antes de escribir código nuevo.
---

# Skill: `search-first` (*Research-Before-You-Code* de `affaan-m/ECC`)

Esta meta-skill establece el protocolo obligatorio de **Gate 0 / Pre-Spec** antes de redactar especificaciones técnicas (`02-tech-spec.md`) o escribir código en cualquier tarea.

## 1. Secuencia Determinista de Investigación (Zero Blind Exploration)

1. **Consultar Primero la Base de Conocimiento Viva (`docs/knowledge/`)**:
   - Leer `SYSTEM_TOPOLOGY.md` para localizar los módulos responsables de cada dominio.
   - Leer `API_CATALOG.md` y `DATA_MODELS.md` para conocer los endpoints, eventos SSE, DTOs y tablas ya existentes.
   - Leer `ADRS.md` para respetar las decisiones arquitectónicas vigentes.
2. **Inspeccionar Contratos Existentes antes de Crear Nuevos**:
   - Verificar en `backend/src/api/dtos/` y `frontend/src/types/` si ya existe un DTO o interfaz que pueda extenderse limpiamente de forma retrocompatible en lugar de duplicar estructuras.
3. **Matriz de Decisión: Reutilizar vs. Extender vs. Construir**:
   - **Reutilizar (Prioridad 1)**: La utilidad, servicio o componente ya existe y cubre el caso $\rightarrow$ Importar y usar directamente.
   - **Extender (Prioridad 2)**: El servicio o DTO cubre el 80% del contrato $\rightarrow$ Añadir campos opcionales retrocompatibles o métodos cohesivos.
   - **Construir (Prioridad 3)**: Solo cuando la capacidad es genuinamente nueva y tiene responsabilidad diferenciada (ej. `AgentAnatomyHydrator`, `AutonomousLearningService`, `CouncilCognitiveRouter`).
