# `sdd-bootstrap` Reference: Dynamic Tree Pruning & `sdd:stack-config` Contract

## 1. Dynamic Tree Pruning Rules
| Condición Detectada | Preguntas Podadas (Omitidas) | Impacto en Escuadrón Agéntico y Packs |
| :--- | :--- | :--- |
| **`Solo Backend / API Only`** | Framework visual, Estilos CSS, Estado cliente, Tests UI, Vercel Previews, todas las preguntas `uiux` (`ui-ux-pro-max`, `hifi_format`, `brand_constraints`) | `@front-engineer` -> **INACTIVO / INACTIVE (N/A)**; omite automáticamente `framework-nextjs`, `capability-ui-design` y `@ui-ux-designer` |
| **`Solo Frontend / Client Only`** | Framework backend, DTOs backend, Event-Driven / Mensajería Asíncrona, ORM, Migraciones BD, Ingeniería de Datos, Testcontainers backend | `@back-engineer` -> **INACTIVO / INACTIVE (N/A)**; omite automáticamente `framework-nestjs`, `capability-event-driven` y `capability-data-engineering`; mantiene preguntas `uiux` activas |
| **`CLI / Herramienta Local`** | Frontend, Hosting serverless/cloud, Contenedores, Vercel, Event-Driven / Mensajería Asíncrona, Aislamiento Multi-Tenant, todas las preguntas `uiux` | `@front-engineer` -> **INACTIVO / INACTIVE (N/A)**; omite automáticamente `framework-nextjs`, `capability-ui-design` y `@ui-ux-designer` |
| **`Persistencia: N/A (Stateless)`** | Motor BD, ORM/Micro-ORM, Migraciones de esquema, Aislamiento Multi-Tenant, Testcontainers de BD | - |
| **`Hosting: Vercel / Netlify / Cloudflare`** | Kubernetes, Docker Swarm, Registries de contenedores | CI/CD orientado a GitOps y Previews por PR |
| **`Hosting: Air-Gapped / Aislado`** | CDNs remotas, Gestores de secretos en nube pública | Assets 100% locales, `.env` o Vault on-prem |

### 1.1. Mapeo de Respuestas de Bootstrap -> IDs `packs` (incluyendo `requires`)
| Ronda / Pregunta | Respuesta Seleccionada | Packs a Declarar en `sdd:stack-config` (`packs`) | Dependencias Transitivas (`requires`) |
| :--- | :--- | :--- | :--- |
| Ronda 1 — IaC, Cloud & GitOps | `Terraform / OpenTofu + IAM/FinOps` | `capability-iac-cloud` | `[]` |
| Ronda 1 — IaC, Cloud & GitOps | `Kubernetes + Helm / ArgoCD / Flux` | `capability-devops` | `[]` |
| Ronda 2 — Backend | `TypeScript / Node.js 22 con NestJS` | `lang-typescript`, `framework-nestjs` | `framework-nestjs` -> `lang:typescript` |
| Ronda 2 — Frontend | `Next.js (App Router + RSC)` | `lang-typescript`, `framework-react`, `framework-nextjs` | `framework-nextjs` -> `lang:typescript`, `framework:react` |
| Ronda 2 — Contratos y Gobierno API | `OpenAPI 3.1 / gRPC Buf / AsyncAPI 3.0` | `capability-api-governance` | `[]` |
| Ronda 2 — Event-Driven | `Kafka / RabbitMQ / SQS / NATS + Outbox/Sagas` | `capability-event-driven` | `[]` |
| Ronda 3 — Aislamiento Multi-Tenant | `Multi-tenant estricto con RLS / tenant_id` | `capability-database` *(incluye `multi-tenant-isolation`)* | `[]` |
| Ronda 3 — Ingeniería de Datos | `dbt / Airflow / Contratos de Calidad` | `capability-data-engineering` | `[]` |

## 2. Emisión del Bloque `sdd:stack-config` en `specs/STACK.md` (§3.3)
- Usar `specs/templates/00-stack.template.md` en el idioma elegido (`ES-ES` o `EN-GB`).
- Mantener `stack_approved: false` (y legacy `gate00_approved: false`) hasta aprobación humana expresa.
- Cuando el proyecto tiene UI (`Fullstack` o `Frontend Only`):
  - Si `uiux.enabled: true`, añadir `capability-web-frontend` y `capability-ui-design` en `packs`:
    ````markdown
    ```yaml sdd:stack-config
    stack_approved: false
    gate00_approved: false
    preset: <compact|granular|spa-only>
    packs:
      - <lang-pack>
      - <framework-pack>
      - capability-web-frontend
      - capability-ui-design
    uiux:
      enabled: true
      provider: ui-ux-pro-max
      version: "2.15.0"
      hifi_format: <html|figma|html+figma>
      # brand_constraints: docs/design-system/BRAND.md  # Optional relative path
    ```
    ````
  - Si `uiux.enabled: false`: incluir `capability-web-frontend` sin `capability-ui-design` y fijar `uiux: { enabled: false }` (mantiene `@a11y-architect` sin `@ui-ux-designer`).
- Cuando sea `Backend Only / API Only` o `CLI`: omitir `capability-ui-design` y fijar `uiux.enabled: false` (u omitir `uiux`).

## 3. Tablas de Escuadrón, Ownership Map (§3.2), Gate S0 y Materialización
1. Completar **Agent Squad Table** (`ACTIVE` vs `INACTIVE (N/A)`), **Ownership Map (§3.2)** y **Golden Samples (Do/Don't)**.
2. Pedir confirmación humana (`RN-SDD-HUMAN-GATE-OWNERSHIP`) antes de marcar `[x] Gate S0 Approved (Human Sign-off)` (alias legacy `Gate 00`) y `stack_approved: true` / `gate00_approved: true`.
3. Tras la aprobación, ejecutar:
   `uv run python scripts/sdd_agent_generator.py --materialize`
4. **Si y solo si `uiux.enabled: true`** tras aprobar Gate S0: registrar una fila en `specs/BACKLOG.md` titulada **`Design System Foundation`** con el siguiente `FEAT-XXX` secuencial, `Gate 0 (Intake)` = `[x]`, Gates 1–5 = `[ ]`, y `Estado Final` = `Backlog`. No crear carpetas ni código durante Gate S0 (`RN-SDD-SESSION-LIFECYCLE`).
