<p align="right">
  <strong>🇬🇧 English (EN-GB)</strong> | <a href="../es/README.md">🇪🇸 Español (ES-ES)</a>
</p>

# Living Functional Documentation (`docs/en/`)

Welcome to the living functional documentation of the **`sdd-agentic-starter`** repository, maintained under the **Zero Document Debt (0DD)** standard with **1:1** equivalence between British English (EN-GB) and Spanish (ES-ES).

---

## Active Baseline

- **Completed / Verified Framework Work Items:**
  - `FWK-001` — *Reliable Pack Materialisation and Activation* (`RFC-001` v2, status `Verified` / `Done`).
  - `FWK-002` — *`capability-ui-design` Pack (UI UX Pro Max)* (`RFC-001` v2, status `Verified` / `Done`).
  - `FWK-003` — *Conditional Visual Quality Gates and Token Anti-Drift* (`RFC-001` v2, status `Verified` / `Done`).
  - `FWK-004` — *Gate Terminology, Status, and DAG Graph Unification* (`RFC-002`, status `Verified` / `Done`).
  - `FWK-005`..`FWK-009` — *Comprehensive Post-Audit Hardening: P0 Fail-Closed Security, `sdd:ownership-map` Compiler & DAG Engine, `< 25k` Token Context Slimming + `/bug-fast-track` + `domains/`, Multi-Worktree Concurrency, and Transactional Sync / `<= 500L` Modularity* (`RFC-003`, status `Verified` / `Done`).
  - `FWK-010` — *Level L5 (10/10) Perfection Hardening: Cryptographic SHA-256 Gate Seals (`sdd_gate_seal.py` / `approve-gate` / `verify-gates`), Polyglot Architectural Boundary Scanner, Parallel DAG Wave `Write-Set` Collision Detection, and CI Audit (`>= 120` tests)* (`RFC-004`, status `Verified` / `Done`).
  - `FWK-011`..`FWK-012` — *POSIX Portability / CI Determinism and `v1.1.1` Coherence Alignment: `sdd work-item`, `HOTFIX`/`SPIKE`, SDD `spec-miner`, and PR-First `release-finish`* (`RFC-005` & `RFC-006`, status `Verified` / `Done`).
  - `FWK-013` — *Portable CI-Agnostic Engine (`sdd ci-verify`), `framework` vs `project` Auto-Detection, Safe `STACK.md §2.5` Execution, and Multi-CI Templates* (`RFC-007`, status `Verified` / `Done`).
  - `FWK-014` — *`Gate 6` (`REL-vX.Y.Z`), Release Readiness Engine (`./sdd release prepare|changelog|verify` in `scripts/sdd_release.py`), Deterministic `CHANGELOG.md`, Fail-Closed `sdd_git.py` Preflight, `08-release-readiness.template.md` Template, and `gate6-release.md` Workflow* (`RFC-007`, status `Verified` / `Done`).
  - `FWK-015` — *Brownfield Adoption Engine (`./sdd adopt --dry-run|--apply` in `scripts/sdd_brownfield.py`), Offline Deterministic Discovery, Fail-Closed Sanitisation, and `/brownfield-adopt` (`@spec-miner`) Workflow* (`RFC-008`, status `Verified` / `Done`, `150/150` offline tests across `14` suites).
- **Project Application:** Pending technology definition and human sign-off at **Gate S0** (`specs/STACK.md`, with legacy support for `Gate 00`). Until then, this documentation covers the operational behaviour of the starter's pack materialisation, activation, offline UI/UX vendoring, catalogue import engine, and unified agentic governance.

---

## Reading Map

