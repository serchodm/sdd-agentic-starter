<p align="right">
  <strong>🇬🇧 English (EN-GB)</strong> | <a href="../../../../es/02-functional/modules/MOD-002/capability-ui-design.md">🇪🇸 Español (ES-ES)</a>
</p>

# `MOD-002`: `capability-ui-design` Pack and SDD Visual Governance

- **Module Identifier:** `MOD-002`
- **Source Work Item / RFC:** `FWK-002-capability-ui-design` ([`RFC-001` v2](../../../../../.sdd/framework/rfcs/RFC-001-ui-ux-pro-max.md))
- **Functional Status:** `Verified` (Confirmed and verified by deterministic offline tests)
- **Master Index:** [DOCUMENTATION-INDEX.md](../../../00-governance/DOCUMENTATION-INDEX.md)

---

## 1. Purpose and Scope

### 1.1. Purpose (Confirmed)
This module equips web-facing SDD projects with a **governed, 100% offline, accessible UI/UX design capability compatible with `RN-SDD-IMMUTABLE-DONE` and `RN-SDD-1-TO-1-CR`**.

It introduces the standalone `.sdd/catalog/packs/capability-ui-design/` pack, the SHA-256-verified vendoring of `ui-ux-pro-max-cli@2.15.0` (MIT), the `@ui-ux-designer` specialist, the `sdd-ui-design` methodology adapter, the Gate 2 visual review workflow (`/ui-design-review`), conditional configuration in `sdd-bootstrap`, and semantic-versioned lifecycle rules for `docs/design-system/`.

### 1.2. In-Scope (Confirmed)
- Standalone non-ECC pack `.sdd/catalog/packs/capability-ui-design/` (`id: "capability:ui-design"`, `requires: ["capability:web-frontend"]`, `targets: ["web"]`, `rules: []`) with MIT `NOTICE.md` and byte-for-byte preservation under `scripts/sdd_catalog_import.py`.
- Offline, integrity-verified vendoring (`VENDOR.lock.json` SHA-256) of `ui-ux-pro-max@2.15.0` (`46` entries: `45` upstream runtime files + MIT `LICENSE`), excluding the 6 sibling skills and `scripts/tests/`, paired with `.gitattributes` (`text eol=lf`).
- Isolated maintainer updater `scripts/sdd_vendor_update.py` (the sole component authorised to invoke `npx` inside a temporary directory, printing a diff prior to `--apply`) plus automatic verification in `scripts/sdd_pack_registry.py` before mutating `.agents/`.
- Fail-closed validation of the `uiux` block in `sdd:stack-config` and strict `uiux.enabled` ↔ `capability-ui-design` coherence after Gate 00 approval.
- Dynamic pruning in `sdd-bootstrap` (ES-ES and EN-GB) for non-UI projects (`Backend Only / API Only`, `CLI`), conditional `uiux` prompts for UI projects, and automatic registration of `Design System Foundation` in `specs/BACKLOG.md` upon Gate 00 approval when `uiux.enabled: true`.
- Strict `@ui-ux-designer` contract, 6-step Gate 2 `ui-design-review.md` workflow (`@ui-ux-designer` → `@a11y-architect` → `@architect` → `[ ] Visual Sign-off (Human)`), §6.1 subsection in `02-technical-spec.template.md`, orchestration rules in `.agents/agents/orchestrator.md`, and Design System DoR/DoD tokens in frontend archetypes (`front-ui`, `front-engineer`, `tier-frontend`).
- Canonical semantic-versioned schema for `docs/design-system/` (`MASTER.md`, `design-tokens.json`, `CHANGELOG.md`, `pages/SCR-XXX.md`) defined inside `skills/sdd-ui-design/SKILL.md`.

### 1.3. Explicitly Out-of-Scope (Future Scope)
- **No** empty `docs/design-system/` directory is created in the starter repository; that directory originates solely in a target project during the `Design System Foundation` feature.
- Automated visual quality gates in `@qa-tester`, `@a11y-architect`, and CI/CD (contrast, keyboard, human-baselined screenshots): belongs to **`FWK-003`**.
- Global Gate terminology unification across `SDD_FRAMEWORK.md`, `BACKLOG.md`, and `AGENTS.md`: belongs to **`FWK-004`**.
- Operational support for non-`web` `targets` (prepared as metadata in `pack.json` only).

