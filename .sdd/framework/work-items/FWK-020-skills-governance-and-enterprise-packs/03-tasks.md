# Plan de Tareas (DAG): `FWK-020` Gobernanza Core (`sdd-security-audit` + `references/` L4), Saneamiento ECC y Packs Enterprise (`v1.5.0`)

- **ID:** `FWK-020-skills-governance-and-enterprise-packs`
- **RFC:** [`RFC-010`](../../rfcs/RFC-010-skills-governance-and-enterprise-packs.md) (`Aceptado`)
- **Especificación Técnica:** [`02-tech-spec.md`](02-tech-spec.md) (`Gate 2 Approved`)
- **Estado:** `Approved`
- **Estrategia Operativa de Sesiones y Cuota (Opción A):**
  - **Oleada 1 (`/continue`):** `Bloque A` + `Bloque B` (`T-01`..`T-05`) — `Gemini 4 Carbon (High)` en `T-01`/`T-02` y `Gemini 4 Neon (High)` en `T-03`..`T-05`.
  - **Oleada 2 (`/continue`):** `Bloque C` (`T-06`..`T-11`) — reparto 50/50 entre **Pool Gemini** (`T-06`, `T-07` en `Neon High`; `T-11` en `Carbon High`) y **Pool Claude** (`T-08`, `T-09`, `T-10` en `Claude Opus 5.5 High`).
  - **Oleada 3 (`/continue`):** `Bloque D` (`T-12`..`T-15`) — `Gemini 4 Neon (Medium)` en `T-12`/`T-14`, `Gemini 4 Hydrogen (Medium)` en `T-13`, y revisores cruzados `Carbon High` + `Opus 5.5 High` en `T-15` (`GATE_4`).
  - **Oleada 4 (`/gate5`):** `Bloque E` (`T-16`, `T-17`) — `Gemini 4 Hydrogen (Low–Medium)` + Santa `GATE_5` (`Neon High`).
- **Gate 3 Sign-off:** `[x] Gate 3 Approved (Authorized by PO on 2026-11-25T00:26:49+01:00 — "Aprobado")`

---

## Grafo DAG por Bloques de Ejecución (5 Bloques · 17 Tareas)

### Bloque A: Gobernanza Core y Saneamiento ECC [PARALLEL: BLOCK_A]

- [x] `T-01` [`@architect`] `[PARALLEL: BLOCK_A]`: Crear la nueva skill Core `.agents/skills/sdd-security-audit/` (`SKILL.md <= 45L` + `references/stride-threat-model.md` y `references/owasp-asvs-checklist.md`) cubriendo modelado STRIDE en `Gate 2` y verificación OWASP Top 10 / ASVS v4+, BOLA/IDOR, secretos, SCA/SBOM y PII en `Gate 4` sin duplicar `05-security-and-secrets.md` ni `security-reviewer.md`.
  - *Archivos exactos*: `.agents/skills/sdd-security-audit/SKILL.md`, `.agents/skills/sdd-security-audit/references/stride-threat-model.md`, `.agents/skills/sdd-security-audit/references/owasp-asvs-checklist.md`
  - *Contrato de referencia*: `02-tech-spec.md` §1.2, §2.1 (`RF-2001`, `CA-2001`)
  - *Comando de verificación DoD*: `uv run python scripts/sdd_cli.py healthcheck`

- [x] `T-02` [`@architect`] `[PARALLEL: BLOCK_A]`: Elevar de `L3` a `L4` las 4 skills Core (`sdd-silent-failure-audit`, `sdd-test-quality-audit`, `sdd-execution-guardrails`, `search-first`), manteniendo cada `SKILL.md <= 35L` y creando sus playbooks bajo demanda en `references/` (`polyglot-silent-failures.md`, `anti-mocking-and-mutation.md`, `worktree-lifecycle.md`, `reuse-vs-build-matrix.md`) dentro del presupuesto `< 15k` tokens de `references/`.
  - *Archivos exactos*: `.agents/skills/sdd-silent-failure-audit/SKILL.md`, `.agents/skills/sdd-silent-failure-audit/references/polyglot-silent-failures.md`, `.agents/skills/sdd-test-quality-audit/SKILL.md`, `.agents/skills/sdd-test-quality-audit/references/anti-mocking-and-mutation.md`, `.agents/skills/sdd-execution-guardrails/SKILL.md`, `.agents/skills/sdd-execution-guardrails/references/worktree-lifecycle.md`, `.agents/skills/search-first/SKILL.md`, `.agents/skills/search-first/references/reuse-vs-build-matrix.md`
  - *Contrato de referencia*: `02-tech-spec.md` §1.2, §2.2 (`RF-2002`, `CA-2002`)
  - *Comando de verificación DoD*: `uv run python scripts/sdd_cli.py healthcheck`

