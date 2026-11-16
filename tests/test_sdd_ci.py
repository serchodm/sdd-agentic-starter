#!/usr/bin/env python3
"""Offline deterministic tests for CI-agnostic verification engine (FWK-013)."""

from __future__ import annotations

import contextlib
import io
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from scripts import sdd_ci  # noqa: E402


def _write(path: pathlib.Path, content: str | bytes) -> pathlib.Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, bytes):
        path.write_bytes(content)
    else:
        path.write_bytes(content.encode("utf-8"))
    return path


def _write_stack(ws: pathlib.Path, *, approved: bool, commands: dict[str, str] | None = None) -> pathlib.Path:
    marker = "[x] Gate S0 Approved" if approved else "[ ] Gate S0 Approved"
    lines = [
        "# Stack",
        "",
        f"> **ESTADO:** `{marker}`",
        "",
        "```yaml sdd:stack-config",
        f"stack_approved: {'true' if approved else 'false'}",
        "preset: compact",
        "packs: []",
        "```",
    ]
    if commands is not None:
        lines.extend(["", "### 2.5. Comandos Deterministas de Verificación DoD", "", "```yaml sdd:verification-commands"])
        for key, val in commands.items():
            escaped = val.replace('"', '\\"')
            lines.append(f'{key}: "{escaped}"')
        lines.append("```")
    return _write(ws / "specs" / "STACK.md", "\n".join(lines) + "\n")


def _seed_odd_docs(ws: pathlib.Path, *, matrix_extra: str = "") -> None:
    for name in ("ADRS.md", "API_CATALOG.md", "DATA_MODELS.md", "SYSTEM_TOPOLOGY.md"):
        _write(ws / "docs" / "knowledge" / name, f"# {name}\n\nDocumented.\n")
    _write(ws / "docs" / "traceability" / "TRACEABILITY-MATRIX.md", "# Traceability Matrix\n\n" + matrix_extra)
    _write(ws / "docs" / "es" / "README.md", "# Documentación\n\nResumen funcional.\n")
    _write(ws / "docs" / "en" / "README.md", "# Documentation\n\nFunctional summary.\n")


def _seed_valid_hooks(ws: pathlib.Path) -> None:
    _write(ws / ".agents" / "scripts" / "hook_ok.py", "print('ok')\n")
    payload = {"hooks": {"PreToolUse": [{"hooks": [{"type": "command", "command": "python .agents/scripts/hook_ok.py"}]}]}}
    _write(ws / ".agents" / "hooks.json", json.dumps(payload, indent=2) + "\n")


def _seed_project_ws(
    ws: pathlib.Path, *, approved: bool = True, commands: dict[str, str] | None = None, with_tests: int = 2
) -> None:
    _seed_valid_hooks(ws)
    _seed_odd_docs(ws)
    _write(
        ws / "specs" / "BACKLOG.md",
        "| ID | Tipo | Titulo | Gate 0 | Estado |\n|---|---|---|---|---|\n| `FEAT-001` | Feature | Widget | [x] | In Progress |\n",
    )
    feat = ws / "specs" / "features" / "FEAT-001-widget"
    _write(feat / "01-spec.md", "# Spec\n\nWHEN user opens widget, THE SYSTEM SHALL render.\n")
    _write(feat / "02-tech-spec.md", "# Tech Spec\n\nComponent contract.\n")
    _write(feat / "03-tasks.md", "# Tasks\n\n- [ ] `T1.1` [`@back-engineer`]: Implement widget\n")
    _write_stack(ws, approved=approved, commands=commands)
    if with_tests > 0:
        tests_code = "\n".join(
            [
                "import unittest",
                "class TestProjectSample(unittest.TestCase):",
                *[f"    def test_case_{i}(self):\n        self.assertEqual({i} + 1, {i + 1})" for i in range(with_tests)],
            ]
        )
        _write(ws / "tests" / "test_sample.py", tests_code + "\n")


def _seed_framework_markers(ws: pathlib.Path) -> None:
    _write(ws / ".sdd" / "framework" / "BACKLOG.md", "# Framework Backlog\n")
    (ws / ".sdd" / "framework" / "work-items").mkdir(parents=True, exist_ok=True)
    _write(ws / "tests" / "test_sdd_governance.py", "import unittest\n")


