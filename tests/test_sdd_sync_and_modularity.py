#!/usr/bin/env python3
"""Tests for sdd_sync hardening, CI/hooks/0DD validation, pyproject.toml, and global modularity."""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest
from unittest import mock

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from scripts import sdd_ci, sdd_sync  # noqa: E402


def _write(path: pathlib.Path, content: str) -> pathlib.Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content.encode("utf-8"))
    return path


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _make_link(link_path: pathlib.Path, target: pathlib.Path) -> None:
    link_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.symlink(target, link_path, target_is_directory=target.is_dir())
        return
    except OSError:
        if os.name == "nt" and target.is_dir():
            res = subprocess.run(
                ["cmd", "/d", "/c", "mklink", "/J", str(link_path), str(target)],
                capture_output=True, text=True, check=False,
            )
            if res.returncode == 0:
                return
        raise


def _seed_sync_pair(base: pathlib.Path) -> tuple[pathlib.Path, pathlib.Path]:
    proj = base / "proj"
    tpl = base / "tpl"
    for root in (proj, tpl):
        _write(root / ".agents" / "workflows" / "pipeline-run.md", "# Pipeline v1\n")
        _write(root / ".agents" / "workflows" / "build-fix.md", "# Build Fix v1\n")
        _write(root / "scripts" / "helper.py", "VERSION = 1\n")
    return proj, tpl


