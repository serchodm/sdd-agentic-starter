#!/usr/bin/env python3
"""Offline deterministic tests for brownfield discovery and adoption (FWK-015)."""

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

from scripts import sdd_brownfield  # noqa: E402
from scripts.sdd_generator_tx import parse_verification_commands  # noqa: E402
from scripts.sdd_ownership import detect_zone_overlaps, parse_ownership_map  # noqa: E402
from scripts.sdd_pack_registry import parse_stack_config  # noqa: E402


def _write(path: pathlib.Path, content: str) -> pathlib.Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _make_dir_link(link_path: pathlib.Path, target: pathlib.Path) -> bool:
    link_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.symlink(target, link_path, target_is_directory=True)
        return True
    except (OSError, NotImplementedError):
        if os.name == "nt":
            res = subprocess.run(
                ["cmd", "/d", "/c", "mklink", "/J", str(link_path), str(target)],
                capture_output=True, text=True, check=False,
            )
            return res.returncode == 0
        return False


def _seed_multistack_repo(repo: pathlib.Path) -> None:
    _write(
        repo / "pyproject.toml",
        '[project]\nname = "multi"\ndependencies = ["fastapi>=0.115", "sqlalchemy>=2.0"]\n'
        '[dependency-groups]\ndev = ["pytest>=8.0", "ruff>=0.6"]\n',
    )
    _write(repo / "uv.lock", "version = 1\n")
    _write(
        repo / "frontend" / "package.json",
        json.dumps({
            "name": "web-ui",
            "dependencies": {"react": "^19.0.0"},
            "scripts": {"lint": "eslint src", "test": "vitest run", "build": "vite build"},
        }),
    )
    _write(repo / "frontend" / "pnpm-lock.yaml", "lockfileVersion: '9.0'\n")
    _write(repo / "services" / "gateway" / "go.mod", "module example.com/gateway\n\ngo 1.23\n")
    _write(repo / "services" / "worker" / "Cargo.toml", '[package]\nname = "worker"\nversion = "0.1.0"\n')
    _write(repo / ".github" / "workflows" / "ci.yml", "name: CI\non: [push]\n")
    _write(repo / "backend" / "billing" / "invoice.py", "def create_invoice(amount: int) -> int:\n    return amount\n")
    _write(repo / "backend" / "auth" / "session.py", "class SessionService:\n    pass\n")
    _write(repo / "backend" / "utils" / "helpers.py", "def noop() -> None:\n    pass\n")
    _write(repo / "frontend" / "checkout" / "Cart.tsx", "export function Cart() { return null; }\n")
    _write(repo / "services" / "gateway" / "main.go", "package main\nfunc main() {}\n")
    _write(repo / "services" / "worker" / "main.rs", "fn main() {}\n")
    _write(repo / "tests" / "test_billing.py", "def test_ok():\n    assert True\n")


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ROOT_DIR / "scripts" / "sdd_cli.py"), *args],
        cwd=str(ROOT_DIR), capture_output=True, text=True, encoding="utf-8",
    )


