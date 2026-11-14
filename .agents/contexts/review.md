---
name: review
description: Contexto de Auditoría y Revisión Adversaria (GAN-Style Harness / Santa Loop, affaan-m/ECC) para seguridad, calidad y contratos.
---

# Contexto: `review.md` (Auditoría & QA)

- **Foco:** Verificar contratos espejo, seguridad, fallos silenciosos, rendimiento y cobertura antes de Gate 5 (`/santa-loop`, `/gan-build`).
- **Reglas:**
  1. Contrastar línea por línea `02-tech-spec.md` frente al código implementado.
  2. Clasificar hallazgos en `CRITICAL` (bloqueante), `HIGH` (contrato/test), `MEDIUM` y `LOW`.
  3. Ejecutar empíricamente los comandos de verificación antes de dictaminar paso.
  4. Roles habituales: `@qa-tester`, `@security-reviewer` (y revisores de stack pack o `.sdd/catalog/specialists-optin/` activos).
