#!/usr/bin/env python3
"""Offline unit and acceptance tests for FWK-004 gate terminology unification."""

from __future__ import annotations

import json
import pathlib
import sys
import tempfile
import unittest

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

AGENTS_SCRIPTS_DIR = ROOT_DIR / ".agents" / "scripts"
if str(AGENTS_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(AGENTS_SCRIPTS_DIR))

from scripts.sdd_pack_registry import (
    StackConfig,
    StackConfigError,
    parse_stack_config,
)
from sdd_healthcheck import check_spec_triads
from sdd_immutable_feature_guard import get_done_features
from sdd_stack_gate_guard import ACCEPTED_STACK_MARKERS, check_stack_gate


def _write_text(path: pathlib.Path, content: str) -> pathlib.Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


class TestStackConfigTerminology(unittest.TestCase):
    """Verifies dual-accept, fail-closed conflicts, and backward compatibility in parse_stack_config."""

    _tmp_ctx: tempfile.TemporaryDirectory[str]
    _tmp_root: pathlib.Path

    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp_ctx = tempfile.TemporaryDirectory()
        cls._tmp_root = pathlib.Path(cls._tmp_ctx.name)

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp_ctx.cleanup()

    def test_canonical_gate_s0_approved(self) -> None:
        doc = (
            "# Stack\n\n> **ESTADO:** `[x] Gate S0 Approved (Human Sign-off)`\n\n"
            "```yaml sdd:stack-config\nstack_approved: true\npreset: compact\npacks: []\n```\n"
        )
        f = _write_text(self._tmp_root / "s0_canonical.md", doc)
        cfg, eff = parse_stack_config(f)
        self.assertTrue(cfg.stack_approved)
        self.assertTrue(cfg.gate00_approved)
        self.assertTrue(eff)

    def test_canonical_gate_s0_uppercase_x(self) -> None:
        doc = (
            "# Stack\n\n> **ESTADO:** `[X] Gate S0 Approved`\n\n"
            "```yaml sdd:stack-config\nstack_approved: true\npreset: compact\npacks: []\n```\n"
        )
        f = _write_text(self._tmp_root / "s0_upper_x.md", doc)
        cfg, eff = parse_stack_config(f)
        self.assertTrue(cfg.stack_approved)
        self.assertTrue(eff)

    def test_legacy_gate_00_approved(self) -> None:
        doc = (
            "# Stack\n\n> **ESTADO:** `[x] Gate 00 Approved (Human Sign-off)`\n\n"
            "```yaml sdd:stack-config\ngate00_approved: true\npreset: compact\npacks: []\n```\n"
        )
        f = _write_text(self._tmp_root / "g00_legacy.md", doc)
        cfg, eff = parse_stack_config(f)
        self.assertTrue(cfg.stack_approved)
        self.assertTrue(cfg.gate00_approved)
        self.assertTrue(eff)

    def test_legacy_gate_00_uppercase_x(self) -> None:
        doc = (
            "# Stack\n\n> **ESTADO:** `[X] Gate 00 Approved`\n\n"
            "```yaml sdd:stack-config\ngate00_approved: true\npreset: compact\npacks: []\n```\n"
        )
        f = _write_text(self._tmp_root / "g00_upper_x.md", doc)
        cfg, eff = parse_stack_config(f)
        self.assertTrue(cfg.stack_approved)
        self.assertTrue(eff)

    def test_coherent_mixed_gate_s0_and_00(self) -> None:
        doc = (
            "# Stack\n\n> **ESTADO:** `[x] Gate S0 Approved`\n\n"
            "```yaml sdd:stack-config\nstack_approved: true\ngate00_approved: true\n"
            "preset: compact\npacks: []\n```\n"
        )
        f = _write_text(self._tmp_root / "s0_g00_mixed_coherent.md", doc)
        cfg, eff = parse_stack_config(f)
        self.assertTrue(cfg.stack_approved)
        self.assertTrue(cfg.gate00_approved)
        self.assertTrue(eff)

    def test_coherent_mixed_false(self) -> None:
        doc = (
            "# Stack\n\n> **ESTADO:** `[ ] Gate S0 Approved`\n\n"
            "```yaml sdd:stack-config\nstack_approved: false\ngate00_approved: false\n"
            "preset: compact\npacks: []\n```\n"
        )
        f = _write_text(self._tmp_root / "mixed_false.md", doc)
        cfg, eff = parse_stack_config(f)
        self.assertFalse(cfg.stack_approved)
        self.assertFalse(cfg.gate00_approved)
        self.assertFalse(eff)

    def test_fail_closed_on_conflicting_boolean_keys(self) -> None:
        conflicts = [
            ("stack_true_gate00_false", "stack_approved: true\ngate00_approved: false\n"),
            ("stack_false_gate00_true", "stack_approved: false\ngate00_approved: true\n"),
        ]
        for name, block in conflicts:
            with self.subTest(conflict=name):
                doc = (
                    f"# Stack\n\n> `[x] Gate S0 Approved`\n\n"
                    f"```yaml sdd:stack-config\n{block}preset: compact\npacks: []\n```\n"
                )
                f = _write_text(self._tmp_root / f"conflict_{name}.md", doc)
                with self.assertRaises(StackConfigError) as ctx:
                    parse_stack_config(f)
                self.assertIn("Conflicting 'stack_approved' and legacy 'gate00_approved'", str(ctx.exception))

    def test_fail_closed_on_missing_both_approval_keys(self) -> None:
        doc = (
            "# Stack\n\n> `[x] Gate S0 Approved`\n\n"
            "```yaml sdd:stack-config\npreset: compact\npacks: []\n```\n"
        )
        f = _write_text(self._tmp_root / "missing_keys.md", doc)
        with self.assertRaises(StackConfigError) as ctx:
            parse_stack_config(f)
        self.assertIn("Missing 'stack_approved' (or legacy 'gate00_approved')", str(ctx.exception))

    def test_fail_closed_on_non_boolean_types(self) -> None:
        cases = [
            ("string_stack", "stack_approved: 'true'\n"),
            ("int_stack", "stack_approved: 1\n"),
            ("string_gate00", "gate00_approved: 'true'\n"),
            ("int_gate00", "gate00_approved: 1\n"),
        ]
        for name, block in cases:
            with self.subTest(case=name):
                doc = (
                    f"# Stack\n\n> `[x] Gate S0 Approved`\n\n"
                    f"```yaml sdd:stack-config\n{block}preset: compact\npacks: []\n```\n"
                )
                f = _write_text(self._tmp_root / f"bad_type_{name}.md", doc)
                with self.assertRaises(StackConfigError) as ctx:
                    parse_stack_config(f)
                self.assertIn("must be a strict boolean (true/false)", str(ctx.exception))

    def test_unsigned_marker_yields_ineffective(self) -> None:
        doc = (
            "# Stack\n\n> **ESTADO:** `[ ] Gate S0 Approved (Human Sign-off)`\n\n"
            "```yaml sdd:stack-config\nstack_approved: true\npreset: compact\npacks: []\n```\n"
        )
        f = _write_text(self._tmp_root / "unsigned_s0.md", doc)
        cfg, eff = parse_stack_config(f)
        self.assertTrue(cfg.stack_approved)
        self.assertFalse(eff)

    def test_stack_config_dataclass_alias_interface(self) -> None:
        cfg = StackConfig(stack_approved=True, preset="compact", packs=("pack-a",))
        self.assertTrue(cfg.stack_approved)
        self.assertTrue(cfg.gate00_approved)

        cfg_legacy = StackConfig(gate00_approved=True, preset="compact", packs=("pack-b",))
        self.assertTrue(cfg_legacy.stack_approved)
        self.assertTrue(cfg_legacy.gate00_approved)


