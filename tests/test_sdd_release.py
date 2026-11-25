#!/usr/bin/env python3
"""Offline integration & fail-closed QA suite for FWK-014 (Gate 6 & CHANGELOG)."""

from __future__ import annotations

import copy
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
for _p in (str(ROOT_DIR), str(ROOT_DIR / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import scripts.sdd_gate_seal as sdd_gate_seal  # noqa: E402
import scripts.sdd_git as sdd_git  # noqa: E402
import scripts.sdd_release as sdd_release  # noqa: E402


def _git(repo: pathlib.Path, *args: str) -> str:
    res = subprocess.run(["git", *args], cwd=str(repo), capture_output=True, text=True, check=True)
    return res.stdout.strip()


def _write(path: pathlib.Path, content: str) -> pathlib.Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _init_sdd_repo(base: pathlib.Path, *, prev_tag: str | None = "v1.1.0") -> pathlib.Path:
    """Create a clean offline SDD git repo that passes `sdd_ci.run_ci_verify` in project mode."""
    repo = base / "repo"
    repo.mkdir(parents=True, exist_ok=True)
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "qa-test@example.com")
    _git(repo, "config", "user.name", "QA Test")

    _write(repo / "README.md", "# Demo SDD Project\n")
    _write(repo / "scripts" / "ok.py", "print('ok')\n")
    _write(
        repo / ".agents" / "hooks.json",
        json.dumps({"hooks": {"PreToolUse": [{"hooks": [{"command": "python scripts/ok.py"}]}]}}, indent=2) + "\n",
    )
    _write(
        repo / ".agents" / "active_work_item.json",
        json.dumps({"active_work_item_id": None, "git": {"branch_name": "develop", "status": "IDLE"}}, indent=2) + "\n",
    )
    _write(repo / ".agents" / "ACTIVE_STATE.md", "# Active State\n- **Active Work Item:** `IDLE`\n")
    for kdoc in ("ADRS.md", "API_CATALOG.md", "DATA_MODELS.md", "SYSTEM_TOPOLOGY.md"):
        _write(repo / "docs" / "knowledge" / kdoc, f"# {kdoc}\nDocumented.\n")
    _write(repo / "docs" / "es" / "index.md", "# Documentacion\nActivo.\n")
    _write(repo / "docs" / "en" / "index.md", "# Documentation\nActive.\n")
    _write(
        repo / "docs" / "traceability" / "TRACEABILITY-MATRIX.md",
        "# Traceability\n| ID | Status |\n| :--- | :--- |\n| FEAT-001 | Done |\n",
    )
    _write(
        repo / "specs" / "BACKLOG.md",
        "# Backlog\n\n| ID | Título | Estado | RFC |\n| :--- | :--- | :--- | :--- |\n"
        "| FEAT-001 | Auth Core | Done | RFC-001 |\n"
        "| FWK-013 | CI Engine | Done | RFC-007 |\n",
    )
    _write(repo / "specs" / "features" / "FEAT-001-auth" / "01-spec.md", "# FEAT-001: Auth Core\nDone spec.\n")
    _write(repo / "specs" / "features" / "FEAT-001-auth" / "02-tech-spec.md", "# Tech Spec\nApproved.\n")
    _write(repo / "specs" / "features" / "FEAT-001-auth" / "03-tasks.md", "# Tasks\n- **T001:** Done\n")

    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "chore: initial baseline")
    if prev_tag:
        _git(repo, "tag", "-a", prev_tag, "-m", f"Release {prev_tag}")
    _git(repo, "checkout", "-b", "develop", "main")
    return repo


