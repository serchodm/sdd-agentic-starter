<p align="right">
  <strong>🇬🇧 English (EN-GB)</strong> | <a href="../../es/00-governance/DOCUMENTATION-INDEX.md">🇪🇸 Español (ES-ES)</a>
</p>

# Functional Documentation Index (`00-governance`)

## Product Information
- **Product:** `sdd-agentic-starter` (Agentic Starter Template under Spec-Driven Development)
- **Brief description:** Multi-stack template governed by SDD quality gates (Gate S0, Gate 0 to Gate 5), featuring an inert catalogue of archetypes, universal specialists, and technology packs activated deterministically and *fail-closed*, including offline UI/UX governance (`capability-ui-design`) and unified DAG orchestration.
- **Current version / functional baseline:** `FWK-001`..`FWK-010` (`RFC-001` v2, `RFC-002`, `RFC-003`, and `RFC-004` — Reliable Pack Materialisation, `capability-ui-design` Pack, Conditional Visual Quality Gates, Gate Terminology Unification, P0 Fail-Closed Security, `sdd:ownership-map` Compiler + DAG Engine, `< 25k` Token Slimming + `/bug-fast-track` + `domains/`, Multi-Worktree Concurrency, Safe Sync `<= 500L`, and L5 Perfection Hardening: Cryptographic SHA-256 Gate Seals, Polyglot Boundaries, DAG Write-Set Overlap Detection, and CI Audit)
- **Global status:** `Verified` (for `FWK-001`..`FWK-010`, `123/123` offline tests across `11` suites); user application pending Gate S0
- **Functional owner:** `@documentator` (supervised by `@orchestrator`)

---

## How to Use This Documentation

1. This documentation follows the modular standard in [`FUNCTIONAL_DOCUMENTATION_STANDARD.md`](../../standards/FUNCTIONAL_DOCUMENTATION_STANDARD.md): it contains exclusively artefacts with confirmed real content; no empty folders or unbacked templates are created.
2. Each document explicitly distinguishes between **Confirmed** facts (supported by approved specifications and verified by tests) and future **Excluded / Deferred** scope (project features after Gate S0).
3. All functional literature maintains strict **1:1** parity between [`docs/es/`](../../es/README.md) and [`docs/en/`](../README.md).

---

## 1. Functionality (`02-functional`)
- [**`MOD-001`: Reliable Pack Materialisation and Activation**](../02-functional/modules/MOD-001/pack-materialization.md) (`Verified` — covers `FWK-001`: `RF-001`..`RF-010`, `RN-01`..`RN-05`, operational flows, and BDD acceptance criteria 1–7).
- [**`MOD-002`: `capability-ui-design` Pack, Visual Governance, and SDD Quality Gates**](../02-functional/modules/MOD-002/capability-ui-design.md) (`Verified` — covers `FWK-002` and `FWK-003`: `RF-001`..`RF-012`, `RN-01`..`RN-07` of FWK-002; `RF-001`..`RF-010`, `RN-01`..`RN-05` of FWK-003, `sdd_tokens_validator.py` validator, Gate 4 bi-level flows, and 45 offline tests).
- [**`MOD-003`: Gate Terminology, Status, and DAG Graph Unification**](../02-functional/modules/MOD-003/gate-terminology-unification.md) (`Verified` — covers `FWK-004`..`FWK-010`: `RF-001`..`RF-007`, canonisation of `Gate S0` / `Gate 0..5`, `Block`, `Session Phase`, fail-closed dual-accept support, P0 security, `sdd:ownership-map` compiler, DAG engine with `Write-Set` collision detection, SHA-256 gate sealing, and polyglot boundary scanner).

## 2. Traceability and Technical Knowledge (`06-traceability` / `knowledge`)
- [**Bidirectional Traceability Matrix (0DD)**](../../traceability/TRACEABILITY-MATRIX.md)
- [**Architecture Decision Records (`ADRS.md`)**](../../knowledge/ADRS.md) *(includes `ADR-001` through `ADR-009`)*
- [**System Topology (`SYSTEM_TOPOLOGY.md`)**](../../knowledge/SYSTEM_TOPOLOGY.md)
- [**Data Models (`DATA_MODELS.md`)**](../../knowledge/DATA_MODELS.md)
- [**Interface and CLI Catalogue (`API_CATALOG.md`)**](../../knowledge/API_CATALOG.md)

---

## Status and Risks

| Aspect | Current Situation (Confirmed) |
| :--- | :--- |
| **Approved and verified artefacts** | `MOD-001` (`FWK-001`, `FWK-006`, `FWK-009`), `MOD-002` (`FWK-002` and `FWK-003`), and `MOD-003` (`FWK-004`, `FWK-005`, `FWK-007`, `FWK-008`, `FWK-010`: `123` offline tests across `11` modules in `tests/`). |
| **Open decisions** | None in `FWK-001`..`FWK-010` (`RFC-001`..`RFC-004` fully accepted and implemented). |
| **Mitigated risks in this baseline** | Accidental activation via prose (`FWK-001`), always-on pollution (`ADR-002`), ECC `design-system` collision / `npx` execution (`ADR-003`), Windows SHA-256 CRLF corruption, visual token and baseline drift (`ADR-004`), numeric collision `Gate 00` vs `Gate 0` (`ADR-005`), P0 fail-open vectors and decorative ownership (`ADR-006`), context bloat (`ADR-007`), multi-worktree races and unsafe sync (`ADR-008`), post-approval mutation of Gates 1..3, forbidden imports in polyglot stacks, and write-set collisions in parallel DAG waves (`ADR-009`). |
| **Next steps (outside this baseline)** | Gate S0 of user project in `specs/STACK.md`. |
