# SDD Starter — Active Session Pointer (Managed by @orchestrator)
- **Timestamp:** 2026-11-09 09:10
- **Active Work Item:** IDLE (Starter Template Ready)
- **Active Branch:** `develop`
- **Spec Folder Path:** None
- **Current Gate:** Gate 00 (Stack Bootstrap / Ready)
- **Recommended Model Tier:** Reasoning (Argon/Opus) for Gates 00-3 | Execution (Flash/Sonnet) for Gates 4-5
- **Last Completed Milestone:** Release v1.0.0 successfully completed, merged to `main` via PR #1, and back-synchronized to `develop`. Starter baseline 10/10 Vanguardia achieved.
- **Next Execution Target:** Run Gate 00 in specs/STACK.md or pick a Feature in specs/BACKLOG.md
- **Mandatory Context Files (MAX 4 FILES):**
  1. `AGENTS.md`
  2. `specs/STACK.md`
  3. `specs/BACKLOG.md`
- **Critical Technical Decisions / Snapshot:**
  - Official Release v1.0.0 merged into `main` with green CI.
  - Branch protection active on `main` (zero direct commits) and `develop` (protected integration).
  - Git worktrees isolated in `.worktrees/` with dynamic ports and test databases.
  - Cross-platform Universal CLI (`./sdd`, `.\sdd.ps1`, `sdd.cmd`) and native hooks (`.githooks/`).
  - Atomic instincts engine active in `.agents/instincts.json` via continuous-learning-v2 + MemGPT semantic clustering.
