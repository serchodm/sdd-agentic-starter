# Tech Spec: Gobernanza Core (`sdd-security-audit` + `references/` L4), Saneamiento ECC y Expansión de Packs Enterprise (`FWK-020`)

- **ID:** `FWK-020-skills-governance-and-enterprise-packs`
- **RFC:** [`RFC-010`](../../rfcs/RFC-010-skills-governance-and-enterprise-packs.md) (`Aceptado`)
- **Versión objetivo:** `v1.5.0` *(SemVer MINOR — 100% retrocompatible con `v1.x`)*
- **Estado:** `Approved`
- **Especificación Funcional:** [`01-spec.md`](01-spec.md) (`Gate 1 Approved`)
- **Sub-Gate 2V (Visual):** `N/A` *(sin pantallas `SCR-###`)*
- **Gate 2 Sign-off:** `[x] Gate 2 Approved (Authorized by PO on 2026-11-24T16:09:11+01:00 — "Aprobada. A por 03-tasks.md")`

## 1. Arquitectura General, Presupuesto de Contexto e Invariantes (`RF-2009`)

### 1.1. Evolución del Inventario y *Zero Default Bloat*
- **Core (`.agents/skills/`):** pasa de `14` a `15` skills activas por defecto (`+1` nueva `sdd-security-audit`; `4` skills Core elevadas de `L3` a `L4` mediante subcarpetas `references/` de carga bajo demanda).
- **Catálogo *Opt-in* (`.sdd/catalog/packs/`):** pasa de `19` a `25` packs (`+6` packs nuevos y `2` packs existentes ampliados; `70 -> 86` skills de catálogo).
- **Total del starter:** `84 -> 101` skills, conservando `active_packs: []` en `.agents/squad.lock.json` (`schema_version: 2`) en la plantilla base (`solo 15 skills Core activas`).
- **Sincronización (`scripts/sdd_sync.py`):** no requiere cambios de código; `is_syncable_framework_file()` ya sincroniza recursivamente `.sdd/catalog/**` y `.agents/skills/**` (incluidos `references/*.md`), excluyendo automáticamente las rutas gestionadas en `squad.lock.json["files"]`.

### 1.2. Contrato de Presupuesto de Contexto (`< 25k` Activo + Techo Lazy `references/`)
- **Estado base medido en disco:** `.agents/` acumula `88,502` caracteres en ficheros activos (`~22.1k` tokens estimados a `4 chars/token`) más `8,235` caracteres en `.agents/skills/santa-method/references/*.md` (`96,737` caracteres totales).
- **Separación formal Activo vs. Bajo Demanda (`AMB-002`, `RF-2009`):**
  1. **Contexto Activo (`"references" not in p.parts`):** todos los `.md`, `.json`, `.yaml` y `.yml` bajo `.agents/` fuera de subdirectorios `references/` deben mantenerse estrictamente **`< 100,000` bytes / `< 25,000` tokens estimados**. Con `sdd-security-audit/SKILL.md` (`<= 45L`, `~1.8k` chars) y ajustes mínimos en las 4 `SKILL.md` (`<= 35L`), `pipeline-run/SKILL.md` y `05-security-and-secrets.md`, el contexto activo quedará en `~90.8k` caracteres (`~22.7k` tokens).
  2. **Referencias Bajo Demanda (`"references" in p.parts`):** los playbooks en `.agents/skills/*/references/*.md` tienen coste `0` en reposo y quedan gobernados por un techo independiente **`< 60,000` bytes / `< 15,000` tokens estimados**.
  3. **Alineación de Suites Existentes:** en `T-14` se aplica `if "references" not in p.parts` sobre el cómputo base de `md_bytes` / `total_chars` en `tests/test_sdd_{release,brownfield,drift,portfolio}.py` (cubriendo tanto `< 100_000` bytes como `< 25_000` tokens) y se añade la doble aserción (`activo < 25k` y `references < 15k`) en `tests/test_sdd_governance.py`.

### 1.3. Invariantes de Modularidad y Seguridad
- **Techo estricto `<= 500` líneas por `.py`:** obligatorio sin excepciones en `scripts/`, `.agents/scripts/` y `tests/` (`test_sdd_sync_and_modularity.py`).
- **Stdlib-only & *Fail-Closed*:** Python `>= 3.12` (`dependencies = []`), prohibido `shell=True`, preservando validación anti-symlinks/junctions y contención `Path.resolve().is_relative_to(...)`.

---

## 2. Gobernanza Core (`T-01`, `T-02`) y Saneamiento ECC (`T-03`)

### 2.1. Nueva Skill Core `sdd-security-audit` (`RF-2001`, `CA-2001`)
- **Ruta y estructura:**
  - `.agents/skills/sdd-security-audit/SKILL.md` (`<= 45` líneas; frontmatter YAML `name: sdd-security-audit`, `description: ...`).
  - `.agents/skills/sdd-security-audit/references/stride-threat-model.md` (`70–110` líneas).
  - `.agents/skills/sdd-security-audit/references/owasp-asvs-checklist.md` (`80–120` líneas).
