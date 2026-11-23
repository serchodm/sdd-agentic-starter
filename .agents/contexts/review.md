---
name: review
description: Contexto de Auditoría y Revisión Adversaria (GAN-Style Harness / Santa Loop, affaan-m/ECC) para seguridad, calidad y contratos.
---

# Contexto: `review.md` (Auditoría & QA)

- **Foco:** Verificar contratos espejo, seguridad, fallos silenciosos, rendimiento y cobertura usando `/gan-build` (evaluación ponderada intra-bloque en Gate 4) y `/santa-loop` (doble certificación binaria independiente en fronteras `Pre-Gate 2`, cierre `Gate 4` post-DoD y cierre `Gate 5`).
- **Reglas:**
  1. Contrastar línea por línea `02-tech-spec.md` frente al código implementado.
  2. Clasificar hallazgos en `CRITICAL` (bloqueante), `HIGH` (contrato/test), `MEDIUM` y `LOW`.
  3. Ejecutar empíricamente los comandos de verificación antes de dictaminar paso.
  4. Roles habituales: `@qa-tester`, `@security-reviewer` (y revisores de stack pack o `.sdd/catalog/specialists-optin/` activos).
