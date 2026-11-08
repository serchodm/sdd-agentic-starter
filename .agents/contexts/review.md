---
name: review
description: Modo de contexto de Auditoría y Revisión Adversaria (GAN-Style Harness / Santa Loop) de affaan-m/ECC orientado a detección de defectos, seguridad y cumplimiento de contratos.
---

# Contexto Operativo: `review.md` (Modo Auditoría y Revisión Adversaria)

- **Modo**: Revisión de Código, Seguridad y Cumplimiento de Especificación (`/review`, `/santa-loop`, `/gan-build`).
- **Foco Principal**: Detectar discrepancias de contratos espejo, vulnerabilidades de seguridad, errores silenciados, regresiones de rendimiento y huecos de cobertura antes de autorizar Gate 5.

## Comportamiento en Modo `review`
1. **Lectura Exhaustiva antes de Emitir Juicio**: Comparar línea por línea `02-tech-spec.md` contra el código implementado.
2. **Clasificación por Severidad**: Agrupar hallazgos en `CRITICAL` (bloqueante), `HIGH` (incumplimiento de contrato/test), `MEDIUM` (mantenibilidad/rendimiento) y `LOW`.
3. **Verificación Empírica**: Nunca asumir que un test pasa sin ejecutarlo.
4. **Agentes Activos Preferentes**: `@gan-evaluator`, `@fastapi-reviewer`, `@python-reviewer`, `@react-reviewer`, `@typescript-reviewer`, `@security-reviewer`, `@silent-failure-hunter`, `@type-design-analyzer`.
