#!/usr/bin/env python3
"""Offline unit and acceptance tests for FWK-003 Conditional Visual Gates & Token Validator."""

from __future__ import annotations

import contextlib
import io
import json
import pathlib
import sys
import tempfile
import unittest

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts import sdd_tokens_validator
from scripts.sdd_tokens_validator import (
    TokenValidationResult,
    TokenViolation,
    ValidationSeverity,
    main,
    validate_design_tokens,
)

CANONICAL_TOKENS_DATA = {
    "$schema": "https://design-tokens.github.io/community-group/format/",
    "version": "1.0.0",
    "color": {
        "brand": {
            "primary": {"value": "#2563eb", "type": "color"},
            "secondary": {"value": "#475569", "type": "color"},
        },
    },
    "spacing": {
        "4": {"value": "1rem", "type": "dimension"},
    },
}

CANONICAL_MASTER_MD = """# Design System Master

Tokens normativos:
| Token | Valor | Tipo |
| :--- | :--- | :--- |
| `color.brand.primary` | #2563eb | color |
| `color.brand.secondary` | #475569 | color |
| `spacing.4` | 1rem | dimension |
"""


def _write_file(path: pathlib.Path, content: str) -> pathlib.Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


class TestSddVisualGates(unittest.TestCase):
    """Pruebas unitarias offline del validador de tokens y visual gates FWK-003."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_dir = pathlib.Path(self.temp_dir.name)
        self.tokens_path = self.base_dir / "docs" / "design-system" / "design-tokens.json"
        self.master_path = self.base_dir / "docs" / "design-system" / "MASTER.md"
        self.sources_dir = self.base_dir / "frontend" / "src"

        _write_file(self.tokens_path, json.dumps(CANONICAL_TOKENS_DATA, indent=2))
        _write_file(self.master_path, CANONICAL_MASTER_MD)
        self.sources_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    # 1. test_valid_tokens_and_master_coherence_passes
    def test_valid_tokens_and_master_coherence_passes(self) -> None:
        clean_file = self.sources_dir / "CleanButton.tsx"
        _write_file(
            clean_file,
            "export const CleanButton = () => (\n"
            "  <button className=\"btn-primary\">Guardar</button>\n"
            ");\n",
        )
        result = validate_design_tokens(
            tokens_path=self.tokens_path,
            master_path=self.master_path,
            check_sources=self.sources_dir,
        )
        self.assertTrue(result.is_valid)
        self.assertEqual(result.missing_in_master, [])
        self.assertEqual(result.missing_in_json, [])
        self.assertEqual(result.violations, [])
        self.assertEqual(result.total_tokens_checked, 3)
        self.assertEqual(result.total_sources_scanned, 1)
        self.assertIsNone(result.skipped_reason)

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = main([
                "--tokens", str(self.tokens_path),
                "--master", str(self.master_path),
                "--check-sources", str(self.sources_dir),
            ])
        output = buf.getvalue()
        self.assertEqual(code, 0)
        self.assertIn("[PASS]", output)
        self.assertIn("Cero discrepancias estilísticas detectadas.", output)

    # 2. test_token_missing_in_master_fails_closed
    def test_token_missing_in_master_fails_closed(self) -> None:
        drift_data = json.loads(json.dumps(CANONICAL_TOKENS_DATA))
        drift_data["color"]["brand"]["accent"] = {"value": "#10b981", "type": "color"}
        _write_file(self.tokens_path, json.dumps(drift_data, indent=2))

        result = validate_design_tokens(
            tokens_path=self.tokens_path,
            master_path=self.master_path,
        )
        self.assertFalse(result.is_valid)
        self.assertIn("color.brand.accent", result.missing_in_master)
        self.assertEqual(result.missing_in_json, [])
        self.assertTrue(any(
            v.category == "drift:missing-in-master" and "color.brand.accent" in v.message
            for v in result.violations
        ))

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = main([
                "--tokens", str(self.tokens_path),
                "--master", str(self.master_path),
            ])
        output = buf.getvalue()
        self.assertEqual(code, 1)
        self.assertIn("[FAIL]", output)
        self.assertIn("color.brand.accent", output)
        self.assertIn("Faltantes en MASTER.md", output)

    # 3. test_token_missing_in_json_fails_closed
    def test_token_missing_in_json_fails_closed(self) -> None:
        orphan_master = CANONICAL_MASTER_MD + "| `color.brand.ghost` | #ffffff | color |\n"
        _write_file(self.master_path, orphan_master)

        result = validate_design_tokens(
            tokens_path=self.tokens_path,
            master_path=self.master_path,
        )
        self.assertFalse(result.is_valid)
        self.assertIn("color.brand.ghost", result.missing_in_json)
        self.assertEqual(result.missing_in_master, [])
        self.assertTrue(any(
            v.category == "drift:missing-in-json" and "color.brand.ghost" in v.message
            for v in result.violations
        ))

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = main([
                "--tokens", str(self.tokens_path),
                "--master", str(self.master_path),
            ])
        output = buf.getvalue()
        self.assertEqual(code, 1)
        self.assertIn("[FAIL]", output)
        self.assertIn("color.brand.ghost", output)
        self.assertIn("Faltantes en JSON", output)

    # 4. test_hardcoded_literal_detected_in_sources
    def test_hardcoded_literal_detected_in_sources(self) -> None:
        bad_file = self.sources_dir / "BadCard.tsx"
        _write_file(
            bad_file,
            "import React from 'react';\n"
            "export const BadCard = () => (\n"
            "  <div style={{ backgroundColor: '#2563eb' }}>\n"
            "    <span>Hardcoded brand color</span>\n"
            "  </div>\n"
            ");\n",
        )

        result = validate_design_tokens(
            tokens_path=self.tokens_path,
            master_path=self.master_path,
            check_sources=self.sources_dir,
        )
        self.assertFalse(result.is_valid)
        violations = [v for v in result.violations if v.category == "literal:forbidden"]
        self.assertEqual(len(violations), 1)
        v = violations[0]
        self.assertEqual(v.line_number, 3)
        self.assertEqual(v.literal_value, "#2563eb")
        self.assertEqual(v.token_name, "color.brand.primary")
        self.assertTrue(v.file_path.endswith("BadCard.tsx"))
        self.assertIn("utilice el token 'color.brand.primary'", v.message)

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = main([
                "--tokens", str(self.tokens_path),
                "--master", str(self.master_path),
                "--check-sources", str(self.sources_dir),
            ])
        output = buf.getvalue()
        self.assertEqual(code, 1)
        self.assertIn("[FAIL]", output)
        self.assertIn("BadCard.tsx:3", output)
        self.assertIn("color.brand.primary", output)

    # 5. test_ignore_comment_skips_literal
    def test_ignore_comment_skips_literal(self) -> None:
        ignored_tsx = self.sources_dir / "IgnoredComponent.tsx"
        _write_file(
            ignored_tsx,
            "// Archivo con escape de token\n"
            "export const rawBrand = '#2563eb'; // sdd-token-ignore\n",
        )
        ignored_css = self.sources_dir / "legacy.css"
        _write_file(
            ignored_css,
            "/* Estilo legado */\n"
            ".legacy-header { background: #2563eb; /* sdd-token-ignore */ }\n",
        )

        result = validate_design_tokens(
            tokens_path=self.tokens_path,
            master_path=self.master_path,
            check_sources=self.sources_dir,
        )
        self.assertTrue(result.is_valid)
        forbidden = [v for v in result.violations if v.category == "literal:forbidden"]
        self.assertEqual(forbidden, [])
        self.assertEqual(result.total_sources_scanned, 2)

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = main([
                "--tokens", str(self.tokens_path),
                "--master", str(self.master_path),
                "--check-sources", str(self.sources_dir),
            ])
        output = buf.getvalue()
        self.assertEqual(code, 0)
        self.assertIn("[PASS]", output)

    # 6. test_allow_missing_flag_for_no_ui_projects
    def test_allow_missing_flag_for_no_ui_projects(self) -> None:
        nonexistent = self.base_dir / "nonexistent" / "design-tokens.json"

        result_allowed = validate_design_tokens(
            tokens_path=nonexistent,
            allow_missing=True,
        )
        self.assertTrue(result_allowed.is_valid)
        self.assertIsNotNone(result_allowed.skipped_reason)
        self.assertIn("--allow-missing", result_allowed.skipped_reason)

        result_strict = validate_design_tokens(
            tokens_path=nonexistent,
            allow_missing=False,
        )
        self.assertFalse(result_strict.is_valid)
        self.assertTrue(any(v.category == "file:not-found" for v in result_strict.violations))

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = main(["--tokens", str(nonexistent), "--allow-missing"])
        output = buf.getvalue()
        self.assertEqual(code, 0)
        self.assertIn("[SKIPPED]", output)
        self.assertIn("--allow-missing", output)

        buf_fail = io.StringIO()
        with contextlib.redirect_stdout(buf_fail):
            code_fail = main(["--tokens", str(nonexistent)])
        output_fail = buf_fail.getvalue()
        self.assertEqual(code_fail, 1)
        self.assertIn("[FAIL]", output_fail)

    # 7. test_json_output_format
    def test_json_output_format(self) -> None:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = main([
                "--tokens", str(self.tokens_path),
                "--master", str(self.master_path),
                "--format", "json",
            ])
        output = buf.getvalue()
        self.assertEqual(code, 0)

        data = json.loads(output)
        self.assertIsInstance(data, dict)
        self.assertTrue(data["is_valid"])
        self.assertEqual(data["total_tokens_checked"], 3)
        self.assertEqual(data["missing_in_master"], [])
        self.assertEqual(data["missing_in_json"], [])
        self.assertEqual(data["violations"], [])
        self.assertIsNone(data["skipped_reason"])

        orphan_master = CANONICAL_MASTER_MD + "| `color.brand.ghost` | #ffffff | color |\n"
        _write_file(self.master_path, orphan_master)
        buf_err = io.StringIO()
        with contextlib.redirect_stdout(buf_err):
            code_err = main([
                "--tokens", str(self.tokens_path),
                "--master", str(self.master_path),
                "--format", "json",
            ])
        output_err = buf_err.getvalue()
        self.assertEqual(code_err, 1)

        data_err = json.loads(output_err)
        self.assertFalse(data_err["is_valid"])
        self.assertIn("color.brand.ghost", data_err["missing_in_json"])
        self.assertGreater(len(data_err["violations"]), 0)
        first_violation = data_err["violations"][0]
        for expected_key in (
            "severity", "category", "message", "file_path",
            "line_number", "token_name", "literal_value",
        ):
            self.assertIn(expected_key, first_violation)

    # 8. test_modularity_line_limit_500
    def test_modularity_line_limit_500(self) -> None:
        validator_path = ROOT_DIR / "scripts" / "sdd_tokens_validator.py"
        test_path = ROOT_DIR / "tests" / "test_sdd_visual_gates.py"

        for p in (validator_path, test_path):
            line_count = len(p.read_text(encoding="utf-8").splitlines())
            self.assertLessEqual(
                line_count, 500,
                f"{p.name} supera el límite estricto de 500 líneas ({line_count} líneas)",
            )


if __name__ == "__main__":
    unittest.main()
