<p align="right">
  <strong>🇬🇧 English (EN-GB)</strong> | <a href="../../../../es/02-functional/modules/MOD-001/pack-materialization.md">🇪🇸 Español (ES-ES)</a>
</p>

# `MOD-001`: Reliable Pack Materialisation and Activation

- **Module Identifier:** `MOD-001`
- **Source Work Item / RFC:** `FWK-001-pack-materialization` ([`RFC-001` v2](../../../../../.sdd/framework/rfcs/RFC-001-ui-ux-pro-max.md))
- **Functional Status:** `Verified` (Confirmed and verified by deterministic offline tests)
- **Master Index:** [DOCUMENTATION-INDEX.md](../../../00-governance/DOCUMENTATION-INDEX.md)

---

## 1. Purpose and Scope

### 1.1. Purpose (Confirmed)
This module ensures that **Stack Packs** from the inert catalogue (`.sdd/catalog/packs/`) and the baseline agent squad (`.agents/`) are selected, materialised, updated, cleaned up, and imported in a **deterministic, traceable, and fail-closed** manner.

Before `FWK-001`, the generator matched technology names across the entire prose of `specs/STACK.md` (activating phantom packs from template examples), ignored pack *skills*, *rules*, and *workflows*, tracked no per-file hashes, and failed to clean up deactivated resources. `MOD-001` eliminates those root causes.

### 1.2. In-Scope (Confirmed)
- Selecting configuration and packs exclusively from the structured ```` ```yaml sdd:stack-config ```` block in `specs/STACK.md`.
- Strictly blocking stack-declared packs while **Gate 00** is unapproved, permitting only explicit manual activations via `--packs`.
- Full, idempotent materialisation of all 4 pack asset types (`specialists`/`agents`, `skills`, `rules`, and `workflows`), alongside builders and the 20 universal specialists.
- Isolating pack rules under `.agents/pack-rules/<pack>/` to preserve lazy context loading (`RN-SDD-SELECTIVE-CONTEXT`).
- Recording provenance (`GENERATED`) and per-file SHA-256 hashes in `.agents/squad.lock.json` (`schema_version: 2`).
- Atomic fail-closed pre-flight validation before any disk mutation: `requires` dependencies, `pack.json` manifests, anti-traversal path checks, intra-pack or unmanaged artisanal destination collisions, and manual edit conflicts.
- Safe cleanup of deactivated pack files and empty inboxes while preserving any inbox holding pending work tickets.
- Downloading `workflows` in the catalogue importer without altering or deleting packs outside `STACK_PACKS`, plus sync protection in `sdd_sync.py`.
- Sanitising the repository starter template in line with an unapproved Gate 00 state.

### 1.3. Explicitly Out-of-Scope (Future Scope)
- Creating or vendoring the `capability-ui-design` pack, `@ui-ux-designer`, `sdd_vendor_update.py`, or `uiux` prompts in `sdd-bootstrap` (belongs to `FWK-002`).
- Visual quality gates, contrast checks, screenshots, or changes to `@a11y-architect` / `@qa-tester` (belongs to `FWK-003`).
- Global Gate terminology unification across `SDD_FRAMEWORK.md` / `BACKLOG.md` / `AGENTS.md` (belongs to `FWK-004`).

---

## 2. Actors and Authority

| Actor | Responsibility | Primary Constraint |
| :--- | :--- | :--- |
| **Human Stakeholder** | Approves **Gate 00** in `specs/STACK.md` (`[x] Gate 00 Approved` + `gate00_approved: true`). | AI agents must never self-approve Gate 00 (`RN-SDD-HUMAN-GATE-OWNERSHIP`). |
| **Developer / `@orchestrator`** | Configures the `sdd:stack-config` block, inspects the catalogue (`--list`), and runs materialisation (`--materialize`) or manual activation (`--packs`). | Must not manually edit generated files; builder customisations belong in `.agents/overrides/<builder>.md`. |
| **Catalogue Maintainer** | Runs `scripts/sdd_catalog_import.py` to refresh universal specialists and `STACK_PACKS` from `affaan-m/ecc`. | External or custom packs inside `.sdd/catalog/packs/` remain untouched (`RN-05`). |

---

## 3. Activation Rules and System Behaviour

### 3.1. Single Activation Source (`RN-01`) and Dual Gate 00 Verification (`RN-02`)
1. The system reads **only** the fenced ```` ```yaml sdd:stack-config ```` block in `specs/STACK.md`. Any technology or framework mentions in prose, tables, or examples outside that block are ignored.
2. At most **one** valid, properly closed `yaml sdd:stack-config` block may exist; multiple blocks, an unclosed fence, or invalid syntax/values (such as tabs, duplicate keys, non-boolean `gate00_approved`, or an unknown `preset`) abort with an error before touching disk.
3. Automatic activation of packs listed in `sdd:stack-config` requires **both** conditions simultaneously:
   - Human sign-off marker in `specs/STACK.md`: `[x] Gate 00 Approved` (or `[X] Gate 00 Approved`).
   - Strict boolean `gate00_approved: true` inside the `sdd:stack-config` block.