def _approved_gate6_doc(version: str = "1.2.0", *, with_seal: bool = True) -> str:
    body = (
        f"# Release Readiness: REL-v{version} (v{version})\n\n"
        f"- **ID:** `REL-v{version}`\n- **Versión / Tag:** `v{version}`\n- **Estado:** `Approved`\n\n"
        "## 1. Alcance y Work Items Incluidos\n- `FEAT-001` (features, `done`): Auth Core\n\n"
        "## 2. Riesgos y Migraciones\n- Sin migraciones destructivas.\n\n"
        "## 3. Plan de Despliegue y Rollback\n"
        "1. Publicar PR hacia `main` y verificar healthcheck.\n"
        "2. Ante fallo S1, revertir merge commit en `main` y redesplegar `v1.1.0`.\n\n"
        "## 4. Aprobación Gate 6\n"
        "- [x] **Gate 6 Approved (Human Sign-off):** Alcance, CI y rollback aprobados por PO.\n"
    )
    if not with_seal:
        return body
    digest = sdd_gate_seal.compute_gate_doc_sha256(body)
    return body + f"\n<!-- sdd:gate-seal gate=6 sha256={digest} -->\n"


class TestSDDRelease(unittest.TestCase):
    """Covers CA-1401..CA-1404, CLI E2E, .agents/ budget, and 500-line ceiling."""

    def test_ca1401_prepare_release_no_autoapprove_and_force_guard(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = _init_sdd_repo(pathlib.Path(tmp))
            (_write(repo / "app.py", "VERSION = '1.2.0'\n"))
            _git(repo, "add", "app.py")
            _git(repo, "commit", "-m", "feat: deliver FEAT-001 and FWK-013")

            rc = sdd_release.main(["prepare", "--version", "1.2.0", "--date", "2026-11-17", "--repo-root", str(repo)])
            self.assertEqual(rc, 0)

            dossier = repo / "specs" / "releases" / "REL-v1.2.0.md"
            self.assertTrue(dossier.is_file())
            dossier_text = dossier.read_text(encoding="utf-8")
            self.assertIn("- [ ] **Gate 6 Approved (Human Sign-off):**", dossier_text)
            self.assertNotRegex(dossier_text, r"\[[xX]\]\s*(?:\*\*)?Gate\s+6\s+Approved")
            self.assertIn("FEAT-001", dossier_text)
            self.assertIn("FWK-013", dossier_text)

            cl_text = (repo / "CHANGELOG.md").read_text(encoding="utf-8")
            self.assertIn("## [v1.2.0] - 2026-11-17", cl_text)
            self.assertIn("**FEAT-001**: Auth Core (RFC-001)", cl_text)

            # Second run without --force must fail with code 1 and not overwrite
            dossier.write_text(dossier_text + "\n<!-- manual note -->\n", encoding="utf-8")
            before_bytes = dossier.read_bytes()
            rc_dup = sdd_release.main(["prepare", "--version", "1.2.0", "--date", "2026-11-17", "--repo-root", str(repo)])
            self.assertEqual(rc_dup, 1)
            self.assertEqual(dossier.read_bytes(), before_bytes)

            # With --force, regeneration succeeds and resets unchecked Gate 6
            rc_force = sdd_release.main(
                ["prepare", "--version", "1.2.0", "--date", "2026-11-17", "--force", "--repo-root", str(repo)]
            )
            self.assertEqual(rc_force, 0)
            self.assertNotIn("<!-- manual note -->", dossier.read_text(encoding="utf-8"))

            # Official template: replaces {{RELEASE_ITEMS}} and vA.B.C, keeps [ ] Gate 6, and parses clean after sign-off
            official_tmpl = (ROOT_DIR / "specs" / "templates" / "08-release-readiness.template.md").read_text(encoding="utf-8")
            _write(repo / "specs" / "templates" / "08-release-readiness.template.md", official_tmpl)
            rc_tmpl = sdd_release.main(
                ["prepare", "--version", "1.2.0", "--date", "2026-11-17", "--force", "--repo-root", str(repo)]
            )
            self.assertEqual(rc_tmpl, 0)
            tmpl_out = dossier.read_text(encoding="utf-8")
            self.assertNotIn("{{RELEASE_ITEMS}}", tmpl_out)
            self.assertNotIn("vA.B.C", tmpl_out)
            self.assertIn("v1.1.0", tmpl_out)
            self.assertIn("FEAT-001", tmpl_out)
            self.assertIn("- [ ] **Gate 6 Approved (Human Sign-off):**", tmpl_out)
            signed_tmpl_out = tmpl_out.replace("- [ ] **Gate 6 Approved (Human Sign-off):**", "- [x] **Gate 6 Approved (Human Sign-off):**", 1)
            ok_tmpl, errs_tmpl = sdd_release.parse_gate6_approval(signed_tmpl_out)
            self.assertTrue(ok_tmpl, errs_tmpl)

    def test_ca1402_changelog_crossref_noise_filter_and_byte_idempotency(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = _init_sdd_repo(pathlib.Path(tmp))
            _write(
                repo / "specs" / "BACKLOG.md",
                "# Backlog\n\n| ID | Estado | RFC |\n| :--- | :--- | :--- |\n"
                "| FEAT-001 | Done | RFC-001 |\n"
                "| CR-003 | Done | RFC-002 |\n"
                "| BUG-007 | Done | - |\n",
            )
            _write(repo / "specs" / "features" / "FEAT-001-auth" / "01-spec.md", "# FEAT-001: Auth Core\nDone.\n")
            _write(repo / "specs" / "changes" / "CR-003-rotation" / "01-spec.md", "# CR-003: Token Rotation\nDone.\n")
            _write(repo / "specs" / "bugs" / "BUG-007-crash" / "01-bug-report.md", "# BUG-007: Crash on empty token\nFixed.\n")
            _write(
                repo / "CHANGELOG.md",
                "# Changelog\n\n## [v1.1.0] - 2026-10-01\n\n### Features\n\n- **FEAT-000**: Legacy baseline\n",
            )
            _git(repo, "add", ".")
            _git(repo, "commit", "-m", "feat: implement FEAT-001 and CR-003")
            _write(repo / "fix.py", "ok = True\n")
            _git(repo, "add", "fix.py")
            _git(repo, "commit", "-m", "fix: resolve BUG-007")
            for idx, msg in enumerate(("chore: format", "ci: tweak pipeline", "style: spaces", "chore(release): v1.1.0")):
                _write(repo / f"n{idx}.txt", f"{idx}\n")
                _git(repo, "add", f"n{idx}.txt")
                _git(repo, "commit", "-m", msg)

            # Real merge commit should also be ignored by --no-merges + noise filter
            _git(repo, "checkout", "-b", "feat/noise-merge", "develop")
            _write(repo / "m.txt", "merge\n")
            _git(repo, "add", "m.txt")
            _git(repo, "commit", "-m", "chore: merge payload")
            _git(repo, "checkout", "develop")
            _git(repo, "merge", "--no-ff", "feat/noise-merge", "-m", "Merge branch 'feat/noise-merge'")

            rc1 = sdd_release.main(["changelog", "--version", "1.2.0", "--date", "2026-11-17", "--repo-root", str(repo)])
            self.assertEqual(rc1, 0)
            cl_path = repo / "CHANGELOG.md"
            bytes_run1 = cl_path.read_bytes()

            rc2 = sdd_release.main(["changelog", "--version", "1.2.0", "--date", "2026-11-17", "--repo-root", str(repo)])
            self.assertEqual(rc2, 0)
            bytes_run2 = cl_path.read_bytes()
            self.assertEqual(bytes_run1, bytes_run2)

            text = cl_path.read_text(encoding="utf-8")
            self.assertIn("## [v1.2.0] - 2026-11-17", text)
            self.assertIn("### Features\n- **FEAT-001**: Auth Core (RFC-001)", text)
            self.assertIn("### Changes\n- **CR-003**: Token Rotation (RFC-002)", text)
            self.assertIn("### Fixes & Hotfixes\n- **BUG-007**: Crash on empty token", text)
            for noise in ("chore: format", "ci: tweak", "style: spaces", "chore(release)", "Merge branch"):
                self.assertNotIn(noise, text)
            self.assertIn("## [v1.1.0] - 2026-10-01\n\n### Features\n\n- **FEAT-000**: Legacy baseline", text)

            # Conventional Commits fallback when no SDD IDs appear in a fresh range
            _git(repo, "tag", "-a", "v1.2.0", "-m", "v1.2.0")
            _write(repo / "perf.py", "fast = 1\n")
            _git(repo, "add", "perf.py")
            _git(repo, "commit", "-m", "feat(core): add streaming parser")
            _write(repo / "junk.py", "j = 1\n")
            _git(repo, "add", "junk.py")
            _git(repo, "commit", "-m", "chore: bump dev tool")
            _, cc_items = sdd_release.collect_release_items(repo, since_tag="v1.2.0", current_tag="v1.3.0")
            self.assertEqual(len(cc_items), 1)
            self.assertEqual((cc_items[0].category, cc_items[0].title), ("features", "core: add streaming parser"))

    def test_ca1403_parse_gate6_and_preflight_fail_closed(self) -> None:
        # 1. Spoofing, placeholders, empty rollback, and SHA-256 seal integrity
        spoof_html = "# REL-v1.2.0\n## Rollback\nRevert tag v1.1.0 cleanly.\n<!-- - [x] Gate 6 Approved -->\n"
        spoof_fence = "# REL-v1.2.0\n## Rollback\nRevert tag v1.1.0 cleanly.\n```md\n- [x] Gate 6 Approved\n```\n"
        placeholder_rb = "# REL-v1.2.0\n## Rollback\n- <Procedimiento pendiente>\n- [x] Gate 6 Approved\n"
        empty_rb = "# REL-v1.2.0\n## Rollback\n\n## Approval\n- [x] **Gate 6 Approved (Human Sign-off):** Ok.\n"
        bad_seal = _approved_gate6_doc("1.2.0", with_seal=False) + "\n<!-- sdd:gate-seal gate=6 sha256=" + ("0" * 64) + " -->\n"
        invalid_seal = _approved_gate6_doc("1.2.0", with_seal=False) + "\n<!-- sdd:gate-seal gate=6 sha256=bad -->\n"

        for sample in (spoof_html, spoof_fence, placeholder_rb, empty_rb, bad_seal, invalid_seal):
            ok, errs = sdd_release.parse_gate6_approval(sample)
            self.assertFalse(ok, f"Should fail closed on: {sample!r}")
            self.assertTrue(errs)

        ok_valid, errs_valid = sdd_release.parse_gate6_approval(_approved_gate6_doc("1.2.0", with_seal=True))
        self.assertTrue(ok_valid, errs_valid)

        # 2. run_release_preflight fail-closed checks on repo state
        with tempfile.TemporaryDirectory() as tmp:
            repo = _init_sdd_repo(pathlib.Path(tmp))
            _write(repo / "specs" / "releases" / "REL-v1.2.0.md", spoof_html)
            _write(repo / "CHANGELOG.md", "# Changelog\n\n## [v1.1.0] - 2026-10-01\n\n- old\n")
            _git(repo, "add", ".")
            _git(repo, "commit", "-m", "chore: prep invalid release")

            rep_spoof = sdd_release.run_release_preflight(repo, "1.2.0", stage="finish", run_ci=False)
            self.assertEqual(rep_spoof.overall_status, "FAIL")
            status_map = {c.name: c.status for c in rep_spoof.checks}
            self.assertEqual(status_map["gate6_approval"], "FAIL")
            self.assertEqual(status_map["changelog"], "FAIL")

            # Blocking statuses in BACKLOG.md and active_work_item.json
            _write(repo / "specs" / "releases" / "REL-v1.2.0.md", _approved_gate6_doc("1.2.0"))
            _write(repo / "CHANGELOG.md", "# Changelog\n\n## [v1.2.0] - 2026-11-17\n\n- **FEAT-001**: Auth Core\n")
            _write(
                repo / "specs" / "BACKLOG.md",
                "# Backlog\n\n| ID | Título | Estado |\n| :--- | :--- | :--- |\n| FEAT-001 | Auth | In Progress |\n",
            )
            _write(repo / ".agents" / "active_work_item.json", json.dumps({"active_work_item_id": "FEAT-099"}) + "\n")
            _git(repo, "add", ".")
            _git(repo, "commit", "-m", "chore: open item state")

            rep_open = sdd_release.run_release_preflight(repo, "1.2.0", stage="finish", run_ci=False)
            self.assertEqual(rep_open.overall_status, "FAIL")
            open_chk = next(c for c in rep_open.checks if c.name == "open_work_items")
            self.assertEqual(open_chk.status, "FAIL")
            self.assertIn("FEAT-099", open_chk.detail)
            self.assertIn("FEAT-001", open_chk.detail)

            # Clean state with active_work_item_id=REL-v1.2.0 and valid Gate 6 passes
            _write(
                repo / "specs" / "BACKLOG.md",
                "# Backlog\n\n| ID | Título | Estado |\n| :--- | :--- | :--- |\n| FEAT-001 | Auth | Done |\n",
            )
            _write(repo / ".agents" / "active_work_item.json", json.dumps({"active_work_item_id": "REL-v1.2.0"}) + "\n")
            _git(repo, "add", ".")
            _git(repo, "commit", "-m", "chore: clear open items")

            rep_ok = sdd_release.run_release_preflight(repo, "1.2.0", stage="finish", run_ci=True)
            self.assertEqual(rep_ok.overall_status, "PASS", [c for c in rep_ok.checks if c.status == "FAIL"])

    def test_ca1404_real_sdd_git_release_start_and_finish_integration(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = _init_sdd_repo(pathlib.Path(tmp))
            gov = copy.deepcopy(sdd_git.DEFAULT_GOVERNANCE)
            main_sha = _git(repo, "rev-parse", "main")

            with mock.patch.object(sdd_git, "ROOT_DIR", repo), mock.patch.object(
                sdd_git.GitProviderAdapter, "create_pr", return_value="https://github.com/acme/demo/pull/77"
            ) as mock_pr:
                # 1. Fail-closed release-start when active_work_item.json is non-IDLE
                _write(repo / ".agents" / "active_work_item.json", json.dumps({"active_work_item_id": "FEAT-099"}) + "\n")
                _git(repo, "add", ".agents")
                _git(repo, "commit", "-m", "chore: active feat")
                args_start = sdd_git.build_parser().parse_args(["release-start", "--version", "1.2.0"])
                self.assertEqual(sdd_git.cmd_release_start(args_start, gov), 1)
                self.assertFalse(sdd_git.GitRunner.branch_exists("release/v1.2.0", cwd=repo))
                mock_pr.assert_not_called()

                # 2. Clear active work item -> release-start passes and creates release/v1.2.0
                _write(repo / ".agents" / "active_work_item.json", json.dumps({"active_work_item_id": "IDLE"}) + "\n")
                _git(repo, "add", ".agents")
                _git(repo, "commit", "-m", "chore: reset idle")
                self.assertEqual(sdd_git.cmd_release_start(args_start, gov), 0)
                self.assertTrue(sdd_git.GitRunner.branch_exists("release/v1.2.0", cwd=repo))

                # 3. Fail-closed release-finish before Gate 6 / CHANGELOG (commit state on develop first)
                _git(repo, "add", ".agents")
                _git(repo, "commit", "-m", "chore: record release staging")
                args_finish = sdd_git.build_parser().parse_args(["release-finish", "--version", "1.2.0"])
                self.assertEqual(sdd_git.cmd_release_finish(args_finish, gov), 1)
                mock_pr.assert_not_called()

                # 4. Prepare & approve Gate 6 + CHANGELOG ONLY on release/v1.2.0, then run release-finish from develop
                _git(repo, "checkout", "release/v1.2.0")
                self.assertEqual(sdd_release.prepare_release(repo, "1.2.0", release_date="2026-11-17")["release_id"], "REL-v1.2.0")
                _write(repo / "specs" / "releases" / "REL-v1.2.0.md", _approved_gate6_doc("1.2.0", with_seal=True))
                _git(repo, "add", "specs/releases/REL-v1.2.0.md", "CHANGELOG.md")
                _git(repo, "commit", "-m", "chore(release): approve Gate 6 for v1.2.0")
                _git(repo, "checkout", "develop")
                self.assertFalse((repo / "specs" / "releases" / "REL-v1.2.0.md").exists())

                self.assertEqual(sdd_git.cmd_release_finish(args_finish, gov), 0)
                mock_pr.assert_called_once_with(
                    "github",
                    "release/v1.2.0",
                    "main",
                    "chore(release): release v1.2.0 into main",
                    "Release v1.2.0 (release/v1.2.0 -> main)",
                )
                self.assertEqual(_git(repo, "rev-parse", "main"), main_sha)

    def test_e2e_cli_verify_json_and_budget_and_modularity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = _init_sdd_repo(pathlib.Path(tmp))
            _write(repo / "specs" / "releases" / "REL-v1.2.0.md", _approved_gate6_doc("1.2.0"))
            _write(repo / "CHANGELOG.md", "# Changelog\n\n## [v1.2.0] - 2026-11-17\n\n- **FEAT-001**: Auth Core\n")
            _git(repo, "add", ".")
            _git(repo, "commit", "-m", "chore(release): approved v1.2.0")

            cli_cmd = [
                sys.executable, str(ROOT_DIR / "scripts" / "sdd_cli.py"),
                "release", "verify", "--version", "1.2.0", "--stage", "finish", "--format", "json", "--repo-root", str(repo),
            ]
            ok_proc = subprocess.run(cli_cmd, cwd=str(ROOT_DIR), capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(ok_proc.returncode, 0, ok_proc.stdout + ok_proc.stderr)
            ok_json = json.loads(ok_proc.stdout)
            self.assertEqual(ok_json["overall_status"], "PASS")
            self.assertEqual(ok_json["release_id"], "REL-v1.2.0")

            # Remove CHANGELOG.md -> CLI verify --format json fails closed with exit 1
            (repo / "CHANGELOG.md").unlink()
            _git(repo, "add", "-u")
            _git(repo, "commit", "-m", "test: drop changelog")
            fail_proc = subprocess.run(cli_cmd, cwd=str(ROOT_DIR), capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(fail_proc.returncode, 1)
            fail_json = json.loads(fail_proc.stdout)
            self.assertEqual(fail_json["overall_status"], "FAIL")
            self.assertEqual(next(c for c in fail_json["checks"] if c["name"] == "changelog")["status"], "FAIL")

        # .agents/ active prompt context budget (< 100 KB / < 25k tokens) & compact workflow
        md_bytes = sum(p.stat().st_size for p in (ROOT_DIR / ".agents").rglob("*.md") if p.is_file() and "references" not in p.parts)
        self.assertLess(md_bytes, 100_000, f".agents markdown context exceeded 100KB ({md_bytes}B)")
        self.assertLess(md_bytes / 4.0, 25_000, f".agents markdown context exceeded 25k est tokens ({md_bytes / 4.0})")
        wf_lines = (ROOT_DIR / ".agents" / "workflows" / "gate6-release.md").read_text(encoding="utf-8").splitlines()
        self.assertLessEqual(len(wf_lines), 25)

        # Strict <= 500-line ceiling on all FWK-014 touched/created Python modules
        for rel in (
            "scripts/sdd_release.py",
            "scripts/sdd_cli.py",
            "scripts/sdd_git.py",
            "tests/test_sdd_release.py",
            "tests/test_sdd_git_concurrency.py",
        ):
            line_count = len((ROOT_DIR / rel).read_text(encoding="utf-8").splitlines())
            self.assertLessEqual(line_count, 500, f"{rel} exceeded 500 lines ({line_count})")


if __name__ == "__main__":
    unittest.main()
