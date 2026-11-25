# Spec Funcional: Gobernanza Core (`sdd-security-audit` + `references/` L4), Saneamiento ECC y Expansión de Packs Enterprise (`FWK-020`)

- **ID:** `FWK-020-skills-governance-and-enterprise-packs`
- **RFC:** [`RFC-010`](../../rfcs/RFC-010-skills-governance-and-enterprise-packs.md) (`Aceptado`)
- **Versión objetivo:** `v1.5.0` *(SemVer MINOR — 100% retrocompatible con `v1.x`)*
- **Estado:** `Approved`
- **Sub-Gate 2V (Visual):** `N/A` *(Work Item de framework, catálogo y CLI sin pantallas `SCR-###`)*
- **Gate 1 Sign-off:** `[x] Gate 1 Approved (Authorized by PO on 2026-11-24T13:45:43+01:00 — "Aprobado Gate 1")`

## 1. Resumen, Fuentes y Alcance

Elevar la madurez del catálogo de skills del starter a nivel **L4/L5** frente a los principales referentes de la comunidad sin penalizar el presupuesto de contexto en reposo (`< 25k` tokens en `.agents/`), incorporando una skill Core transversal de auditoría de seguridad (`sdd-security-audit`), dotando de carga progresiva `references/` a las 4 skills Core compactas de nivel `L3`, eliminando todas las referencias/agentes huérfanos heredados de ECC en los 19 packs actuales con verificación determinista en tests, y ampliando el catálogo *opt-in* de `19` a `25` packs (`70 -> 86` skills de catálogo; `84 -> 101` skills totales en el starter, manteniendo solo `15` activas por defecto).

### Fuentes (`SRC-###`) y Ambigüedades (`AMB-###`)
- `SRC-001`: Directriz y plan definitivo v2.2 aprobados por PO (`2026-11-24T13:26:22+01:00` y sign-off de `RFC-010` en `2026-11-24T13:35:02+01:00` — alcance completo en 1 Feature cohesiva, 5 Bloques DAG, 17 Tareas `T-01`..`T-17`, versión `v1.5.0` y estrategia de cuota Opción A).
- `SRC-002`: Auditoría comparativa `L0–L5` sobre las 14 skills Core y 19 packs existentes frente a `affaan-m/everything-claude-code`, `obra/superpowers`, `trailofbits/skills`, `agamm/claude-code-owasp`, `github/awesome-copilot`, `hashicorp/agent-skills`, `antonbabenko/terraform-skill`, `BagelHole/DevOps-Security-Agent-Skills`, `confluentinc/agent-skills`, `lensesio/agentic-engineering-for-apache-kafka`, `bufbuild/claude-plugins`, `speakeasy-api/sdk-generation-skills`, `vercel-labs/agent-skills`, `nestjs/agent-skills`, `Kadajett/agent-nestjs-skills`, `dbt-labs/dbt-agent-skills`, `GoogleCloudPlatform/data-agent-kit-plugin` y `wshobson/agents`.
- `AMB-001` *(Resolved)*: Empaquetado conjunto vs. separado para `Next.js` y `NestJS`. Resolución PO: packs separados `framework-nextjs` (`requires: ["lang:typescript", "framework:react"]`) y `framework-nestjs` (`requires: ["lang:typescript"]`), en simetría con `framework-django` y `framework-fastapi`.
- `AMB-002` *(Resolved)*: Profundización de las skills Core sin degradar el techo `< 25k` tokens de `.agents/`. Resolución: mantener `sdd-security-audit/SKILL.md <= 45` líneas y los 4 `SKILL.md` mejorados `<= 35` líneas, alojando playbooks extensos en subcarpetas `references/` de lectura bajo demanda (modelo `santa-method`).
- `AMB-003` *(Resolved)*: Destino de `helm-gitops-patterns` y `multi-tenant-isolation`. Resolución PO: integrarlos como ampliaciones retrocompatibles en `capability-devops` (`4 -> 5` skills) y `capability-database` (`6 -> 7` skills).

