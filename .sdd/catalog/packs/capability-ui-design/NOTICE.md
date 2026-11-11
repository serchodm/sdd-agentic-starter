# Third-Party Notice & Provenance (`capability-ui-design`)

## 1. Upstream Attribution (Vendorized Design Intelligence)

This pack vendors third-party design intelligence data and offline search scripts from:

- **Upstream Repository**: `nextlevelbuilder/ui-ux-pro-max-skill`
- **Upstream Package**: `ui-ux-pro-max-cli@2.15.0`
- **License**: MIT License
- **Copyright**: `Copyright (c) 2024 Next Level Builder`
- **Full License Copy**: [`vendor/ui-ux-pro-max/LICENSE`](vendor/ui-ux-pro-max/LICENSE)
- **Integrity Lock Manifest**: [`vendor/ui-ux-pro-max/VENDOR.lock.json`](vendor/ui-ux-pro-max/VENDOR.lock.json)

## 2. Exclusive Extraction Scope

When staging `ui-ux-pro-max-cli@2.15.0` (`init --ai antigravity --offline`) in an isolated temporary directory via `scripts/sdd_vendor_update.py`, this pack extracts **exclusively** `.agents/skills/ui-ux-pro-max/` (`45` upstream runtime files: `SKILL.md`, `data/*.csv`, `data/*.json`, `data/stacks/*.csv`, and Python stdlib scripts under `scripts/`, plus `LICENSE` MIT = `46` entries in `VENDOR.lock.json`).

The following upstream contents are explicitly **excluded and discarded**:

- Sibling skills installed by the upstream CLI (`banner-design`, `brand`, `design`, `design-system` which would collide with `capability-web-frontend/skills/design-system`, `slides`, and `ui-styling` which carries an Apache 2.0 `LICENSE.txt`).
- Upstream test suites (`scripts/tests/`).

## 3. Provenance Separation from `affaan-m/ecc`

- `capability-ui-design` is a standalone, non-ECC SDD capability pack located outside `STACK_PACKS` in `scripts/sdd_catalog_import.py`.
- Its SDD-authored artefacts (`pack.json`, `NOTICE.md`, `agents/ui-ux-designer.md`, `skills/sdd-ui-design/SKILL.md`, `workflows/ui-design-review.md`) and its vendorized upstream assets (`vendor/ui-ux-pro-max/`) are **not** sourced from `affaan-m/ecc` and must never be attributed to ECC or modified by `scripts/sdd_catalog_import.py`.
- Accessibility and frontend quality assets from ECC (`@a11y-architect`, `design-system`, `accessibility`, `browser-qa`, etc.) remain governed independently inside `.sdd/catalog/packs/capability-web-frontend/`.

## 4. Offline Operation & Zero-Telemetry Policy

- **Zero network / zero telemetry at design time and materialization**: `sdd_agent_generator.py --materialize`, `@ui-ux-designer`, and `vendor/ui-ux-pro-max/scripts/search.py` operate 100% offline using local CSV/JSON datasets and Python standard library only.
- **No `npx` during design or materialization**: invoking `npx` is strictly forbidden outside explicit maintainer updates run through `scripts/sdd_vendor_update.py` in an isolated temporary directory with human diff review.
- **Fail-closed integrity verification**: every vendorized file is verified byte-for-byte (LF-normalized SHA-256 and byte length) against `vendor/ui-ux-pro-max/VENDOR.lock.json` before materializing into `.agents/`.