- **Diseño funcional y fronteras sin duplicación:**
  - **En `Gate 2` (`02-tech-spec.md`):** exige cargar `references/stride-threat-model.md` cuando el Work Item toque AuthN/AuthZ, multi-tenancy, pagos, webhooks, subida de ficheros, secretos/KMS o PII, documentando fronteras de confianza y mitigaciones *fail-closed* por categoría **STRIDE** (*Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege*).
  - **En `Gate 4` (Capa 1 + `@security-reviewer`):** exige cargar `references/owasp-asvs-checklist.md` para auditar OWASP Top 10 / ASVS v4+ (BOLA/IDOR y autorización por objeto/tenant, validación estricta en frontera productora, parametrización SQL/NoSQL/OS, prevención SSRF/XXE/XSS/CSRF, higiene de secretos, SCA/SBOM sobre dependencias aprobadas en `STACK.md` y ausencia de PII/credenciales en logs y errores).
  - **Coordinación:** referencia `.agents/rules/05-security-and-secrets.md` y el subagente `.agents/agents/security-reviewer.md` sin copiar sus tablas.
- **Enlaces en el flujo Core (`T-12`):**
  - `.agents/skills/pipeline-run/SKILL.md` (`<= 30L`): en `3. QA & Boundary Audit Block (Gate 4 — Layer 1)` añade `sdd-security-audit` junto a `sdd-spec-compliance-audit`, `sdd-silent-failure-audit` y `sdd-test-quality-audit`.
  - `.agents/rules/05-security-and-secrets.md` (`<= 20L`): añade `## 4. Auditoría Transversal por Gate` enlazando `.agents/skills/sdd-security-audit/SKILL.md` para `Gate 2` (STRIDE) y `Gate 4` (OWASP/ASVS).

### 2.2. Upgrade Modular `L3 -> L4` de 4 Skills Core (`RF-2002`, `CA-2002`)
Cada skill conserva su `SKILL.md` compacto (`<= 35` líneas) y añade una referencia bajo demanda (`65–115` líneas, `<= 6,500` caracteres c/u):

| Skill Core (`.agents/skills/<skill>/`) | Límite `SKILL.md` | Fichero Bajo Demanda en `references/` | Cobertura Técnica Obligatoria (`L4`) |
| :--- | :---: | :--- | :--- |
| `sdd-silent-failure-audit` | `<= 35L` | `references/polyglot-silent-failures.md` | Patrones prohibidos y remediación *fail-closed* en Python (`except: pass`, `contextlib.suppress` abusivo), TS/JS (`.catch(() => {})`, promesas flotantes), Go (`_ = err`), Rust (`let _ =`, `unwrap_or_default()` ocultando fallos IO), Java/Kotlin (`catch` vacío), SQL (transacciones sin rollback/check) y mensajería asíncrona (consumidores que hacen `ack` sin procesar ni enviar a DLQ). |
| `sdd-test-quality-audit` | `<= 35L` | `references/anti-mocking-and-mutation.md` | Tautologías de mocks (asertar solo `mock.assert_called` sin verificar estado/salida), frontera permitida de dobles (reloj/red/proveedor externo vs. prohibición de mockear dominio interno), determinismo ante flakiness/concurrencia/tiempo y protocolo de sondas de mutación por escenario `Given-When-Then`. |
| `sdd-execution-guardrails` | `<= 35L` | `references/worktree-lifecycle.md` | Ciclo de vida OS-agnóstico (Windows/Linux/macOS) de Git Worktrees bajo `.worktrees/` usando `sdd git worktree-create` / `worktree-remove`: aislamiento de puertos (`ports_registry.json`), copia segura desde `.env.example` (cero secretos reales), verificación baseline pre-edición, ejecución Python determinista (`uv run python` / `.venv` / `python3` / `py -3`) y poda limpia post-merge. |
| `search-first` | `<= 35L` | `references/reuse-vs-build-matrix.md` | Orden de consulta en `docs/knowledge/{SYSTEM_TOPOLOGY,API_CATALOG,DATA_MODELS,ADRS}.md` y código existente; matriz cuantitativa *Reutilizar -> Extender -> Adoptar librería aprobada -> Construir*; verificación de compatibilidad con `specs/STACK.md`, licencia permisiva, mantenimiento y superficie de dependencias (cero alucinación de paquetes). |

### 2.3. Saneamiento Exhaustivo de los 19 Packs Actuales (`RF-2003`, `CA-2003`, `T-03`)
El criterio de cierre exacto de `T-03` es alcanzar **`0` hallazgos** de `audit_catalog_pack_references()` (§5.2, Reglas `R0`–`R4`) sobre los `19` packs existentes (`~84` ficheros Markdown fuera de `capability-ui-design/vendor/ui-ux-pro-max/`, que permanece intacto bajo `VENDOR.lock.json`):
1. **Reparación de cercas Markdown corruptas (`R0`, `5` ficheros):** convertir a cercas externas de 4 backticks (` ````text ... ```` `) las cercas ` ```text ` que anidan bloques ` ```<lang> ` internos en `lang-cpp/workflows/{cpp-build,cpp-review}.md`, `lang-go/workflows/{go-build,go-review}.md` y `lang-python/workflows/python-review.md`.
2. **Rutas heredadas prohibidas (`R1`, `~34` ocurrencias):**
   - Sustituir `rules/ecc/...`, `commands/ecc/...`, `agents/ecc/...` y rutas no prefijadas `rules/<dir>/<file>` en prosa/workflows (p. ej. `typescript-patterns/SKILL.md`, `lang-dart/{skills/dart-flutter-patterns/SKILL.md,workflows/flutter-review.md,workflows/flutter-test.md}`) por rutas canónicas materializadas en código `` `.agents/pack-rules/<pack>/<file>` `` o `.agents/rules/07-engineering-baseline.md`.
   - Sustituir `~/.claude/...` y `.claude/...` (`canary-watch/SKILL.md`, `lang-{csharp,go,java,kotlin,python,typescript}/rules/hooks.md`, `motion-foundations/SKILL.md`, `prompt-optimizer/SKILL.md`) por `.agents/hooks.json` o rutas locales del workspace (`.agents/logs/`).