### Alcance
- **In-Scope:**
  - **Core (`.agents/skills/`):** nueva skill `sdd-security-audit` (`SKILL.md <= 45L` + `references/{stride-threat-model.md,owasp-asvs-checklist.md}`) y enlace ligero en `.agents/skills/pipeline-run/SKILL.md` y `.agents/rules/05-security-and-secrets.md`; upgrade `L3 -> L4` con carpeta `references/` en `sdd-silent-failure-audit`, `sdd-test-quality-audit`, `sdd-execution-guardrails` y `search-first` (`SKILL.md <= 35L` cada una).
  - **Saneamiento Catálogo Existente:** limpieza de enlaces a `rules/ecc/...`, enlaces relativos rotos y menciones a agentes/skills inexistentes (`code-reviewer`, `typescript-build-resolver`, `backend-patterns`, `tdd-workflow`, `e2e-testing`, etc.) en los `19` packs actuales de `.sdd/catalog/packs/`.
  - **6 Packs Nuevos *Opt-in* (`.sdd/catalog/packs/`):**
    1. `capability-event-driven` (`kafka-streaming-patterns`, `async-messaging-patterns`, `microservices-boundaries`).
    2. `capability-api-governance` (`openapi-contract-governance`, `grpc-protobuf-patterns`, `asyncapi-event-contracts`).
    3. `capability-iac-cloud` (`terraform-opentofu-patterns`, `cloud-iam-security`, `cloud-finops-guardrails`).
    4. `framework-nextjs` (`nextjs-patterns`, `requires: ["lang:typescript", "framework:react"]`).
    5. `framework-nestjs` (`nestjs-patterns`, `requires: ["lang:typescript"]`).
    6. `capability-data-engineering` (`dbt-modeling-patterns`, `airflow-dag-patterns`, `data-quality-governance`).
  - **2 Packs Existentes Ampliados:** `capability-devops` (`+helm-gitops-patterns`) y `capability-database` (`+multi-tenant-isolation`).
  - **Integración, Licencias y QA:** reglas de incompatibilidad de presets en `scripts/sdd_pack_registry.py` (`<= 500L`), preguntas ES/EN y poda dinámica en `.sdd/catalog/bootstrap-references/`, atribución legal en `.sdd/catalog/UPSTREAM.md` y `THIRD_PARTY_NOTICES.md`, y cobertura determinista en `tests/test_sdd_pack_materialization.py` y `tests/test_sdd_governance.py` (incluido guardián anti-referencias huérfanas).
- **Out-of-Scope:**
  - Contabilidad FinOps CLI (`FWK-018` `sdd finops`) y verificador CLI de contratos multi-servicio (`FWK-019` `sdd contracts`).
  - Inclusión de binarios, SDKs externos o dependencias fuera de la librería estándar de Python `>= 3.12`.
  - Modificación de `STACK_PACKS` en `scripts/sdd_catalog_import.py` para importar packs no pertenecientes a `affaan-m/ecc`.

## 2. Requisitos Funcionales y No Funcionales (EARS)