4. **When Gate 00 is NOT approved:**
   - If the `sdd:stack-config` block is missing and there is no `[x]` human sign-off, the system safely defaults to `preset: compact` and `packs: []`.
   - Any packs listed inside `sdd:stack-config` are **ignored**.
   - Packs can only be activated explicitly via the CLI `--packs <name...>` flag, and are recorded in `.agents/squad.lock.json` with `"source": "manual"`.
5. **If human sign-off `[x]` is present without a `sdd:stack-config` block:** the system fails explicitly (*fail-closed*).
6. **When Gate 00 IS approved:** packs from `sdd:stack-config` activate with `"source": "stack-config"`, and any extra `--packs` entries not already listed are appended with `"source": "manual"`.

### 3.2. Materialisation Destinations and Context Isolation
On every valid materialisation run (even with `active_packs: []` prior to Gate 00), the selected preset's builders (`compact`, `granular`, `api-only`, or `spa-only`) and all **20 universal specialists** from `.sdd/catalog/specialists/` are materialised (`AMB-001`).

For each active pack (referenced by directory name, e.g. `lang-python`, or by `id`, e.g. `lang:python`):

| Asset Type in `pack.json` | Materialised Destination | Special Behaviour |
| :--- | :--- | :--- |
| **`specialists` (pack agents)** | `.agents/agents/<file>.md` + `.agent-inbox/<agent>/.gitkeep` | Receives `GENERATED` header after YAML frontmatter; inbox folder is created automatically. |
| **`skills`** | `.agents/skills/<slug>/<rel_path>` | Full recursive copy (Markdown and helper files such as `.py`, `.json`, etc.); every skill directory must contain `SKILL.md`. |
| **`rules`** | `.agents/pack-rules/<pack>/<file>.md` | **Never** placed in `.agents/rules/`, preserving lazy loading (`RN-SDD-SELECTIVE-CONTEXT`) and preventing filename collisions such as `coding-style.md` across combinable packs. |
| **`workflows`** | `.agents/workflows/<file>.md` | Receives `GENERATED` header after YAML frontmatter when applicable. |

### 3.3. Provenance (`GENERATED`) and Lock v2
- Every generated Markdown file receives the marker `<!-- GENERATED by sdd_agent_generator (<owner>). Do not edit directly. -->`:
  - If the file begins with YAML frontmatter (`--- ... ---`), the marker is inserted **immediately after** the closing `---` so IDE frontmatter parsers remain valid.
  - Otherwise, it is prepended on line 1.
- Non-Markdown files inside a skill (e.g. `.py`, `.json`, `.csv`, `.sh`) do **not** receive HTML comments; their provenance and integrity are tracked by relative path and **SHA-256** hash in `.agents/squad.lock.json` (`schema_version: 2`).
- **Idempotency:** consecutive runs with unchanged configuration and catalogue yield identical files on disk and preserve the existing lock `timestamp` without rewriting `.agents/squad.lock.json`.

