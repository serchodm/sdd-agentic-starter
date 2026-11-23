---
description: Ejecuta el ciclo Gate 6 de Release Readiness (REL-vX.Y.Z), CHANGELOG y PR hacia main.
---

# Workflow `/gate6-release` — Release Readiness (`Gate 6`)

Flujo obligatorio PR-first (`RN-SDD-BRANCH-SYNC`) y *fail-closed* para publicar `vX.Y.Z` hacia `main`:

1. **Preflight e inicio de rama:** `./sdd git release-start --version X.Y.Z` (valida SemVer, tag inexistente, cero work items abiertos y `ci-verify`).
2. **Expediente y CHANGELOG:** `./sdd release prepare --version X.Y.Z` genera `specs/releases/REL-vX.Y.Z.md` (con `[ ] Gate 6 Approved` sin marcar) y actualiza `CHANGELOG.md`.
3. **Documentación y CI:** Completa riesgos, migraciones y plan de despliegue/rollback en `REL-vX.Y.Z.md`, sincroniza el badge/baseline `vX.Y.Z` en `README.md` y `docs/{en,es}/README.md`, comitea cambios y ejecuta `./sdd ci-verify`.
4. **Firma humana obligatoria (`RN-SDD-HUMAN-GATE-OWNERSHIP`):** Detente y solicita al usuario marcar `[x] **Gate 6 Approved (Human Sign-off):**` en `specs/releases/REL-vX.Y.Z.md`. Prohibido autoaprobar.
5. **Validación final, PR a `main` y publicación automática:** Ejecuta `./sdd release verify --version X.Y.Z --stage finish` y `./sdd git release-finish --version X.Y.Z` para abrir la PR hacia `main` (nunca push directo). Al mergear la PR en `main`, `.github/workflows/release.yml` crea el tag `vX.Y.Z`, publica la GitHub Release como *Latest* e intenta el back-merge a `develop`.
