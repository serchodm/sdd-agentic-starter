# Spec Funcional: Slimming de Contexto y Adopción DX `sdd-starter` (`FWK-007`)

- **ID:** `FWK-007-context-slim-dx`
- **RFC:** [`RFC-003`](../../rfcs/RFC-003-audit-remediation-and-hardening.md) (`Aceptado`)
- **Gate 1 Sign-off:** `[x] Gate 1 Approved (Pre-authorized by PO on 2026-11-14T16:05:46+01:00)`

## Requisitos (EARS)
- `RF-701` (`AUD-017`, `A3`): Reducir la huella base activa de `.agents/` desde `~73.9k` tokens estimados (`88` ficheros) a `< 25,000` tokens eliminando `.agents/archetypes/`, deduplicando pares idénticos en catálogo, limpiando referencias residuales `PACO`/`JARVIS`, recortando `sdd-bootstrap/SKILL.md` (`22.4 KB`), y consolidando agentes base activos a `~9` roles (moviendo especialistas extra a catálogo/pack opt-in en `.sdd/catalog/`).
- `RF-702` (`AUD-017`): Alinear métricas de `README.md` con los recuentos verificables del starter.
- `RF-703` (DX `sdd-starter`): Incorporar vía rápida documentada para `BUG-XXX` / cambios pequeños (`01-bug-report.md` -> `02-fix-spec.md` -> `03-tasks.md`) y directorio liviano `domains/` (`_template/overview.md` y `_template/decisions.md` + `README.md`) evitando el acoplamiento rígido de `AUD-020`.