class TestStackGateGuard(unittest.TestCase):
    """Verifies check_stack_gate in sdd_stack_gate_guard.py."""

    _tmp_ctx: tempfile.TemporaryDirectory[str]
    _tmp_root: pathlib.Path

    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp_ctx = tempfile.TemporaryDirectory()
        cls._tmp_root = pathlib.Path(cls._tmp_ctx.name)

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp_ctx.cleanup()

    def test_all_accepted_markers_pass(self) -> None:
        for idx, marker in enumerate(ACCEPTED_STACK_MARKERS):
            with self.subTest(marker=marker):
                ws = self._tmp_root / f"ws_marker_{idx}"
                _write_text(ws / "specs" / "STACK.md", f"# Stack\n\n> Estado: `{marker}`\n")
                ok, msg = check_stack_gate(ws)
                self.assertTrue(ok)
                self.assertEqual(msg, "Gate S0 OK")

    def test_missing_stack_file_fails(self) -> None:
        ws = self._tmp_root / "ws_no_stack"
        ws.mkdir(parents=True, exist_ok=True)
        ok, msg = check_stack_gate(ws)
        self.assertFalse(ok)
        self.assertIn("Gate S0 LOCKED: Falta el fichero specs/STACK.md", msg)

    def test_unapproved_marker_fails(self) -> None:
        ws = self._tmp_root / "ws_unapproved"
        _write_text(ws / "specs" / "STACK.md", "# Stack\n\n> Estado: `[ ] Gate S0 Approved`\n")
        ok, msg = check_stack_gate(ws)
        self.assertFalse(ok)
        self.assertIn("Gate S0 LOCKED", msg)