3. **Enlaces Markdown relativos (`R2`, `~82` ocurrencias — Validez Dual Catálogo + Materializado):**
   - Dado que `sdd_agent_generator.py` materializa `skills/` en `.agents/skills/<slug>/`, `rules/` en `.agents/pack-rules/<pack>/`, `agents/` en `.agents/agents/` y `workflows/` en `.agents/workflows/`, **queda prohibido usar hipervínculos Markdown relativos entre carpetas distintas de un pack** (como `../common/*.md`, `../typescript/*.md`, `../../rules/*`, `../accessibility/SKILL.md`, `../frontend-patterns/SKILL.md`, `../seo/SKILL.md`, `../e2e-testing/SKILL.md`, `../angular-developer/SKILL.md`, `../nextjs-turbopack/SKILL.md`, `../tdd-workflow/SKILL.md`, `../../docs/*`, `../../hooks/README.md`). Todos ellos se convierten a referencias textuales en código (`` `.agents/pack-rules/<pack>/<rule>.md` ``, `` `.agents/rules/07-engineering-baseline.md` ``, `` `.agents/rules/05-security-and-secrets.md` `` o `` `docs/standards/FUNCTIONAL_DOCUMENTATION_STANDARD.md` `` en `sdd-ui-design/SKILL.md` preservando todos los literales de `tests/test_sdd_ui_design.py` `Group 6`). Solo se admiten hipervínculos relativos dentro del mismo directorio de skill (p. ej. `[references/...](references/...)`).
4. **Agentes y skills ECC huérfanos en prosa, listas y tablas (`R3` y `R4`):**
   - **Agentes inexistentes (`R3`):** sustituir `code-reviewer` (`mle-workflow`, `prompt-optimizer`), `planner` (`prompt-optimizer`), `typescript-build-resolver` (`react-build-resolver.md`) y cualquier mención `agent:` / tabla de agentes no registrada por equivalentes SDD reales (`@qa-tester`, `@architect`, `build-error-resolver`, `typescript-reviewer` o `santa-method`). *(En `postgres-patterns/SKILL.md`, `database-reviewer` se mantiene como especialista válido de `capability:database`, complementando a `@back-engineer` y `@db-specialist`).*
   - **Skills inexistentes (`R4`):** sustituir o limpiar todas las referencias huérfanas en prefijos `Skill:`/`skill:`/`Skills:`, rutas `skills/<slug>`, patrones `` `<slug>` skill `` / `` skill `<slug>` `` y listas `## Related` / `## Related Skills`, incluyendo `backend-patterns` (`postgres`/`mysql`/`redis`/`prisma-patterns`, `typescript-patterns`, `vite-patterns`, `vue-patterns`, `mle-workflow`), `security-review` / `security-scan` (`mysql-patterns`, `kubernetes-patterns`, `fastapi-review.md`, `lang-{csharp,java,typescript}`), `git-workflow` (`kubernetes-patterns`), `tdd-workflow` / `e2e-testing` / `verification-loop` / `continuous-learning` (workflows y rules de `framework-react`, `lang-{cpp,dart,go,kotlin,python,rust}`, `capability-ai-llm/{mle-workflow,prompt-optimizer,iterative-retrieval,eval-harness}`), `seo` (`seo-specialist.md`), `quarkus-*` (`lang-java/{agents,rules}`) y `android-clean-architecture` / `compose-multiplatform-patterns` (`lang-kotlin`), mapeándolas a skills reales del starter (`sdd-security-audit`, `sdd-test-quality-audit`, `continuous-learning-v2`, `database-migrations`, `prisma-patterns`, `accessibility`, etc.) o descripciones conceptuales sin identificadores fantasma.

---

## 3. Especificación de Packs Enterprise Nuevos y Ampliados (`RF-2004`..`RF-2006`)

### 3.1. Esquema Uniforme de `pack.json` y `upstream` (`T-04`..`T-11`)
Todos los manifiestos cumplen `load_pack_manifest()` (`scripts/sdd_pack_registry.py`): `rules: []`, `workflows: []`, `specialists: []` (salvo `capability-database`, que conserva `["agents/database-reviewer.md"]`), sin `vendor_lock`. El objeto `upstream` sigue un esquema JSON uniforme:
`{"repo": "<owner/repo>", "license": "<MIT|Apache-2.0>", "references": ["<owner/repo> (<MIT|Apache-2.0>)", ...]}` (donde `references` es `list[str]` opcional):

