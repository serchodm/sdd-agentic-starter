---
name: sdd-bootstrap
description: Executes the interactive Gate S0 Bootstrap Wizard to define system topology, hosting, architecture, stack packs, persistence, CI/CD, and agent squad activation in specs/STACK.md (ES-ES / EN-GB).
---

# Skill: `sdd-bootstrap` (Gate S0 Architectural Bootstrap Wizard)

Executed by `@orchestrator` during **Gate S0** before any feature spec or `src/` file is created.

## 1. Multilingual & Trigger Conditions
- **Languages (`0DD` aligned):** Auto-detect or prompt between `Español (ES-ES)` (`docs/es/`) and `English (EN-GB)` (`docs/en/`).
- **Triggers:**
  1. `specs/STACK.md` contains `[ ] Gate S0 Approved (Human Sign-off)` (or legacy `[ ] Gate 00 Approved (Human Sign-off)`).
  2. User starts a project (`ES-ES` / `EN-GB`) or attempts to write specs/code while Gate S0 is locked (**Fail-Closed Intercept**).

## 2. On-Demand Reference Catalogs
Load only the matching reference file when running the wizard (kept outside `.agents/` to keep always-on context minimal):
- Spanish questions (Rounds 1–3): `.sdd/catalog/bootstrap-references/question-catalog-es.md`
- English questions (Rounds 1–3): `.sdd/catalog/bootstrap-references/question-catalog-en.md`
- Full pruning matrix & `sdd:stack-config` template: `.sdd/catalog/bootstrap-references/stack-config-and-pruning.md`

## 3. Dynamic Tree Pruning (Core Rules)
Prune irrelevant branches immediately from Round 1/2 answers:
- **`Solo Backend / API Only`** / **`Backend Only`**: prune UI framework, CSS, client state, UI tests, Vercel previews, and all `uiux` questions (`ui-ux-pro-max`, `hifi_format`, `brand_constraints`). Mark `@front-engineer` = `INACTIVE (N/A)`; omit `capability-ui-design` and `@ui-ux-designer`.
- **`CLI / Herramienta Local`**: prune frontend, cloud/serverless hosting, containers, and all `uiux` questions; `@front-engineer` = `INACTIVE (N/A)`.
- **`Solo Frontend / Client Only`**: prune backend framework, DTOs, ORM, DB migrations, Testcontainers; mark `@back-engineer` = `INACTIVE (N/A)`, keep `uiux` active.
- **`Stateless`** / **`Vercel-Netlify-Cloudflare`** / **`Air-Gapped`**: prune DB/ORM/migrations, K8s/Swarm, or external CDNs respectively.

## 4. Interactive Wizard Outline (3 Rounds)
1. **Round 1 (Scope, Hosting, Network, CI/CD, Quality Gates):** Macro-scope, hosting runtime, network posture, CI platform, deploy/preview strategy, CI gates.
2. **Round 2 (Architecture, Backend, Frontend, Contracts, `uiux`):** Architectural pattern, error handling (`Result<T, E>` vs exceptions), backend stack & DTO validator, frontend framework/styling/state/contracts, plus UI visual design questions when UI is active:
   - `uiux`: `(Recommended) Enable ui-ux-pro-max` (`capability-web-frontend` + `capability-ui-design` + `@ui-ux-designer`) vs ECC skills only (`uiux.enabled: false`).
   - `uiux.hifi_format`: `html` (Recommended) | `figma` | `html+figma`.
   - `uiux.brand_constraints`: `None` | relative path (e.g. `docs/design-system/BRAND.md`).
3. **Round 3 (Persistence, Auth/Secrets, Golden Samples, Squad Topology):** DB engine, ORM, migrations, test isolation, auth, secret management, Do/Don't Golden Samples, squad preset (`compact` vs `granular`), extra business constraints.

## 5. Deterministic Output, Materialization & Gate 0 Intake
1. Populate `specs/STACK.md` from `specs/templates/00-stack.template.md` in the chosen language (`ES-ES` / `EN-GB`), including §2.5 deterministic DoD commands, §3.2 Ownership Map, Golden Samples, and §3.3 `yaml sdd:stack-config` (`stack_approved: false`, `gate00_approved: false`, `preset`, `packs`, `uiux`).
2. **Human Sign-off (`RN-SDD-HUMAN-GATE-OWNERSHIP`):** Present the proposed stack and squad in chat; ONLY mark `[x] Gate S0 Approved (Human Sign-off)` (and `stack_approved: true` / `gate00_approved: true`) after explicit user approval.
3. **Materialize Squad:** Run `uv run python scripts/sdd_agent_generator.py --materialize` to compile builders, universal specialists, and active packs (including `capability-ui-design` assets when `uiux.enabled: true`) into `.agents/` and initialize `.agent-inbox/`.
4. **Conditional `Design System Foundation` Backlog Row (`RF-008`, `AMB-005`):**
   - **ONLY when `uiux.enabled: true`** after Gate S0 approval, add one row in `specs/BACKLOG.md` titled **`Design System Foundation`** with the next sequential `FEAT-XXX` ID, `Gate 0` (`Gate 0 (Intake)`) = `[x]`, Gates 1–5 = `[ ]`, and `Estado Final` = `Backlog`.
   - Never create `specs/features/FEAT-XXX-*/`, `docs/design-system/`, or code during Gate S0 (`RN-SDD-SESSION-LIFECYCLE`).