class TestSddBrownfieldDiscovery(unittest.TestCase):
    """CA-1501: Multi-stack discovery, catalog pack filtering, zones, contexts, and JSON output."""

    def test_ca1501_multistack_discovery_and_json_output(self) -> None:
        real_packs = {
            p.name for p in (ROOT_DIR / ".sdd" / "catalog" / "packs").iterdir()
            if p.is_dir() and not p.name.startswith(".")
        }
        with tempfile.TemporaryDirectory() as tmp:
            repo = pathlib.Path(tmp) / "brownfield"
            repo.mkdir()
            _seed_multistack_repo(repo)

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                rc = sdd_brownfield.main(["--repo-root", str(repo), "--format", "json"])
            self.assertEqual(rc, 0)
            payload = json.loads(stdout.getvalue())

            self.assertTrue(payload["dry_run"])
            self.assertFalse(payload["applied"])
            disc = payload["discovery"]
            self.assertEqual(disc["ecosystems"], ["python", "typescript", "go", "rust"])
            for expected_pack in (
                "lang-python", "framework-fastapi", "capability-database",
                "lang-typescript", "framework-react", "capability-web-frontend",
                "lang-go", "lang-rust", "capability-devops",
            ):
                self.assertIn(expected_pack, disc["suggested_packs"])
            self.assertTrue(set(disc["suggested_packs"]).issubset(real_packs))
            self.assertEqual(disc["suggested_preset"], "granular")

            zones = {z["zone_id"]: z for z in disc["candidate_zones"]}
            self.assertIn("backend", zones)
            self.assertIn("frontend", zones)
            self.assertIn("services-gateway", zones)
            self.assertIn("services-worker", zones)
            self.assertIn("tests", zones)
            self.assertEqual(zones["frontend"]["owner"], "front-ui")
            self.assertEqual(zones["tests"]["owner"], "qa-tester")
            self.assertEqual(zones["backend"]["paths"], ["backend/**"])

            self.assertIn("backend/billing", disc["bounded_contexts"])
            self.assertIn("backend/auth", disc["bounded_contexts"])
            self.assertIn("frontend/checkout", disc["bounded_contexts"])
            self.assertNotIn("backend/utils", disc["bounded_contexts"])
            self.assertIn("uv run ruff check .", disc["verification_commands"]["lint"])
            self.assertIn("pnpm run build", disc["verification_commands"]["build"])

    def test_ca1501_catalog_filtering_and_compact_preset_selection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = pathlib.Path(tmp) / "small_repo"
            repo.mkdir()
            _write(repo / "pyproject.toml", '[project]\nname = "mini"\ndependencies = ["fastapi"]\n')
            _write(repo / "src" / "orders" / "service.py", "def list_orders():\n    return []\n")
            _write(repo / ".sdd" / "catalog" / "packs" / "lang-python" / "pack.json", "{}\n")

            disc = sdd_brownfield.discover_brownfield_repo(repo)
            self.assertEqual(disc.suggested_packs, ("lang-python",))
            self.assertEqual(disc.suggested_preset, "compact")
            self.assertEqual(disc.bounded_contexts, ("src/orders",))
            self.assertEqual(disc.candidate_zones[0].owner, "back-engineer")

            forced = sdd_brownfield.discover_brownfield_repo(repo, preset_override="granular")
            self.assertEqual(forced.suggested_preset, "granular")
            self.assertEqual(forced.candidate_zones[0].owner, "back-api")