| Directorio (`.sdd/catalog/packs/`) | `id` | `family` | `requires` | `targets` | `skills` Declaradas | `upstream.repo` (`license`) y `upstream.references` |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `capability-event-driven` *(Nuevo, `T-04`)* | `capability:event-driven` | `capability` | `[]` | `["api", "backend", "server", "microservice"]` | `skills/kafka-streaming-patterns`, `skills/async-messaging-patterns`, `skills/microservices-boundaries` | `repo`: `confluentinc/agent-skills` (`Apache-2.0`)<br>`references`: `["lensesio/agentic-engineering-for-apache-kafka (Apache-2.0)", "wshobson/agents (MIT)"]` |
| `capability-api-governance` *(Nuevo, `T-05`)* | `capability:api-governance` | `capability` | `[]` | `["all"]` | `skills/openapi-contract-governance`, `skills/grpc-protobuf-patterns`, `skills/asyncapi-event-contracts` | `repo`: `bufbuild/claude-plugins` (`Apache-2.0`)<br>`references`: `["speakeasy-api/sdk-generation-skills (Apache-2.0)", "asyncapi/spec (Apache-2.0)"]` |
| `capability-iac-cloud` *(Nuevo, `T-06`)* | `capability:iac-cloud` | `capability` | `[]` | `["all"]` | `skills/terraform-opentofu-patterns`, `skills/cloud-iam-security`, `skills/cloud-finops-guardrails` | `repo`: `antonbabenko/terraform-skill` (`Apache-2.0`)<br>`references`: `["BagelHole/DevOps-Security-Agent-Skills (MIT)", "trailofbits/skills (Apache-2.0)"]` |
| `capability-devops` *(Ampliado, `T-07`)* | `capability:devops` | `capability` | `[]` | *(sin campo: `()`)* | Existentes (`4`) + `skills/helm-gitops-patterns` (`5` total) | `repo`: `affaan-m/ecc` (`MIT`, copyright preservado)<br>`references`: `["wshobson/agents (MIT)"]` |
| `framework-nextjs` *(Nuevo, `T-08`)* | `framework:nextjs` | `framework` | `["lang:typescript", "framework:react"]` | `["web"]` | `skills/nextjs-patterns` | `repo`: `vercel-labs/agent-skills` (`MIT`)<br>`references`: `[]` |
| `framework-nestjs` *(Nuevo, `T-09`)* | `framework:nestjs` | `framework` | `["lang:typescript"]` | `["api", "backend", "server"]` | `skills/nestjs-patterns` | `repo`: `nestjs/agent-skills` (`MIT`)<br>`references`: `["Kadajett/agent-nestjs-skills (MIT)"]` |
| `capability-data-engineering` *(Nuevo, `T-10`)* | `capability:data-engineering` | `capability` | `[]` | `["api", "backend", "database", "db"]` | `skills/dbt-modeling-patterns`, `skills/airflow-dag-patterns`, `skills/data-quality-governance` | `repo`: `dbt-labs/dbt-agent-skills` (`Apache-2.0`)<br>`references`: `["GoogleCloudPlatform/data-agent-kit-plugin (Apache-2.0)", "wshobson/agents (MIT)"]` |
| `capability-database` *(Ampliado, `T-11`)* | `capability:database` | `capability` | `[]` | *(sin campo: `()`)* | Existentes (`6`) + `skills/multi-tenant-isolation` (`7` total) | `repo`: `affaan-m/ecc` (`MIT`, copyright preservado)<br>`references`: `["supabase/agent-skills (MIT)", "agamm/claude-code-owasp (MIT)"]` |

> **Nota sobre `targets` en `framework-nestjs`:** el rol backend/worker descrito en `RFC-010 §2.2` se codifica como `["api", "backend", "server"]` para intersectar exactamente con `_PRESET_IMPLIED_TARGETS` de `scripts/sdd_pack_registry.py` (`compact`, `granular`, `api-only`) y rechazar `spa-only`.

### 3.2. Estándar Estructural y Alcance de las 16 Nuevas Skills (`L4`, `150–320L` c/u)
Toda nueva `SKILL.md` de catálogo incluye frontmatter YAML válido (`name`, `description`), cumple las Reglas `R0`–`R4` de §5.2 (`0` hallazgos) y desarrolla 5 secciones canónicas: *(1) When to Activate*, *(2) Production Architecture & Patterns*, *(3) SDD Gate 2 & Gate 4 Contract Alignment*, *(4) Anti-Patterns & Fail-Closed Guards*, *(5) Deterministic Verification Commands*:

- **`capability-event-driven` (`T-04`):**
  1. `kafka-streaming-patterns`: diseño de tópicos/particiones por clave de ordenación, productores idempotentes (`acks=all`, `enable.idempotence=true`), consumer groups, control de *consumer lag*, poison pills -> DLQ, Schema Registry y CDC (Debezium).
  2. `async-messaging-patterns`: *Transactional Outbox*, *Inbox / Idempotency Key* con TTL/tabla única, Sagas (coreografía vs. orquestación con compensaciones explícitas), backoff exponencial con jitter y DLQ obligatoria en RabbitMQ/SQS/SNS/NATS/Redis Streams.
  3. `microservices-boundaries`: *Bounded Contexts* (DDD), matriz Sync (REST/gRPC) vs. Async (eventos), prohibición de compartir tablas entre servicios (`verify_architecture_boundaries.py`), *circuit breaker*, *bulkhead*, *timeouts* explícitos y propagación de `traceparent`/`correlation-id`.
- **`capability-api-governance` (`T-05`):**
  4. `openapi-contract-governance`: diseño *Contract-First* OpenAPI 3.1, versionado explícito, evolución retrocompatible, detección de *breaking changes* (`oasdiff`), paginación por cursor, errores RFC 9457 (`Problem Details`), seguridad OAuth2/JWT y sincronía con `docs/knowledge/API_CATALOG.md` + `santa-method` (`backward-compatibility`).
  5. `grpc-protobuf-patterns`: esquemas `.proto` (proto3/editions), linting y *breaking-change detection* con `buf` (`buf lint`, `buf breaking`), reserva de tags/nombres eliminados (`reserved`), *deadlines* obligatorios, códigos gRPC canónicos y streaming backpressure.
  6. `asyncapi-event-contracts`: contratos de eventos AsyncAPI 3.0, envoltura CloudEvents (`event_id`, `occurred_at`, `schema_version`, `tenant_id`), modos de compatibilidad (`BACKWARD`, `FULL`) en Avro/Protobuf/JSON Schema y trazabilidad en `02-tech-spec.md`.