- `RF-2001` (**Skill Core `sdd-security-audit` y Triggers de Seguridad**): El framework SDD deberá proveer la skill Core `.agents/skills/sdd-security-audit/SKILL.md` (`<= 45` líneas) junto con `.agents/skills/sdd-security-audit/references/stride-threat-model.md` y `.agents/skills/sdd-security-audit/references/owasp-asvs-checklist.md`; y CUANDO una iteración transite por `Gate 2` o `Gate 4` (`pipeline-run` y `.agents/rules/05-security-and-secrets.md`), el sistema deberá activar el modelado de amenazas ligero STRIDE (en `Gate 2`) y la verificación OWASP Top 10 / ASVS v4+, AuthN/AuthZ/IDOR, gestión de secretos, SCA/SBOM y exposición de PII (en `Gate 4`).
- `RF-2002` (**Upgrade Modular `L3 -> L4` de 4 Skills Core con `references/`**): El framework SDD deberá actualizar `.agents/skills/{sdd-silent-failure-audit,sdd-test-quality-audit,sdd-execution-guardrails,search-first}/SKILL.md` manteniendo cada fichero `SKILL.md` en `<= 35` líneas e incorporando ficheros bajo demanda en `references/` que cubran: (a) patrones políglotas de fallos silenciosos en Python, TS/JS, Go, Rust, Java/Kotlin, transacciones SQL y colas sin DLQ; (b) catálogo anti-mocking, concurrencia/flakiness y guía de mutación; (c) ciclo de vida multiplataforma Windows/POSIX de Git Worktrees en `.worktrees/`; y (d) matriz de decisión Reutilizar vs. Extender vs. Adoptar librería madura vs. Construir.
- `RF-2003` (**Saneamiento de Referencias Huérfanas ECC y Guardián de Gobernanza**): El catálogo `.sdd/catalog/packs/` deberá carecer de referencias a rutas inexistentes heredadas de upstream (`rules/ecc/...`), enlaces relativos rotos y agentes o skills no registrados en el starter (`code-reviewer`, `typescript-build-resolver`, `backend-patterns`, etc.) en todos sus packs; y SI cualquier documento Markdown bajo `.sdd/catalog/packs/` (fuera de `vendor/`) contiene una ruta `rules/ecc/`, un enlace relativo roto o una invocación a un agente o skill inexistente en el inventario oficial del framework, ENTONCES la suite `tests/test_sdd_governance.py` deberá fallar de forma determinista reportando el archivo e identificador infractor.
- `RF-2004` (**Materialización de Packs *Opt-in* de Microservicios y Gobierno de APIs — Punto 3**): DONDE un proyecto declare `capability:event-driven` o `capability:api-governance` en el bloque `sdd:stack-config` de `specs/STACK.md`, el motor `sdd_agent_generator.py` deberá validar su `pack.json` y materializar transaccionalmente `.sdd/catalog/packs/capability-event-driven/` (`kafka-streaming-patterns`, `async-messaging-patterns`, `microservices-boundaries`) y `.sdd/catalog/packs/capability-api-governance/` (`openapi-contract-governance`, `grpc-protobuf-patterns`, `asyncapi-event-contracts`) con `rules: []` y trazabilidad explícita hacia `02-tech-spec.md`, `docs/knowledge/API_CATALOG.md` y `santa-method`.
- `RF-2005` (**Materialización y Dependencias Transitivas de IaC/Cloud, Next.js, NestJS y Data Engineering — Punto 5**): DONDE un proyecto declare `capability:iac-cloud`, `framework:nextjs`, `framework:nestjs` o `capability:data-engineering` en `specs/STACK.md`, `scripts/sdd_pack_registry.py` y `scripts/sdd_agent_generator.py` deberán exigir y resolver sus dependencias `requires` (`framework:nextjs -> ["lang:typescript", "framework:react"]`, `framework:nestjs -> ["lang:typescript"]`) y materializar sin colisiones `.sdd/catalog/packs/capability-iac-cloud/` (`terraform-opentofu-patterns`, `cloud-iam-security`, `cloud-finops-guardrails`), `.sdd/catalog/packs/framework-nextjs/` (`nextjs-patterns`), `.sdd/catalog/packs/framework-nestjs/` (`nestjs-patterns`) y `.sdd/catalog/packs/capability-data-engineering/` (`dbt-modeling-patterns`, `airflow-dag-patterns`, `data-quality-governance`).
- `RF-2006` (**Ampliación Retrocompatible de `capability-devops` y `capability-database`**): DONDE un proyecto active `capability:devops` o `capability:database` en `specs/STACK.md`, el generador deberá materializar `helm-gitops-patterns` junto a las 4 skills preexistentes de `capability-devops` (`5` en total) y `multi-tenant-isolation` junto a las 6 skills preexistentes de `capability-database` (`7` en total), manteniendo intacta la estructura `squad.lock.json` (`schema_version: 2`).
- `RF-2007` (**Incompatibilidades *Fail-Closed* de Presets y Poda Dinámica en `sdd-bootstrap`**): SI `specs/STACK.md` declara `preset: "api-only"` junto con `framework:nextjs`, o declara `preset: "spa-only"` junto con `framework:nestjs`, `capability:event-driven` o `capability:data-engineering`, ENTONCES `scripts/sdd_pack_registry.py` deberá abortar la validación en modo *fail-closed* con un error descriptivo; y CUANDO el usuario ejecute el wizard `sdd-bootstrap`, los catálogos `.sdd/catalog/bootstrap-references/{question-catalog-es,question-catalog-en,stack-config-and-pruning}.md` deberán presentar preguntas equivalentes ES/EN para los nuevos packs podando automáticamente las opciones incompatibles con la topología elegida.
- `RF-2008` (**Atribución Legal Upstream 1:1 y Aislamiento frente a `sdd_catalog_import.py`**): Cada `pack.json` de los `6` packs nuevos y `2` packs ampliados deberá declarar metadatos `upstream` válidos con licencias permisivas (`MIT` o `Apache-2.0`) reflejados con correspondencia 1:1 en `.sdd/catalog/UPSTREAM.md` y `THIRD_PARTY_NOTICES.md`, y CUANDO se ejecute `scripts/sdd_catalog_import.py`, el importador deberá preservar intactos los directorios de los `6` packs no pertenecientes a `STACK_PACKS`.
- `RF-2009` (**Presupuesto de Contexto `< 25k`, Modularidad `<= 500L` y Verificación Integral CI**): MIENTRAS el repositorio starter permanezca en estado de plantilla base (`active_packs: []`), el conjunto de ficheros Markdown activos bajo `.agents/` deberá mantenerse estrictamente por debajo de `25k` tokens estimados, todos los ficheros `.py` en `scripts/`, `.agents/scripts/` y `tests/` deberán cumplir `<= 500` líneas sin dependencias externas ni `shell=True`, y `./sdd ci-verify` deberá concluir en `PASS`.

