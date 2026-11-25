# Third-Party Notices & Attribution

This project (`sdd-agentic-starter`) incorporates, adapts, or is inspired by open-source works subject to the licenses described below.

---

## 1. Everything Claude Code (ECC)

- **Upstream Repository**: [https://github.com/affaan-m/ecc](https://github.com/affaan-m/ecc)
- **Author & Copyright**: Copyright (c) 2026 Affaan Mustafa
- **License**: MIT License ([https://opensource.org/licenses/MIT](https://opensource.org/licenses/MIT))

### Upstream MIT License Text:

```text
MIT License

Copyright (c) 2026 Affaan Mustafa

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

### Components Adapted from ECC:
- **Ultra-Specialist Reviewers & Build Resolvers**: Code review lenses, diagnostic commands, prompt defense baselines, and surgical build-repair workflows.
- **Continuous Learning v2 & Instinct Engine**: Atomic instinct scoring, confidence thresholds, and skill evolution patterns.
- **GAN-Style Harness**: Generator-Evaluator pattern for complex deliverables with weighted rubrics.
- **Santa Method ("Checking It Twice")**: Independent dual-review convergence verification.
- **Language & Framework Quality Packs**: Canonical patterns, testing strategies, and coding standards across TypeScript, Python, C#, Go, Rust, Java, Kotlin, Swift, and more.

---

## 2. REA Framework (morluto/rea)

- **Inspiration**: Fail-Closed engineering governance, Human Gate Ownership, and Definition of Ready/Done lifecycle standards.

---

## 3. Core Governance, Security & UI Design References

- **UI/UX Pro Max Skill (`nextlevelbuilder/ui-ux-pro-max-skill`)**
  - **Upstream Repository**: [https://github.com/nextlevelbuilder/ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill)
  - **License**: `MIT`
  - **Scope**: `capability-ui-design` (`vendor/ui-ux-pro-max`, `ui-ux-pro-max-cli` v2.15.0).
- **Claude Code OWASP (`agamm/claude-code-owasp`)**
  - **Upstream Repository**: [https://github.com/agamm/claude-code-owasp](https://github.com/agamm/claude-code-owasp)
  - **License**: `MIT`
  - **Scope**: Core `sdd-security-audit` skill (STRIDE / OWASP Top 10 / ASVS v4+) and `capability-database` security reference.
- **Superpowers (`obra/superpowers`)**
  - **Upstream Repository**: [https://github.com/obra/superpowers](https://github.com/obra/superpowers)
  - **License**: `MIT`
  - **Scope**: Core SDD skill governance, modular L4 `references/` progressive disclosure, and verification discipline.

---

## 4. Enterprise & Ecosystem Catalog Packs Attribution (`25` Packs)

All upstream repositories and reference inspirations declared in `.sdd/catalog/packs/*/pack.json` (`upstream.repo` and `upstream.references`) are attributed below with 1:1 parity:

### Event-Driven Architecture (`capability-event-driven`)
- **`confluentinc/agent-skills`** — License: `Apache-2.0` ([https://github.com/confluentinc/agent-skills](https://github.com/confluentinc/agent-skills)) — Primary upstream for Kafka streaming and event-driven patterns.
- **`lensesio/agentic-engineering-for-apache-kafka`** — License: `Apache-2.0` ([https://github.com/lensesio/agentic-engineering-for-apache-kafka](https://github.com/lensesio/agentic-engineering-for-apache-kafka)) — Reference for Apache Kafka operational patterns.
- **`wshobson/agents`** — License: `MIT` ([https://github.com/wshobson/agents](https://github.com/wshobson/agents)) — Reference for microservices boundaries and distributed messaging (also referenced in `capability-devops` and `capability-data-engineering`).

### API Governance & Contracts (`capability-api-governance`)
- **`bufbuild/claude-plugins`** — License: `Apache-2.0` ([https://github.com/bufbuild/claude-plugins](https://github.com/bufbuild/claude-plugins)) — Primary upstream for Protobuf/gRPC and Buf governance patterns.
- **`speakeasy-api/sdk-generation-skills`** — License: `Apache-2.0` ([https://github.com/speakeasy-api/sdk-generation-skills](https://github.com/speakeasy-api/sdk-generation-skills)) — Reference for OpenAPI contract-first governance.
- **`asyncapi/spec`** — License: `Apache-2.0` ([https://github.com/asyncapi/spec](https://github.com/asyncapi/spec)) — Reference for AsyncAPI 3.0 event contract specifications.

### Infrastructure as Code & Cloud (`capability-iac-cloud`)
- **`antonbabenko/terraform-skill`** — License: `Apache-2.0` ([https://github.com/antonbabenko/terraform-skill](https://github.com/antonbabenko/terraform-skill)) — Primary upstream for Terraform/OpenTofu HCL module patterns.
- **`BagelHole/DevOps-Security-Agent-Skills`** — License: `MIT` ([https://github.com/BagelHole/DevOps-Security-Agent-Skills](https://github.com/BagelHole/DevOps-Security-Agent-Skills)) — Reference for cloud IAM and DevSecOps guardrails.
- **`trailofbits/skills`** — License: `Apache-2.0` ([https://github.com/trailofbits/skills](https://github.com/trailofbits/skills)) — Reference for cloud security and IaC hardening checks.

### Web & Backend Frameworks (`framework-nextjs`, `framework-nestjs`)
- **`vercel-labs/agent-skills`** — License: `MIT` ([https://github.com/vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills)) — Primary upstream for `framework-nextjs` (Next.js App Router & RSC patterns).
- **`nestjs/agent-skills`** — License: `MIT` ([https://github.com/nestjs/agent-skills](https://github.com/nestjs/agent-skills)) — Primary upstream for `framework-nestjs` (NestJS modular architecture).
- **`Kadajett/agent-nestjs-skills`** — License: `MIT` ([https://github.com/Kadajett/agent-nestjs-skills](https://github.com/Kadajett/agent-nestjs-skills)) — Reference for NestJS testing and dependency injection patterns.

### Data Engineering & Multi-Tenant Databases (`capability-data-engineering`, `capability-database`)
- **`dbt-labs/dbt-agent-skills`** — License: `Apache-2.0` ([https://github.com/dbt-labs/dbt-agent-skills](https://github.com/dbt-labs/dbt-agent-skills)) — Primary upstream for `capability-data-engineering` (dbt modeling & contracts).
- **`GoogleCloudPlatform/data-agent-kit-plugin`** — License: `Apache-2.0` ([https://github.com/GoogleCloudPlatform/data-agent-kit-plugin](https://github.com/GoogleCloudPlatform/data-agent-kit-plugin)) — Reference for data pipelines and analytical quality governance.
- **`supabase/agent-skills`** — License: `MIT` ([https://github.com/supabase/agent-skills](https://github.com/supabase/agent-skills)) — Reference for `capability-database` (PostgreSQL RLS & multi-tenant isolation).
