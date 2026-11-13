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
- **Project Application:** Pending technology definition and human sign-off at **Gate S0** (`specs/STACK.md`, with legacy support for `Gate 00`). Until then, this documentation covers the operational behaviour of the starter's pack materialisation, activation, offline UI/UX vendoring, catalogue import engine, and unified agentic governance.

---

## Reading Map

| Block / Resource | Contents | Link |
| :--- | :--- | :--- |
| **Master Index (`00-governance`)** | Normative entry point, artefact statuses, and active documentation scope. | [DOCUMENTATION-INDEX.md](./00-governance/DOCUMENTATION-INDEX.md) |
| **Module `MOD-001` (`02-functional`)** | Functional and operational guide for pack materialisation (`sdd:stack-config`, Gate S0 / Gate 00, lazy loading, fail-closed cleanup, and catalogue import). | [pack-materialization.md](./02-functional/modules/MOD-001/pack-materialization.md) |
| **Module `MOD-002` (`02-functional`)** | Functional guide for `capability-ui-design` (offline `ui-ux-pro-max@2.15.0` vendoring with `VENDOR.lock.json`, `uiux` pruning in `sdd-bootstrap`, Gate 2 review with `@ui-ux-designer` + `@a11y-architect`, `docs/design-system/` semver lifecycle, `sdd_tokens_validator.py` validator, and Gate 4 bi-level visual quality gates). | [capability-ui-design.md](./02-functional/modules/MOD-002/capability-ui-design.md) |
| **Module `MOD-003` (`02-functional`)** | Unification of Gate terminology (`Gate S0`, `Gate 0..5`), statuses (`Candidate`..`Done`), DAG blocks (`Block`), session phases, and fail-closed dual-accept support. | [gate-terminology-unification.md](./02-functional/modules/MOD-003/gate-terminology-unification.md) |
| **Knowledge Base (`docs/knowledge/`)** | Architecture decision records (`ADR-001`..`ADR-005`), system topology, data models, and CLI/API catalogue. | [ADRS.md](../knowledge/ADRS.md) · [SYSTEM_TOPOLOGY.md](../knowledge/SYSTEM_TOPOLOGY.md) · [DATA_MODELS.md](../knowledge/DATA_MODELS.md) · [API_CATALOG.md](../knowledge/API_CATALOG.md) |
| **Traceability Matrix (0DD)** | Bidirectional traceability for `FWK-001` through `FWK-004` from EARS requirements, business rules, and NFRs to code, offline tests, and documentation. | [TRACEABILITY-MATRIX.md](../traceability/TRACEABILITY-MATRIX.md) |