class TestGuardStates(unittest.TestCase):
    """Verifies state recognition in immutable feature guard and healthcheck."""

    _tmp_ctx: tempfile.TemporaryDirectory[str]
    _tmp_root: pathlib.Path

    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp_ctx = tempfile.TemporaryDirectory()
        cls._tmp_root = pathlib.Path(cls._tmp_ctx.name)

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp_ctx.cleanup()

    def test_get_done_features_recognizes_canonical_and_legacy_states(self) -> None:
        backlog_content = (
            "# Backlog\n\n"
            "| ID | Tipo | Titulo | G0 | G1 | G2 | G3 | G4 | G5 | Estado Final |\n"
            "| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |\n"
            "| `FEAT-001` | Feature | Item 1 | [x] | [x] | [x] | [x] | [x] | [x] | Done |\n"
            "| `FEAT-002` | Feature | Item 2 | [x] | [x] | [x] | [x] | [x] | [x] | Completado |\n"
            "| `FEAT-003` | Feature | Item 3 | [x] | [x] | [x] | [x] | [x] | [x] | Completed |\n"
            "| `FEAT-004` | Feature | Item 4 | [x] | [x] | [x] | [x] | [x] | [ ] | In Progress |\n"
            "| `FEAT-005` | Feature | Item 5 | [x] | [ ] | [ ] | [ ] | [ ] | [ ] | Backlog |\n"
            "| `FEAT-006` | Feature | Item 6 | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | Candidate |\n\n"
            "#### `FEAT-007`: Detalle Seccion\n"
            "- **Estado:** `Completed / Done`\n\n"
            "#### `FEAT-008`: Detalle Legacy\n"
            "- **Estado:** `Completado`\n\n"
            "#### `FEAT-009`: Detalle Activo\n"
            "- **Estado:** `In Progress`\n"
        )
        backlog_path = _write_text(self._tmp_root / "specs" / "BACKLOG.md", backlog_content)
        done_features = get_done_features(backlog_path)
        self.assertEqual(done_features, {"FEAT-001", "FEAT-002", "FEAT-003", "FEAT-007", "FEAT-008"})
        self.assertNotIn("FEAT-004", done_features)
        self.assertNotIn("FEAT-005", done_features)
        self.assertNotIn("FEAT-006", done_features)
        self.assertNotIn("FEAT-009", done_features)

    def test_check_spec_triads_accepts_initial_states(self) -> None:
        specs_dir = self._tmp_root / "triads_ws" / "specs"
        backlog_content = (
            "# Backlog\n\n"
            "| `FEAT-010` | Feature | Draft Item | [x] | [ ] | [ ] | [ ] | [ ] | [ ] | Draft |\n"
            "| `FEAT-011` | Feature | Proposed Item | [x] | [ ] | [ ] | [ ] | [ ] | [ ] | Proposed |\n"
            "| `FEAT-012` | Feature | Propuesto Item | [x] | [ ] | [ ] | [ ] | [ ] | [ ] | Propuesto |\n"
            "| `FEAT-013` | Feature | Gate 1 Item | [x] | [ ] | [ ] | [ ] | [ ] | [ ] | Gate 1 |\n"
            "| `FEAT-014` | Feature | Active Item | [x] | [x] | [x] | [ ] | [ ] | [ ] | In Progress |\n"
        )
        backlog_path = _write_text(specs_dir / "BACKLOG.md", backlog_content)

        # Para los 4 items iniciales (Gate 1), solo existe 01-spec.md
        for fid in ("FEAT-010-draft", "FEAT-011-proposed", "FEAT-012-propuesto", "FEAT-013-gate1"):
            _write_text(specs_dir / "features" / fid / "01-spec.md", f"# {fid}\n")

        # Para FEAT-014 (In Progress), solo existe 01-spec.md (le faltan 02 y 03)
        _write_text(specs_dir / "features" / "FEAT-014-active" / "01-spec.md", "# FEAT-014\n")

        errors = check_spec_triads(specs_dir, backlog_path)

        # Los 4 iniciales no generan error; FEAT-014 genera 2 errores por 02-tech-spec.md y 03-tasks.md
        feat_014_errors = [e for e in errors if "FEAT-014" in e]
        self.assertEqual(len(feat_014_errors), 2)
        self.assertTrue(any("02-tech-spec.md" in e for e in feat_014_errors))
        self.assertTrue(any("03-tasks.md" in e for e in feat_014_errors))

        # Comprobar que ninguno de los iniciales tiene errores
        for initial_id in ("FEAT-010", "FEAT-011", "FEAT-012", "FEAT-013"):
            self.assertFalse(any(initial_id in e for e in errors), f"Unexpected error for initial {initial_id}")