- [x] `T-03` [`@back-engineer`] `[PARALLEL: BLOCK_A]`: Ejecutar el saneamiento exhaustivo de los 19 packs existentes en `.sdd/catalog/packs/` (sin tocar `capability-ui-design/vendor/ui-ux-pro-max/` ni romper `test_sdd_ui_design.py` Group 6): reparar las 5 cercas anidadas a ````text (`R0`), limpiar rutas `rules/ecc/`, `.claude/`, `~/.claude/` y `rules/<dir>/*` (`R1`), convertir los ~82 enlaces relativos inter-carpeta a rutas canónicas en código (`R2`) y sustituir agentes/skills huérfanos (`R3` y `R4`).
  - *Archivos exactos*: `.sdd/catalog/packs/**`
  - *Contrato de referencia*: `02-tech-spec.md` §2.3, §5.2 (`RF-2003`, `CA-2003`)
  - *Comando de verificación DoD*: `uv run pytest tests/test_sdd_ui_design.py -q`

### Bloque B: Punto 3 — Microservicios, Event-Driven y Gobierno de APIs [PARALLEL: After BLOCK_A]

- [x] `T-04` [`@back-engineer`] `[PARALLEL: BLOCK_B]`: Crear el pack `.sdd/catalog/packs/capability-event-driven/` (`pack.json` con `id: "capability:event-driven"`, `targets: ["api", "backend", "server", "microservice"]`, `upstream` uniforme `Apache-2.0`/`MIT`) y sus 3 skills `L4` (`kafka-streaming-patterns`, `async-messaging-patterns`, `microservices-boundaries`) cumpliendo `R0`–`R4`.
  - *Archivos exactos*: `.sdd/catalog/packs/capability-event-driven/**`
  - *Contrato de referencia*: `02-tech-spec.md` §3.1, §3.2 (`RF-2004`, `CA-2004`)
  - *Comando de verificación DoD*: `uv run python scripts/sdd_agent_generator.py --verify`

- [x] `T-05` [`@back-engineer`] `[PARALLEL: BLOCK_B]`: Crear el pack `.sdd/catalog/packs/capability-api-governance/` (`pack.json` con `id: "capability:api-governance"`, `targets: ["all"]`, `upstream` uniforme `Apache-2.0`) y sus 3 skills `L4` (`openapi-contract-governance`, `grpc-protobuf-patterns`, `asyncapi-event-contracts`) alineadas con `API_CATALOG.md` y `santa-method` (`R0`–`R4`).
  - *Archivos exactos*: `.sdd/catalog/packs/capability-api-governance/**`
  - *Contrato de referencia*: `02-tech-spec.md` §3.1, §3.2 (`RF-2004`, `CA-2004`)
  - *Comando de verificación DoD*: `uv run python scripts/sdd_agent_generator.py --verify`

### Bloque C: Punto 5 — IaC/Cloud, GitOps, Frameworks TS, Data y Multi-Tenancy [PARALLEL: After BLOCK_B]

