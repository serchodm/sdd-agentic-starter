# Plan de Tareas (DAG): `FWK-005` Stop-the-Line P0 Seguridad

- **ID:** `FWK-005-p0-security-hardening`
- **Gate 3 Sign-off:** `[x] Gate 3 Approved (Pre-authorized by PO on 2026-11-14T16:05:46+01:00)`

## Grafo DAG

- `T5.1` `[PARALLEL: BLOCK_A]` (`W1.1`): Corregir `.agents/hooks.json`, `sdd_immutable_feature_guard.py`, `sdd_code_gate_guard.py`, `sdd_stack_gate_guard.py`, `sdd_trim_exec.py`.
  - *DoD:* `uv run python -c "import json,pathlib; b=pathlib.Path('.agents/hooks.json').read_bytes(); assert not b.startswith(b'\xef\xbb\xbf'); json.loads(b)"` y pruebas CLI de guardias.
- `T5.2` `[PARALLEL: BLOCK_A]` (`W1.2`): Corregir columna Status y checks Done/anti-inyección en `.agents/scripts/sdd_healthcheck.py` + `specs/BACKLOG.md`.
  - *DoD:* `uv run python .agents/scripts/sdd_healthcheck.py`
- `T5.3` `[PARALLEL: BLOCK_A]` (`W1.3`): Endurecer `scripts/sdd_hooks.py`, `.githooks/*`, `sdd.cmd` y `WorktreeManager.remove` en `scripts/sdd_git.py`.
  - *DoD:* `uv run python -m unittest tests.test_sdd_governance -v`
- `T5.4` `[PARALLEL: BLOCK_A]` (`W1.4`): Retirar las 3 skills filtradas de `.agents/skills/`.
  - *DoD:* comprobar ausencia de `fastapi-patterns`, `postgres-patterns`, `react-performance-and-patterns` bajo `.agents/skills/`.
- `T5.5` `[SEQUENTIAL: AFTER_BLOCK_A]` (`W1.5` `@qa-tester`): Crear `tests/test_sdd_security_guards.py` (`<=500L`) y validar suite completa.
  - *DoD:* `uv run python -m unittest discover -s tests -v`