---

## 2. Actors and Authority

| Actor | Responsibility | Primary Constraint |
| :--- | :--- | :--- |
| **Human Stakeholder** | Chooses `uiux` settings in `sdd-bootstrap` and approves Gate 00, Gate 1 (wireframes), `[x] Visual Sign-off (Human)`, and Gate 2. | AI agents must never self-approve `[x] Visual Sign-off (Human)` or Gate 00/1/2 (`RN-SDD-HUMAN-GATE-OWNERSHIP`). |
| **`@orchestrator`** | Runs `sdd-bootstrap`, registers `Design System Foundation` after Gate 00 when `uiux.enabled: true`, drives `/ui-design-review` at Gate 2, and propagates `SCR-XXX`, `MASTER@version`, and tokens to Gate 3 DoR. | When a feature touches no `SCR-###` screens, marks §6.1 and `Visual Sign-off (Human)` as `N/A`. |
| **`@ui-ux-designer`** | Queries `search.py --json` offline (`sdd-ui-design`), drafts token proposals (`Design System Foundation` or its CR), `pages/SCR-XXX.md` overrides, and hi-fi prototypes traced to `RF-###` / `SCR-###` / tokens. | Blocked without Gate 1 + §18 wireframes; forbidden from `src/**`, `tests/**`, `01-spec.md`, `Done` features, `npx`, or `--force` on `MASTER.md`. |
| **`@a11y-architect`** | Performs independent WCAG 2.2 AA review across tokens, `pages/SCR-XXX.md`, and hi-fi using the `accessibility` skill. | Remains active even when `uiux.enabled: false` if `capability-web-frontend` is enabled (`RN-03`). |
| **`@architect`** | Validates UI states, DTOs, and `MASTER@version` ranges, populating `02-tech-spec.md` §6.1. | Triggers *Stop-the-Line* if an unapproved functional change leaks into visual design. |
| **UI Builders (`@front-ui`, `@front-engineer`, `tier-frontend`)** | Implement views and components during Gate 4 using tokens from `docs/design-system/design-tokens.json`. | Require `SCR-XXX`, `MASTER@version`, `pages/SCR-XXX.md`, and tokens in DoR; hardcoding literal values when a token exists is forbidden. |
| **Framework Maintainer** | Verifies or updates the vendored provider via `scripts/sdd_vendor_update.py`. | Must inspect the staged diff before passing `--apply` and never run `npx` outside this script. |

---

## 3. Business Rules and System Behaviour

### 3.1. Exclusive Offline Provenance and Vendor Integrity (`RN-01`, `RF-001`, `RF-002`, `RF-004`, `RF-012`)
1. `capability-ui-design` is a standalone pack outside `STACK_PACKS` in `scripts/sdd_catalog_import.py`: running the ECC importer leaves its directory **byte-for-byte untouched**.
2. Its vendored assets under `vendor/ui-ux-pro-max/` originate solely from `ui-ux-pro-max-cli@2.15.0` (MIT, explicitly attributed in `NOTICE.md` separately from `affaan-m/ecc`).
3. Extraction keeps **exclusively** the `45` runtime files of `ui-ux-pro-max` plus MIT `LICENSE` (`46` entries in `VENDOR.lock.json`), discarding the 6 sibling skills (`banner-design`, `brand`, `design`, `design-system`—which would collide with `capability-web-frontend/skills/design-system`—, `slides`, and Apache-2.0 `ui-styling`) and `scripts/tests/`.
4. Every vendored file is verified by exact `bytes` length and `sha256` digest against `VENDOR.lock.json` both via `scripts/sdd_vendor_update.py --verify` and automatically inside `sdd_pack_registry.resolve_pack_assets()` / `sdd_agent_generator.py --materialize`. Any missing, modified (even 1 byte), or undeclared file aborts fail-closed before touching `.agents/`.
5. `.gitattributes` enforces `text eol=lf` for `.sdd/catalog/packs/capability-ui-design/**` and `.agents/**`, ensuring deterministic SHA-256 hashes across Windows and POSIX.