class TestSddBrownfieldAdoptNonDestructive(unittest.TestCase):
    """CA-1502: Dry-run vs apply, parser compatibility, repo-map excerpt, and idempotence."""

    def test_ca1502_dry_run_vs_apply_and_parser_compatibility(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = pathlib.Path(tmp) / "app"
            repo.mkdir()
            _seed_multistack_repo(repo)

            dry_plan = sdd_brownfield.apply_adopt(repo, dry_run=True, with_repo_map=True)
            self.assertTrue(dry_plan.dry_run)
            self.assertFalse(dry_plan.applied)
            self.assertEqual(
                dry_plan.created,
                ("specs/STACK.md", "docs/knowledge/BROWNFIELD_INVENTORY.md", "specs/BACKLOG.md"),
            )
            self.assertFalse((repo / "specs" / "STACK.md").exists())
            self.assertFalse((repo / "docs" / "knowledge" / "BROWNFIELD_INVENTORY.md").exists())
            self.assertFalse((repo / "specs" / "BACKLOG.md").exists())

            applied = sdd_brownfield.apply_adopt(repo, dry_run=False, with_repo_map=True)
            self.assertFalse(applied.dry_run)
            self.assertTrue(applied.applied)
            self.assertEqual(applied.skipped_existing, ())

            stack_path = repo / "specs" / "STACK.md"
            inv_path = repo / "docs" / "knowledge" / "BROWNFIELD_INVENTORY.md"
            backlog_path = repo / "specs" / "BACKLOG.md"
            self.assertTrue(stack_path.is_file())
            self.assertTrue(inv_path.is_file())
            self.assertTrue(backlog_path.is_file())

            stack_text = stack_path.read_text(encoding="utf-8")
            self.assertIn("[ ] Gate S0 Approved (Human Sign-off)", stack_text)
            self.assertNotIn("[x] Gate S0 Approved", stack_text)

            stack_cfg, gate_approved = parse_stack_config(stack_path)
            self.assertFalse(gate_approved)
            self.assertFalse(stack_cfg.stack_approved)
            self.assertFalse(stack_cfg.gate00_approved)
            self.assertEqual(stack_cfg.preset, "granular")
            self.assertIn("lang-python", stack_cfg.packs)

            ownership_cfg = parse_ownership_map(stack_path)
            self.assertIsNotNone(ownership_cfg)
            assert ownership_cfg is not None
            self.assertEqual(ownership_cfg.unowned_policy, "error")
            detect_zone_overlaps(ownership_cfg)

            verif_cmds = parse_verification_commands(stack_path)
            self.assertIsNotNone(verif_cmds.lint)
            self.assertIsNotNone(verif_cmds.unit_test)

            inv_text = inv_path.read_text(encoding="utf-8")
            self.assertIn("## Repo Map Excerpt", inv_text)
            self.assertIn("create_invoice", inv_text)
            self.assertIn("SessionService", inv_text)

            # Re-running --apply must preserve all existing files intact
            stack_path.write_text(stack_text + "\n<!-- custom user note -->\n", encoding="utf-8")
            backlog_path.write_text(backlog_path.read_text(encoding="utf-8") + "| `FEAT-001` | Feature | Existing | - | Draft |\n", encoding="utf-8")
            inv_path.write_text("# Custom Inventory\n", encoding="utf-8")
            before_stack = stack_path.read_bytes()
            before_backlog = backlog_path.read_bytes()
            before_inv = inv_path.read_bytes()

            rerun = sdd_brownfield.apply_adopt(repo, dry_run=False)
            self.assertEqual(rerun.created, ())
            self.assertEqual(
                rerun.skipped_existing,
                ("specs/STACK.md", "docs/knowledge/BROWNFIELD_INVENTORY.md", "specs/BACKLOG.md"),
            )
            self.assertEqual(stack_path.read_bytes(), before_stack)
            self.assertEqual(backlog_path.read_bytes(), before_backlog)
            self.assertEqual(inv_path.read_bytes(), before_inv)

            # --overwrite-inventory updates only BROWNFIELD_INVENTORY.md, never STACK.md or BACKLOG.md
            overwrite = sdd_brownfield.apply_adopt(repo, dry_run=False, overwrite_inventory=True)
            self.assertEqual(overwrite.created, ("docs/knowledge/BROWNFIELD_INVENTORY.md",))
            self.assertEqual(overwrite.skipped_existing, ("specs/STACK.md", "specs/BACKLOG.md"))
            self.assertEqual(stack_path.read_bytes(), before_stack)
            self.assertEqual(backlog_path.read_bytes(), before_backlog)
            self.assertIn("# Brownfield Inventory", inv_path.read_text(encoding="utf-8"))


class TestSddBrownfieldSecurityAndSanitization(unittest.TestCase):
    """CA-1503: Fail-closed repo_root validation and unsafe package.json command sanitization."""

    def test_ca1503_fail_closed_invalid_and_symlink_repo_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = pathlib.Path(tmp)
            missing = base / "does-not-exist"
            with self.assertRaises(sdd_brownfield.BrownfieldError):
                sdd_brownfield.discover_brownfield_repo(missing)

            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                rc = sdd_brownfield.main(["--repo-root", str(missing)])
            self.assertEqual(rc, 1)
            self.assertIn("[ERROR]", stderr.getvalue())

            regular_file = _write(base / "not_a_dir.txt", "hello\n")
            with self.assertRaises(sdd_brownfield.BrownfieldError):
                sdd_brownfield.discover_brownfield_repo(regular_file)

            with self.assertRaises(sdd_brownfield.BrownfieldError):
                sdd_brownfield.discover_brownfield_repo("   ")

            real_dir = base / "real_repo"
            real_dir.mkdir()
            link_dir = base / "link_repo"
            if _make_dir_link(link_dir, real_dir):
                with self.assertRaises(sdd_brownfield.BrownfieldError):
                    sdd_brownfield.discover_brownfield_repo(link_dir)
                stderr_link = io.StringIO()
                with contextlib.redirect_stderr(stderr_link):
                    rc_link = sdd_brownfield.main(["--repo-root", str(link_dir)])
                self.assertEqual(rc_link, 1)
            else:
                with mock.patch.object(
                    sdd_brownfield, "is_link_or_junction", side_effect=lambda p: p == link_dir
                ):
                    with self.assertRaises(sdd_brownfield.BrownfieldError):
                        sdd_brownfield.discover_brownfield_repo(link_dir)

    def test_ca1503_sanitizes_unsafe_package_json_scripts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = pathlib.Path(tmp) / "unsafe_node"
            repo.mkdir()
            _write(
                repo / "package.json",
                json.dumps({
                    "name": "unsafe-app",
                    "dependencies": {"react": "^18.3.0"},
                    "scripts": {
                        "lint": "eslint . ; rm -rf /",
                        "typecheck": "tsc --noEmit | cat",
                        "test": "jest $(whoami)",
                        "build": "vite build",
                    },
                }),
            )
            _write(repo / "src" / "App.tsx", "export const App = () => null;\n")

            plan = sdd_brownfield.apply_adopt(repo, dry_run=False)
            disc = plan.discovery
            self.assertEqual(len(disc.rejected_commands), 3)
            joined_rejected = "\n".join(disc.rejected_commands)
            self.assertIn("eslint . ; rm -rf /", joined_rejected)
            self.assertIn("tsc --noEmit | cat", joined_rejected)
            self.assertIn("jest $(whoami)", joined_rejected)

            self.assertEqual(disc.verification_commands, {"build": "npm run build"})
            for cmd in disc.verification_commands.values():
                for bad_tok in (";", "|", "$("):
                    self.assertNotIn(bad_tok, cmd)

            stack_path = repo / "specs" / "STACK.md"
            stack_text = stack_path.read_text(encoding="utf-8")
            self.assertNotIn("rm -rf", stack_text)
            self.assertNotIn("$(whoami)", stack_text)
            self.assertNotIn("| cat", stack_text)

            verif = parse_verification_commands(stack_path)
            self.assertIsNone(verif.lint)
            self.assertIsNone(verif.unit_test)
            self.assertEqual(verif.build, "npm run build")

            inv_text = (repo / "docs" / "knowledge" / "BROWNFIELD_INVENTORY.md").read_text(encoding="utf-8")
            self.assertIn("### Rejected Unsafe Commands", inv_text)


class TestSddBrownfieldCliAndFrameworkBudget(unittest.TestCase):
    """CA-1504: CLI dispatch (`sdd_cli.py adopt`), compact workflow, .agents/ budget, and <=500L ceiling."""

    def test_ca1504_cli_adopt_json_and_help(self) -> None:
        help_root = _run_cli("--help")
        self.assertEqual(help_root.returncode, 0, help_root.stderr)
        self.assertIn("adopt", help_root.stdout)

        help_adopt = _run_cli("adopt", "--help")
        self.assertEqual(help_adopt.returncode, 0, help_adopt.stderr)
        self.assertIn("--repo-root", help_adopt.stdout)
        self.assertIn("--apply", help_adopt.stdout)

        with tempfile.TemporaryDirectory() as tmp:
            repo = pathlib.Path(tmp) / "cli_repo"
            repo.mkdir()
            _seed_multistack_repo(repo)

            dry_proc = _run_cli("adopt", "--repo-root", str(repo), "--format", "json")
            self.assertEqual(dry_proc.returncode, 0, dry_proc.stdout + dry_proc.stderr)
            dry_json = json.loads(dry_proc.stdout)
            self.assertTrue(dry_json["dry_run"])
            self.assertFalse((repo / "specs" / "STACK.md").exists())

            apply_proc = _run_cli("adopt", "--repo-root", str(repo), "--apply", "--format", "json")
            self.assertEqual(apply_proc.returncode, 0, apply_proc.stdout + apply_proc.stderr)
            apply_json = json.loads(apply_proc.stdout)
            self.assertTrue(apply_json["applied"])
            self.assertTrue((repo / "specs" / "STACK.md").is_file())
            self.assertTrue((repo / "docs" / "knowledge" / "BROWNFIELD_INVENTORY.md").is_file())
            self.assertTrue((repo / "specs" / "BACKLOG.md").is_file())

    def test_ca1504_workflow_compact_token_budget_and_500_line_ceiling(self) -> None:
        wf_path = ROOT_DIR / ".agents" / "workflows" / "brownfield-adopt.md"
        self.assertTrue(wf_path.is_file(), f"Missing workflow: {wf_path}")
        wf_lines = wf_path.read_text(encoding="utf-8").splitlines()
        self.assertLessEqual(len(wf_lines), 25, f"brownfield-adopt.md exceeded 25 lines ({len(wf_lines)})")

        md_bytes = sum(p.stat().st_size for p in (ROOT_DIR / ".agents").rglob("*.md") if p.is_file() and "references" not in p.parts)
        self.assertLess(md_bytes, 100_000, f".agents/ markdown exceeded 100KB ({md_bytes}B)")
        self.assertLess(md_bytes / 4.0, 25_000, f".agents/ markdown exceeded 25k tokens ({md_bytes / 4.0:.1f})")

        offenders: list[tuple[str, int]] = []
        for rel_dir in ("scripts", ".agents/scripts", "tests"):
            for py_file in sorted((ROOT_DIR / rel_dir).rglob("*.py")):
                if "__pycache__" in py_file.parts:
                    continue
                line_count = len(py_file.read_text(encoding="utf-8").splitlines())
                if line_count > 500:
                    offenders.append((py_file.relative_to(ROOT_DIR).as_posix(), line_count))
        self.assertEqual(offenders, [], f"Python files exceeding 500-line ceiling: {offenders}")


if __name__ == "__main__":
    unittest.main()
