# RFC-010: Gobernanza Core L4/L5 (`sdd-security-audit` + `references/`) y Expansión de Packs Enterprise (`v1.5.0`)

- **ID:** `RFC-010`
- **Versión objetivo:** `v1.5.0` *(SemVer MINOR — 100% retrocompatible con proyectos `v1.x` y `sdd sync`)*
- **Estado:** `Implementado / Done` *(Autorización explícita PO: `2026-11-24T13:35:02+01:00` — "Aprobado"; `FWK-020` completado hasta Gate 5)*
- **Rama base:** `develop` (`feat/fwk-020-skills-governance-and-enterprise-packs`)
- **Antecedentes:** [`RFC-001`](RFC-001-ui-ux-pro-max.md), [`RFC-003`](RFC-003-audit-remediation-and-hardening.md) (`FWK-006`, `FWK-007`), [`RFC-007`](RFC-007-release-ops-ci-agnostic.md) (`FWK-013`, `FWK-014`), [`RFC-009`](RFC-009-portfolio-finops-multiservice.md) (`FWK-017`)

## 1. Motivación y Análisis Crítico

Tras consolidar la gestión de Portfolio y Épicas en `v1.4.0` (`FWK-017`), una auditoría exhaustiva de madurez (`L0–L5`) frente a los principales referentes comunitarios (`affaan-m/everything-claude-code`, `obra/superpowers`, `trailofbits/skills`, `agamm/claude-code-owasp`, `hashicorp/agent-skills`, `antonbabenko/terraform-skill`, `confluentinc/agent-skills`, `lensesio/agentic-engineering-for-apache-kafka`, `bufbuild/claude-plugins`, `speakeasy-api/sdk-generation-skills`, `vercel-labs/agent-skills`, `nestjs/agent-skills`, `dbt-labs/dbt-agent-skills` y `wshobson/agents`) evidenció cuatro brechas estructurales en el catálogo de skills del starter:

1. **Ausencia de una skill transversal de auditoría de seguridad en el Core (`sdd-security-audit`, `L0 -> L5`):**
   - El Core actual (`14` skills en `.agents/skills/`) carece de una skill dedicada que articule el modelado de amenazas ligero (**STRIDE** en `Gate 2`) con la auditoría de implementación (**OWASP Top 10 / ASVS v4+**, AuthN/AuthZ/IDOR, secretos, SCA/SBOM y protección de PII en `Gate 4`), conectando `.agents/rules/05-security-and-secrets.md`, `.agents/agents/security-reviewer.md`, `pipeline-run` y `santa-method`.
2. **Asimetría de madurez (`L3 -> L4`) en 4 skills Core ultracompactas:**
   - Cuatro skills nucleares (`sdd-silent-failure-audit`, `sdd-test-quality-audit`, `sdd-execution-guardrails` y `search-first`, de `12–17` líneas) carecen de carga progresiva bajo demanda (`references/`), limitando su cobertura en escenarios políglotas (Go `_ = err`, Rust `let _ =` / `unwrap_or_default`, Java/Kotlin, transacciones SQL, colas sin DLQ), detección de tautologías de mocks/mutación, ciclo de vida OS-agnóstico de Git Worktrees (`.worktrees/`) y evaluación disciplinada de librerías externas. Replicar el patrón modular de `santa-method` (`SKILL.md <= 35` líneas + `references/`) eleva su rigor a **L4** sin penalizar la ventana de contexto en reposo.
3. **Deuda de portabilidad y referencias huérfanas heredadas de ECC en los 19 packs actuales:**
   - El inventario de `.sdd/catalog/packs/` conserva enlaces rotos a rutas inexistentes de upstream (`rules/ecc/typescript/coding-style.md` y `rules/ecc/typescript/patterns.md` en `typescript-patterns`), menciones a agentes no registrados en el starter (`code-reviewer`, `typescript-build-resolver`) y skills huérfanas (`backend-patterns`, `tdd-workflow`, `e2e-testing`, `seo`, `security-review`, `security-scan`). Es necesario sanear los `19` packs existentes e incorporar un test determinista en `tests/test_sdd_governance.py` que impida futuras referencias huérfanas.