### 3.2. UI-Only Pruning, `uiux` Configuration, and Clean Degradation (`RN-02`, `RN-03`, `RF-003`, `RF-006`, `RF-007`, `RF-008`)
1. **Pruning in `sdd-bootstrap` (ES-ES and EN-GB):** for `Backend Only / API Only` or `CLI` projects, the wizard skips all 3 `uiux` prompts and omits `capability-ui-design`. For UI projects (`Fullstack` or `Frontend Only`), it asks: (a) enable `ui-ux-pro-max` vs ECC-only skills, (b) `uiux.hifi_format` (`html` recommended / `figma` / `html+figma`), and (c) optional `uiux.brand_constraints`.
2. **Strict `uiux` validation in `sdd:stack-config`:** permits only `enabled` (required strict `bool`), `provider` (`"ui-ux-pro-max"` when `enabled: true`), `version`, `hifi_format` (`html` | `figma` | `html+figma`), and `brand_constraints` (`null` or safe relative path). Rejects `uiux.enabled: true` when `preset == "api-only"`.
3. **`uiux.enabled` ↔ `packs` coherence:** once Gate 00 is approved, `uiux.enabled: true` requires `capability-ui-design` (and its dependency `capability:web-frontend`) in `packs`, and listing `capability-ui-design` requires `uiux.enabled: true`.
4. **Materialisation when provider is active:** `sdd_agent_generator.py --materialize` generates `.agents/agents/ui-ux-designer.md` (with `GENERATED` header), `.agent-inbox/ui-ux-designer/.gitkeep`, `.agents/skills/sdd-ui-design/`, `.agents/skills/ui-ux-pro-max/` (including `scripts/search.py` and datasets), and `.agents/workflows/ui-design-review.md`, protected against reverse template sync by `squad.lock.json` v2 and `sdd_sync.py`.
5. **Clean ECC fallback (`RN-03`):** with `capability-web-frontend` active and `uiux.enabled: false`, the project retains `@a11y-architect` and the ECC skills (`design-system`, `accessibility`, `browser-qa`, `frontend-a11y`, `make-interfaces-feel-better`, `motion-foundations`, `i18n-sync`), without materialising `@ui-ux-designer` or `ui-ux-pro-max`.
6. **Automatic `specs/BACKLOG.md` registration (`RF-008`):** strictly when Gate 00 is approved with `uiux.enabled: true`, `sdd-bootstrap` instructs `@orchestrator` to register a **`Design System Foundation`** row in `specs/BACKLOG.md` with the next available sequential `FEAT-XXX` ID, `Gate 0 (Intake)` = `[x]`, and status `Backlog` (creating no feature folders or code until its dedicated Gate 1–5 session).

### 3.3. Gate 1 Prerequisite, Gate 2 Review Chain, and Stop-the-Line (`RN-04`, `RN-05`, `RN-06`, `RF-009`, `RF-010`)
1. **Blocking `@ui-ux-designer` DoR:** simultaneously requires (1) Gate 00 approved with `uiux.enabled: true`, (2) `01-spec.md` with `[x] Gate 1 Aprobado` and validated §18 wireframes (`wireframe.excalidraw` + `screen-spec.md`), and (3) a live `docs/design-system/MASTER.md` (or the active feature being `Design System Foundation` / a CR over it). Missing any item writes `.agent-inbox/ui-ux-designer/BLOCKED_DOR_<FEAT-ID>.md` and stops.
2. **Safe offline querying:** runs `uv run python .agents/skills/ui-ux-pro-max/scripts/search.py "<query>" --design-system -p "<project>" --json` (`python3` / `py -3` fallbacks; never `npx` or `--force` over an existing `MASTER.md`; if `--persist` is used, always passes `--output-dir <temp_dir>`). Emits an Air-Gapped warning if external Google Fonts URLs are suggested.
3. **Functional non-invasion (`RN-04`):** if a visual adjustment introduces or alters controls, fields, validations, or flows absent from `01-spec.md`, it writes `BLOCKED_<FEAT-ID>.md` and returns the work item to Gate 1 (*Stop-the-Line*).
4. **Mandatory Gate 2 chain (`RN-05`):** every feature touching `SCR-###` flows through `@ui-ux-designer` (`RF-###` → `SCR-###` → token traceability, `Confirmed`/`Proposed`/`Pending` tags, UI states `default`/`loading`/`empty`/`error`, responsive) → `@a11y-architect` (WCAG 2.2 AA) → `@architect` (`02-tech-spec.md` §6.1 `MASTER@version`) → `[ ] Visual Sign-off (Human)` (§8).
5. **Write boundary (`RN-06`):** `@ui-ux-designer` writes exclusively to `docs/design-system/**` (via `Design System Foundation` or its CR, plus `pages/SCR-XXX.md` for the active feature) and `specs/features/<active>/ux/**`; it is forbidden from editing `src/**`, `tests/**`, `01-spec.md`, `Done` features, or sign-off checkboxes.

