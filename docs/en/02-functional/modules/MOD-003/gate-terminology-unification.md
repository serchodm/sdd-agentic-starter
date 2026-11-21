<p align="right">
  <strong>🇬🇧 English (EN-GB)</strong> | <a href="../../../../es/02-functional/modules/MOD-003/gate-terminology-unification.md">🇪🇸 Español (ES-ES)</a>
</p>

# `MOD-003`: Gate Terminology, Status, and DAG Graph Unification

- **Module Identifier:** `MOD-003`
- **Source Work Item / RFC:** `FWK-004`..`FWK-016` ([`RFC-002`](../../../../../.sdd/framework/rfcs/RFC-002-gate-terminology-unification.md) .. [`RFC-008`](../../../../../.sdd/framework/rfcs/RFC-008-brownfield-adoption-and-spec-drift.md))
- **Functional Status:** `Verified` (Confirmed and verified by 160 offline unit tests across 15 suites)
- **Master Index:** [DOCUMENTATION-INDEX.md](../../../00-governance/DOCUMENTATION-INDEX.md)

---

## 1. Purpose and Scope

### 1.1. Purpose (Confirmed)
This module eliminates normative ambiguities, numeric collisions (`Gate 00` vs `Gate 0`), bilingual status divergence (`Done`/`Completado`), and conceptual cross-contamination (`Gate` vs `Block` vs `Session Phase`) across the starter, and consolidates the governance pipeline from `Gate S0` through `Gate 6` (`v1.3.0`).

It guarantees that human engineers and AI agents share an unambiguous mental model backed by strict zero-breaking dual-acceptance and fail-closed validation.

### 1.2. In-Scope Features (Confirmed)
- **Canonical Gate Table:** `Gate S0` for project-level Stack Lock (`specs/STACK.md`), `Gate 0..5` for Work Items (including conditional `Sub-Gate 2V` for visual validation on `SCR-###` screens), and `Gate 6` for Release Readiness (`specs/releases/REL-vX.Y.Z.md`).
- **Orthogonal Conceptual Separation:**
  - `Gate`: Formal quality and SDD governance gates (`Gate S0`, `Gate 0..6`).
  - `Block` / `DAG Block`: Atomic batches of concurrent or sequential tasks in `03-tasks.md`.
  - `Session Phase`: Conversation context partitions (`Session Phase A: Gates 0–3` / `Session Phase B: Gates 4–5`).
- **Fail-Closed Dual-Acceptance:**
  - `scripts/sdd_pack_registry.py` and `.agents/scripts/sdd_stack_gate_guard.py` accept canonical markers (`[x] Gate S0 Approved`, `stack_approved`) and legacy aliases (`[x] Gate 00 Approved`, `gate00_approved`).
  - Detection of boolean inconsistency between `stack_approved` and `gate00_approved` aborting with `StackConfigError`.
  - `StackConfig` and `squad.lock.json` retain backward compatibility via compatibility aliases.
- **Status Normalisation and CR Template Consolidation:**
  - Work Items: `Candidate` → `Backlog` → `In Progress` → `In Review` → `Done` (or `Blocked`).
  - Specs: `Draft` → `In Review` → `Approved` → `Done`.
  - Consolidation of Change Request templates into [`specs/templates/04-change-request-spec.template.md`](../../../../../specs/templates/04-change-request-spec.template.md) and removal of `04-change-spec.template.md`.
  - Fixed legacy broken links pointing to `03-ears-requirements.md`.

### 1.3. Out-of-Scope (Explicitly Excluded)
- Mutating historical completed items (`FWK-001`, `FWK-002`, `FWK-003`, `RFC-001`) protected by `RN-SDD-IMMUTABLE-DONE`.
- Upstream vendored files in `.sdd/catalog/packs/capability-ui-design/vendor/`.
- Production application code in `src/`.

---

## 2. Actors and Authority

| Actor | Responsibility | Key Constraint |
| :--- | :--- | :--- |
| **Human User / Tech Lead** | Authorises formal gates via explicit human sign-off (`[x] Gate S0 Approved`, `[x] Gate 1 Approved`, `[x] Gate 2 Approved`, `[x] Gate 2 Visual Sign-off`, `[x] Gate 3 Approved`, `[x] Gate 6 Approved`). | AI agents never auto-approve gates (`RN-SDD-HUMAN-GATE-OWNERSHIP`). |
| **`@orchestrator`** | Structures the task DAG (`03-tasks.md`) into parallel and sequential blocks (`Block`), dispatches tasks to specialists, and monitors context session limits. | Does not write production code in the main thread (`RN-SDD-ORCHESTRATOR-SUBAGENTS`). |
| **`@back-engineer` / `@qa-tester`** | Implement executable contracts and test suites respecting modularity ($\le 500$ lines per file). | Must execute deterministic DoD verification commands without blind exploration. |
| **`@documentator`** | Maintains bilingual living documentation (0DD) and updates technical catalogues and traceability matrices at Gate 5. | Cannot close Gate 5 without certifying 1:1 bilingual consistency. |

---

## 3. Canonical Matrix of Gates and Statuses

