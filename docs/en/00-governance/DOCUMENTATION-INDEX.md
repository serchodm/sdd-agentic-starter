<p align="right">
  <strong>🇬🇧 English (EN-GB)</strong> | <a href="../../es/00-governance/DOCUMENTATION-INDEX.md">🇪🇸 Español (ES-ES)</a>
</p>

# Functional Documentation Index (`00-governance`)

## Product Information
- **Product:** `sdd-agentic-starter` (Spec-Driven Development Agentic Starter Template)
- **Brief description:** Multi-stack starter governed by SDD gates (Gate 00 to Gate 5), featuring an inert catalogue of archetypes, universal specialists, and technology packs activated deterministically and fail-closed, including offline UI/UX governance (`capability-ui-design`).
- **Active functional version / baseline:** `FWK-001` + `FWK-002` (`RFC-001` v2 — Reliable Pack Materialisation and `capability-ui-design` Pack)
- **Overall status:** `Verified` (for `FWK-001` and `FWK-002`); user project application pending Gate 00
- **Functional custodian:** `@documentator` (supervised by `@orchestrator`)

---

## How to Use This Documentation

1. This documentation follows the modular standard in [`FUNCTIONAL_DOCUMENTATION_STANDARD.md`](../../standards/FUNCTIONAL_DOCUMENTATION_STANDARD.md): it contains only artefacts backed by real, confirmed scope without empty placeholder folders (such as an empty `docs/design-system/` in the starter).
2. Each document clearly separates **Confirmed** facts (backed by approved specifications and verified by tests) from **Excluded / Deferred** future scope (`FWK-003`, `FWK-004`, and project features after Gate 00).
3. All functional documentation maintains strict **1:1** equivalence between [`docs/en/`](../README.md) and [`docs/es/`](../../es/README.md).

---

## 1. Functionality (`02-functional`)
- [**`MOD-001`: Reliable Pack Materialisation and Activation**](../02-functional/modules/MOD-001/pack-materialization.md) (`Verified` — covers `FWK-001`: `RF-001`..`RF-010`, `RN-01`..`RN-05`, operational flows, and BDD acceptance scenarios 1–7).
- [**`MOD-002`: `capability-ui-design` Pack and SDD Visual Governance**](../02-functional/modules/MOD-002/capability-ui-design.md) (`Verified` — covers `FWK-002`: `RF-001`..`RF-012`, `RN-01`..`RN-07`, `REL-VENDOR-INTEGRITY-01`, `PERF-FWK-TESTS-01`, Gate 2 / semver flows, and BDD scenarios 1–7).

## 2. Traceability and Technical Knowledge (`06-traceability` / `knowledge`)
- [**Bidirectional Traceability Matrix (0DD)**](../../traceability/TRACEABILITY-MATRIX.md)
- [**Architecture Decision Records (`ADRS.md`)**](../../knowledge/ADRS.md) *(includes `ADR-001`, `ADR-002`, and `ADR-003`)*
- [**System Topology (`SYSTEM_TOPOLOGY.md`)**](../../knowledge/SYSTEM_TOPOLOGY.md)
- [**Data Models (`DATA_MODELS.md`)**](../../knowledge/DATA_MODELS.md)
- [**Interface & CLI Catalogue (`API_CATALOG.md`)**](../../knowledge/API_CATALOG.md)

---

## Status and Risks

| Aspect | Current Status (Confirmed) |
| :--- | :--- |
| **Approved & verified artefacts** | `MOD-001` (`FWK-001`) and `MOD-002` (`FWK-002`: `RF-001`..`RF-012`, `RN-01`..`RN-07`, BDD Scenarios 1–7; `37` offline tests in `tests/`). |
| **Open decisions** | None in `FWK-001` or `FWK-002` (`AMB-001`..`AMB-007` resolved at Gate 1; `<PIN_APROBADO> = "2.15.0"` validated after Gate 2 PoC spike). |
| **Risks mitigated in this baseline** | Accidental pack activation from prose (`FWK-001` `RN-01`), global always-on rule pollution (`ADR-002`), artisanal skill overwriting, silent loss of manual edits, ECC `design-system` collision / runtime `npx` usage (`ADR-003`), Windows SHA-256 mismatch (`VENDOR.lock.json` + `.gitattributes`), hi-fi bypassing Gate 1 (`RN-04`), and `RN-SDD-IMMUTABLE-DONE` breakage (`RN-07`). |
| **Next steps (outside this baseline)** | `FWK-003` (visual quality gates), `FWK-004` (Gate terminology unification), and user project Gate 00 in `specs/STACK.md`. |
