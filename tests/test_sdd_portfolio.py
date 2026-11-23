#!/usr/bin/env python3
"""Offline unit and CLI integration tests for FWK-017 (Portfolio, Epics & Feature DAG)."""

from __future__ import annotations

import json, os, pathlib, subprocess, sys, tempfile, textwrap, unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
for _p in (str(REPO_ROOT), str(REPO_ROOT / "scripts"), str(REPO_ROOT / ".agents" / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import sdd_ci, sdd_cli, sdd_portfolio  # noqa: E402

CLI_SCRIPT = REPO_ROOT / "scripts" / "sdd_cli.py"
TEMPLATE_PATH = REPO_ROOT / "specs" / "templates" / "09-epic-roadmap.template.md"


def _write(path: pathlib.Path, content: str) -> pathlib.Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    return subprocess.run(
        [sys.executable, str(CLI_SCRIPT), *args],
        cwd=str(REPO_ROOT), env=env, capture_output=True, text=True, encoding="utf-8", errors="replace", shell=False,
    )


def _create_dir_link(target: pathlib.Path, link_path: pathlib.Path) -> None:
    try:
        os.symlink(target, link_path, target_is_directory=True)
        return
    except OSError:
        if os.name != "nt":
            raise
    res = subprocess.run(["cmd", "/c", "mklink", "/J", str(link_path), str(target)], capture_output=True, text=True, shell=False)
    if res.returncode != 0:
        raise AssertionError(f"Failed to create Windows junction: {res.stderr or res.stdout}")


def _epic_md(epic_id: str, yaml_body: str, title: str = "Test Epic") -> str:
    return f"# Épica: `{epic_id}` — {title}\n\n```yaml sdd:epic\n{textwrap.dedent(yaml_body).strip()}\n```\n"


class TestPortfolioInitCA1701(unittest.TestCase):
    """CA-1701: Safe deterministic `portfolio init` without accidental overwrite or symlinks."""

    def test_cli_init_creates_valid_epic_and_blocks_overwrite_without_force(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = pathlib.Path(tmp)
            if TEMPLATE_PATH.is_file():
                _write(repo / "specs" / "templates" / "09-epic-roadmap.template.md", TEMPLATE_PATH.read_text(encoding="utf-8"))
            res1 = _run_cli("portfolio", "init", "--repo-root", str(repo), "--id", "EPIC-001", "--title", "Core Billing")
            self.assertEqual(res1.returncode, 0, res1.stderr or res1.stdout)
            target = repo / "specs" / "epics" / "EPIC-001-core-billing.md"
            self.assertTrue(target.is_file())
            content = target.read_text(encoding="utf-8")
            self.assertIn("```yaml sdd:epic", content)
            self.assertIn('status: "Draft"', content)
            self.assertNotIn("[x]", content.lower())

            report = sdd_portfolio.analyze_portfolio(repo)
            self.assertEqual((report.status, report.epics[0].epic_id, report.epics[0].title, report.epics[0].status), ("PASS", "EPIC-001", "Core Billing", "Draft"))

            _write(target, content + "\n<!-- keep-sentinel -->\n")
            before = target.read_text(encoding="utf-8")
            res2 = _run_cli("portfolio", "init", "--repo-root", str(repo), "--id", "EPIC-001", "--title", "Core Billing")
            self.assertNotEqual(res2.returncode, 0)
            self.assertEqual(target.read_text(encoding="utf-8"), before)

            res3 = _run_cli("portfolio", "init", "--repo-root", str(repo), "--id", "EPIC-001", "--title", "Core Billing", "--force", "--format", "json")
            self.assertEqual(res3.returncode, 0, res3.stderr or res3.stdout)
            self.assertEqual(json.loads(res3.stdout)["status"], "CREATED")
            self.assertNotIn("keep-sentinel", target.read_text(encoding="utf-8"))

    def test_init_rejects_invalid_ids_and_unsafe_titles(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = pathlib.Path(tmp)
            for bad_id in ("BAD-001", "EPIC-12", "../EPIC-001", "FEAT-001", ""):
                with self.assertRaises(sdd_portfolio.PortfolioError):
                    sdd_portfolio.init_epic_doc(repo, bad_id, "Valid Title")
            for bad_title in ("", "   ", "!!!"):
                with self.assertRaises(sdd_portfolio.PortfolioError):
                    sdd_portfolio.init_epic_doc(repo, "EPIC-002", bad_title)
            self.assertNotEqual(_run_cli("portfolio", "init", "--repo-root", str(repo), "--id", "INVALID-1", "--title", "Bad").returncode, 0)

    def test_rejects_symlinks_or_junctions_on_repo_root_and_epics_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = pathlib.Path(tmp)
            real_repo, linked_repo = base / "real_repo", base / "linked_repo"
            real_repo.mkdir()
            _create_dir_link(real_repo, linked_repo)
            self.assertNotEqual(_run_cli("portfolio", "init", "--repo-root", str(linked_repo), "--id", "EPIC-001", "--title", "Core Billing").returncode, 0)
            with self.assertRaises(sdd_portfolio.PortfolioError):
                sdd_portfolio.analyze_portfolio(linked_repo)

            outside_epics = base / "outside_epics"
            outside_epics.mkdir()
            (real_repo / "specs").mkdir()
            _create_dir_link(outside_epics, real_repo / "specs" / "epics")
            self.assertNotEqual(_run_cli("portfolio", "init", "--repo-root", str(real_repo), "--id", "EPIC-001", "--title", "Core Billing").returncode, 0)
            self.assertEqual(sdd_ci.check_portfolio(real_repo).status, "FAIL")


class TestPortfolioRollupAndMetricsCA1702(unittest.TestCase):
    """CA-1702: Epic rollup (`progress_pct`, `done_features`, `ready_features`), MoSCoW, and RICE."""

    def test_rollup_moscow_rice_40_and_ready_features_crossing_backlog(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = pathlib.Path(tmp)
            _write(repo / "specs" / "BACKLOG.md", "| ID | Título | Estado |\n| :--- | :--- | :--- |\n| FEAT-001 | Invoice Core | Done |\n| FEAT-002 | Payment Gateway | In Progress |\n| FEAT-003 | Dunning Automation | Backlog |\n")
            _write(
                repo / "specs" / "epics" / "EPIC-001-core-billing.md",
                _epic_md("EPIC-001", """
                    epic_id: "EPIC-001"
                    title: "Core Billing"
                    status: "Active"
                    priority: "must"
                    features:
                      - id: "FEAT-001"
                        title: "Invoice Core"
                        priority: "must"
                        depends_on: []
                      - id: "FEAT-002"
                        title: "Payment Gateway"
                        priority: "MUST"
                        depends_on: ["FEAT-001"]
                      - id: "FEAT-003"
                        title: "Dunning Automation"
                        priority: "should"
                        depends_on: ["FEAT-002"]
                        rice:
                          reach: 100
                          impact: 2
                          confidence: 0.8
                          effort: 4
                """, title="Core Billing"),
            )
            res = _run_cli("portfolio", "status", "--repo-root", str(repo), "--format", "json")
            self.assertEqual(res.returncode, 0, res.stderr or res.stdout)
            data = json.loads(res.stdout)
            self.assertEqual((data["status"], data["has_portfolio_data"], len(data["epics"])), ("PASS", True, 1))
            epic = data["epics"][0]
            self.assertEqual((epic["priority"], epic["total_features"], epic["done_features"], epic["in_progress_features"], epic["blocked_features"], epic["progress_pct"]), ("Must", 3, 1, 1, 1, 33.3))
            self.assertEqual(epic["ready_features"], ["FEAT-002"])
            feats = {f["feature_id"]: f for f in data["features"]}
            self.assertEqual((feats["FEAT-002"]["ready"], feats["FEAT-002"]["blocked_by"]), (True, []))
            self.assertEqual((feats["FEAT-003"]["priority"], feats["FEAT-003"]["ready"], feats["FEAT-003"]["blocked_by"], feats["FEAT-003"]["rice_score"]), ("Should", False, ["FEAT-002"], 40.0))

            filtered = _run_cli("portfolio", "status", "--repo-root", str(repo), "--epic", "EPIC-001", "--format", "json")
            self.assertEqual((filtered.returncode, len(json.loads(filtered.stdout)["features"])), (0, 3))

    def test_backlog_columns_and_status_precedence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = pathlib.Path(tmp)
            _write(
                repo / "specs" / "BACKLOG.md",
                "| ID | Título | Estado | Épica | Prioridad | Depende de | RICE |\n| :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n"
                "| FEAT-010 | Auth | Done | EPIC-010 | must | - | 50/2/1/2 |\n"
                "| FEAT-011 | Audit | Backlog | EPIC-010 | could | FEAT-010 | reach=100, impact=2, confidence=0.8, effort=4 |\n",
            )
            report = sdd_portfolio.analyze_portfolio(repo)
            self.assertEqual((report.status, report.epics[0].epic_id, report.epics[0].progress_pct, report.epics[0].ready_features), ("PASS", "EPIC-010", 50.0, ("FEAT-011",)))
            by_id = {f.feature_id: f for f in report.features}
            self.assertEqual((by_id["FEAT-010"].priority, by_id["FEAT-010"].rice.score), ("Must", 50.0))  # type: ignore[union-attr]
            self.assertEqual((by_id["FEAT-011"].priority, by_id["FEAT-011"].rice.score), ("Could", 40.0))  # type: ignore[union-attr]


class TestPortfolioValidationCA1703(unittest.TestCase):
    """CA-1703: Fail-closed cycle, unknown dependency, invalid RICE, and priority inversion detection."""

    def test_cycle_detected_returns_nonzero_and_finding(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = pathlib.Path(tmp)
            _write(repo / "specs" / "epics" / "EPIC-001-cycle.md", _epic_md("EPIC-001", """
                epic_id: "EPIC-001"
                title: "Cycle"
                status: "Active"
                priority: "Must"
                features:
                  - id: "FEAT-010"
                    priority: "Must"
                    depends_on: ["FEAT-011"]
                  - id: "FEAT-011"
                    priority: "Must"
                    depends_on: ["FEAT-010"]
            """))
            res = _run_cli("portfolio", "validate", "--repo-root", str(repo), "--format", "json")
            self.assertNotEqual(res.returncode, 0)
            data = json.loads(res.stdout)
            codes = {f["code"]: f for f in data["findings"]}
            self.assertEqual((data["status"], codes["CYCLE_DETECTED"]["severity"]), ("FAIL", "error"))
            self.assertIn("FEAT-010", codes["CYCLE_DETECTED"]["detail"])
            self.assertIn("FEAT-011", codes["CYCLE_DETECTED"]["detail"])

    def test_unknown_dependency_returns_nonzero_and_finding(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = pathlib.Path(tmp)
            _write(repo / "specs" / "epics" / "EPIC-001-orphan-dep.md", _epic_md("EPIC-001", """
                epic_id: "EPIC-001"
                title: "Orphan Dep"
                status: "Active"
                priority: "Must"
                features:
                  - id: "FEAT-010"
                    priority: "Must"
                    depends_on: ["FEAT-999"]
            """))
            res = _run_cli("portfolio", "validate", "--repo-root", str(repo), "--format", "json")
            self.assertNotEqual(res.returncode, 0)
            data = json.loads(res.stdout)
            self.assertEqual(data["status"], "FAIL")
            self.assertIn("UNKNOWN_DEPENDENCY", {f["code"] for f in data["findings"]})

    def test_invalid_rice_effort_zero_or_negative_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = pathlib.Path(tmp)
            _write(repo / "specs" / "epics" / "EPIC-001-bad-rice.md", _epic_md("EPIC-001", """
                epic_id: "EPIC-001"
                title: "Bad RICE"
                status: "Active"
                priority: "Must"
                features:
                  - id: "FEAT-010"
                    priority: "Must"
                    rice:
                      reach: 100
                      impact: 2
                      confidence: 0.8
                      effort: 0
                  - id: "FEAT-011"
                    priority: "Should"
                    rice:
                      reach: -5
                      impact: 2
                      confidence: 0.8
                      effort: 2
            """))
            res = _run_cli("portfolio", "validate", "--repo-root", str(repo), "--format", "json")
            self.assertNotEqual(res.returncode, 0)
            data = json.loads(res.stdout)
            rice_findings = [f for f in data["findings"] if f["code"] == "INVALID_RICE"]
            self.assertEqual((data["status"], len(rice_findings)), ("FAIL", 2))
            self.assertTrue(all(f["severity"] == "error" for f in rice_findings))

    def test_priority_inversion_must_depends_on_wont_emits_warning(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = pathlib.Path(tmp)
            _write(repo / "specs" / "BACKLOG.md", "| ID | Título | Estado |\n| :--- | :--- | :--- |\n| FEAT-001 | Nice | Backlog |\n| FEAT-002 | Core | Backlog |\n")
            _write(repo / "specs" / "epics" / "EPIC-001-prio.md", _epic_md("EPIC-001", """
                epic_id: "EPIC-001"
                title: "Priority Check"
                status: "Active"
                priority: "Must"
                features:
                  - id: "FEAT-001"
                    priority: "Wont"
                    depends_on: []
                  - id: "FEAT-002"
                    priority: "Must"
                    depends_on: ["FEAT-001"]
            """))
            res = _run_cli("portfolio", "validate", "--repo-root", str(repo), "--format", "json")
            self.assertEqual(res.returncode, 0, res.stderr or res.stdout)
            data = json.loads(res.stdout)
            inv = [f for f in data["findings"] if f["code"] == "PRIORITY_INVERSION"]
            self.assertEqual((data["status"], len(inv), inv[0]["severity"], inv[0]["subject"]), ("PASS", 1, "warning", "FEAT-002"))

    def test_additional_schema_and_yaml_fail_closed_checks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = pathlib.Path(tmp)
            _write(repo / "specs" / "epics" / "EPIC-001-a.md", _epic_md("EPIC-001", """
                epic_id: "EPIC-001"
                title: "One"
                status: "Active"
                priority: "Urgent"
                features:
                  - id: "FEAT-001"
                    status: "Done"
                    priority: "Must"
            """))
            _write(repo / "specs" / "epics" / "EPIC-002-b.md", _epic_md("EPIC-002", """
                epic_id: "EPIC-002"
                title: "Two"
                status: "Active"
                priority: "Should"
                features:
                  - id: "FEAT-001"
                    priority: "Should"
            """))
            report = sdd_portfolio.analyze_portfolio(repo)
            self.assertEqual(report.status, "FAIL")
            self.assertTrue({"INVALID_PRIORITY", "ORPHAN_FEATURE_REF", "DUPLICATE_FEATURE_EPIC"}.issubset({f.code for f in report.findings}))

        with tempfile.TemporaryDirectory() as tmp:
            bad_repo = pathlib.Path(tmp)
            _write(bad_repo / "specs" / "epics" / "EPIC-001-tab.md", '# Bad\n\n```yaml sdd:epic\nepic_id: "EPIC-001"\n\tpriority: "Must"\n```\n')
            with self.assertRaises(sdd_portfolio.PortfolioError):
                sdd_portfolio.analyze_portfolio(bad_repo)


class TestPortfolioCliCiAndBudgetCA1704(unittest.TestCase):
    """CA-1704: CLI `graph`, `sdd_ci.check_portfolio`, `.agents/` budget < 25k tokens, and <= 500L."""

    def test_cli_portfolio_graph_waves_and_critical_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = pathlib.Path(tmp)
            _write(repo / "specs" / "BACKLOG.md", "| ID | Título | Estado |\n| :--- | :--- | :--- |\n| FEAT-001 | Base | Done |\n| FEAT-002 | Mid | In Progress |\n| FEAT-003 | Top | Backlog |\n")
            _write(repo / "specs" / "epics" / "EPIC-001-graph.md", _epic_md("EPIC-001", """
                epic_id: "EPIC-001"
                title: "Graph"
                status: "Active"
                priority: "Must"
                features:
                  - id: "FEAT-001"
                    priority: "Must"
                    depends_on: []
                  - id: "FEAT-002"
                    priority: "Must"
                    depends_on: ["FEAT-001"]
                  - id: "FEAT-003"
                    priority: "Should"
                    depends_on: ["FEAT-002"]
            """))
            res = _run_cli("portfolio", "graph", "--repo-root", str(repo), "--format", "json")
            self.assertEqual(res.returncode, 0, res.stderr or res.stdout)
            data = json.loads(res.stdout)
            self.assertEqual(data["waves"], [["FEAT-001"], ["FEAT-002"], ["FEAT-003"]])
            self.assertEqual(data["critical_path"], ["FEAT-002", "FEAT-003"])

            _write(repo / "specs" / "BACKLOG.md", "| ID | Título | Estado |\n| :--- | :--- | :--- |\n| FEAT-001 | Base | Backlog |\n| FEAT-002 | Mid | Backlog |\n| FEAT-003 | Top | Backlog |\n")
            res_all = _run_cli("portfolio", "graph", "--repo-root", str(repo), "--format", "json")
            self.assertEqual((res_all.returncode, json.loads(res_all.stdout)["critical_path"]), (0, ["FEAT-001", "FEAT-002", "FEAT-003"]))

    def test_cli_dispatch_map_and_help_expose_portfolio(self) -> None:
        self.assertEqual(sdd_cli.DISPATCH_MAP["portfolio"].resolve(), (REPO_ROOT / "scripts" / "sdd_portfolio.py").resolve())
        help_res = _run_cli("--help")
        self.assertEqual(help_res.returncode, 0)
        self.assertIn("portfolio", help_res.stdout)

    def test_ci_check_portfolio_skipped_pass_and_fail(self) -> None:
        self.assertEqual(sdd_ci.check_portfolio(REPO_ROOT).status, "SKIPPED_NO_APPLICABLE")
        with tempfile.TemporaryDirectory() as tmp:
            repo = pathlib.Path(tmp)
            _write(repo / "specs" / "BACKLOG.md", "| ID | Título | Estado |\n| :--- | :--- | :--- |\n| FEAT-001 | Init | Backlog |\n")
            self.assertEqual(sdd_ci.check_portfolio(repo).status, "SKIPPED_NO_APPLICABLE")
            _write(repo / "specs" / "epics" / "EPIC-001-ok.md", _epic_md("EPIC-001", 'epic_id: "EPIC-001"\ntitle: "Ok"\nstatus: "Active"\npriority: "Must"\nfeatures:\n  - id: "FEAT-001"\n    priority: "Must"\n    depends_on: []'))
            self.assertEqual(sdd_ci.check_portfolio(repo).status, "PASS")
            _write(repo / "specs" / "epics" / "EPIC-002-bad.md", _epic_md("EPIC-002", 'epic_id: "EPIC-002"\ntitle: "Bad"\nstatus: "Active"\npriority: "Must"\nfeatures:\n  - id: "FEAT-002"\n    priority: "Must"\n    depends_on: ["FEAT-404"]'))
            self.assertEqual(sdd_ci.check_portfolio(repo).status, "FAIL")

    def test_python_line_ceiling_and_agents_token_budget(self) -> None:
        self.assertTrue(TEMPLATE_PATH.is_file(), "Missing specs/templates/09-epic-roadmap.template.md")
        for folder in ("scripts", ".agents/scripts", "tests"):
            for py_file in sorted((REPO_ROOT / folder).rglob("*.py")):
                if "__pycache__" not in py_file.parts:
                    lines = len(py_file.read_text(encoding="utf-8").splitlines())
                    self.assertLessEqual(lines, 500, f"{py_file.relative_to(REPO_ROOT).as_posix()} has {lines} lines (> 500)")

        total_chars = sum(
            len(p.read_text(encoding="utf-8", errors="ignore"))
            for p in (REPO_ROOT / ".agents").rglob("*")
            if p.is_file() and "__pycache__" not in p.parts and p.suffix in {".md", ".json", ".yaml", ".yml"}
        )
        self.assertLess(total_chars // 4, 25000, f".agents/ estimated tokens {total_chars // 4} >= 25000")


if __name__ == "__main__":
    unittest.main()
