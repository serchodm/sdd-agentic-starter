#!/usr/bin/env python3
"""Offline adversarial & BDD acceptance suite for FWK-016 (CA-1601..CA-1604)."""

from __future__ import annotations

import json, os, pathlib, subprocess, sys, tempfile, unittest

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
for _p in (ROOT_DIR, ROOT_DIR / "scripts", ROOT_DIR / ".agents" / "scripts"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import sdd_ci, sdd_cli, sdd_drift, sdd_gate_seal, sdd_healthcheck, sdd_ownership  # noqa: E402

CODE_GUARD_SCRIPT = ROOT_DIR / ".agents" / "scripts" / "sdd_code_gate_guard.py"
CLI_SCRIPT = ROOT_DIR / "scripts" / "sdd_cli.py"
_GIT_ENV = {
    **os.environ,
    "GIT_AUTHOR_NAME": "SDD Test", "GIT_AUTHOR_EMAIL": "sdd@example.invalid",
    "GIT_COMMITTER_NAME": "SDD Test", "GIT_COMMITTER_EMAIL": "sdd@example.invalid",
}


def _write(path: pathlib.Path, content: str) -> pathlib.Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _git(cwd: pathlib.Path, *args: str) -> str:
    res = subprocess.run(
        ["git", *args], cwd=str(cwd), env=_GIT_ENV,
        capture_output=True, text=True, encoding="utf-8", errors="replace", check=True,
    )
    return res.stdout.strip()


def _init_git_repo(root: pathlib.Path, branch: str = "develop") -> pathlib.Path:
    root.mkdir(parents=True, exist_ok=True)
    _git(root, "init", "-b", branch)
    _git(root, "config", "user.name", "SDD Test")
    _git(root, "config", "user.email", "sdd@example.invalid")
    return root


def _run_guard(cwd: pathlib.Path, rel_path: str, tool: str = "write_file", content: str = "x = 1\n") -> dict[str, object]:
    payload = json.dumps({"toolCall": {"name": tool, "args": {"Path": rel_path, "Content": content}}})
    proc = subprocess.run(
        [sys.executable, str(CODE_GUARD_SCRIPT)], cwd=str(cwd), input=payload,
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if proc.returncode != 0:
        raise AssertionError(f"sdd_code_gate_guard exited {proc.returncode}: {proc.stderr!r}")
    return json.loads(proc.stdout.strip())


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CLI_SCRIPT), *args], cwd=str(ROOT_DIR),
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )


def _seed_strangler_stack(root: pathlib.Path, *, invalid_gov: bool = False) -> pathlib.Path:
    gov = "frozen" if invalid_gov else "legacy-readonly"
    return _write(
        root / "specs" / "STACK.md",
        "# Stack\n\n> **ESTADO:** `[x] Gate S0 Approved`\n\n"
        "```yaml sdd:ownership-map\n"
        "unowned_policy: error\n"
        "zones:\n"
        "  legacy-billing:\n"
        "    owner: back-engineer\n"
        f"    governance: {gov}\n"
        "    paths:\n      - app/legacy/**\n"
        "  new-billing:\n"
        "    owner: back-engineer\n"
        "    governance: governed\n"
        "    paths:\n      - app/billing/**\n"
        "```\n",
    )


def _seed_active_work_item(root: pathlib.Path, item_id: str = "FEAT-010") -> pathlib.Path:
    spec_dir = root / "specs" / "features" / f"{item_id}-billing"
    _write(
        root / "specs" / "BACKLOG.md",
        "# Backlog\n\n| ID | Tipo | Titulo | Estado Final |\n| :--- | :--- | :--- | :--- |\n"
        f"| `{item_id}` | Feature | Billing | In Progress |\n",
    )
    _write(spec_dir / "01-spec.md", "# Spec\n\nFunctional billing spec.\n\n- [x] Gate 1 Approved\n")
    _write(spec_dir / "02-tech-spec.md", "# Tech\n\nBilling service architecture.\n\n- [x] Gate 2 Approved\n")
    _write(spec_dir / "03-tasks.md", "# Tasks\n\nAtomic billing task breakdown.\n\n- [x] Gate 3 Approved\n")
    _write(
        root / ".agents" / "active_work_item.json",
        json.dumps({
            "active_work_item_id": item_id, "spec_dir": spec_dir.relative_to(root).as_posix(),
            "gate_1_approved": True, "gate_2_approved": True, "gate_3_approved": True, "approved_by_human": True,
        }),
    )
    sdd_gate_seal.seal_work_item_gates(root, item_id)
    return spec_dir