### 3.4. Canonical `docs/design-system/` Schema, SemVer, and CR Cardinality (`RN-07`, `RF-011`)
- The `sdd-ui-design` skill defines the language-neutral visual schema for target projects (`MASTER.md`, `design-tokens.json`, `CHANGELOG.md`, `pages/SCR-XXX.md`), mandating token references (forbidding raw `#hex`/`px` literals without tokens) and distinguishing auxiliary ECC `design-system` previews from the normative authority of `MASTER.md`.
- The `front-ui`, `front-engineer`, and `tier-frontend` archetypes enforce `SCR-XXX`, `MASTER@version`, `docs/design-system/pages/SCR-XXX.md`, hi-fi prototypes, and `design-tokens.json` tokens in their `DoR` and `DoD`.
- **Post-`Done` evolution (`RN-07`):** after `Design System Foundation` reaches `Done`, global token or rule updates flow through **1 single `CR-XXX` against `Design System Foundation`** with a semver bump (`MAJOR` listing impacted `SCR-###`, backwards-compatible `MINOR`, or value-only `PATCH`) and a `CHANGELOG.md` entry:
  - **Pure token re-skin:** does not open CRs on `Done` consumer features (their `specs/features/` folders stay untouched).
  - **Functional behaviour change:** requires **1 separate CR per affected `Done` feature** (`RN-SDD-1-TO-1-CR`).

---

## 4. Step-by-Step Operational Flows

### Flow 1: UI vs Non-UI Project Bootstrap (`sdd-bootstrap`)
1. The user launches Gate 00 with `@orchestrator`.
2. Choosing `Backend Only` or `CLI` automatically prunes all `uiux` prompts and leaves `uiux.enabled` disabled.
3. Choosing `Fullstack` or `Frontend Only` lets the user select `ui-ux-pro-max` (`hifi_format`, `brand_constraints`) or ECC-only frontend skills under `capability-web-frontend`.
4. After `[x] Gate 00 Approved`, `@orchestrator` runs `--materialize` and, if `uiux.enabled: true`, appends `Design System Foundation` to `specs/BACKLOG.md`.

### Flow 2: Integrity Verification and Materialisation (`--verify` / `--materialize`)
1. Run `uv run python scripts/sdd_vendor_update.py --verify` to validate all `46` files in `vendor/ui-ux-pro-max/` against `VENDOR.lock.json`.
2. Running `uv run python scripts/sdd_agent_generator.py --materialize` with `capability-ui-design` active automatically runs the same SHA-256 verification inside `resolve_pack_assets()` before touching `.agents/`.

### Flow 3: Gate 2 Visual Review (`/ui-design-review`)
1. Confirm DoR (Gate 00 + `[x]` Gate 1 with §18 wireframes + `MASTER.md` or `Design System Foundation`).
2. `@ui-ux-designer` queries `search.py --json` offline and writes tokens/overrides/hi-fi under `specs/features/<feat>/ux/SCR-XXX/hi-fi/`.
3. `@a11y-architect` audits WCAG 2.2 AA; `@architect` validates contracts and fills `02-tech-spec.md` §6.1 (`MASTER@version`).
4. Once zero unapproved functional changes are confirmed, the human stakeholder reviews and signs `[x] Visual Sign-off (Human)` and Gate 2.

### Flow 4: Post-`Done` Token Evolution
1. Open **1 single `CR-XXX`** against `Design System Foundation`.
2. Update `MASTER.md`, `design-tokens.json`, and `CHANGELOG.md` with the appropriate semver bump.
3. Keep `Done` consumer features untouched unless functional screen behaviour changes (which opens 1 CR per affected feature).