- [x] `T-06` [`@devops`] `[PARALLEL: BLOCK_C]`: Crear el pack `.sdd/catalog/packs/capability-iac-cloud/` (`pack.json` con `id: "capability:iac-cloud"`, `targets: ["all"]`, `upstream.repo: "antonbabenko/terraform-skill"`, `license: "Apache-2.0"`) y sus 3 skills `L4` (`terraform-opentofu-patterns`, `cloud-iam-security`, `cloud-finops-guardrails`) cumpliendo `R0`–`R4`.
  - *Archivos exactos*: `.sdd/catalog/packs/capability-iac-cloud/**`
  - *Contrato de referencia*: `02-tech-spec.md` §3.1, §3.2 (`RF-2005`, `CA-2005`)
  - *Comando de verificación DoD*: `uv run python scripts/sdd_agent_generator.py --verify`

- [x] `T-07` [`@devops`] `[PARALLEL: BLOCK_C]`: Ampliar `.sdd/catalog/packs/capability-devops/` añadiendo `skills/helm-gitops-patterns/SKILL.md` (`L4`, `R0`–`R4`) y actualizando `capability-devops/pack.json` (`4 -> 5` skills + `upstream.references: ["wshobson/agents (MIT)"]`).
  - *Archivos exactos*: `.sdd/catalog/packs/capability-devops/skills/helm-gitops-patterns/SKILL.md`, `.sdd/catalog/packs/capability-devops/pack.json`
  - *Contrato de referencia*: `02-tech-spec.md` §3.1, §3.2 (`RF-2006`, `CA-2006`)
  - *Comando de verificación DoD*: `uv run python scripts/sdd_agent_generator.py --verify`

- [x] `T-08` [`@front-engineer`] `[PARALLEL: BLOCK_C]`: Crear el pack `.sdd/catalog/packs/framework-nextjs/` (`pack.json` con `id: "framework:nextjs"`, `requires: ["lang:typescript", "framework:react"]`, `targets: ["web"]`, `upstream.repo: "vercel-labs/agent-skills"`, `license: "MIT"`) y su skill `L4` `skills/nextjs-patterns/SKILL.md` cumpliendo `R0`–`R4`.
  - *Archivos exactos*: `.sdd/catalog/packs/framework-nextjs/**`
  - *Contrato de referencia*: `02-tech-spec.md` §3.1, §3.2 (`RF-2005`, `CA-2005`)
  - *Comando de verificación DoD*: `uv run python scripts/sdd_agent_generator.py --verify`

- [x] `T-09` [`@back-engineer`] `[PARALLEL: BLOCK_C]`: Crear el pack `.sdd/catalog/packs/framework-nestjs/` (`pack.json` con `id: "framework:nestjs"`, `requires: ["lang:typescript"]`, `targets: ["api", "backend", "server"]`, `upstream.repo: "nestjs/agent-skills"`, `license: "MIT"`) y su skill `L4` `skills/nestjs-patterns/SKILL.md` cumpliendo `R0`–`R4`.
  - *Archivos exactos*: `.sdd/catalog/packs/framework-nestjs/**`
  - *Contrato de referencia*: `02-tech-spec.md` §3.1, §3.2 (`RF-2005`, `CA-2005`)
  - *Comando de verificación DoD*: `uv run python scripts/sdd_agent_generator.py --verify`

- [x] `T-10` [`@back-engineer`] `[PARALLEL: BLOCK_C]`: Crear el pack `.sdd/catalog/packs/capability-data-engineering/` (`pack.json` con `id: "capability:data-engineering"`, `targets: ["api", "backend", "database", "db"]`, `upstream.repo: "dbt-labs/dbt-agent-skills"`, `license: "Apache-2.0"`) y sus 3 skills `L4` (`dbt-modeling-patterns`, `airflow-dag-patterns`, `data-quality-governance`) cumpliendo `R0`–`R4`.
  - *Archivos exactos*: `.sdd/catalog/packs/capability-data-engineering/**`
  - *Contrato de referencia*: `02-tech-spec.md` §3.1, §3.2 (`RF-2005`, `CA-2005`)
  - *Comando de verificación DoD*: `uv run python scripts/sdd_agent_generator.py --verify`