4. **Cobertura incompleta de stacks enterprise *opt-in* (Puntos 3 y 5):**
   - El catálogo actual (`19` packs, `70` skills) no cubre de forma nativa arquitecturas orientadas a eventos y microservicios (`Kafka`, `Outbox/Inbox`, `Sagas`, `DDD`), gobierno formal de contratos de API (`OpenAPI 3.1`, `gRPC/Buf`, `AsyncAPI 3.0`), infraestructura cloud declarativa (`Terraform/OpenTofu`, `IAM OIDC`, `FinOps`, `Helm/GitOps`), frameworks TypeScript modernos de producción (`Next.js App Router/RSC`, `NestJS`), ingeniería de datos (`dbt`, `Airflow`, calidad/linaje) ni aislamiento `multi-tenant` extremo a extremo en SaaS.

## 2. Decisiones de Diseño Acordadas

1. **Evolución del Inventario con *Zero Default Bloat*:**
   - **Core (`.agents/skills/`):** `14 -> 15` skills (`+1` nueva `sdd-security-audit` con `SKILL.md <= 45L` + `references/`, y upgrade `L3 -> L4` con `references/` en `4` skills Core manteniendo cada `SKILL.md <= 35L`).
   - **Catálogo *opt-in* (`.sdd/catalog/packs/`):** `19 -> 25` packs (`+6` packs nuevos y `2` packs existentes ampliados; `70 -> 86` skills de catálogo).
   - **Total del starter:** `84 -> 101` skills, manteniendo **únicamente 15 skills Core activas por defecto** (`active_packs: []`) y respetando el techo `< 25k` tokens del contexto Markdown activo en `.agents/`.
2. **Separación Granular de Frameworks TypeScript/Node:**
   - Siguiendo la convención de `framework-django` y `framework-fastapi`, se separan `framework-nextjs` (`id: "framework:nextjs"`, `requires: ["lang:typescript", "framework:react"]`, `targets: ["web"]`) y `framework-nestjs` (`id: "framework:nestjs"`, `requires: ["lang:typescript"]`, `targets: ["api", "worker"]`), garantizando resolución transitiva determinista de dependencias.
3. **Gobierno de Presets y Poda Dinámica en Gate S0 (`sdd-bootstrap`):**
   - `scripts/sdd_pack_registry.py` extiende las reglas *fail-closed* de presets: `_API_FORBIDDEN_PACKS` incorpora `framework-nextjs`; `_SPA_FORBIDDEN_PACKS` incorpora `framework-nestjs`, `capability-event-driven` y `capability-data-engineering`.
   - `.sdd/catalog/bootstrap-references/` (`question-catalog-es.md`, `question-catalog-en.md`, `stack-config-and-pruning.md`) añade preguntas simétricas ES/EN en Rondas 2 y 3 con poda automática según topología.
4. **Aislamiento No-ECC y Trazabilidad Legal Upstream:**
   - Los `6` packs nuevos quedan fuera de `STACK_PACKS` en `scripts/sdd_catalog_import.py` (inmunes a sobreescritura por sincronizaciones ECC) y declaran metadatos estructurados `upstream` (licencias permisivas MIT / Apache-2.0) auditados 1:1 contra `.sdd/catalog/UPSTREAM.md` y `THIRD_PARTY_NOTICES.md`.