- **`capability-iac-cloud` (`T-06`):**
  7. `terraform-opentofu-patterns`: módulos HCL componibles, *remote state* cifrado con locking, bloques `moved`/`import` sin recreación destructiva, `terraform validate` / `tofu test` / TFLint, escaneo Checkov/Trivy y paridad multi-cloud (AWS/GCP/Azure) Terraform <-> OpenTofu.
  8. `cloud-iam-security`: mínimo privilegio estricto (bloqueo de `Action: "*"` / `Resource: "*"` injustificados), federación OIDC sin claves estáticas en CI/CD, segmentación VPC/subredes privadas, cifrado KMS y gestores de secretos alineados con `05-security-and-secrets.md`.
  9. `cloud-finops-guardrails`: etiquetas obligatorias (`env`, `service`, `owner`, `cost-center`), alertas y presupuestos pre-aprovisionamiento, *rightsizing*, ciclo de vida/retención de logs/snapshots/buckets y control de costes ocultos (NAT Gateways, egress inter-AZ, loops serverless).
- **`capability-devops` Ampliación (`T-07`):**
  10. `helm-gitops-patterns`: charts Helm (`values.schema.json`, plantillas deterministas, `helm lint`/`helm template`), Kustomize bases/overlays, reconciliación GitOps con ArgoCD/Flux, detección de *drift*, External Secrets / SOPS y vínculo con `gate6-release.md`.
- **`framework-nextjs` (`T-08`):**
  11. `nextjs-patterns`: Next.js App Router (15+), frontera Server Components vs. Client Components (`"use client"` mínimo), Server Actions con validación Zod y AuthZ *fail-closed* por invocación, directivas de caché (`use cache` / `revalidateTag`), Partial Prerendering, `middleware.ts` ligero y protección `server-only`.
- **`framework-nestjs` (`T-09`):**
  12. `nestjs-patterns`: módulos por dominio en NestJS, DI sin ciclos (`forwardRef` como code smell), validación con Zod o `class-validator` (`whitelist: true`, `forbidNonWhitelisted: true`), orden Guards -> Interceptors -> Pipes -> Exception Filters, graceful shutdown y tests con `TestingModule` + Prisma/Drizzle/TypeORM.
- **`capability-data-engineering` (`T-10`):**
  13. `dbt-modeling-patterns`: capas `staging -> intermediate -> marts`, modelos incrementales idempotentes (`merge`, `insert_overwrite`, `unique_key`), uso estricto de `source()` y `ref()`, `model contracts` (`contract: { enforced: true }`), tests SQL y capa semántica.
  14. `airflow-dag-patterns`: TaskFlow API (decoradores `@dag` y `@task`), prohibición de I/O o red en *top-level DAG parse time*, tareas idempotentes para *backfill* (`logical_date` / data interval), sensores *deferrable*, gestión segura de Connections/Variables y tests de carga sin ciclos.
  15. `data-quality-governance`: contratos productor-consumidor de datos, SLAs de frescura/completitud/volumen/unicidad (dbt tests, Soda, Great Expectations), linaje columna a columna, evolución segura de esquemas analíticos y anonimización/tokenización de PII conforme a `DATA_MODELS.md`.
- **`capability-database` Ampliación (`T-11`):**
  16. `multi-tenant-isolation`: propagación inmutable de `tenant_id` extremo a extremo (JWT/cabecera validada -> contexto de request -> consultas SQL/ORM -> mensajes/jobs -> prefijos Redis y rutas S3), políticas PostgreSQL RLS (`ENABLE` + `FORCE ROW LEVEL SECURITY` con `current_setting('app.current_tenant', true)`), uso de `SET LOCAL` en pools de conexiones y batería obligatoria de tests negativos cruzados (*Tenant A nunca lee/muta datos de Tenant B*).

---

## 4. Integración en Registry, Importer, Bootstrap y Atribución (`RF-2007`, `RF-2008`, `T-12`, `T-13`)

### 4.1. `scripts/sdd_pack_registry.py` (`347L -> ~360L <= 500L`)
Actualizar las constantes *fail-closed* de incompatibilidad de presets (que disparan `PackCompatibilityError`, subclase de `StackConfigError`, en `validate_pack_preset_compatibility()`):
- `_API_FORBIDDEN_PACKS`: añadir `"framework-nextjs"` y `"framework:nextjs"`.
- `_SPA_FORBIDDEN_PACKS`: añadir `"framework-nestjs"`, `"framework:nestjs"`, `"capability-event-driven"`, `"capability:event-driven"`, `"capability-data-engineering"` y `"capability:data-engineering"`.