## 3. Criterios de Aceptación (BDD / Given-When-Then)

1. **Escenario `CA-2001` (Presencia, compacidad y carga bajo demanda de `sdd-security-audit`):**
   - **Dado** el directorio `.agents/skills/sdd-security-audit/` en la plantilla base del starter
   - **Cuando** se auditan `SKILL.md`, `references/stride-threat-model.md`, `references/owasp-asvs-checklist.md`, `.agents/skills/pipeline-run/SKILL.md` y `.agents/rules/05-security-and-secrets.md`
   - **Entonces** `SKILL.md` contiene frontmatter YAML válido, tiene `<= 45` líneas, referencia ambos documentos bajo demanda para `Gate 2` (STRIDE) y `Gate 4` (OWASP/ASVS, IDOR, secretos, SCA/SBOM, PII), y `pipeline-run` / `05-security-and-secrets.md` la invocan explícitamente.
2. **Escenario `CA-2002` (Upgrade `L3 -> L4` de las 4 skills Core sin inflación de `SKILL.md`):**
   - **Dado** el conjunto `.agents/skills/{sdd-silent-failure-audit,sdd-test-quality-audit,sdd-execution-guardrails,search-first}/`
   - **Cuando** se inspeccionan sus `SKILL.md` y subcarpetas `references/`
   - **Entonces** cada `SKILL.md` tiene `<= 35` líneas y enlaza al menos un documento no vacío en `references/` con cobertura verificable políglota (Go/Rust/Java/SQL/colas), anti-mocking/mutación, worktrees Windows/POSIX y evaluación de paquetes.
3. **Escenario `CA-2003` (Cero referencias huérfanas ECC en los 25 packs y fallo determinista ante regresión):**
   - **Dado** el árbol completo `.sdd/catalog/packs/` (19 packs existentes saneados + 6 packs nuevos)
   - **Cuando** se ejecuta el test anti-referencias huérfanas en `tests/test_sdd_governance.py` (tanto sobre el catálogo real como sobre una fixture temporal que inyecta `rules/ecc/foo.md`, el agente inexistente `code-reviewer` o la skill inexistente `backend-patterns`)
   - **Entonces** pasa en verde sobre `.sdd/catalog/packs/` con `0` enlaces, agentes o skills huérfanas y falla de forma determinista sobre la fixture corrupta.
4. **Escenario `CA-2004` (Materialización limpia de `capability-event-driven` y `capability-api-governance`):**
   - **Dado** un repositorio temporal con `Gate S0` aprobado y `packs: ["capability:event-driven", "capability:api-governance"]`
   - **Cuando** se ejecuta `sdd_agent_generator.py --materialize`
   - **Entonces** se materializan las `6` skills (`kafka-streaming-patterns`, `async-messaging-patterns`, `microservices-boundaries`, `openapi-contract-governance`, `grpc-protobuf-patterns`, `asyncapi-event-contracts`) en `.agents/skills/` registradas con hash SHA-256 en `squad.lock.json` y `0` reglas *always-on* añadidas.
