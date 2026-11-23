---
name: pipeline-run
description: Executes the full autonomous SDD development lifecycle for an approved Feature (specs/features/FEAT-XXX) or Change Request (specs/changes/CR-XXX) across specialist agents, ending with compliance/test audits and regression verification.
---

# Skill: `pipeline-run`

Executes Gate 4 & Gate 5 for an approved `FEAT-XXX`, `CR-XXX`, or `BUG-XXX` (Gates 1–3 human-signed).

## Parameters & Pre-Flight
- **Input:** `<work-item-id>` (e.g. `FEAT-001-scaffolding`, `CR-002-checkout-flow`).
- **Pre-Flight:**
  1. Resolve `<spec-dir>` (`specs/features/`, `specs/changes/`, or `specs/bugs/`) and verify `01-spec.md`, `02-tech-spec.md`, `03-tasks.md` are approved (`RN-SDD-GATE2-CODE-LOCK`).
  2. Verify `.agents/active_work_item.json` has `active_work_item_id = <work-item-id>` and `approved_by_human = true`.
  3. Abort immediately if a `FEAT-XXX` is already `Done` in `specs/BACKLOG.md` (`RN-SDD-IMMUTABLE-DONE`).

## Multi-Agent DAG Execution (`RN-SDD-ORCHESTRATOR-SUBAGENTS`)
`@orchestrator` never writes `src/` or `tests/` code; it dispatches `<spec-dir>/03-tasks.md` block by block via `opsx-delegate` + `invoke_subagent` / `runSubAgent`:
1. **`[PARALLEL]` Blocks:** Dispatch orthogonal tasks concurrently across Ownership Map zones and wait reactively at the Synchronization Barrier until all return green.
2. **`[SEQUENTIAL]` Blocks:** Execute after prerequisite blocks pass, verifying `[x]` checkboxes in `03-tasks.md`.
3. **QA & Boundary Audit Block (Gate 4 — Layer 1 Deterministic $\rightarrow$ Layer 2 Conditional Santa):**
   - **Layer 1 (Deterministic, always):** Run `sdd-spec-compliance-audit`, `sdd-silent-failure-audit`, `sdd-test-quality-audit`, `uv run python .agents/scripts/verify_architecture_boundaries.py`, full §2.5 DoD suites from `specs/STACK.md`, and `uv run python .agents/scripts/sdd_healthcheck.py`.
   - **Layer 2 (Semantic, conditional):** Only after Layer 1 is green, evaluate `.agents/skills/santa-method/SKILL.md` Gate 4 triggers (risk or volume/context-contamination). If triggered, run `/santa-loop` (`GATE_4` rubric, 2 fresh isolated reviewers) until `NICE + NICE` (max 3 rounds before human escalation).
   - **Conditional Auto-Learn (Gate 4):** Only if `BLOCKED_*.md`, audit/test failures, `NAUGHTY` Santa rounds, or user corrections occurred during Gate 4, record 1–2 atomic instincts via `uv run python scripts/sdd_instincts.py record` (skip if clean).
4. **Gate 5 Living Docs (`@documentator`, `RN-SDD-0DD`):** Update `docs/knowledge/{API_CATALOG,DATA_MODELS,ADRS,SYSTEM_TOPOLOGY}.md`, `docs/es/`, `docs/en/`, `docs/traceability/TRACEABILITY-MATRIX.md`; if `santa-method` Gate 5 triggers apply (public contract docs or $\ge 4$ docs modified), run `/santa-loop` (`GATE_5` rubric, or *Batch Sampling* if $> 15$ docs) before closure; run conditional `sdd_instincts.py record` + read-only `sdd_instincts.py evolve` (notify user if promotion candidates appear; never auto-edit `.agents/rules/` or `.agents/skills/`), mark `Done` in `specs/BACKLOG.md`, reset `.agents/active_work_item.json`, and run `git add` / `commit` / `push origin <branch>` (`RN-SDD-BRANCH-SYNC`).
