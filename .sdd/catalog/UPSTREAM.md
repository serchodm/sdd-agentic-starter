# SDD Agentic Catalog — Upstream Attribution & Tracking

This catalog (`.sdd/catalog/`) contains the framework's reusable archetype recipes, clean ECC specialists, and language/framework/capability stack packs.

## Upstream Tracking
- **Upstream Repository**: `affaan-m/ecc` (Everything Claude Code)
- **Upstream Branch**: `main`
- **License**: MIT License
- **Copyright**: (c) 2026 Affaan Mustafa
- **Import Methodology**:
  - Reviewers and build resolvers are converted to SDD Subagents with the standard Prompt Defense baseline and read-only safety restrictions (`tools: read, grep, glob, bash` where allowed; no unauthorized direct writes).
  - Language rules from `rules/common/` are condensed into `07-engineering-baseline.md`.
  - Framework rules and skills are encapsulated into discrete, lazy-loadable stack packs (`.sdd/catalog/packs/`).
