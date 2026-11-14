# RFC-003: Endurecimiento Integral Post-Auditoría Adversarial, Ownership Compiler, Concurrencia y Slimming

- **ID:** `RFC-003`
- **Estado:** `Aceptado` *(Autorización explícita PO: `2026-11-14T16:05:46+01:00` — Pre-autorización A1/A2/A3/A4)*
- **Rama base:** `develop` (prohibido tocar `main` directamente)
- **Alcance de auditoría origen:** `.worktrees/audit-env/audit/09-findings-register.md`, `10-remediation-roadmap.md`, `11-independent-review.md`, `12-final-verdict.md` (`AUD-001`..`AUD-019`, `AUD-021`..`AUD-025`, más adopción DX `BUG-XXX` y `domains/` de `facuzarate04/sdd-starter`).

## 1. Motivación y Decisión Arquitectónica

La auditoría técnica adversarial sobre `develop@48340d40` demostró fallos de seguridad *fail-open* (`AUD-007`..`AUD-011`, `AUD-021`..`AUD-024`), compilación estática ignorando la Ownership Map (`AUD-001`), mutaciones no transaccionales (`AUD-013`), ausencia de verificador real de grafos DAG (`AUD-015`), colisiones en worktrees concurrentes (`AUD-016`), sobrecarga inicial de contexto (`AUD-017`: ~73.9k tokens estimados), brechas de CI/0DD (`AUD-014`/`AUD-018`) y violaciones al techo modular `<= 500` líneas (`AUD-025`).

Se aprueban los siguientes pilares vinculantes:
1. **Fail-Closed Absoluto (P0):** Retirar `SDD_FORCE_MAIN_PUSH`, prohibir `shell=True` en `sdd_trim_exec.py`, corregir `.agents/hooks.json` (sin BOM y rutas `.agents/scripts/`), validar `[x] Gate 1/2/3 Approved` y contenido en `01/02/03.md`, proteger `tests/`, `.agents/`, `specs/STACK.md`, contener `WorktreeManager.remove` a `worktrees_root`, endurecer `sdd.cmd`, limpiar skills filtradas (`fastapi-patterns`, `postgres-patterns`, `react-performance-and-patterns`) y validar estado `Draft` por columna.
2. **Modularidad Estricta `<= 500` Líneas:** Ningún módulo Python nuevo, modificado o de test superará `500` líneas. `sdd_ownership.py`, `sdd_dag.py`, `sdd_generator_tx.py` nacen desacoplados; `sdd_git.py` (`743L`), `sdd_token_usage.py` (`901L`) y `sdd_repo_map.py` (`681L`) se dividen en submódulos cohesivos.
3. **Slimming `< 25k` Tokens & Opt-In Catalog:** Eliminar `.agents/archetypes/`, deduplicar catálogo, erradicar referencias residuales PACO/JARVIS y consolidar agentes base activos a `~9` roles moviendo especialistas extra a catálogo/skills opt-in.
4. **Particionado DAG Ortogonal (`FWK-005` -> `FWK-006 || FWK-007 || FWK-008 || FWK-009` -> Integración & Gate 5):** Cero solapamiento de ficheros entre worktrees paralelos; validación final post-fix contra los casos de `audit/tests/run_audit_tests.py` antes de limpiar `.worktrees/audit-env/`.