def _seed_drift_repo(root: pathlib.Path) -> str:
    _init_git_repo(root)
    _write(root / "app" / "orders" / "service.py", "def create_order(order_id: str) -> str:\n    return order_id\n")
    _write(root / "app" / "legacy" / "old.py", "def legacy_calc() -> int:\n    return 42\n")
    _git(root, "add", ".")
    _git(root, "commit", "-m", "chore: initial brownfield code")
    code_sha = _git(root, "rev-parse", "HEAD")

    _write(
        root / "specs" / "STACK.md",
        "# Stack\n\n> **ESTADO:** `[x] Gate S0 Approved`\n\n"
        "```yaml sdd:ownership-map\n"
        "unowned_policy: error\n"
        "zones:\n"
        "  legacy-core:\n"
        "    owner: back-engineer\n"
        "    governance: legacy-readonly\n"
        "    paths:\n      - app/legacy/**\n"
        "  orders-core:\n"
        "    owner: back-engineer\n"
        "    governance: governed\n"
        "    paths:\n      - app/orders/**\n"
        "```\n",
    )
    _write(
        root / "specs" / "BACKLOG.md",
        "# Backlog\n\n| ID | Tipo | Titulo | Feature Afectada | Estado |\n"
        "| :--- | :--- | :--- | :--- | :--- |\n| `FEAT-001` | Feature | Orders | - | Done |\n",
    )
    feat_dir = root / "specs" / "features" / "FEAT-001-orders"
    _write(
        feat_dir / "01-spec.md",
        f"# Spec FEAT-001\n\n- Origin: brownfield-mined\n- SRC-001: `app/orders/service.py::create_order` ({code_sha[:10]})\n\n- [x] Gate 1 Approved\n",
    )
    _write(feat_dir / "02-tech-spec.md", "# Tech FEAT-001\n\nAs-built orders service contract.\n\n- [x] Gate 2 Approved\n")
    _write(
        root / "docs" / "traceability" / "TRACEABILITY-MATRIX.md",
        "# Traceability\n\n| Feature | Source |\n| :--- | :--- |\n| `FEAT-001` | `app/orders/service.py` |\n",
    )
    _git(root, "add", ".")
    _git(root, "commit", "-m", "docs: baseline FEAT-001")
    return code_sha


