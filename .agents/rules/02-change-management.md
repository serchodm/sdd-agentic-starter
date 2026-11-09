# Reglas Técnicas: Gestión del Cambio en SDD (Change Management & Spec Drift Prevention)

## 1. Principio Fundamental de Gobernanza del Cambio
- **Cero Cambios Directos en Código ("Zero Code-First"):** Queda estrictamente prohibido modificar, refactorizar o añadir código de producción ante cualquier nueva petición, feedback visual o cambio de requisitos sin haber formalizado y validado previamente la especificación del cambio paso a paso con el usuario.
- **Inmutabilidad de Features Completadas (`RN-SDD-IMMUTABLE-DONE`):** Una vez que una Feature (`FEAT-XXX`) tiene estado `Done` / `Completado` en `specs/BACKLOG.md` (Gate 5 superado), sus archivos en `specs/features/FEAT-XXX-*/` (`01-spec.md`, `02-tech-spec.md`, `03-tasks.md`) quedan **CONGELADOS EN MODO LECTURA (READ-ONLY)** como baseline histórico. **Jamás deben sobrescribirse ni editarse** para introducir cambios de requisitos, reemplazos de librerías o rediseños arquitectónicos.
- **Cardinalidad 1:1 de Change Requests (`RN-SDD-1-TO-1-CR`):** Toda evolución posterior al cierre de una Feature debe documentarse en su propio expediente `specs/changes/CR-<NUM>-<kebab-case-name>/`. Si una petición afecta a $N$ Features ya implementadas (`Done`), se deben crear **$N$ Change Requests separados (1 CR por cada Feature afectada)**.

---

## 2. Árbol de Decisión Pre-Edición (Obligatorio Antes de Editar `specs/`)
Antes de invocar `edit_file` o `write_file` sobre cualquier especificación:
1. Consultar el estado de la Feature en `specs/BACKLOG.md`.
2. Si la Feature está **`Pending` o `In Progress`** (Gate 5 no superado): se puede actualizar `specs/features/<FEAT-ID>/` mediante parada de línea (*Stop-the-Line*).
3. Si la Feature está **`Done` / `Completado`** (Gate 5 superado):
   - **PROHIBIDO** editar `specs/features/<FEAT-ID>/01-spec.md`, `02-tech-spec.md` o `03-tasks.md`.
   - **OBLIGATORIO** crear un expediente nuevo en `specs/changes/CR-<NUM>-<kebab-case-name>/` por cada Feature `Done` afectada:
```text
specs/changes/CR-<NUM>-<kebab-case-name>/
├── 01-spec.md          # Gate 1: Especificación Funcional del Cambio (Scope Delta, User Stories, Criterios BDD)
├── 02-tech-spec.md     # Gate 2: Especificación Técnica del Cambio (Arquitectura delta, contratos, rendimiento)
└── 03-tasks.md         # Gate 3: Plan de Tareas Atómicas Secuenciadas con Comandos de Verificación
```

---

## 3. Calidad y Validación Secuencial por Gates (Paso a Paso)
El agente de IA y el equipo deben avanzar de manera estrictamente secuencial, **solicitando validación explícita del usuario en cada compuerta** (`RN-SDD-HUMAN-GATE-OWNERSHIP`):

1. **Gate 1 — Especificación Funcional (`01-spec.md`):**
   - Identificador de la única Feature base afectada (`Target Feature: FEAT-XXX`).
   - Justificación del cambio y problema u oportunidad detectada.
   - Alcance exacto (*In-Scope* vs *Out-of-Scope* respecto a la spec base).
   - Historias de usuario modificadas o nuevas y criterios de aceptación Given-When-Then.
   - 🛑 **Punto de Parada Obligatorio:** Presentar al usuario y esperar su aprobación formal.

2. **Gate 2 — Especificación Técnica (`02-tech-spec.md`):**
   - Arquitectura delta y tecnologías adoptadas para el cambio.
   - Contratos de interfaz, tipos y DTOs afectados (Tabla comparativa *Antes en FEAT-XXX vs Después en CR-XXX*).
   - Impacto en rendimiento, compatibilidad y riesgos de regresión.
   - 🛑 **Punto de Parada Obligatorio:** Presentar al usuario y esperar su aprobación formal.

3. **Gate 3 — Plan de Tareas Atómicas (`03-tasks.md`):**
   - Desglose detallado de tareas ordenadas por capas arquitectónicas.
   - Comandos de prueba y criterios de verificación unitarios.
   - 🛑 **Punto de Parada Obligatorio:** Validar el plan de trabajo con el usuario antes de tocar una sola línea de código fuente.

---

## 4. Cierre del Cambio, Prevención de "Spec Drift" y Sincronización en GitHub
- **Preservación Intacta de la Spec Base:** Al finalizar la implementación y verificación de un CR (Gate 5), los documentos originales de `specs/features/<FEAT-ID>/` **permanecen intactos** como línea base original.
- **Trazabilidad en Backlog y Docs Vivos:** El estado del CR se actualiza a `Done` en `specs/BACKLOG.md` referenciando la Feature base modificada, y la documentación funcional/técnica viva en `docs/es/`, `docs/en/` y `specs/architecture/` se sincroniza con el estado vigente en producción.
- **Commit y Push Obligatorios (`RN-SDD-BRANCH-SYNC`):** Todo cambio validado (tanto de especificaciones/roadmap como de implementación) debe consolidarse inmediatamente con `git add`, `git commit` y `git push origin <rama-activa>` hacia la rama de trabajo o `develop`. Prohibido el push directo a `main`.
