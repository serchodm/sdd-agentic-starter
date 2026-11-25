---
name: sdd-security-audit
description: Auditoría transversal SDD con modelado STRIDE en Gate 2 y verificación OWASP Top 10 / ASVS v4+ en Gate 4 bajo controles fail-closed.
---

# Skill: `sdd-security-audit`

Extiende `.agents/rules/05-security-and-secrets.md` y coordina `.agents/agents/security-reviewer.md` sin copiar sus tablas.

> **Referencias bajo demanda:** [references/stride-threat-model.md](references/stride-threat-model.md) (`Gate 2` — STRIDE) y [references/owasp-asvs-checklist.md](references/owasp-asvs-checklist.md) (`Gate 4` — OWASP/ASVS).

## 1. Gate 2 (`02-tech-spec.md` — Modelado STRIDE)
- **Trigger:** Cargar `references/stride-threat-model.md` cuando el Work Item toque **AuthN/AuthZ**, **multi-tenancy**, **pagos**, **webhooks**, **subida de ficheros**, **secretos/KMS** o **PII**.
- **Contrato:** Documentar fronteras de confianza y mitigaciones *fail-closed* por las 6 categorías **STRIDE** (*Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege*).
- **Parada (`RN-SDD-FAIL-CLOSED`):** Detener antes de `Gate 2` ante ambigüedad en propiedad de recursos, firmas externas o PII.

## 2. Gate 4 (`Capa 1` + `@security-reviewer` — Código)
- **Trigger:** Cargar `references/owasp-asvs-checklist.md` en `Gate 4` y al despachar `@security-reviewer`.
- **Checklist OWASP Top 10 / ASVS v4+:**
  1. **BOLA/IDOR y AuthZ:** *Deny-by-default* y autorización por objeto/`tenant_id` autenticado.
  2. **Frontera e Inyección:** Validación estricta en frontera productora, parametrización `SQL/NoSQL/OS` y prevención `SSRF`/`XXE`/`XSS`/`CSRF`.
  3. **Secretos, SCA/SBOM y PII:** Higiene de secretos, `SCA/SBOM` sobre dependencias aprobadas en `STACK.md` y ausencia de `PII`/credenciales en logs y errores.

## 3. Cierre DoD
- Exigir tests negativos (`@qa-tester`) BOLA/tenant/frontera y `0` hallazgos `CRITICAL`/`HIGH` antes de `Gate 5`.