- [x] `T-11` [`@back-engineer`] `[PARALLEL: BLOCK_C]`: Ampliar `.sdd/catalog/packs/capability-database/` añadiendo `skills/multi-tenant-isolation/SKILL.md` (`L4`, RLS Postgres + propagación `tenant_id` + tests negativos anti-IDOR, cumpliendo `R0`–`R4`) y actualizando `capability-database/pack.json` (`6 -> 7` skills, conservando `agents/database-reviewer.md` + `upstream.references`).
  - *Archivos exactos*: `.sdd/catalog/packs/capability-database/skills/multi-tenant-isolation/SKILL.md`, `.sdd/catalog/packs/capability-database/pack.json`
  - *Contrato de referencia*: `02-tech-spec.md` §3.1, §3.2 (`RF-2006`, `CA-2006`)
  - *Comando de verificación DoD*: `uv run python scripts/sdd_agent_generator.py --verify`

### Bloque D: Integración en Motor, Licencias, Pruebas y Gate 4 QA [PARALLEL: After BLOCK_C]

- [ ] `T-12` [`@back-engineer`] `[PARALLEL: BLOCK_D]`: Actualizar `_API_FORBIDDEN_PACKS` y `_SPA_FORBIDDEN_PACKS` en `scripts/sdd_pack_registry.py` (`<= 500L`), implementar la preservación *fail-closed* de extensiones SDD en `scripts/sdd_catalog_import.py` (`<= 500L`), actualizar con simetría ES/EN y reglas de poda `.sdd/catalog/bootstrap-references/{question-catalog-es,question-catalog-en,stack-config-and-pruning}.md`, y enlazar `sdd-security-audit` en `.agents/skills/pipeline-run/SKILL.md` y `.agents/rules/05-security-and-secrets.md`.
  - *Archivos exactos*: `scripts/sdd_pack_registry.py`, `scripts/sdd_catalog_import.py`, `.sdd/catalog/bootstrap-references/question-catalog-es.md`, `.sdd/catalog/bootstrap-references/question-catalog-en.md`, `.sdd/catalog/bootstrap-references/stack-config-and-pruning.md`, `.agents/skills/pipeline-run/SKILL.md`, `.agents/rules/05-security-and-secrets.md`
  - *Contrato de referencia*: `02-tech-spec.md` §2.1, §4.1, §4.2, §4.3 (`RF-2001`, `RF-2007`, `RF-2008`)
  - *Comando de verificación DoD*: `uv run python scripts/sdd_agent_generator.py --verify`

- [ ] `T-13` [`@documentator`] `[PARALLEL: BLOCK_D]`: Actualizar `.sdd/catalog/UPSTREAM.md` (tabla maestra de los `25` packs) y `THIRD_PARTY_NOTICES.md` con paridad 1:1 exacta de todos los repositorios y licencias (`MIT` / `Apache-2.0`) declarados en `upstream.repo` y `upstream.references` de los `25` `pack.json` (incluidos `nextlevelbuilder/ui-ux-pro-max-skill`, `asyncapi/spec` y los referentes Core).
  - *Archivos exactos*: `.sdd/catalog/UPSTREAM.md`, `THIRD_PARTY_NOTICES.md`
  - *Contrato de referencia*: `02-tech-spec.md` §3.1, §4.4 (`RF-2008`, `CA-2008`)
  - *Comando de verificación DoD*: `uv run python scripts/sdd_cli.py healthcheck`

- [ ] `T-14` [`@qa-tester`] `[SEQUENTIAL: AFTER T-12, T-13]`: Crear `tests/test_sdd_enterprise_packs.py` (`<= 380L`, `CA-2004`..`CA-2008`), actualizar `tests/test_sdd_pack_materialization.py` (`<= 498L`), implementar `audit_catalog_pack_references` (`R0`–`R4`) y tests `CA-2001`..`CA-2003` + `CA-2009` en `tests/test_sdd_governance.py` (`<= 495L`), y aplicar el filtro `"references" not in p.parts` sobre el presupuesto activo en `tests/test_sdd_{release,brownfield,drift,portfolio}.py` (`<= 500L` en todos los `.py`).
  - *Archivos exactos*: `tests/test_sdd_enterprise_packs.py`, `tests/test_sdd_pack_materialization.py`, `tests/test_sdd_governance.py`, `tests/test_sdd_release.py`, `tests/test_sdd_brownfield.py`, `tests/test_sdd_drift.py`, `tests/test_sdd_portfolio.py`
  - *Contrato de referencia*: `02-tech-spec.md` §1.2, §5.1, §5.2 (`CA-2001`..`CA-2009`)
  - *Comando de verificación DoD*: `uv run pytest tests/test_sdd_pack_materialization.py tests/test_sdd_enterprise_packs.py tests/test_sdd_governance.py tests/test_sdd_sync_and_modularity.py -q`