### 4.2. `scripts/sdd_catalog_import.py` (`480L -> ~498L <= 500L`)
- `STACK_PACKS` (`18` packs ECC) permanece inalterado: `import_packs()` ignora cualquier directorio fuera de `STACK_PACKS`, preservando byte a byte los `6` packs nuevos no-ECC.
- **Preservación *Fail-Closed* de extensiones SDD en packs ECC (`capability-devops`, `capability-database`):** `sdd_catalog_import.py` es una utilidad manual de mantenimiento. Cuando `import_packs()` procese un `pack_dir` donde `(pack_dir / "pack.json").exists()`, leerá y validará dicho JSON en modo **estrictamente *fail-closed***:
  1. Si ocurre `OSError`, `UnicodeDecodeError` o `json.JSONDecodeError`, o si la raíz no es `dict`, o `skills` no es `list` de `str` no vacíos, o `upstream` (cuando exista) no es `dict`, o `upstream.get("references")` (cuando exista) no es `list` de `str` no vacíos, abortará inmediatamente lanzando `ValueError`.
  2. Inicializará `manifest["skills"] = list(meta["skills"])` (sin mutar `STACK_PACKS`). Para cada entrada `s` en `prev["skills"]` fuera de `meta["skills"]`, validará contención estricta (`pack_root = pack_dir.resolve()`, `cand = (pack_root / s).resolve()`, exigiendo `cand != pack_root`, `cand.is_relative_to(pack_root)` y ausencia de symlinks con `ValueError`); si `(cand / "SKILL.md").is_file()`, añadirá `s` al final de `manifest["skills"]`. De forma independiente, si `prev.get("upstream", {}).get("references")` existe, la conservará en `manifest["upstream"]["references"]`.

### 4.3. `.sdd/catalog/bootstrap-references/` (Simetría ES-ES / EN-GB y Poda)
- `question-catalog-es.md` y `question-catalog-en.md`:
  - **Ronda 1:** añadir pregunta de **Aprovisionamiento IaC, Cloud & GitOps** (`Terraform / OpenTofu + IAM/FinOps` -> `capability-iac-cloud`; `Kubernetes + Helm / ArgoCD / Flux` -> `capability-devops`; `Sin IaC declarativo`).
  - **Ronda 2:** explicitar en Backend `TypeScript / Node.js 22 con NestJS` (`lang-typescript` + `framework-nestjs`); explicitar en Frontend `Next.js (App Router + RSC)` (`lang-typescript` + `framework-react` + `framework-nextjs`); ampliar **Sincronización de Contratos y Gobierno de APIs** (`OpenAPI 3.1 / gRPC Buf / AsyncAPI 3.0` -> `capability-api-governance`); añadir **Arquitectura Event-Driven y Mensajería Asíncrona** *(Omitida si es Solo Frontend / CLI local)* (`Kafka / RabbitMQ / SQS / NATS + Outbox/Sagas` -> `capability-event-driven` | `N/A — Comunicación síncrona únicamente`).
  - **Ronda 3:** añadir **Aislamiento Multi-Tenant** *(Omitida si es Stateless / CLI)* (`Multi-tenant estricto con RLS / tenant_id` -> `capability-database` con `multi-tenant-isolation` | `Single-tenant`) e **Ingeniería de Datos y Pipelines Analíticos** *(Omitida si es Solo Frontend)* (`dbt / Airflow / Contratos de Calidad` -> `capability-data-engineering` | `N/A`).
- `stack-config-and-pruning.md`:
  - Documentar en **Dynamic Tree Pruning Rules** la omisión automática de `framework-nextjs` en `Solo Backend / API Only` y `CLI`, y la omisión de `framework-nestjs`, `capability-event-driven` y `capability-data-engineering` en `Solo Frontend / Client Only`, más tabla de mapeo respuesta -> IDs `packs` (incluyendo dependencias transitivas `requires`).

### 4.4. `.sdd/catalog/UPSTREAM.md` y `THIRD_PARTY_NOTICES.md` (`T-13`, Paridad 1:1 Total)
Tanto `.sdd/catalog/UPSTREAM.md` (tabla maestra de los `25` packs) como `THIRD_PARTY_NOTICES.md` documentarán con correspondencia **1:1 exacta** el `100%` de los repositorios declarados en `upstream.repo` y `upstream.references` de los `25` `pack.json` del catálogo (además de los referentes Core):
- **Orígenes de packs previos:** `affaan-m/ecc` (`MIT`) y `nextlevelbuilder/ui-ux-pro-max-skill` (`MIT`, `capability-ui-design`).
- **Orígenes de los 6 packs nuevos, 2 ampliados y Core (`MIT` / `Apache-2.0`):** `confluentinc/agent-skills` (`Apache-2.0`), `lensesio/agentic-engineering-for-apache-kafka` (`Apache-2.0`), `wshobson/agents` (`MIT`), `bufbuild/claude-plugins` (`Apache-2.0`), `speakeasy-api/sdk-generation-skills` (`Apache-2.0`), `asyncapi/spec` (`Apache-2.0`), `antonbabenko/terraform-skill` (`Apache-2.0`), `BagelHole/DevOps-Security-Agent-Skills` (`MIT`), `trailofbits/skills` (`Apache-2.0`), `vercel-labs/agent-skills` (`MIT`), `nestjs/agent-skills` (`MIT`), `Kadajett/agent-nestjs-skills` (`MIT`), `dbt-labs/dbt-agent-skills` (`Apache-2.0`), `GoogleCloudPlatform/data-agent-kit-plugin` (`Apache-2.0`), `supabase/agent-skills` (`MIT`), `agamm/claude-code-owasp` (`MIT`) y `obra/superpowers` (`MIT`).

---

## 5. Diseño de Pruebas Automatizadas y Guardián de Gobernanza (`T-14`, `<= 500L`)

Para cumplir estrictamente el techo `<= 500` líneas por módulo `.py`, `tests/test_sdd_pack_materialization.py` (`491L -> <= 497L`) añade la aserción global `len(registry) == 25` e incluye `tests/test_sdd_enterprise_packs.py` en la comprobación `<= 500L` (sin re-exportar clases para evitar doble ejecución en `unittest discover -s tests`), `tests/test_sdd_enterprise_packs.py` (`<= 380L`) aloja la suite enterprise completa, y `tests/test_sdd_governance.py` queda en `<= 495L`:

