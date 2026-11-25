# SDD Agentic Catalog — Upstream Attribution & Tracking

This catalog (`.sdd/catalog/`) contains the framework's reusable archetype recipes, clean ECC specialists, and language/framework/capability stack packs (`25` packs, `86` total catalog skills).

## Upstream Tracking (Primary Core & ECC)

- **Upstream Repository**: `affaan-m/ecc` (Everything Claude Code)
- **Upstream Branch**: `main`
- **License**: MIT License
- **Copyright**: (c) 2026 Affaan Mustafa
- **Import Methodology**:
  - Reviewers and build resolvers are converted to SDD Subagents with the standard Prompt Defense baseline and read-only safety restrictions (`tools: read, grep, glob, bash` where allowed; no unauthorized direct writes).
  - Language rules from `rules/common/` are condensed into `07-engineering-baseline.md`.
  - Framework rules and skills are encapsulated into discrete, lazy-loadable stack packs (`.sdd/catalog/packs/`).

## Core & Governance Upstream References

| Repository | License | Scope in SDD Framework |
| :--- | :--- | :--- |
| `affaan-m/ecc` | `MIT` | Core engineering baseline, specialist agents, and 18 base language/framework/capability packs |
| `nextlevelbuilder/ui-ux-pro-max-skill` | `MIT` | `capability-ui-design` (`vendor/ui-ux-pro-max`, `ui-ux-pro-max-cli` v2.15.0) |
| `agamm/claude-code-owasp` | `MIT` | Core `sdd-security-audit` skill (STRIDE / OWASP Top 10 / ASVS v4+) and `capability-database` security reference |
| `obra/superpowers` | `MIT` | Core SDD skill governance, modular L4 `references/` progressive disclosure, and verification discipline |

## Master Catalog Table (`25` Packs — `86` Skills)

| Pack ID | Directory (`.sdd/catalog/packs/`) | Family | Skills | Primary Upstream (`license`) | Additional References (`upstream.references`) |
| :--- | :--- | :--- | :---: | :--- | :--- |
| `capability:ai-llm` | `capability-ai-llm` | `capability` | 9 | `affaan-m/ecc` (`MIT`) | — |
| `capability:api-governance` | `capability-api-governance` *(New)* | `capability` | 3 | `bufbuild/claude-plugins` (`Apache-2.0`) | `speakeasy-api/sdk-generation-skills (Apache-2.0)`, `asyncapi/spec (Apache-2.0)` |
| `capability:data-engineering` | `capability-data-engineering` *(New)* | `capability` | 3 | `dbt-labs/dbt-agent-skills` (`Apache-2.0`) | `GoogleCloudPlatform/data-agent-kit-plugin (Apache-2.0)`, `wshobson/agents (MIT)` |
| `capability:database` | `capability-database` *(Expanded)* | `capability` | 7 | `affaan-m/ecc` (`MIT`) | `supabase/agent-skills (MIT)`, `agamm/claude-code-owasp (MIT)` |
| `capability:devops` | `capability-devops` *(Expanded)* | `capability` | 5 | `affaan-m/ecc` (`MIT`) | `wshobson/agents (MIT)` |
| `capability:event-driven` | `capability-event-driven` *(New)* | `capability` | 3 | `confluentinc/agent-skills` (`Apache-2.0`) | `lensesio/agentic-engineering-for-apache-kafka (Apache-2.0)`, `wshobson/agents (MIT)` |
| `capability:iac-cloud` | `capability-iac-cloud` *(New)* | `capability` | 3 | `antonbabenko/terraform-skill` (`Apache-2.0`) | `BagelHole/DevOps-Security-Agent-Skills (MIT)`, `trailofbits/skills (Apache-2.0)` |
| `capability:ui-design` | `capability-ui-design` | `capability` | 2 | `nextlevelbuilder/ui-ux-pro-max-skill` (`MIT`) | — |
| `capability:web-frontend` | `capability-web-frontend` | `capability` | 7 | `affaan-m/ecc` (`MIT`) | — |
| `framework:django` | `framework-django` | `framework` | 5 | `affaan-m/ecc` (`MIT`) | — |
| `framework:fastapi` | `framework-fastapi` | `framework` | 1 | `affaan-m/ecc` (`MIT`) | — |
| `framework:nestjs` | `framework-nestjs` *(New)* | `framework` | 1 | `nestjs/agent-skills` (`MIT`) | `Kadajett/agent-nestjs-skills (MIT)` |
| `framework:nextjs` | `framework-nextjs` *(New)* | `framework` | 1 | `vercel-labs/agent-skills` (`MIT`) | — |
| `framework:react` | `framework-react` | `framework` | 4 | `affaan-m/ecc` (`MIT`) | — |
| `framework:vue` | `framework-vue` | `framework` | 3 | `affaan-m/ecc` (`MIT`) | — |
| `lang:cpp` | `lang-cpp` | `language` | 2 | `affaan-m/ecc` (`MIT`) | — |
| `lang:csharp` | `lang-csharp` | `language` | 2 | `affaan-m/ecc` (`MIT`) | — |
| `lang:dart` | `lang-dart` | `language` | 2 | `affaan-m/ecc` (`MIT`) | — |
| `lang:go` | `lang-go` | `language` | 2 | `affaan-m/ecc` (`MIT`) | — |
| `lang:java` | `lang-java` | `language` | 6 | `affaan-m/ecc` (`MIT`) | — |
| `lang:kotlin` | `lang-kotlin` | `language` | 4 | `affaan-m/ecc` (`MIT`) | — |
| `lang:python` | `lang-python` | `language` | 2 | `affaan-m/ecc` (`MIT`) | — |
| `lang:rust` | `lang-rust` | `language` | 2 | `affaan-m/ecc` (`MIT`) | — |
| `lang:swift` | `lang-swift` | `language` | 4 | `affaan-m/ecc` (`MIT`) | — |
| `lang:typescript` | `lang-typescript` | `language` | 3 | `affaan-m/ecc` (`MIT`) | — |
| **Total** | **25 packs** | **3 families** | **86** | — | — |