5. **Ejecución DAG Multi-Oleada y Balanceo de Cuota Multi-Familia (Opción A):**
   - Entrega cohesionada en un único Work Item (`FWK-020`, `5` bloques DAG, `17` tareas `T-01`..`T-17` con *Write-Sets* 100% disjuntos), ejecutando Gate 4 en tres oleadas limpias (`/continue`) más cierre `/gate5`, y balanceando cuota entre **Pool Gemini** (`Carbon High`, `Neon High/Medium`, `Hydrogen Low/Medium`) y **Pool Claude** (`Claude Opus 5.5 High` al 50% en Bloque `C` y como segundo revisor adversario independiente en `santa-method`).

## 3. Descomposición en Work Items

| ID | Título | Prioridad | Depende de | Alcance (`5` Bloques DAG · `17` Tareas) |
| :--- | :--- | :---: | :---: | :--- |
| **`FWK-020`** | Gobernanza Core (`sdd-security-audit` + `references/` L4), Saneamiento ECC y Expansión de Packs Enterprise (`v1.5.0`) | P0 | — | **Bloque A (Core & Saneamiento):** `sdd-security-audit` (`T-01`), upgrade `L3->L4` de 4 skills Core con `references/` (`T-02`) y limpieza de enlaces/agentes huérfanos ECC en 19 packs (`T-03`).<br>**Bloque B (Microservicios & APIs):** `capability-event-driven` (`T-04`, 3 skills) y `capability-api-governance` (`T-05`, 3 skills).<br>**Bloque C (Cloud, TS Frameworks, Data & Multi-Tenant):** `capability-iac-cloud` (`T-06`, 3 skills), `capability-devops` `+helm-gitops-patterns` (`T-07`), `framework-nextjs` (`T-08`), `framework-nestjs` (`T-09`), `capability-data-engineering` (`T-10`, 3 skills) y `capability-database` `+multi-tenant-isolation` (`T-11`).<br>**Bloque D (Integración & QA):** `sdd_pack_registry.py` + `bootstrap-references/` ES/EN + `pipeline-run`/`05-security-and-secrets.md` (`T-12`), `UPSTREAM.md` + `THIRD_PARTY_NOTICES.md` (`T-13`), tests de materialización y anti-enlaces huérfanos (`T-14`) y auditoría `ci-verify` + Santa `GATE_4` (`T-15`).<br>**Bloque E (0DD & Release):** documentación bilingüe + Santa `GATE_5` (`T-16`) y Gate 6 `REL-v1.5.0` (`T-17`). |

## 4. Restricciones Transversales

- **Stdlib-only & Límite Estricto `<= 500L`:** Python `>= 3.12` sin dependencias externas (`pyproject.toml`); todo archivo `.py` en `scripts/`, `.agents/scripts/` y `tests/` debe mantenerse estrictamente en `<= 500` líneas (incluyendo `scripts/sdd_pack_registry.py`, actualmente en `496L`, y los módulos de test ampliados en `T-14`).
- **Seguridad *Fail-Closed* (`shell=False`):** prohibido `shell=True`; preservación íntegra de guardas anti-symlinks/junctions, normalización Win32 `\\?\` y validación anti-*path-traversal*.
- **Presupuesto de Contexto (`< 25k` tokens en `.agents/`):** los ficheros `references/*.md` solo se leen bajo demanda y los `16` nuevos `SKILL.md` de dominio residen exclusivamente bajo `.sdd/catalog/packs/` hasta su activación explícita en `specs/STACK.md`.
- **Compatibilidad Retroactiva (`v1.5.0` SemVer MINOR):** proyectos existentes con `squad.lock.json` (`schema_version: 2`) y `specs/STACK.md` previos continúan operando y sincronizando mediante `sdd sync` sin cambios disruptivos.
- **Autoridad Humana (`RN-SDD-HUMAN-GATE-OWNERSHIP`):** sign-off humano explícito obligatorio en `RFC-010`, `Gate 1`, `Gate 2` (tras veredicto unánime `NICE + NICE` en `/santa-loop` `PRE_GATE_2`), `Gate 3` y `Gate 6` (`REL-v1.5.0`).