class TestStranglerFigOwnershipAndGuard(unittest.TestCase):
    """CA-1601: Strangler Fig governance zones, brownfield roots, and PreToolUse guard lock."""

    def test_ownership_governance_validation_and_candidate_roots(self) -> None:
        with self.assertRaises(sdd_ownership.OwnershipError):
            sdd_ownership.OwnershipZone(zone_id="bad", owner="back-engineer", paths=("app/**",), governance="frozen")  # type: ignore[arg-type]

        with tempfile.TemporaryDirectory() as tmp:
            repo = pathlib.Path(tmp) / "repo"
            bad_stack = _seed_strangler_stack(repo, invalid_gov=True)
            with self.assertRaises(sdd_ownership.OwnershipError):
                sdd_ownership.parse_ownership_map(bad_stack)

            cfg = sdd_ownership.parse_ownership_map(_seed_strangler_stack(repo, invalid_gov=False))
            assert cfg is not None

            legacy_zone = sdd_ownership.resolve_path_zone(cfg, "app/legacy/invoice.py")
            governed_zone = sdd_ownership.resolve_path_zone(cfg, "app/billing/service.py")
            self.assertIsNotNone(legacy_zone)
            self.assertEqual(legacy_zone.governance, "legacy-readonly")
            self.assertIsNotNone(governed_zone)
            self.assertEqual(governed_zone.governance, "governed")
            self.assertIsNone(sdd_ownership.resolve_path_zone(cfg, "other/unmatched.py"))

            roots = sdd_ownership.derive_candidate_roots(cfg)
            self.assertIn("app", roots)
            for default_root in sdd_ownership.DEFAULT_CANDIDATE_ROOTS:
                self.assertIn(default_root, roots)

            _write(repo / "app" / "legacy" / "invoice.py", "def old(): pass\n")
            _write(repo / "app" / "billing" / "service.py", "def new(): pass\n")
            self.assertEqual(sdd_ownership.validate_repo_coverage(cfg, repo), [])

            _write(repo / "app" / "orphan" / "leak.py", "def leak(): pass\n")
            with self.assertRaises(sdd_ownership.OwnershipError):
                sdd_ownership.validate_repo_coverage(cfg, repo)

    def test_code_gate_guard_strangler_fig_and_brownfield_lock(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = _init_git_repo(pathlib.Path(tmp) / "repo")
            _seed_strangler_stack(repo)

            self.assertEqual(_run_guard(repo, "app/billing/service.py")["decision"], "deny")

            _seed_active_work_item(repo, "FEAT-010")
            deny_legacy = _run_guard(repo, "app/legacy/invoice.py")
            self.assertEqual(deny_legacy["decision"], "deny")
            self.assertIn("legacy-readonly", str(deny_legacy["reason"]))

            self.assertEqual(_run_guard(repo, "app/billing/service.py")["decision"], "allow")

            _seed_strangler_stack(repo, invalid_gov=True)
            self.assertEqual(_run_guard(repo, "app/billing/service.py")["decision"], "deny")


class TestBrownfieldMinedBaseline(unittest.TestCase):
    """CA-1602: Light retroactive baseline (`Origin: brownfield-mined`) & fail-closed checks."""

    def test_brownfield_mined_baseline_passes_healthcheck_and_gate_seals(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = pathlib.Path(tmp) / "repo"
            feat_dir = repo / "specs" / "features" / "FEAT-001-auth"
            _write(
                repo / "specs" / "BACKLOG.md",
                "# Backlog\n\n| ID | Tipo | Titulo | Estado |\n| :--- | :--- | :--- | :--- |\n| `FEAT-001` | Feature | Auth | Done |\n",
            )
            _write(feat_dir / "01-spec.md", "# Auth Spec\n\nOrigin: brownfield-mined\n\n- [x] Gate 1 Approved\n")
            _write(feat_dir / "02-tech-spec.md", "# Auth Tech\n\nMined auth architecture.\n\n- [x] Gate 2 Approved\n")

            self.assertTrue(sdd_gate_seal.is_brownfield_mined_baseline(feat_dir))
            self.assertEqual(sdd_gate_seal.validate_brownfield_baseline_docs(feat_dir, "specs/features/FEAT-001-auth"), [])
            self.assertEqual(sdd_healthcheck.check_spec_triads(repo / "specs", repo / "specs" / "BACKLOG.md"), [])

            _write(
                repo / ".agents" / "active_work_item.json",
                json.dumps({"active_work_item_id": "FEAT-001", "spec_dir": "specs/features/FEAT-001-auth"}),
            )
            seals = sdd_gate_seal.seal_work_item_gates(repo, "FEAT-001")
            self.assertEqual(sorted(seals), ["1", "2"])
            ok, msg = sdd_gate_seal.verify_work_item_gate_seals(repo, require_seals=True)
            self.assertTrue(ok, msg)

            _write(feat_dir / "02-tech-spec.md", "# Tampered\n\nModified text.\n\n- [x] Gate 2 Approved\n")
            self.assertFalse(sdd_gate_seal.verify_work_item_gate_seals(repo, require_seals=True)[0])

    def test_normal_feature_and_invalid_brownfield_markers_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = pathlib.Path(tmp) / "repo"
            _write(
                repo / "specs" / "BACKLOG.md",
                "# Backlog\n\n| ID | Tipo | Titulo | Estado |\n| :--- | :--- | :--- | :--- |\n"
                "| `FEAT-002` | Feature | Orders | Done |\n"
                "| `FEAT-003` | Feature | Payments | Done |\n"
                "| `FEAT-004` | Feature | Hidden | Done |\n",
            )
            f2 = repo / "specs" / "features" / "FEAT-002-orders"
            _write(f2 / "01-spec.md", "# Orders\n\nNormal spec without tasks.\n\n- [x] Gate 1 Approved\n")
            _write(f2 / "02-tech-spec.md", "# Orders Tech\n\nNormal tech spec.\n\n- [x] Gate 2 Approved\n")

            f3 = repo / "specs" / "features" / "FEAT-003-payments"
            _write(f3 / "01-spec.md", "# Payments\n\nOrigin: brownfield-mined\n\n- [x] Gate 1 Approved\n")
            _write(f3 / "02-tech-spec.md", "# Payments Tech\n\nMissing Gate 2 checkbox.\n\n- [ ] Gate 2 Approved\n")

            f4 = repo / "specs" / "features" / "FEAT-004-hidden"
            _write(f4 / "01-spec.md", "# Hidden\n\n<!-- Origin: brownfield-mined -->\n```yaml\nOrigin: brownfield-mined\n```\n\n- [x] Gate 1 Approved\n")
            _write(f4 / "02-tech-spec.md", "# Hidden Tech\n\nTech spec content.\n\n- [x] Gate 2 Approved\n")

            self.assertFalse(sdd_gate_seal.is_brownfield_mined_baseline(f4))
            joined = "\n".join(sdd_healthcheck.check_spec_triads(repo / "specs", repo / "specs" / "BACKLOG.md"))
            for name in ("FEAT-002-orders", "FEAT-003-payments", "FEAT-004-hidden"):
                self.assertIn(name, joined)

            for fid, fdir in (("FEAT-002", f2), ("FEAT-003", f3), ("FEAT-004", f4)):
                _write(
                    repo / ".agents" / "active_work_item.json",
                    json.dumps({"active_work_item_id": fid, "spec_dir": fdir.relative_to(repo).as_posix()}),
                )
                self.assertFalse(sdd_gate_seal.verify_work_item_gate_seals(repo, require_seals=False)[0], fid)
                with self.assertRaises(ValueError):
                    sdd_gate_seal.seal_work_item_gates(repo, fid)


class TestSpecDriftDetectorAndCli(unittest.TestCase):
    """CA-1603: Offline Spec Drift detector (`UNCOVERED_FILE`, `MISSING_*`, `UNLINKED_CODE_DRIFT`, CR lifecycle)."""

    def test_clean_baseline_uncovered_file_and_strict_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = pathlib.Path(tmp) / "repo"
            _seed_drift_repo(repo)

            clean = sdd_drift.run_drift_check(repo)
            self.assertEqual(clean.status, "PASS")
            self.assertEqual(clean.findings, ())
            self.assertEqual((clean.governed_files, clean.legacy_readonly_files, clean.citations_checked), (1, 1, 1))

            _write(repo / "app" / "orders" / "orphan.py", "def orphan_fn() -> None:\n    pass\n")
            text_proc = _run_cli("drift", "--repo-root", str(repo), "--format", "text")
            self.assertEqual(text_proc.returncode, 0, text_proc.stdout + text_proc.stderr)
            self.assertIn("UNCOVERED_FILE", text_proc.stdout)

            strict_proc = _run_cli("drift", "--repo-root", str(repo), "--strict", "--format", "json")
            self.assertEqual(strict_proc.returncode, 1)
            strict_json = json.loads(strict_proc.stdout)
            self.assertEqual(strict_json["status"], "FAIL")
            self.assertTrue(any(f["kind"] == "UNCOVERED_FILE" and f["severity"] == "error" for f in strict_json["findings"]))

    def test_missing_symbol_and_missing_source_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = pathlib.Path(tmp) / "repo"
            _seed_drift_repo(repo)

            svc = repo / "app" / "orders" / "service.py"
            _write(svc, "def submit_order(order_id: str) -> str:\n    return order_id\n")
            renamed = sdd_drift.run_drift_check(repo)
            self.assertEqual(renamed.status, "FAIL")
            self.assertTrue(any(f.kind == "MISSING_SYMBOL" and f.severity == "error" and f.feature_id == "FEAT-001" and f.symbol == "create_order" for f in renamed.findings))

            svc.unlink()
            missing = sdd_drift.run_drift_check(repo)
            self.assertEqual(missing.status, "FAIL")
            self.assertTrue(any(f.kind == "MISSING_SOURCE_FILE" and f.severity == "error" and f.path == "app/orders/service.py" for f in missing.findings))

    def test_unlinked_code_drift_and_cr_open_closed_post_cr_lifecycle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = pathlib.Path(tmp) / "repo"
            _seed_drift_repo(repo)
            svc = repo / "app" / "orders" / "service.py"

            _write(svc, "def create_order(order_id: str) -> str:\n    return order_id.strip()\n")
            drift_proc = _run_cli("drift", "--repo-root", str(repo), "--format", "json")
            self.assertEqual(drift_proc.returncode, 1)
            drift_json = json.loads(drift_proc.stdout)
            self.assertEqual(drift_json["status"], "FAIL")
            self.assertTrue(any(f["kind"] == "UNLINKED_CODE_DRIFT" and f["severity"] == "error" and f["path"] == "app/orders/service.py" for f in drift_json["findings"]))

            # Open CR-001 linked to FEAT-001 and rename symbol -> PASS while CR-001 is active
            _write(svc, "def submit_order(order_id: str) -> str:\n    return order_id.strip()\n")
            _write(
                repo / "specs" / "BACKLOG.md",
                "# Backlog\n\n| ID | Tipo | Titulo | Feature Afectada | Estado |\n| :--- | :--- | :--- | :--- | :--- |\n"
                "| `FEAT-001` | Feature | Orders | - | Done |\n| `CR-001` | Change | Rename create_order | `FEAT-001` | In Progress |\n",
            )
            cr_dir = repo / "specs" / "changes" / "CR-001-rename-order"
            _write(cr_dir / "01-spec.md", "# CR-001\n\n- **Feature Afectada:** `FEAT-001`\n- SRC-001: `app/orders/service.py::submit_order`\n\n- [x] Gate 1 Approved\n")
            _write(cr_dir / "02-tech-spec.md", "# Tech CR-001\n\nRename contract.\n\n- [x] Gate 2 Approved\n")
            _write(cr_dir / "03-tasks.md", "# Tasks CR-001\n\nUpdate service.\n\n- [x] Gate 3 Approved\n")

            open_proc = _run_cli("drift", "--repo-root", str(repo), "--format", "json")
            self.assertEqual(open_proc.returncode, 0, open_proc.stdout + open_proc.stderr)
            self.assertEqual(json.loads(open_proc.stdout)["status"], "PASS")

            # Commit code, close CR-001 as Done with updated SRC-001 SHA without mutating FEAT-001
            _git(repo, "add", "app/orders/service.py")
            _git(repo, "commit", "-m", "feat(orders): rename create_order to submit_order")
            cr_sha = _git(repo, "rev-parse", "HEAD")

            _write(cr_dir / "01-spec.md", f"# CR-001\n\n- **Feature Afectada:** `FEAT-001`\n- SRC-001: `app/orders/service.py::submit_order` ({cr_sha[:10]})\n\n- [x] Gate 1 Approved\n")
            _write(
                repo / "specs" / "BACKLOG.md",
                "# Backlog\n\n| ID | Tipo | Titulo | Feature Afectada | Estado |\n| :--- | :--- | :--- | :--- | :--- |\n"
                "| `FEAT-001` | Feature | Orders | - | Done |\n| `CR-001` | Change | Rename create_order | `FEAT-001` | Done |\n",
            )
            _git(repo, "add", "specs")
            _git(repo, "commit", "-m", "docs(cr-001): close CR-001 as Done")

            closed_proc = _run_cli("drift", "--repo-root", str(repo), "--format", "json")
            self.assertEqual(closed_proc.returncode, 0, closed_proc.stdout + closed_proc.stderr)
            closed_json = json.loads(closed_proc.stdout)
            self.assertEqual(closed_json["status"], "PASS")
            self.assertEqual(closed_json["findings"], [])

            # Subsequent edit after CR-001 is Done without opening CR-002 must trigger UNLINKED_CODE_DRIFT
            _write(svc, "def submit_order(order_id: str) -> str:\n    return order_id.upper()\n")
            post_proc = _run_cli("drift", "--repo-root", str(repo), "--format", "json")
            self.assertEqual(post_proc.returncode, 1)
            post_json = json.loads(post_proc.stdout)
            self.assertEqual(post_json["status"], "FAIL")
            self.assertTrue(any(f["kind"] == "UNLINKED_CODE_DRIFT" for f in post_json["findings"]))


class TestCiIntegrationAndModularity(unittest.TestCase):
    """CA-1604: sdd_ci integration, CLI dispatch, <= 500L ceiling, and < 25k token budget."""

    def test_ci_verify_framework_and_project_modes(self) -> None:
        fwk_report = sdd_ci.run_ci_verify(ROOT_DIR, mode="framework", skip_tests=True)
        self.assertEqual(fwk_report.overall_status, "PASS")
        self.assertEqual(next(c for c in fwk_report.checks if c.name == "spec_drift").status, "SKIPPED_NO_APPLICABLE")

        with tempfile.TemporaryDirectory() as tmp:
            repo = pathlib.Path(tmp) / "proj"
            _seed_drift_repo(repo)
            for rel in ("ADRS.md", "API_CATALOG.md", "DATA_MODELS.md", "SYSTEM_TOPOLOGY.md"):
                _write(repo / "docs" / "knowledge" / rel, f"# {rel}\n\nSeeded knowledge.\n")
            _write(repo / "docs" / "es" / "guide.md", "# Guia\n\nDocumentacion.\n")
            _write(repo / "docs" / "en" / "guide.md", "# Guide\n\nDocumentation.\n")
            _write(repo / "app" / "orders" / "service.py", "def create_order(order_id: str) -> str:\n    return order_id.upper()\n")

            drift_res = sdd_ci.check_spec_drift(repo, mode="project")
            self.assertEqual(drift_res.status, "FAIL")
            self.assertTrue(any(f["kind"] == "UNLINKED_CODE_DRIFT" for f in drift_res.data["findings"]))

            proj_report = sdd_ci.run_ci_verify(repo, mode="project")
            self.assertEqual(proj_report.overall_status, "FAIL")
            self.assertEqual(next(c for c in proj_report.checks if c.name == "spec_drift").status, "FAIL")

    def test_cli_dispatch_and_help_expose_drift(self) -> None:
        self.assertEqual(sdd_cli.DISPATCH_MAP["drift"], ROOT_DIR / "scripts" / "sdd_drift.py")
        help_proc = _run_cli("--help")
        self.assertEqual(help_proc.returncode, 0)
        self.assertIn("drift", help_proc.stdout)

    def test_modularity_500_line_ceiling_and_agents_token_budget(self) -> None:
        offenders: list[tuple[str, int]] = []
        for rel_dir in ("scripts", ".agents/scripts", "tests"):
            for py_file in sorted((ROOT_DIR / rel_dir).rglob("*.py")):
                if "__pycache__" in py_file.parts:
                    continue
                lines = len(py_file.read_text(encoding="utf-8").splitlines())
                if lines > 500:
                    offenders.append((py_file.relative_to(ROOT_DIR).as_posix(), lines))
        self.assertEqual(offenders, [], f"Python files exceeding 500-line ceiling: {offenders}")

        md_bytes = sum(p.stat().st_size for p in (ROOT_DIR / ".agents").rglob("*.md") if p.is_file() and "references" not in p.parts)
        self.assertLess(md_bytes / 4.0, 25_000, f".agents/ markdown exceeded 25k tokens ({md_bytes / 4.0:.1f})")


if __name__ == "__main__":
    unittest.main()