| ID | Scope | EN Term | ES Term | Sign-off Criterion |
| :--- | :--- | :--- | :--- | :--- |
| `Gate S0` | Project | Stack Lock | Bloqueo de Stack | `[x] Gate S0 Approved (Human Sign-off)` / `stack_approved: true` |
| `Gate 0` | Work Item | Backlog Intake | Registro en Backlog | Unique ID in `specs/BACKLOG.md` + spec folder in `specs/` |
| `Gate 1` | Work Item | Functional Spec | Especificación Funcional | `[x] Gate 1 Approved (Human Sign-off)` |
| `Gate 2` | Work Item | Technical Spec | Especificación Técnica | `[x] Gate 2 Approved (Human Sign-off)` |
| *Sub-Gate 2V* | Work Item (`SCR-###`) | Visual Sign-off | Validación Visual | `[x] Gate 2 Visual Sign-off (Human)` |
| `Gate 3` | Work Item | Task Graph (DAG) | Plan de Tareas (DAG) | `[x] Gate 3 Approved (Human Sign-off)` *(exempt only under `Origin: brownfield-mined`)* |
| `Gate 4` | Work Item | Implementation & QA | Implementación y QA | Tests + 4 quality audits passing green |
| `Gate 5` | Work Item | Living Docs (0DD) & Closure | Documentación Viva (0DD) y Cierre | `docs/`, `TRACEABILITY-MATRIX.md`, `git push` |
| `Gate 6` | Release | Release Readiness | Preparación de Release | `[x] Gate 6 Approved (Human Sign-off)` in `REL-vX.Y.Z.md` + `CHANGELOG.md` + PR to `main` |

---

## 4. `RFC-003`..`RFC-008` Hardening, CI-Agnostic Engine, `Gate 6` (`v1.2.0`), and Brownfield / *Spec Drift* (`v1.3.0`) (`FWK-005`..`FWK-016`)