5. **Escenario `CA-2005` (Resolución de `requires` y materialización en `framework-nextjs`, `framework-nestjs`, `capability-iac-cloud` y `capability-data-engineering`):**
   - **Dado** un repositorio temporal con `Gate S0` aprobado
   - **Cuando** se intenta validar `framework:nextjs` sin `lang:typescript` o `framework:react` (o `framework:nestjs` sin `lang:typescript`), y posteriormente se materializa con sus dependencias completas junto a `capability:iac-cloud` y `capability:data-engineering`
   - **Entonces** el caso incompleto falla en modo *fail-closed* indicando la dependencia `requires` ausente, y el caso completo materializa las `8` skills correspondientes sin colisiones de rutas.
6. **Escenario `CA-2006` (Ampliación sin regresiones de `capability-devops` y `capability-database`):**
   - **Dado** un repositorio temporal con `packs: ["capability:devops", "capability:database"]` y `Gate S0` aprobado
   - **Cuando** se ejecuta `sdd_agent_generator.py --materialize` y luego `--verify`
   - **Entonces** se materializan las `5` skills de `capability-devops` (incluida `helm-gitops-patterns`) y las `7` skills de `capability-database` (incluida `multi-tenant-isolation`), pasando `--verify` con código `0`.
7. **Escenario `CA-2007` (Bloqueo *fail-closed* de presets incompatibles y paridad ES/EN en `bootstrap-references`):**
   - **Dado** un `STACK.md` `api-only` que incluye `framework:nextjs` y otro `spa-only` que incluye `framework:nestjs`, `capability:event-driven` o `capability:data-engineering`
   - **Cuando** `sdd_pack_registry.py` valida ambos `STACK.md` y se auditan `question-catalog-es.md`, `question-catalog-en.md` y `stack-config-and-pruning.md`
   - **Entonces** `sdd_pack_registry.py` rechaza todas las combinaciones prohibidas con `StackConfigError`, y los tres documentos de `bootstrap-references/` mantienen simetría bilingüe ES/EN y reglas explícitas de poda.
8. **Escenario `CA-2008` (Trazabilidad 1:1 de licencias upstream y preservación ante `sdd_catalog_import.py`):**
   - **Dado** el conjunto de `25` `pack.json` en `.sdd/catalog/packs/`, `.sdd/catalog/UPSTREAM.md` y `THIRD_PARTY_NOTICES.md`
   - **Cuando** se valida la correspondencia de campos `upstream` y se ejecuta una importación simulada offline de `sdd_catalog_import.py`
   - **Entonces** todos los orígenes declarados constan con licencia permisiva (`MIT` / `Apache-2.0`) en `UPSTREAM.md` y `THIRD_PARTY_NOTICES.md`, y los `6` packs no-ECC permanecen intactos tras la importación simulada.
9. **Escenario `CA-2009` (Cumplimiento de `< 25k` tokens en `.agents/`, `<= 500L` en `.py` y `ci-verify` en `PASS`):**
   - **Dado** el repositorio starter en estado base (`active_packs: []`) tras integrar `FWK-020`
   - **Cuando** se ejecutan `tests/test_sdd_governance.py`, `tests/test_sdd_sync_and_modularity.py` y `uv run python scripts/sdd_cli.py ci-verify --mode framework`
   - **Entonces** el presupuesto estimado de `.agents/` es `< 25k` tokens (`15` skills Core activas), `0` archivos `.py` superan `500` líneas y `ci-verify` finaliza en `PASS`.

## 4. Aprobación Formal Gate 1 (`RN-SDD-HUMAN-GATE-OWNERSHIP`)
- [x] **Gate 1 Approved (Human Sign-off):** Revisado y validado por Stakeholder Humano (`2026-11-24T13:45:43+01:00` — `"Aprobado Gate 1"`; precisión factual `RF-2003`/`CA-2003` autorizada en `2026-11-24T15:26:19+01:00` — `"Si autorizo"`).

<!-- sdd:gate-seal gate=1 sha256=f99e58c3c2cb6bc037c56a5c242b3411f00befb55b866aaa7ee539113b280192 -->