### 5.1. `tests/test_sdd_enterprise_packs.py` (módulo autodescubierto por `unittest` / `pytest`, `<= 380L`)
- **`CA-2004`:** materialización limpia de `capability:event-driven` y `capability:api-governance` (`6` skills en `.agents/skills/`, hashes SHA-256 en `squad.lock.json`, `0` reglas en `pack-rules`).
- **`CA-2005`:** fallo `PackDependencyError` cuando `framework:nextjs` omite `lang:typescript` o `framework:react`, y cuando `framework:nestjs` omite `lang:typescript`; materialización exitosa con dependencias completas junto a `capability:iac-cloud` y `capability:data-engineering` (`8` skills nuevas sin colisiones).
- **`CA-2006`:** materialización y `--verify` de `capability:devops` (`5` skills incluyendo `helm-gitops-patterns`) y `capability:database` (`7` skills incluyendo `multi-tenant-isolation`).
- **`CA-2007`:** fallo `PackCompatibilityError` (`isinstance(err, StackConfigError)`) en `api-only` + `framework:nextjs` y en `spa-only` + cualquiera de `{framework:nestjs, capability:event-driven, capability:data-engineering}`; verificación de paridad estructural ES/EN y reglas de poda en `.sdd/catalog/bootstrap-references/`.
- **`CA-2008`:** validación de inventario `25` packs (`86` skills de catálogo), esquema uniforme y licencias `MIT`/`Apache-2.0` en cada `pack.json["upstream"]`, presencia 1:1 de todos los `upstream.repo` y `upstream.references` de los `25` packs en `UPSTREAM.md` y `THIRD_PARTY_NOTICES.md`, simulación offline de `sdd_catalog_import.import_packs()` preservando los `6` packs no-ECC + las `2` skills SDD extra, y test negativo *fail-closed* ante un `pack.json` previo malformado o con ruta fuera de `pack_dir` (`ValueError`).

### 5.2. `tests/test_sdd_governance.py` (`382L -> <= 495L`) + Normalización en `tests/test_sdd_{release,brownfield,drift,portfolio}.py`
Función determinista `audit_catalog_pack_references(repo_root: Path, packs_dir: Path) -> list[str]`:
1. **Alcance y Regla R0 (Parser de Cercas *Fail-Closed*):** recorre `sorted(packs_dir.rglob("*.md"))` excluyendo `vendor/` (`if "vendor" in md.parts: continue`). Analiza cercas con `^([ \t]*)(`{3,}|~{3,})(.*)$` ignorando aperturas con backticks en el `info`-string (`not (ch == '`' and '`' in info)`). Mientras una cerca `(open_ch, open_len)` esté abierta: ignora cualquier línea con `ch != open_ch` o `len(fence) < open_len` (permitiendo bloques internos ` ```<lang> ` dentro de cercas externas ` ````text `); y únicamente cuando `ch == open_ch and len(fence) >= open_len`, cierra la cerca si `info.strip() == ""` o registra error determinista `R0` si `info.strip() != ""` (*apertura anidada de longitud `>= open_len` dentro de cerca sin cerrar*). Si llega a `EOF` con cerca abierta, registra error `R0`.
2. **Inventarios canónicos desde `repo_root` + `packs_dir`:**
   - `official_agents`: unión de stems en `repo_root/.agents/agents/*.md`, `repo_root/.sdd/catalog/{specialists,specialists-optin}/*.md`, `repo_root/.sdd/catalog/archetypes/*.md` (`name.removesuffix(".archetype.md").removesuffix(".md")`), nombres de builders en `scripts.sdd_agent_generator.PRESET_CONFIGS` (`{b["name"] for cfg in PRESET_CONFIGS.values() for b in cfg["builders"]}`), y `PurePosixPath(s).stem` de cada `specialists` en `packs_dir/*/pack.json`.
   - `official_skills`: unión de directorios en `repo_root/.agents/skills/*` y `PurePosixPath(s.rstrip("/")).name` de cada entrada `skills` en `packs_dir/*/pack.json`.
3. **Reglas Léxicas Deterministas `R1`–`R4` (sobre la prosa fuera de cercas):**
   - **Regla R1 (Rutas legacy prohibidas):** tras limpiar URLs `https?://\S+`, falla si aparece `(?:rules/ecc/|commands/ecc/|agents/ecc/|~/.claude/|(?:^|[\s(\[`])\.claude/|(?:^|[\s(\[`])rules/(?!0[0-7]-)[a-z0-9-]+/[a-z0-9_.*-]+)`.
   - **Regla R2 (Enlaces Markdown relativos intra-skill seguros):** tras limpiar spans inline `` `[^`\n]+` ``, para cada `[label](target)` cuyo `target` no empiece por `http://`, `https://`, `mailto:`, `file:` o `#`, extrae `rel = target.split("#", 1)[0].strip()`. Solo se permite cuando `md` reside bajo `packs/<pack>/skills/<slug>/` y `dest = (md.parent / rel).resolve()` existe en disco sin symlinks manteniendo `dest.is_relative_to(skill_dir.resolve())` (lo que garantiza validez idéntica antes y después de materializar `skills/<slug>/` aunque `active_packs == []`); cualquier otro enlace relativo (escapes fuera de `skills/<slug>/` o enlaces relativos en `rules/`, `agents/` o `workflows/`) falla determinísticamente `R2`.
   - **Regla R3 (Agentes huérfanos):** tras limpiar URLs `https?://\S+`, extrae candidatos mediante `(?:^|[\s(\[*])(?i:agents?:\s*)\`?(?:agents/)?([a-z0-9-]+)(?:\.md)?\`?`, `\b([a-z][a-z0-9-]+-(?:reviewer|resolver))\b`, `(?:^|[\s(\[`])@([a-z][a-z0-9-]+-(?:engineer|specialist|architect|analyst|tester|reviewer|resolver)|orchestrator|devops|documentator)\b`, y primera celda `` `([a-z][a-z0-9-]+)` `` en tablas bajo cabeceras `## Agents` / `### Agent`; falla si algún candidato (en minúsculas) no pertenece a `official_agents`.
   - **Regla R4 (Skills huérfanas):** tras limpiar URLs `https?://\S+`, extrae candidatos mediante `(?i:\bskills?:\s*)\`?(?:skills/)?([a-z0-9-]+)(?:/|/SKILL\.md)?\`?`, `(?:^|[\s(\[`])skills/([a-z0-9-]+)(?:/|\b)`, `` `([a-z][a-z0-9-]+)`\s+skill\b ``, `` \bskill\s+`([a-z][a-z0-9-]+)` `` y viñetas `` ^\s*[-*]\s+`([a-z][a-z0-9-]+)`\b `` dentro de secciones `## Related` / `## Related Skills` / `### Related Skills`; falla si algún candidato no pertenece a `official_skills` (ni a `official_agents` en secciones mixtas `## Related`).
