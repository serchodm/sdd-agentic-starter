# Regla 02: Gestión del Cambio (Change Management & Spec Drift Prevention)

## 1. Invariantes
- **Zero Code-First:** Prohibido modificar código ante cambios o feedback sin especificación validada.
- **`RN-SDD-IMMUTABLE-DONE`:** Una Feature `Done`/`Completado` (Gate 5 superado) congela `specs/features/FEAT-XXX-*/` en modo **SOLO LECTURA**. Jamás sobrescribirla.
- **`RN-SDD-1-TO-1-CR`:** Si un cambio afecta $N$ Features `Done`, crear **$N$ Change Requests separados** en `specs/changes/CR-<NUM>-<kebab-case-name>/`.

## 2. Decisión Pre-Edición en `specs/`
1. Consultar estado en `specs/BACKLOG.md`.
2. Si `Candidate`, `Backlog`, `In Progress` o `In Review`: actualizar `specs/features/<FEAT-ID>/` (Stop-the-Line).
3. Si **`Done` / `Completado`**: prohibido tocar `specs/features/<FEAT-ID>/`; crear `specs/changes/CR-<NUM>-<kebab-case-name>/` con `01-spec.md`, `02-tech-spec.md` y `03-tasks.md`.

## 3. Validación Secuencial (`RN-SDD-HUMAN-GATE-OWNERSHIP`)
- **Gate 1 (`01-spec.md`):** `Target Feature: FEAT-XXX`, justificación, scope delta (*In/Out-of-Scope*), historias y Given-When-Then -> Esperar aprobación humana.
- **Gate 2 (`02-tech-spec.md`):** Arquitectura delta, contratos/DTOs (*Antes vs Después*), rendimiento/riesgos -> Esperar aprobación humana.
- **Gate 3 (`03-tasks.md`):** Tareas por capa con DoD determinista -> Esperar aprobación humana antes de codificar.

## 4. Cierre (`RN-SDD-BRANCH-SYNC`)
- Al cerrar CR (Gate 5), la spec base sigue intacta; se actualiza `specs/BACKLOG.md`, `docs/es/`, `docs/en/` y `docs/knowledge/`, y se sincroniza con `git add`, `git commit` y `git push origin <rama-activa>` (prohibido push directo a `main`).