| Block / Resource | Contents | Link |
| :--- | :--- | :--- |
| **Master Index (`00-governance`)** | Normative entry point, artefact statuses, and active documentation scope. | [DOCUMENTATION-INDEX.md](./00-governance/DOCUMENTATION-INDEX.md) |
| **Module `MOD-001` (`02-functional`)** | Functional and operational guide for pack materialisation (`sdd:stack-config`, Gate S0 / Gate 00, lazy loading, fail-closed cleanup, and catalogue import). | [pack-materialization.md](./02-functional/modules/MOD-001/pack-materialization.md) |
| **Module `MOD-002` (`02-functional`)** | Functional guide for `capability-ui-design` (offline `ui-ux-pro-max@2.15.0` vendoring with `VENDOR.lock.json`, `uiux` pruning in `sdd-bootstrap`, Gate 2 review with `@ui-ux-designer` + `@a11y-architect`, `docs/design-system/` semver lifecycle, `sdd_tokens_validator.py` validator, and Gate 4 bi-level visual quality gates). | [capability-ui-design.md](./02-functional/modules/MOD-002/capability-ui-design.md) |
| **Module `MOD-003` (`02-functional`)** | Unification of Gate terminology (`Gate S0`, `Gate 0..6`), statuses (`Candidate`..`Done`), DAG blocks (`Block`), session phases, fail-closed dual-accept support, CI-agnostic engine (`sdd ci-verify`), and hardening (`FWK-005`..`FWK-014`). | [gate-terminology-unification.md](./02-functional/modules/MOD-003/gate-terminology-unification.md) |
| **Knowledge Base (`docs/knowledge/`)** | Architecture decision records (`ADR-001`..`ADR-013`), system topology, data models, and CLI/API catalogue (`./sdd release prepare|changelog|verify`, `./sdd adopt --dry-run|--apply`). | [ADRS.md](../knowledge/ADRS.md) · [SYSTEM_TOPOLOGY.md](../knowledge/SYSTEM_TOPOLOGY.md) · [DATA_MODELS.md](../knowledge/DATA_MODELS.md) · [API_CATALOG.md](../knowledge/API_CATALOG.md) |
| **Traceability Matrix (0DD)** | Bidirectional traceability for `FWK-001` through `FWK-015` from EARS requirements, business rules, and NFRs to code, offline tests (`150` tests), and documentation. | [TRACEABILITY-MATRIX.md](../traceability/TRACEABILITY-MATRIX.md) |

## `Gate 6` (`REL-vX.Y.Z`) Operational Lifecycle

1. **Preflight and branch creation:** `./sdd git release-start --version X.Y.Z` validates SemVer, tag absence, zero open work items, and passing `ci-verify` before creating `release/vX.Y.Z`.
2. **Release dossier and deterministic `CHANGELOG.md`:** `./sdd release prepare --version X.Y.Z` instantiates `specs/releases/REL-vX.Y.Z.md` from `specs/templates/08-release-readiness.template.md` (keeping `[ ] Gate 6 Approved` unchecked) and updates `CHANGELOG.md` idempotently (also invokable standalone via `./sdd release changelog --version X.Y.Z`).
3. **Human sign-off and PR-First finish:** Following `.agents/workflows/gate6-release.md`, after human sign-off in `REL-vX.Y.Z.md`, `./sdd release verify --version X.Y.Z --stage finish` and `./sdd git release-finish --version X.Y.Z` run fail-closed checks and open the PR toward `main` (`RN-SDD-BRANCH-SYNC`).

## Brownfield Adoption Lifecycle (`sdd adopt` + `@spec-miner`)

1. **Read-only discovery (`--dry-run`) and non-destructive scaffolding:** `./sdd adopt --format text` deterministically and offline inspects manifests, ecosystems, candidate ownership zones, and safe DoD commands (filtering unsafe metacharacters). After reviewing the plan, `./sdd adopt --apply` (optionally `--with-repo-map`) creates only missing draft artefacts: `specs/STACK.md` (`[ ] Gate S0 Approved`, `stack_approved: false`), `docs/knowledge/BROWNFIELD_INVENTORY.md`, and `specs/BACKLOG.md`, without overwriting existing files.
2. **Human `Gate S0` sign-off and materialisation:** Complete/refine `specs/STACK.md`, obtain explicit human sign-off at `Gate S0` (`RN-SDD-HUMAN-GATE-OWNERSHIP`), and run `./sdd generate --materialize`.
3. **AST extraction and reverse mining via `@spec-miner`:** Following `.agents/workflows/brownfield-adopt.md` (`/brownfield-adopt`), select a bounded context from `docs/knowledge/BROWNFIELD_INVENTORY.md`, extract its symbol skeleton via `./sdd repo-map <context-path>`, and invoke `@spec-miner` (`.sdd/catalog/specialists-optin/spec-miner.md`) to draft `specs/features/FEAT-XXX-<slug>/01-spec.md` (`SRC-###`, `AMB-###`, EARS requirements, `Given-When-Then`) and `domains/<slug>/{overview,decisions}.md` without editing `src/` or auto-approving `Gate 1`.