4. **Tests añadidos en `TestSDDGovernance`:**
   - **`CA-2001` & `CA-2002`:** verifica `15` skills Core, `sdd-security-audit/SKILL.md <= 45L` + 2 `references/*.md` + enlaces en `pipeline-run/SKILL.md` y `05-security-and-secrets.md`, y las 4 skills Core mejoradas con `SKILL.md <= 35L` + `references/*.md` no vacíos.
   - **`CA-2003`:** verifica `audit_catalog_pack_references(ROOT_DIR, ROOT_DIR / ".sdd/catalog/packs") == []` sobre los `25` packs reales, y verifica fallo determinista de `R0`, `R1`, `R2`, `R3` y `R4` sobre una fixture temporal corrupta (cerca sin cerrar, `rules/ecc/foo.md`, enlace relativo roto, agente inexistente `code-reviewer` y skill inexistente `backend-patterns`).
   - **`CA-2009`:** verifica presupuesto activo de `.agents/` (`"references" not in p.parts`) `< 25,000` tokens (`< 100,000` bytes) y presupuesto lazy `references/` (`"references" in p.parts`) `< 15,000` tokens (`< 60,000` bytes).

---

## 6. Matriz de Trazabilidad Técnica (`01-spec.md` <-> `02-tech-spec.md`)

| Requisito EARS | Escenario BDD | Secciones `02-tech-spec.md` | Componentes y Tests Verificadores |
| :--- | :--- | :---: | :--- |
| `RF-2001` | `CA-2001` | §2.1 | `.agents/skills/sdd-security-audit/**`, `pipeline-run/SKILL.md`, `05-security-and-secrets.md` · `test_sdd_governance.py` |
| `RF-2002` | `CA-2002` | §2.2 | `.agents/skills/{sdd-silent-failure-audit,sdd-test-quality-audit,sdd-execution-guardrails,search-first}/**` · `test_sdd_governance.py` |
| `RF-2003` | `CA-2003` | §2.3, §5.2 | `.sdd/catalog/packs/**` (`19` saneados + `6` nuevos), `audit_catalog_pack_references` (`R0`–`R4`) · `test_sdd_governance.py` |
| `RF-2004` | `CA-2004` | §3.1, §3.2, §5.1 | `.sdd/catalog/packs/{capability-event-driven,capability-api-governance}/**` · `test_sdd_enterprise_packs.py` |
| `RF-2005` | `CA-2005` | §3.1, §3.2, §5.1 | `.sdd/catalog/packs/{capability-iac-cloud,framework-nextjs,framework-nestjs,capability-data-engineering}/**` · `test_sdd_enterprise_packs.py` |
| `RF-2006` | `CA-2006` | §3.1, §3.2, §5.1 | `.sdd/catalog/packs/{capability-devops,capability-database}/**` · `test_sdd_enterprise_packs.py` |
| `RF-2007` | `CA-2007` | §4.1, §4.3, §5.1 | `scripts/sdd_pack_registry.py`, `.sdd/catalog/bootstrap-references/*.md` · `test_sdd_enterprise_packs.py` |
| `RF-2008` | `CA-2008` | §3.1, §4.2, §4.4, §5.1 | `scripts/sdd_catalog_import.py`, `.sdd/catalog/UPSTREAM.md`, `THIRD_PARTY_NOTICES.md` · `test_sdd_enterprise_packs.py` |
| `RF-2009` | `CA-2009` | §1.1–§1.3, §5.2 | Presupuesto `.agents/` `< 25k` activo / `< 15k` `references/`, `.py <= 500L` · `test_sdd_governance.py`, `test_sdd_pack_materialization.py`, `test_sdd_sync_and_modularity.py`, `sdd_ci.py` |

## 7. Aprobación Formal Gate 2 (`RN-SDD-HUMAN-GATE-OWNERSHIP`)
- [x] **Gate 2 Approved (Human Sign-off):** Revisado y validado por Stakeholder Humano (`2026-11-24T16:09:11+01:00` — `"Aprobada. A por 03-tasks.md"`).

<!-- sdd:gate-seal gate=2 sha256=ce568223bcc607eebeafe239d7939ce18c58b474a507ed355412f159228fde38 -->