- [ ] `T-15` [`@qa-tester`] `[SEQUENTIAL: AFTER T-14]`: Ejecutar la auditoría integral `Gate 4`: **Capa 1 Determinista** (`uv run pytest -q`, `uv run python scripts/sdd_cli.py ci-verify --mode framework`, `verify_architecture_boundaries.py`, `sdd_healthcheck.py`) seguida de **Capa 2 Semántica** (`/santa-loop` con rúbrica `GATE_4` y 2 revisores frescos aislados hasta veredicto unánime `NICE + NICE`).
  - *Archivos exactos*: N/A
  - *Contrato de referencia*: `02-tech-spec.md` §5, §6 (`RF-2009`, `CA-2009`)
  - *Comando de verificación DoD*: `uv run python scripts/sdd_cli.py ci-verify --mode framework`

### Bloque E: Documentación Viva 0DD (Gate 5) y Release `v1.5.0` (Gate 6) [SEQUENTIAL: AFTER T-15]

- [ ] `T-16` [`@documentator`] `[SEQUENTIAL: AFTER T-15]`: Actualizar en paridad bilingüe `docs/es/README.md`, `docs/en/README.md`, `docs/knowledge/SYSTEM_TOPOLOGY.md`, `docs/traceability/TRACEABILITY-MATRIX.md`, `README.md` y marcar `FWK-020` como `Done` (`RFC-010` -> `Implementado / Done`) en `.sdd/framework/BACKLOG.md`; ejecutar `/santa-loop` (`GATE_5` -> `NICE + NICE`), verificar `ci-verify` en verde y hacer `git commit` + `git push origin feat/fwk-020-skills-governance-and-enterprise-packs` + PR a `develop`.
  - *Archivos exactos*: `docs/es/README.md`, `docs/en/README.md`, `docs/knowledge/SYSTEM_TOPOLOGY.md`, `docs/traceability/TRACEABILITY-MATRIX.md`, `README.md`, `.sdd/framework/BACKLOG.md`
  - *Contrato de referencia*: `AGENTS.md` (`RN-SDD-0DD`, `RN-SDD-BRANCH-SYNC`)
  - *Comando de verificación DoD*: `uv run python scripts/sdd_cli.py ci-verify --mode framework`

- [ ] `T-17` [`@devops`] `[SEQUENTIAL: AFTER T-16]`: Ejecutar `/gate6-release` (`REL-v1.5.0`) sobre rama `release/v1.5.0` desde `develop` actualizado mediante `sdd release prepare --version v1.5.0` y `sdd release changelog --version v1.5.0`, solicitar sign-off humano explícito de `Gate 6`, verificar `sdd release verify --version v1.5.0` y abrir PR de release hacia `main`.
  - *Archivos exactos*: `CHANGELOG.md`, `specs/releases/REL-v1.5.0.md`
  - *Contrato de referencia*: `.agents/workflows/gate6-release.md`, `RFC-010` (`v1.5.0`)
  - *Comando de verificación DoD*: `uv run python scripts/sdd_cli.py release verify --version v1.5.0`

---

## Aprobación Formal Gate 3 (`RN-SDD-HUMAN-GATE-OWNERSHIP`)
- [x] **Gate 3 Approved (Human Sign-off):** Revisado y validado por Stakeholder Humano (`2026-11-25T00:26:49+01:00` — `"Aprobado"`).

<!-- sdd:gate-seal gate=3 sha256=19ec6a9188b327e9a44fb95bed6c3d0001de693df361ed12ee220dd4d7f403ef -->