class TestContractualArtefactIntegrity(unittest.TestCase):
    """Verifies repository-level governance artefacts and templates."""

    def test_legacy_change_spec_template_does_not_exist(self) -> None:
        legacy_path = ROOT_DIR / "specs" / "templates" / "04-change-spec.template.md"
        self.assertFalse(legacy_path.exists(), "specs/templates/04-change-spec.template.md must be removed")

    def test_canonical_change_request_spec_template_exists_and_clean(self) -> None:
        cr_tpl_path = ROOT_DIR / "specs" / "templates" / "04-change-request-spec.template.md"
        self.assertTrue(cr_tpl_path.is_file(), "specs/templates/04-change-request-spec.template.md must exist")
        text = cr_tpl_path.read_text(encoding="utf-8")
        self.assertNotIn("08-ears-requirements-standard.md", text)
        for expected in (
            "## 2. Alcance Delta (Delta Scope)",
            "## 3. Matriz Comparativa del Delta",
            "## 4. Historias de Usuario Delta y Criterios BDD",
            "## 5. Aprobación Formal del Stakeholder",
            "[ ] **Gate 1 Approved (Human Sign-off):**",
            "[ ] **Gate 2 Approved (Human Sign-off):**",
            "[ ] **Gate 3 Approved (Human Sign-off):**",
        ):
            self.assertIn(expected, text)

    def test_functional_spec_template_references_correct_ears_rule(self) -> None:
        fn_tpl_path = ROOT_DIR / "specs" / "templates" / "01-functional-spec.template.md"
        self.assertTrue(fn_tpl_path.is_file())
        text = fn_tpl_path.read_text(encoding="utf-8")
        self.assertNotIn("08-ears-requirements-standard.md", text)
        self.assertIn(".agents/rules/03-ears-requirements.md", text)

    def test_templates_do_not_contain_broken_ears_link(self) -> None:
        templates_dir = ROOT_DIR / "specs" / "templates"
        for tpl in templates_dir.glob("*.template.md"):
            text = tpl.read_text(encoding="utf-8")
            self.assertNotIn(
                "08-ears-requirements-standard.md",
                text,
                f"{tpl.name} still contains broken reference to 08-ears-requirements-standard.md",
            )

    def test_squad_lock_contains_canonical_and_legacy_fields(self) -> None:
        lock_path = ROOT_DIR / ".agents" / "squad.lock.json"
        self.assertTrue(lock_path.is_file())
        lock_data = json.loads(lock_path.read_text(encoding="utf-8"))
        self.assertIn("stack_approved", lock_data)
        self.assertIn("gate00_approved", lock_data)
        self.assertEqual(lock_data["stack_approved"], lock_data["gate00_approved"])

    def test_modularity_line_limit_500(self) -> None:
        this_file = pathlib.Path(__file__)
        lines = this_file.read_text(encoding="utf-8").splitlines()
        self.assertLessEqual(len(lines), 500, f"{this_file.name} exceeds 500 lines ({len(lines)})")


if __name__ == "__main__":
    unittest.main()