### 3.4. Fail-Closed Validations and Safe Cleanup (`RN-03`, `RN-04`)
Before writing or deleting **a single byte** under `.agents/` or `.agent-inbox/`, the system validates the entire plan:
1. **Dependencies (`requires`):** if an active pack requires another pack (e.g. `framework-fastapi` requires `lang:python`) that is absent from the active set, execution aborts naming the missing dependencies.
2. **Manifest integrity and anti-traversal:** malformed `pack.json`, missing required fields (`id`, `family`, `description`, asset lists), duplicate pack IDs across the catalogue, missing referenced files, absolute paths, or `..` escapes fail immediately.
3. **Intra-plan collisions:** if two active packs target the same destination (e.g. two packs declaring the same skill slug or workflow), execution aborts naming both owners and the colliding path.
4. **Protection of unmanaged artisanal destinations (`AMB-002`):** if a target file already exists on disk without being tracked in `.agents/squad.lock.json` (such as the starter's artisanal `fastapi-patterns` or `postgres-patterns` skills), execution aborts without overwriting it.
5. **Manual edit protection (`RN-03`):** if a managed file's SHA-256 on disk differs from the hash recorded in `squad.lock.json`, both re-materialisation and pack deactivation **abort** without deleting or overwriting the user's changes.
6. **Safe deactivation cleanup:** when hashes match cleanly, files belonging to deactivated packs are removed and empty subdirectories under `.agents/skills/` and `.agents/pack-rules/` are pruned. An `.agent-inbox/<agent>/` directory is removed only if it contains nothing other than `.gitkeep`; if pending tickets exist, the folder is preserved with a `[WARN]` notice.

### 3.5. Catalogue Import and Synchronisation (`RN-05`)
- `scripts/sdd_catalog_import.py` fetches universal specialists and all `STACK_PACKS` assets, **including `workflows`** (creating `<pack>/workflows/` only when the workflows list is non-empty), adapts agent frontmatter, and records `[WARN]` notices for any failed download without aborting remaining packs.
- The importer operates solely on `STACK_PACKS`: any external or custom pack directory under `.sdd/catalog/packs/` remains **byte-for-byte untouched**.
- `scripts/sdd_sync.py` excludes every path recorded in `squad.lock.json["files"]` and expands its `GENERATED` header inspection window to `4096` characters (accommodating long YAML frontmatters), preventing generated files from contaminating the starter template.

---

## 4. Step-by-Step Operational Flows

### Flow 1: Inspect available packs and presets
1. Run `uv run python scripts/sdd_agent_generator.py --list`.
2. The tool loads and validates the catalogue manifests and prints available archetypes, universal specialists, stack packs (with `id` and description), and presets (`compact`, `granular`, `api-only`, `spa-only`).

### Flow 2: Activate or trial a pack manually before Gate 00 sign-off
1. With Gate 00 unapproved in `specs/STACK.md`, run for example:
   `uv run python scripts/sdd_agent_generator.py --materialize --packs lang-python`
2. The generator ignores `packs:` inside `sdd:stack-config` (because Gate 00 is unapproved) and materialises only `lang-python` alongside the baseline (builders + 20 specialists), recording `"source": "manual"` in `.agents/squad.lock.json`.

### Flow 3: Activate the full stack after Gate 00 approval
1. Complete `specs/STACK.md`, tick `[x] Gate 00 Approved (Human Sign-off)`, and configure the block:
   ````yaml
   ```yaml sdd:stack-config
   gate00_approved: true
   preset: compact
   packs:
     - lang-python
     - capability-database
   ```
   ````
2. Run `uv run python scripts/sdd_agent_generator.py --materialize`.
3. If an existing artisanal skill collides with a pack skill (e.g. `postgres-patterns`), execution halts with a collision error so the user can explicitly decide whether to keep or retire the artisanal version before retrying.

### Flow 4: Safely deactivate a pack without losing work
1. Remove the pack from `packs:` in `sdd:stack-config` (or run `--materialize` without `--packs` if activated manually).
2. Provided no managed files were manually edited, its pack agents, skills, `pack-rules/<pack>/`, and workflows are removed cleanly from `.agents/`.
3. If any file was manually edited, execution aborts reporting the exact path so the user can resolve the conflict safely.

### Flow 5: Customise a builder agent safely
1. Create or edit `.agents/overrides/<builder>.md` (for example `.agents/overrides/back-engineer.md`).
2. When running `--materialize`, the generator prioritises that override file over the base archetype and inserts the corresponding override marker.

---

## 5. Verified Baseline State of the Starter Template (`RF-010`)

In the clean starter template (with `[ ] Gate 00 Approved`):
- `specs/STACK.md` contains the initial `sdd:stack-config` block (`gate00_approved: false`, `preset: compact`, `packs: []`).
- `.agents/agents/` holds exactly **28** agents (6 core + 2 builders `back-engineer`/`front-engineer` + 20 universal specialists) and **0** pack agents.
- `.agent-inbox/` contains the **28** matching subdirectories.
- `.agents/pack-rules/` does not exist until a pack with rules is activated.
- `.agents/squad.lock.json` uses `schema_version: 2`, `gate00_approved: false`, `active_packs: []`, and **22** SHA-256 tracked entries in `files` (2 builders + 20 specialists).

---

## 6. Verified Requirements, Business Rules, and Acceptance Criteria

| Reference | Summary | Status |
| :--- | :--- | :--- |
| `RF-001`, `RN-01` | Strict selection solely from the `yaml sdd:stack-config` block, ignoring prose and examples. | `Verified` |
| `RF-002`, `RN-02` | Dual Gate 00 lock (`[x]` + `gate00_approved: true`) and manual `--packs` activation mode. | `Verified` |
| `RF-003` | Materialisation of all 4 asset kinds with lazy rule isolation in `.agents/pack-rules/<pack>/`. | `Verified` |
| `RF-004` | `GENERATED` header preserving YAML frontmatter and SHA-256 tracking in `squad.lock.json` v2. | `Verified` |
| `RF-005`, `RN-03` | Safe deactivation cleanup, inbox preservation with pending tickets, and manual edit conflict abort. | `Verified` |
| `RF-006`, `RN-04` | Atomic pre-flight detection of intra-pack collisions and unmanaged artisanal destinations. | `Verified` |
| `RF-007`, `REL-GEN-DETERMINISM-01` | 100% idempotency across consecutive runs (identical hashes and preserved lock `timestamp`). | `Verified` |
| `RF-008` | Fail-closed validation of `pack.json`, `requires` dependencies, and anti-traversal paths. | `Verified` |
| `RF-009`, `RN-05` | Downloading `workflows` in `sdd_catalog_import.py` while keeping external packs untouched. | `Verified` |
| `RF-010` | Full starter template sanitisation free of orphaned pack agents. | `Verified` |
| `PERF-TEST-OFFLINE-01` | 100% offline unit test suite (`< 2.0s`, `0` real network requests). | `Verified` |

*(For exact source file and test method mappings, see [TRACEABILITY-MATRIX.md](../../../../traceability/TRACEABILITY-MATRIX.md)).*