class TestDetectCiMode(unittest.TestCase):
    """RF-1302: Auto-detection between framework starter and derived projects."""

    def test_detect_ci_mode_framework_vs_project_variants(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = pathlib.Path(tmp)

            fwk_ws = base / "fwk"
            _seed_framework_markers(fwk_ws)
            _write_stack(fwk_ws, approved=False)
            self.assertEqual(sdd_ci.detect_ci_mode(fwk_ws, "auto"), "framework")

            proj_s0 = base / "proj_s0"
            _seed_framework_markers(proj_s0)
            _write_stack(proj_s0, approved=True)
            self.assertEqual(sdd_ci.detect_ci_mode(proj_s0, "auto"), "project")

            proj_no_gov = base / "proj_no_gov"
            _write(proj_no_gov / ".sdd" / "framework" / "BACKLOG.md", "# Fwk\n")
            (proj_no_gov / ".sdd" / "framework" / "work-items").mkdir(parents=True, exist_ok=True)
            _write_stack(proj_no_gov, approved=False)
            self.assertEqual(sdd_ci.detect_ci_mode(proj_no_gov, "auto"), "project")

            self.assertEqual(sdd_ci.detect_ci_mode(fwk_ws, "project"), "project")
            self.assertEqual(sdd_ci.detect_ci_mode(proj_no_gov, "framework"), "framework")
            with self.assertRaises(ValueError):
                sdd_ci.detect_ci_mode(fwk_ws, "invalid")


class TestHooksAndOddChecks(unittest.TestCase):
    """CA-1304: Fail-closed checks for .agents/hooks.json and 0DD compliance."""

    def test_check_hooks_json_valid_and_fail_closed_rejections(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ws = pathlib.Path(tmp)
            _seed_valid_hooks(ws)
            ok = sdd_ci.check_hooks_json(ws)
            self.assertEqual(ok.status, "PASS", ok.detail)
            self.assertEqual(ok.data.get("commands"), 1)

            hooks_file = ws / ".agents" / "hooks.json"
            raw = hooks_file.read_bytes()

            hooks_file.write_bytes(b"\xef\xbb\xbf" + raw)
            bom = sdd_ci.check_hooks_json(ws)
            self.assertEqual(bom.status, "FAIL")
            self.assertIn("BOM", bom.detail)

            hooks_file.write_text(
                json.dumps({"hooks": {"PreToolUse": [{"hooks": [{"type": "command", "command": "python scripts/missing.py"}]}]}}),
                encoding="utf-8",
            )
            missing = sdd_ci.check_hooks_json(ws)
            self.assertEqual(missing.status, "FAIL")
            self.assertIn("missing", missing.detail.lower())

            outside = _write(ws.parent / "outside_escape.py", "print('escape')\n")
            self.assertTrue(outside.is_file())
            hooks_file.write_text(
                json.dumps({"hooks": {"PreToolUse": [{"hooks": [{"type": "command", "command": "python ../outside_escape.py"}]}]}}),
                encoding="utf-8",
            )
            escaped = sdd_ci.check_hooks_json(ws)
            self.assertEqual(escaped.status, "FAIL")
            self.assertIn("outside_escape.py", escaped.detail)

    def test_check_odd_compliance_valid_untraced_done_and_missing_lang(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ws = pathlib.Path(tmp)
            _seed_odd_docs(ws, matrix_extra="| `FEAT-042` | Widget | Valid |\n")
            _write(
                ws / "specs" / "BACKLOG.md",
                "| ID | Tipo | Titulo | Gate 0 | Estado |\n|---|---|---|---|---|\n| `FEAT-042` | Feature | Widget | [x] | Done |\n",
            )
            ok = sdd_ci.check_odd_compliance(ws)
            self.assertEqual(ok.status, "PASS", ok.detail)
            self.assertEqual(ok.data.get("done_features_count"), 1)

            _write(
                ws / "specs" / "BACKLOG.md",
                "| ID | Tipo | Titulo | Gate 0 | Estado |\n|---|---|---|---|---|\n"
                "| `FEAT-042` | Feature | Widget | [x] | Done |\n"
                "| `FEAT-099` | Feature | Orphan | [x] | Done |\n",
            )
            untraced = sdd_ci.check_odd_compliance(ws)
            self.assertEqual(untraced.status, "FAIL")
            self.assertIn("FEAT-099", untraced.detail)
            self.assertEqual(untraced.data.get("untraced"), ["FEAT-099"])

            _write(ws / "docs" / "traceability" / "TRACEABILITY-MATRIX.md", "# Matrix\n\nFEAT-042\nFEAT-099\n")
            (ws / "docs" / "en" / "README.md").unlink()
            missing_en = sdd_ci.check_odd_compliance(ws)
            self.assertEqual(missing_en.status, "FAIL")
            self.assertIn("docs/en/", missing_en.detail)


class TestSafeStackCommandExecution(unittest.TestCase):
    """RF-1303 / CA-1303: Safe && splitting, shell=False execution, and fail-closed guards."""

    def test_split_safe_chained_command_accepts_and_rejects_metachars(self) -> None:
        parsed = sdd_ci.split_safe_chained_command('python -c "print(\'a && b\')" && python -c "print(2)"')
        self.assertEqual(parsed, [["python", "-c", "print('a && b')"], ["python", "-c", "print(2)"]])

        for unsafe in (
            "",
            "python -V; rm -rf /",
            "python -V | cat",
            "python -c $(id)",
            "python -V > out.txt",
            "python -V < in.txt",
            "python -V & echo hi",
            "python -V &&& echo hi",
            "python -V && ",
            'python -c "unclosed',
            "python -V\necho hi",
        ):
            with self.assertRaises(ValueError, msg=f"Expected rejection for: {unsafe!r}"):
                sdd_ci.split_safe_chained_command(unsafe)

    def test_run_stack_executes_safe_chained_commands_and_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ws = pathlib.Path(tmp)
            marker_a = ws / "seg_a.txt"
            marker_b = ws / "seg_b.txt"
            py_exe = sys.executable.replace("\\", "/")
            cmd_chain = (
                f'"{py_exe}" -c "__import__(\'pathlib\').Path(\'seg_a.txt\').write_text(\'A\')" '
                f'&& "{py_exe}" -c "__import__(\'pathlib\').Path(\'seg_b.txt\').write_text(\'B\')"'
            )
            _seed_project_ws(ws, approved=True, commands={"lint": cmd_chain, "unit_test": f'"{py_exe}" -c "assert 1 == 1"'})
            res = sdd_ci.check_stack_commands(ws, "project", run_stack=True)
            self.assertEqual(res.status, "PASS", res.detail)
            self.assertEqual(res.data.get("slots"), ["lint", "unit_test"])
            self.assertEqual(marker_a.read_text(encoding="utf-8"), "A")
            self.assertEqual(marker_b.read_text(encoding="utf-8"), "B")

            for bad_cmd in ("python -V; rm -rf /", "python -V | cat", "echo $(id)", "python -V > pwn.txt", "python -V & echo x"):
                _write_stack(ws, approved=True, commands={"lint": bad_cmd})
                with mock.patch("scripts.sdd_ci.subprocess.run") as sub_mock:
                    bad_res = sdd_ci.check_stack_commands(ws, "project", run_stack=True)
                self.assertEqual(bad_res.status, "FAIL")
                sub_mock.assert_not_called()

            _write_stack(ws, approved=False, commands={"lint": f'"{py_exe}" -V'})
            unapproved = sdd_ci.check_stack_commands(ws, "project", run_stack=True)
            self.assertEqual(unapproved.status, "FAIL")
            self.assertIn("Gate S0", unapproved.detail)

    def test_run_stack_if_approved_behavior_in_framework_vs_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = pathlib.Path(tmp)
            fwk_ws = base / "fwk"
            _seed_framework_markers(fwk_ws)
            _write_stack(fwk_ws, approved=False)
            fwk_res = sdd_ci.check_stack_commands(fwk_ws, "framework", run_stack_if_approved=True)
            self.assertEqual(fwk_res.status, "SKIPPED_NO_APPLICABLE")

            proj_unapproved = base / "proj_unapproved"
            _write_stack(proj_unapproved, approved=False)
            opt_res = sdd_ci.check_stack_commands(proj_unapproved, "project", run_stack_if_approved=False)
            self.assertEqual(opt_res.status, "SKIPPED_OPT_IN")

            proj_ws = base / "proj_approved"
            py_exe = sys.executable.replace("\\", "/")
            _seed_project_ws(proj_ws, approved=True, commands={"lint": f'"{py_exe}" -c "print(123)"'})
            proj_res = sdd_ci.check_stack_commands(proj_ws, "project", run_stack_if_approved=True)
            self.assertEqual(proj_res.status, "PASS", proj_res.detail)
            self.assertEqual(proj_res.data.get("slots"), ["lint"])


class TestCiVerifyEndToEnd(unittest.TestCase):
    """CA-1301..CA-1304: End-to-end CLI JSON output, project auto mode, and <= 500L limit."""

    def test_project_auto_mode_succeeds_with_2_tests_and_skipped_opt_in(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ws = pathlib.Path(tmp)
            py_exe = sys.executable.replace("\\", "/")
            _seed_project_ws(ws, approved=True, commands={"lint": f'"{py_exe}" -c "print(1)"'}, with_tests=2)
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = sdd_ci.main(["--repo-root", str(ws), "--mode", "auto", "--format", "json"])
            self.assertEqual(rc, 0, buf.getvalue())
            payload = json.loads(buf.getvalue())
            self.assertEqual(payload["mode"], "project")
            self.assertEqual(payload["overall_status"], "PASS")
            by_name = {c["name"]: c for c in payload["checks"]}
            self.assertNotIn("framework_tests", by_name)
            self.assertEqual(by_name["stack_commands"]["status"], "SKIPPED_OPT_IN")
            self.assertEqual(by_name["odd_compliance"]["status"], "PASS")
            self.assertEqual(by_name["dag_verify"]["status"], "PASS")

    def test_framework_unittest_threshold_enforcement_real_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ws = pathlib.Path(tmp)
            _seed_project_ws(ws, approved=False, with_tests=2)
            clean_env = {k: v for k, v in os.environ.items() if k != "SDD_CI_NESTED_TEST"}
            with mock.patch.dict(os.environ, clean_env, clear=True):
                fail_res = sdd_ci.check_framework_unittest(ws, min_tests=5)
                self.assertEqual(fail_res.status, "FAIL")
                self.assertEqual(fail_res.data.get("tests_run"), 2)
                pass_res = sdd_ci.check_framework_unittest(ws, min_tests=2)
                self.assertEqual(pass_res.status, "PASS", pass_res.detail)
                self.assertEqual(pass_res.data.get("tests_run"), 2)

    def test_ca1304_cli_returns_1_on_hooks_bom_or_untraced_done(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ws = pathlib.Path(tmp)
            _seed_project_ws(ws, approved=True, with_tests=0)
            hooks_file = ws / ".agents" / "hooks.json"
            hooks_file.write_bytes(b"\xef\xbb\xbf" + hooks_file.read_bytes())
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = sdd_ci.main(["--repo-root", str(ws), "--mode", "project", "--format", "json"])
            self.assertEqual(rc, 1)
            payload = json.loads(buf.getvalue())
            self.assertEqual(payload["overall_status"], "FAIL")
            by_name = {c["name"]: c for c in payload["checks"]}
            self.assertEqual(by_name["hooks"]["status"], "FAIL")

    def test_cli_ci_verify_framework_json_and_all_py_files_under_500_lines(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(ROOT_DIR / "scripts" / "sdd_cli.py"), "ci-verify", "--mode", "framework", "--skip-tests", "--format", "json"],
            cwd=str(ROOT_DIR),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["mode"], "framework")
        self.assertEqual(payload["overall_status"], "PASS")
        check_names = {c["name"] for c in payload["checks"]}
        self.assertTrue(
            {
                "hooks", "healthcheck", "odd_compliance", "boundaries", "catalog_verify",
                "dag_verify", "gate_seals", "git_and_instincts", "tokens", "framework_tests", "stack_commands",
            }.issubset(check_names)
        )

        offenders: list[tuple[str, int]] = []
        for rel_dir in ("scripts", ".agents/scripts", "tests"):
            for py_file in sorted((ROOT_DIR / rel_dir).rglob("*.py")):
                if "__pycache__" in py_file.parts:
                    continue
                line_count = len(py_file.read_text(encoding="utf-8").splitlines())
                if line_count > 500:
                    offenders.append((py_file.relative_to(ROOT_DIR).as_posix(), line_count))
        self.assertEqual(offenders, [], f"Files exceeding 500 lines: {offenders}")


if __name__ == "__main__":
    unittest.main()