- **P0 Fail-Closed Security (`FWK-005`):** `.agents/hooks.json` (UTF-8 without BOM) invokes `sdd_immutable_feature_guard.py` and `sdd_code_gate_guard.py`, requiring `Gate S0` approval and genuine `[x] Gate 1/2/3 Approved` markers in `01..03.md` before modifying `src/`, `tests/`, `.agents/`, or `specs/STACK.md`. `sdd_trim_exec.py` executes subcommands with `shell=False`, and `sdd_hooks.py` removes the `SDD_FORCE_MAIN_PUSH` bypass.
- **`sdd:ownership-map` Compiler, Transactionality, and DAG Engine (`FWK-006`):** `scripts/sdd_ownership.py` compiles ownership zones and enforces `forbid_imports` via AST in `verify_architecture_boundaries.py`; `scripts/sdd_generator_tx.py` materialises with backup/rollback and `content_digest` (`--verify`, `--strict-agents`, `--drain-inboxes`); `scripts/sdd_dag.py` (`--verify`, `--plan`) validates acyclicity in `03-tasks.md` and governs `.agent-inbox/` state transitions.
- **`< 25k` Token Slimming, `/bug-fast-track`, and `domains/` (`FWK-007`):** The starter keeps **9 active base agents** in `.agents/agents/`, **19 opt-in universal specialists** in `.sdd/catalog/specialists-optin/`, and **12 unique canonical archetypes** in `.sdd/catalog/archetypes/`. Scoped defects use `/bug-fast-track` (`specs/bugs/BUG-XXX-<slug>/{01-bug-report,02-fix-spec,03-tasks}.md` generated from `05-bug-fast-track.template.md` while preserving `Gate S0` and `[x] Gate 1/2/3 Approved`), and bounded-context knowledge loads on demand from `domains/<domain-slug>/` (`_template/{overview,decisions}.md`).
- **Multi-Worktree Concurrency and Safe Sync `<= 500L` (`FWK-008` & `FWK-009`):** `sdd_git_state.py` and `sdd_git_worktree.py` isolate per-worktree state (`.agents/worktree_states/<wt_id>.json`) and ports (`ports_registry.json`), auto-synchronising `.agents/ACTIVE_STATE.md`. `sdd_sync.py` operates without hardcoded paths using `--dry-run`, `--force`, and transactional rollback backed by `.agents/.sdd-sync-state.json`. Every Python module in the repository strictly obeys `<= 500` lines.
- **Level L5 Hardening: Cryptographic SHA-256 Gate Seals, Polyglot Boundaries, DAG Write-Set Overlap Detection, and CI Audit (`FWK-010` / `RFC-004`):** `scripts/sdd_gate_seal.py` (`sdd approve-gate`, `sdd verify-gates`) records SHA-256 digests in `.agents/active_work_item.json` (`gate_seals`) and inline comments `<!-- sdd:gate-seal ... -->`, blocking post-approval tampering in `.agents/scripts/sdd_code_gate_guard.py`; `.agents/scripts/verify_architecture_boundaries.py` extends `forbid_imports` via `check_polyglot_imports` across `.ts/.tsx/.js/.jsx/.cs/.go/.rs/.java/.kt` while ignoring comments; `scripts/sdd_dag.py` detects overlapping target paths/globs within parallel waves (`DagWriteSetCollisionError`, `--auto-split`); and CI verifies all `03-tasks.md` files via `sdd_dag.py --verify` while enforcing `>= 120` deterministic tests.
- **POSIX Portability & CI Time Determinism (`FWK-011` / `RFC-005`):** `.agents/scripts/sdd_immutable_feature_guard.py` rejects Windows drive/UNC paths on POSIX (`^[A-Za-z]:` / `\\?\C:\...`) in fail-closed mode, and `tests/test_sdd_governance.py` anchors instinct decay assertions to relative `datetime.now(timezone.utc)` offsets.
- **Coherence Alignment `v1.1.1` (`FWK-012` / `RFC-006`):** `scripts/sdd_cli.py` adds `work-item show/set` in `PENDING_APPROVAL` mode (without auto-approving Gates 1..3); guards, SHA-256 seals, and `sdd_healthcheck.py` support `HOTFIX-*` (triad under `specs/bugs/HOTFIX-*/`) and audit `specs/spikes/SPIKE-*/SPIKE_REPORT.md` together with `06-spike-report.template.md` and `07-hotfix-fast-track.template.md`; `.sdd/catalog/specialists-optin/spec-miner.md` outputs native SDD specs (`specs/features/` and `domains/`) protected by `SDD_CUSTOMIZED_SPECIALISTS` in `scripts/sdd_catalog_import.py`; and `release-finish` / `hotfix-finish` in `scripts/sdd_git.py` default to a PR-first workflow (`--local-merge` opt-in without direct push to `main`).
- **Portable CI-Agnostic Engine (`FWK-013` / `RFC-007`):** `scripts/sdd_ci.py` (invoked as `scripts/sdd_cli.py ci-verify` / `./sdd ci-verify`) unifies all SDD governance checks (`hooks.json` without BOM or path escapes, `sdd_healthcheck`, 0DD compliance, polyglot AST boundaries, catalogue/`squad.lock.json`, `sdd_dag --verify`, SHA-256 gate seals, `sdd_git`/`sdd_instincts`, and `sdd_tokens_validator --allow-missing`) with `text|json` output, automatic `framework` (`>= 120` tests threshold) vs `project` mode detection from `Gate S0`, and fail-closed `shell=False` execution of `specs/STACK.md §2.5` via `--run-stack` / `--run-stack-if-approved`; `.github/workflows/ci.yml` delegates to `ci-verify` and `specs/templates/ci/` provides equivalent templates for GitLab CI, Bitbucket Pipelines, and POSIX shell.
- **`Gate 6` Release Readiness and Deterministic `CHANGELOG.md` (`FWK-014` / `RFC-007`, `v1.2.0`):** `scripts/sdd_release.py` (`./sdd release prepare|changelog|verify`) instantiates `specs/releases/REL-vX.Y.Z.md` from `specs/templates/08-release-readiness.template.md` without auto-approving `Gate 6`, builds idempotent `CHANGELOG.md` entries from `<prev_tag>..HEAD` cross-referenced with `BACKLOG.md` and `01-*.md`, and integrates fail-closed `_run_release_preflight` in `scripts/sdd_git.py` (`release-start` / `release-finish`) alongside `.agents/workflows/gate6-release.md` and `REL-*` exemption in `sdd_ci.py` (`check_gate_seals`).
- **Non-Destructive Brownfield Adoption (`FWK-015` / `RFC-008`, `v1.3.0`):** `scripts/sdd_brownfield.py` (`./sdd adopt --dry-run|--apply`, `--with-repo-map`) performs 100% offline discovery of manifests, ecosystems, candidate ownership zones, and bounded contexts (`MAX_SCAN_DEPTH = 3`), filters unsafe manifest scripts via `split_safe_chained_command`, generates non-destructive drafts (`specs/STACK.md` with `Gate S0` locked `stack_approved: false`, `docs/knowledge/BROWNFIELD_INVENTORY.md`, and `specs/BACKLOG.md`), and chains into `.agents/workflows/brownfield-adopt.md` + `./sdd repo-map` + `@spec-miner`.
- **Offline *Spec Drift* Detector, *Strangler Fig* Zones, and Light Retroactive Baseline (`FWK-016` / `RFC-008`, `v1.3.0`):** `scripts/sdd_drift.py` (`./sdd drift`) detects `UNCOVERED_FILE`, `MISSING_SOURCE_FILE`, `MISSING_SYMBOL`, and `UNLINKED_CODE_DRIFT` offline across `governed` zones, `SRC-###` citations, and closed `CR-XXX` lifecycles without mutating `Done` features; `scripts/sdd_ownership.py` and `.agents/scripts/sdd_code_gate_guard.py` enforce `governance: governed | legacy-readonly` (*Strangler Fig* lock); `sdd_healthcheck.py` and `sdd_gate_seal.py` support `Origin: brownfield-mined` retroactive baselines (exempting `03-tasks.md` only when genuine human `[x] Gate 1 Approved` and `[x] Gate 2 Approved` markers exist); and `sdd_ci.py` integrates `check_spec_drift` (`160/160` tests passing across `15` suites).