class TestSddSyncHardening(unittest.TestCase):
    """AUD-006: strict template resolution, dry-run, conflict detection, and rollback."""

    def test_no_hardcoded_paths_and_requires_explicit_or_env(self) -> None:
        src_text = (ROOT_DIR / "scripts" / "sdd_sync.py").read_text(encoding="utf-8")
        self.assertNotIn("C:/Projects/", src_text)
        self.assertNotIn("C:\\Projects\\", src_text)

        env_clean = {k: v for k, v in os.environ.items() if k != sdd_sync.TEMPLATE_DIR_ENV_VAR}
        with mock.patch.dict(os.environ, env_clean, clear=True):
            with self.assertRaises(sdd_sync.SyncConfigError):
                sdd_sync.resolve_template_root(None)
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(sdd_sync.main(["--status"]), 1)

        with tempfile.TemporaryDirectory() as tmp:
            base = pathlib.Path(tmp)
            proj, tpl = _seed_sync_pair(base)
            with self.assertRaises(sdd_sync.SyncConfigError):
                sdd_sync.resolve_template_root(base / "does-not-exist")
            with self.assertRaises(sdd_sync.SyncConfigError):
                sdd_sync.resolve_template_root(tpl, source_root=tpl)
            with mock.patch.dict(os.environ, {sdd_sync.TEMPLATE_DIR_ENV_VAR: str(tpl)}):
                self.assertEqual(sdd_sync.resolve_template_root(None, source_root=proj), tpl.resolve())
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(sdd_sync.main(["--template-dir", str(tpl), "--pull-from-template", str(proj)]), 1)

    def test_symlink_or_junction_template_and_member_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = pathlib.Path(tmp)
            proj, tpl = _seed_sync_pair(base)
            outside = _write(base / "outside" / "secret.md", "SECRET\n").parent
            tpl_link = base / "tpl_junction"
            _make_link(tpl_link, tpl)
            with self.assertRaises(sdd_sync.SyncSecurityError):
                sdd_sync.resolve_template_root(tpl_link, source_root=proj)

            member_link = tpl / ".agents" / "workflows" / "escape_dir"
            _make_link(member_link, outside)
            with self.assertRaises(sdd_sync.SyncSecurityError):
                sdd_sync.pull_from_template(proj, tpl)

    def test_dry_run_reports_plan_without_modifying_destination(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            proj, tpl = _seed_sync_pair(pathlib.Path(tmp))
            baseline = {
                "schema_version": 1,
                "direction": "pull",
                "files": {
                    ".agents/workflows/pipeline-run.md": _sha256("# Pipeline v1\n"),
                    ".agents/workflows/build-fix.md": _sha256("# Build Fix v1\n"),
                    "scripts/helper.py": _sha256("VERSION = 1\n"),
                },
            }
            _write(proj / ".agents" / ".sdd-sync-state.json", json.dumps(baseline))
            _write(tpl / ".agents" / "workflows" / "build-fix.md", "# Build Fix v2\n")
            _write(tpl / ".agents" / "workflows" / "new-wf.md", "# Brand New\n")
            _write(tpl / "scripts" / "helper.py", "VERSION = 2\n")
            _write(proj / "scripts" / "helper.py", "VERSION = 999  # local edit\n")
            _write(tpl / ".agents" / "skills" / "gen.md", "GENERATED by sdd_agent_generator\n")

            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                plan = sdd_sync.pull_from_template(proj, tpl, dry_run=True)

            out = buf.getvalue()
            self.assertFalse(plan.applied)
            self.assertTrue(plan.dry_run)
            self.assertEqual(plan.added, (".agents/workflows/new-wf.md",))
            self.assertEqual(plan.updated, (".agents/workflows/build-fix.md",))
            self.assertEqual(plan.conflicts, ("scripts/helper.py",))
            self.assertEqual(plan.skipped, (".agents/workflows/pipeline-run.md",))
            self.assertIn("[DRY-RUN]", out)
            self.assertIn("[ADD] .agents/workflows/new-wf.md", out)
            self.assertIn("[UPDATE] .agents/workflows/build-fix.md", out)
            self.assertIn("[CONFLICT] scripts/helper.py", out)
            self.assertIn("[SKIP] .agents/workflows/pipeline-run.md", out)
            self.assertFalse((proj / ".agents" / "workflows" / "new-wf.md").exists())
            self.assertEqual((proj / ".agents" / "workflows" / "build-fix.md").read_text(encoding="utf-8"), "# Build Fix v1\n")
            self.assertEqual((proj / "scripts" / "helper.py").read_text(encoding="utf-8"), "VERSION = 999  # local edit\n")

    def test_conflict_fails_closed_unless_force_and_state_enables_clean_updates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            proj, tpl = _seed_sync_pair(pathlib.Path(tmp))
            _write(proj / ".agents" / "workflows" / "pipeline-run.md", "# Custom local edit\n")
            _write(tpl / ".agents" / "workflows" / "new-wf.md", "# New Workflow\n")

            with contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(sdd_sync.SyncConflictError):
                    sdd_sync.pull_from_template(proj, tpl)
            self.assertEqual(
                (proj / ".agents" / "workflows" / "pipeline-run.md").read_text(encoding="utf-8"),
                "# Custom local edit\n",
            )
            self.assertFalse((proj / ".agents" / "workflows" / "new-wf.md").exists())
            self.assertFalse((proj / ".agents" / ".sdd-sync-state.json").exists())

            with mock.patch.object(sdd_sync, "pull_from_template") as mock_pull:
                self.assertEqual(sdd_sync.main(["--pull-from-template", str(tpl), "--allow-overwrite", "--dry-run"]), 0)
                mock_pull.assert_called_once()
                _, kwargs = mock_pull.call_args
                self.assertEqual(kwargs, {"dry_run": True, "force": True})

            with contextlib.redirect_stdout(io.StringIO()):
                res = sdd_sync.pull_from_template(proj, tpl, force=True)
            self.assertTrue(res.applied)
            self.assertEqual(
                (proj / ".agents" / "workflows" / "pipeline-run.md").read_text(encoding="utf-8"),
                "# Pipeline v1\n",
            )
            self.assertTrue((proj / ".agents" / "workflows" / "new-wf.md").is_file())

            _write(tpl / ".agents" / "workflows" / "pipeline-run.md", "# Pipeline v2\n")
            with contextlib.redirect_stdout(io.StringIO()):
                res2 = sdd_sync.pull_from_template(proj, tpl, force=False)
            self.assertEqual(res2.updated, (".agents/workflows/pipeline-run.md",))
            self.assertEqual(
                (proj / ".agents" / "workflows" / "pipeline-run.md").read_text(encoding="utf-8"),
                "# Pipeline v2\n",
            )

    def test_push_to_template_sanitizes_and_respects_conflicts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            proj, tpl = _seed_sync_pair(pathlib.Path(tmp))
            _write(proj / ".agents" / "workflows" / "custom-paco.md", "Ask @jarvis in P.A.C.O. / PACO\n")
            _write(proj / ".agents" / "skills" / "gen.md", "GENERATED by sdd_agent_generator\n")
            _write(tpl / ".agents" / "workflows" / "pipeline-run.md", "# Divergent template\n")

            with contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(sdd_sync.SyncConflictError):
                    sdd_sync.push_to_template(proj, tpl)
            self.assertFalse((tpl / ".agents" / "workflows" / "custom-paco.md").exists())

            with contextlib.redirect_stdout(io.StringIO()):
                sdd_sync.push_to_template(proj, tpl, force=True)
            self.assertEqual(
                (tpl / ".agents" / "workflows" / "custom-paco.md").read_text(encoding="utf-8"),
                "Ask @orchestrator in Project / Project\n",
            )
            self.assertFalse((tpl / ".agents" / "skills" / "gen.md").exists())

    def test_copy_oserror_triggers_full_rollback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            proj, tpl = _seed_sync_pair(pathlib.Path(tmp))
            _write(proj / ".agents" / "workflows" / "build-fix.md", "# Build Fix v1\n")
            _write(tpl / ".agents" / "workflows" / "build-fix.md", "# Build Fix v2\n")
            _write(tpl / ".agents" / "workflows" / "nested" / "brand-new.md", "# Brand New\n")
            _write(tpl / "scripts" / "helper.py", "VERSION = 2\n")

            real_copy2 = shutil.copy2
            calls = {"n": 0}

            def flaky_copy2(src: pathlib.Path, dst: pathlib.Path, *args: object, **kwargs: object) -> object:
                calls["n"] += 1
                if calls["n"] >= 3:
                    raise OSError("Simulated disk error mid-sync")
                return real_copy2(src, dst, *args, **kwargs)

            with mock.patch("shutil.copy2", side_effect=flaky_copy2):
                with contextlib.redirect_stdout(io.StringIO()):
                    with self.assertRaises(OSError):
                        sdd_sync.pull_from_template(proj, tpl, force=True)

            self.assertEqual((proj / ".agents" / "workflows" / "build-fix.md").read_text(encoding="utf-8"), "# Build Fix v1\n")
            self.assertEqual((proj / "scripts" / "helper.py").read_text(encoding="utf-8"), "VERSION = 1\n")
            self.assertFalse((proj / ".agents" / "workflows" / "nested" / "brand-new.md").exists())
            self.assertFalse((proj / ".agents" / "workflows" / "nested").exists())
            self.assertFalse((proj / ".agents" / ".sdd-sync-state.json").exists())

            blocker = proj / "scripts" / "helper.py"
            blocker.unlink()
            blocker.mkdir()
            with contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(OSError):
                    sdd_sync.pull_from_template(proj, tpl, force=True)
            self.assertTrue(blocker.is_dir())
            self.assertEqual((proj / ".agents" / "workflows" / "build-fix.md").read_text(encoding="utf-8"), "# Build Fix v1\n")
            self.assertFalse((proj / ".agents" / "workflows" / "nested").exists())


class TestCiHooksPyprojectAndModularity(unittest.TestCase):
    """AUD-014, AUD-018, AUD-019, AUD-025: CI steps, hooks.json, pyproject.toml & 500L limit."""

    def test_hooks_json_and_ci_hooks_step_behavior(self) -> None:
        hooks_path = ROOT_DIR / ".agents" / "hooks.json"
        raw = hooks_path.read_bytes()
        self.assertFalse(raw.startswith(b"\xef\xbb\xbf"), ".agents/hooks.json must have zero UTF-8 BOM")
        data = json.loads(raw.decode("utf-8"))
        self.assertIn("PreToolUse", data["hooks"])

        ci_text = (ROOT_DIR / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        self.assertIn("scripts/sdd_cli.py ci-verify", ci_text)
        ok = sdd_ci.check_hooks_json(ROOT_DIR)
        self.assertEqual(ok.status, "PASS", ok.detail)

        with tempfile.TemporaryDirectory() as tmp:
            ws = pathlib.Path(tmp)
            (ws / ".agents" / "scripts").mkdir(parents=True)
            (ws / ".agents" / "hooks.json").write_bytes(b"\xef\xbb\xbf" + raw)
            bad_bom = sdd_ci.check_hooks_json(ws)
            self.assertEqual(bad_bom.status, "FAIL")
            self.assertIn("BOM", bad_bom.detail)

            (ws / ".agents" / "hooks.json").write_text(
                json.dumps({"hooks": {"PreToolUse": [{"hooks": [{"type": "command", "command": "uv run python scripts/missing.py"}]}]}}),
                encoding="utf-8",
            )
            bad_path = sdd_ci.check_hooks_json(ws)
            self.assertEqual(bad_path.status, "FAIL")
            self.assertIn("missing.py", bad_path.detail)

    def test_ci_workflow_coverage_and_0dd_step_behavior(self) -> None:
        ci_text = (ROOT_DIR / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        self.assertNotIn("\t", ci_text)
        self.assertIn("uv run python scripts/sdd_cli.py ci-verify", ci_text)
        self.assertIn("--mode auto", ci_text)
        self.assertIn("--run-stack-if-approved", ci_text)

        sdd_ci_text = (ROOT_DIR / "scripts" / "sdd_ci.py").read_text(encoding="utf-8")
        for expected in (
            "sdd_healthcheck.py",
            "verify_architecture_boundaries.py",
            "sdd_agent_generator.py",
            ".agents/hooks.json",
            "TRACEABILITY-MATRIX.md",
            "sdd_git.py",
            "sdd_instincts.py",
            "sdd_tokens_validator.py",
            "sdd_dag.py",
            "sdd_gate_seal.py",
            '"unittest"',
        ):
            self.assertIn(expected, sdd_ci_text, f"Missing expected CI check in sdd_ci.py: {expected}")

        ok = sdd_ci.check_odd_compliance(ROOT_DIR)
        self.assertEqual(ok.status, "PASS", ok.detail)

        with tempfile.TemporaryDirectory() as tmp:
            ws = pathlib.Path(tmp)
            shutil.copytree(ROOT_DIR / ".agents" / "scripts", ws / ".agents" / "scripts", ignore=shutil.ignore_patterns("__pycache__"))
            shutil.copytree(ROOT_DIR / "docs", ws / "docs")
            (ws / "specs").mkdir()
            _write(ws / "specs" / "BACKLOG.md", "| `FEAT-042` | Feature | Widget | [x] | Done |\n")
            untraced = sdd_ci.check_odd_compliance(ws)
            self.assertEqual(untraced.status, "FAIL")
            self.assertIn("FEAT-042", untraced.detail)

            matrix = ws / "docs" / "traceability" / "TRACEABILITY-MATRIX.md"
            matrix.write_text(matrix.read_text(encoding="utf-8") + "\n## FEAT-042\n", encoding="utf-8")
            traced = sdd_ci.check_odd_compliance(ws)
            self.assertEqual(traced.status, "PASS", traced.detail)

            (ws / "docs" / "knowledge" / "API_CATALOG.md").unlink()
            missing_doc = sdd_ci.check_odd_compliance(ws)
            self.assertEqual(missing_doc.status, "FAIL")
            self.assertIn("API_CATALOG.md", missing_doc.detail)

    def test_pyproject_toml_valid_pep621_and_offline_clean(self) -> None:
        pyproject_path = ROOT_DIR / "pyproject.toml"
        self.assertTrue(pyproject_path.is_file())
        parsed = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
        project = parsed.get("project", {})
        self.assertEqual(project.get("name"), "sdd-agentic-starter")
        self.assertEqual(project.get("requires-python"), ">=3.12")
        self.assertEqual(project.get("dependencies"), [])
        self.assertIn("unittest", parsed.get("tool", {}))
        self.assertEqual(parsed.get("tool", {}).get("uv", {}).get("managed"), False)

    def test_all_framework_python_files_under_500_lines(self) -> None:
        """AUD-025: enforce <= 500 lines on EVERY .py file under scripts/, .agents/scripts/, and tests/."""
        offenders: list[tuple[str, int]] = []
        checked = 0
        for rel_dir in ("scripts", ".agents/scripts", "tests"):
            base_dir = ROOT_DIR / rel_dir
            self.assertTrue(base_dir.is_dir(), f"Expected Python directory missing: {rel_dir}")
            for py_file in sorted(base_dir.rglob("*.py")):
                if "__pycache__" in py_file.parts:
                    continue
                checked += 1
                line_count = len(py_file.read_text(encoding="utf-8").splitlines())
                if line_count > 500:
                    offenders.append((py_file.relative_to(ROOT_DIR).as_posix(), line_count))
        self.assertGreater(checked, 0)
        self.assertLessEqual(len((ROOT_DIR / "scripts" / "sdd_sync.py").read_text(encoding="utf-8").splitlines()), 500)
        self.assertLessEqual(len(pathlib.Path(__file__).read_text(encoding="utf-8").splitlines()), 500)
        self.assertEqual(offenders, [], f"Python files exceeding 500-line ceiling (no exclusions): {offenders}")


if __name__ == "__main__":
    unittest.main()