### Flow 5: Controlled Maintainer Provider Update (`sdd_vendor_update.py`)
1. Preview the staged diff in an isolated temporary directory (no catalogue writes):
   `uv run python scripts/sdd_vendor_update.py --version <X.Y.Z>`
2. Inspect added/modified/removed files and the `pack.json` version delta.
3. Apply and regenerate `VENDOR.lock.json` only after explicit review:
   `uv run python scripts/sdd_vendor_update.py --version <X.Y.Z> --apply`

---

## 5. Verified Baseline State of the Starter Template (Confirmed)

In the clean starter template (with `[ ] Gate 00 Approved`):
- `specs/STACK.md` keeps `gate00_approved: false`, `preset: compact`, `packs: []`, and `uiux: {enabled: false}`.
- `specs/templates/00-stack.template.md` includes the full `yaml sdd:stack-config` block with documented `uiux` defaults (`provider: ui-ux-pro-max`, `version: "2.15.0"`, `hifi_format: html`).
- `specs/templates/02-technical-spec.template.md` includes subsection `### 6.1. Diseño Visual` and the `- [ ] **Visual Sign-off (Human)**` checkbox in §8.
- `docs/design-system/` **does not exist** in the empty starter.
- `.sdd/catalog/packs/capability-ui-design/` holds the full pack with `vendor/ui-ux-pro-max/` (`46` entries verified in `VENDOR.lock.json`), preserved untouched by `sdd_catalog_import.py`.
- `.agents/` retains only the `28` baseline agents and `22` tracked entries in `squad.lock.json` (`active_packs: []`), without materialising `@ui-ux-designer` until a project approves Gate 00 with `uiux.enabled: true`.

---

## 6. Verified Requirements, Business Rules, and Acceptance Criteria

| Reference | Summary | Status |
| :--- | :--- | :--- |
| `RF-001`, `RF-002`, `RN-01` | `capability-ui-design` pack (`NOTICE.md`, `pack.json`, `rules: []`) and `VENDOR.lock.json` SHA-256 (`46` entries) 100% offline without `npx`. | `Verified` |
| `RF-003`, `RF-006`, `RN-02`, `RN-03` | Topology activation and pruning (`api-only`, `spa-only` with `uiux.enabled: true`, ECC fallback with `uiux.enabled: false`) + strict `uiux` validation. | `Verified` |
| `RF-004`, `REL-VENDOR-INTEGRITY-01` | Fail-closed abort in `--verify` and `--materialize` upon 1-byte modification, missing file, or undeclared file under `vendor/`. | `Verified` |
| `RF-005` | Isolated `TemporaryDirectory` update via `sdd_vendor_update.py` running `validate_data.py`, excluding sibling skills/tests, LF-normalising, and diffing prior to `--apply`. | `Verified` |
| `RF-007`, `RF-008` | Conditional ES-ES/EN-GB prompts in `sdd-bootstrap`, `sdd:stack-config` template block, and `Design System Foundation` registration in `specs/BACKLOG.md`. | `Verified` |
| `RF-009`, `RF-010`, `RN-04`, `RN-05`, `RN-06` | Gate 1 + §18 wireframe DoR (`BLOCKED_DOR_`), functional Stop-the-Line, `@ui-ux-designer` → `@a11y-architect` → `@architect` → `[ ] Visual Sign-off (Human)` chain, and write boundaries. | `Verified` |
| `RF-011`, `RN-07` | Semver `docs/design-system/` schema, `--force` prohibition, token references in `SCR-XXX` / frontend archetypes, and 1:1 CR cardinality post-`Done`. | `Verified` |
| `RF-012` | Byte-for-byte preservation of `capability-ui-design` during `scripts/sdd_catalog_import.py`. | `Verified` |
| `PERF-FWK-TESTS-01` | Full offline test suite in `tests/` (`37` total tests, target `< 3.0s` / ceiling `<= 8.0s`, `0` real network requests, modules `<= 500` lines). | `Verified` |

*(For exact source file and test method mappings, see [TRACEABILITY-MATRIX.md](../../../../traceability/TRACEABILITY-MATRIX.md)).*
