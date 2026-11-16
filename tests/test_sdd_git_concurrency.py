#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Concurrency, isolation, dynamic git resolution, ACTIVE_STATE sync & modularity tests (FWK-008)."""

from __future__ import annotations

import concurrent.futures
import copy
import json
import os
import pathlib
import shutil
import socket
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "scripts"))

import scripts.sdd_git as sdd_git
import scripts.sdd_git_state as sdd_git_state
import scripts.sdd_git_worktree as sdd_git_worktree


def _git(repo: pathlib.Path, *args: str) -> str:
    res = subprocess.run(["git", *args], cwd=str(repo), capture_output=True, text=True, check=True)
    return res.stdout.strip()


def _init_temp_repo(base: pathlib.Path, *, initial_branch: str = "main", with_develop: bool = False, with_agents: bool = True) -> pathlib.Path:
    repo = base / "repo"
    repo.mkdir(parents=True, exist_ok=True)
    _git(repo, "init", "-b", initial_branch)
    _git(repo, "config", "user.email", "sdd-test@example.com")
    _git(repo, "config", "user.name", "SDD Test")
    (repo / "README.md").write_text("# Test Repo\n", encoding="utf-8")
    if with_agents:
        agents = repo / ".agents"
        agents.mkdir(parents=True, exist_ok=True)
        (agents / "active_work_item.json").write_text(
            json.dumps({
                "active_work_item_id": None,
                "gate_0_approved": False, "gate_1_approved": False,
                "gate_2_approved": False, "gate_3_approved": False,
                "approved_by_human": False,
                "git": {"branch_name": initial_branch, "status": "IDLE"},
            }, indent=2) + "\n",
            encoding="utf-8",
        )
        (agents / "ACTIVE_STATE.md").write_text(
            "# SDD Starter — Active Session Pointer (Managed by @orchestrator)\n"
            "- **Timestamp:** 2026-01-01 00:00 UTC\n"
            "- **Active Work Item:** `IDLE (No Active Work Item)`\n"
            f"- **Active Branch:** `{initial_branch}`\n"
            "- **Spec Folder Path:** `N/A`\n"
            "- **Current Gate:** `IDLE`\n",
            encoding="utf-8",
        )
        feat_dir = repo / "specs" / "features" / "FEAT-010-demo"
        feat_dir.mkdir(parents=True, exist_ok=True)
        (feat_dir / "01-spec.md").write_text("# FEAT-010\n", encoding="utf-8")
        (repo / ".gitignore").write_text(".worktrees/\n.agents/worktree_states/\n.agents/.*.lock\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "chore: initial commit")
    if with_develop:
        _git(repo, "branch", "develop", initial_branch)
    return repo


class TestSDDGitConcurrencyAndHardening(unittest.TestCase):
    """Covers AUD-003, AUD-016, AUD-019, AUD-021 preservation, and AUD-025."""

    def test_load_git_governance_deepcopy_and_invalid_bool_fails_closed(self):
        gov1 = sdd_git.load_git_governance()
        gov1["branches"]["production"] = "hacked-prod"
        gov1["worktrees"]["directory"] = "hacked-wt"
        gov1["auto_merge"]["develop"] = "hacked"

        gov2 = sdd_git.load_git_governance()
        self.assertEqual(gov2["branches"]["production"], sdd_git.DEFAULT_GOVERNANCE["branches"]["production"])
        self.assertEqual(gov2["worktrees"]["directory"], sdd_git.DEFAULT_GOVERNANCE["worktrees"]["directory"])
        self.assertIs(gov2["auto_merge"]["develop"], True)
        self.assertIs(gov2["worktrees"]["enabled"], True)

        with tempfile.TemporaryDirectory() as tmp:
            bad_stack = pathlib.Path(tmp) / "STACK.md"
            bad_stack.write_text("```yaml\ngit_governance:\n  worktrees:\n    enabled: maybe\n```\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                sdd_git.load_git_governance(stack_path=bad_stack)

    def test_dynamic_base_branch_and_remote_detection_without_develop(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = pathlib.Path(tmp)
            bare = tmp_path / "remote.git"
            bare.mkdir()
            _git(bare, "init", "--bare", "-b", "trunk")

            repo = _init_temp_repo(tmp_path, initial_branch="main", with_develop=False)
            _git(repo, "remote", "add", "origin", "git@github.com:custom-org/custom-repo.git")
            gov = copy.deepcopy(sdd_git.DEFAULT_GOVERNANCE)

            self.assertEqual(sdd_git_state.get_origin_remote_url(cwd=repo), "git@github.com:custom-org/custom-repo.git")
            self.assertEqual(sdd_git_state.detect_default_base_branch(gov, cwd=repo), "main")
            self.assertEqual(sdd_git_state.get_base_branch("feat/FEAT-12", gov, cwd=repo), "main")
            self.assertEqual(sdd_git_state.get_base_branch("hotfix/BUG-55", gov, cwd=repo), "main")

            # Repo whose only branch is master (neither develop nor main exists)
            master_repo = tmp_path / "master_only"
            master_repo.mkdir()
            _git(master_repo, "init", "-b", "master")
            _git(master_repo, "config", "user.email", "sdd@example.com")
            _git(master_repo, "config", "user.name", "SDD")
            (master_repo / "a.txt").write_text("x\n", encoding="utf-8")
            _git(master_repo, "add", ".")
            _git(master_repo, "commit", "-m", "init")
            self.assertEqual(sdd_git_state.detect_default_base_branch(gov, cwd=master_repo), "master")

            # Local branch with explicit upstream tracking ref (@{u}) takes priority over fallback main
            _git(repo, "remote", "set-url", "origin", str(bare))
            _git(repo, "checkout", "-b", "trunk")
            _git(repo, "push", "-u", "origin", "trunk")
            _git(repo, "branch", "-D", "main")
            self.assertEqual(sdd_git_state.detect_default_base_branch(gov, cwd=repo), "trunk")

    def test_concurrent_worktree_creation_anagrams_and_isolated_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = _init_temp_repo(pathlib.Path(tmp), initial_branch="main", with_develop=False)
            _git(repo, "remote", "add", "origin", "https://user:token@git.example.org/org/demo.git")
            gov = copy.deepcopy(sdd_git.DEFAULT_GOVERNANCE)
            root_item_before = (repo / ".agents" / "active_work_item.json").read_text(encoding="utf-8")

            specs = ["FEAT-12", "FEAT-21", "FEAT-103", "FEAT-301"]

            def worker(spec_id: str):
                mgr = sdd_git_worktree.WorktreeManager(gov, root_dir=repo)
                branch = sdd_git_state.resolve_branch_name(spec_id, gov)
                base = sdd_git_state.get_base_branch(branch, gov, cwd=repo)
                wt_path = mgr.create(branch, base)
                ports = mgr.get_ports_for_worktree(wt_path)
                remote_url = sdd_git_state.get_origin_remote_url(cwd=wt_path)
                sdd_git_state.sync_active_state_git(
                    spec_id, branch, wt_path, "IN_PROGRESS",
                    base_branch=base, remote_url=remote_url, ports=ports, root_dir=repo,
                )
                return spec_id, wt_path, ports

            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
                results = list(pool.map(worker, specs))

            all_ports = []
            for spec_id, wt_path, ports in results:
                self.assertIsNotNone(ports)
                bp, fp = ports
                self.assertNotEqual(bp, fp)
                self.assertTrue(sdd_git_worktree.BACKEND_PORT_RANGE[0] <= bp <= sdd_git_worktree.BACKEND_PORT_RANGE[1])
                self.assertTrue(sdd_git_worktree.FRONTEND_PORT_RANGE[0] <= fp <= sdd_git_worktree.FRONTEND_PORT_RANGE[1])
                all_ports.extend([bp, fp])

                env_text = (wt_path / ".env.test").read_text(encoding="utf-8")
                self.assertIn(f"BACKEND_PORT={bp}", env_text)
                self.assertIn(f"FRONTEND_PORT={fp}", env_text)

                local_state = json.loads((wt_path / ".agents" / "active_work_item.json").read_text(encoding="utf-8"))
                self.assertEqual(local_state["active_work_item_id"], spec_id)
                self.assertEqual(local_state["git"]["backend_port"], bp)
                self.assertEqual(local_state["git"]["frontend_port"], fp)
                self.assertIs(local_state["gate_0_approved"], False)
                self.assertIs(local_state["approved_by_human"], False)

                reg_state = json.loads((repo / ".agents" / "worktree_states" / f"{wt_path.name}.json").read_text(encoding="utf-8"))
                self.assertEqual(reg_state["active_work_item_id"], spec_id)
                self.assertEqual(sdd_git_state.load_active_work_item(wt_path=wt_path, root_dir=repo)["active_work_item_id"], spec_id)

            # All backend & frontend ports across concurrent anagrams are strictly unique
            self.assertEqual(len(all_ports), len(set(all_ports)))
            # Root singleton active_work_item.json was NOT clobbered by concurrent worktrees
            self.assertEqual((repo / ".agents" / "active_work_item.json").read_text(encoding="utf-8"), root_item_before)

            root_md = (repo / ".agents" / "ACTIVE_STATE.md").read_text(encoding="utf-8")
            self.assertIn("`IDLE (No Active Work Item)`", root_md)
            for spec_id in specs:
                self.assertIn(spec_id, root_md)

    def test_port_allocator_skips_bound_loopback_sockets_and_multiprocess_races(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = _init_temp_repo(pathlib.Path(tmp), initial_branch="main", with_develop=False)
            slug_a, slug_b = "feat-FEAT-12", "feat-FEAT-21"

            # Probe candidate starting port for slug_a and intentionally occupy it on 127.0.0.1
            bp_preview, fp_preview = sdd_git_worktree.allocate_worktree_ports(slug_a, root_dir=repo)
            sdd_git_worktree.release_worktree_ports(slug_a, root_dir=repo)

            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as occupied:
                if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
                    occupied.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
                occupied.bind(("127.0.0.1", bp_preview))
                occupied.listen(1)

                bp_actual, fp_actual = sdd_git_worktree.allocate_worktree_ports(slug_a, root_dir=repo)
                self.assertNotEqual(bp_actual, bp_preview)
                self.assertTrue(sdd_git_worktree.is_port_available(bp_actual))
                self.assertTrue(sdd_git_worktree.is_port_available(fp_actual))
                self.assertEqual(fp_actual, fp_preview)

            sdd_git_worktree.release_worktree_ports(slug_a, root_dir=repo)

            # Real cross-process lock & registry contention
            py_code = (
                "import pathlib, sys; "
                f"sys.path.insert(0, {str(ROOT_DIR)!r}); "
                "from scripts.sdd_git_worktree import allocate_worktree_ports; "
                "bp, fp = allocate_worktree_ports(sys.argv[1], root_dir=pathlib.Path(sys.argv[2])); "
                "print(f'{bp},{fp}')"
            )
            p1 = subprocess.Popen([sys.executable, "-c", py_code, slug_a, str(repo)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            p2 = subprocess.Popen([sys.executable, "-c", py_code, slug_b, str(repo)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            out1, err1 = p1.communicate(timeout=20)
            out2, err2 = p2.communicate(timeout=20)
            self.assertEqual(p1.returncode, 0, err1)
            self.assertEqual(p2.returncode, 0, err2)
            ports1 = tuple(int(x) for x in out1.strip().splitlines()[-1].split(","))
            ports2 = tuple(int(x) for x in out2.strip().splitlines()[-1].split(","))
            self.assertEqual(len({*ports1, *ports2}), 4)

    def test_active_state_md_auto_sync_across_cli_lifecycle(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = _init_temp_repo(pathlib.Path(tmp), initial_branch="main", with_develop=True)
            gov = copy.deepcopy(sdd_git.DEFAULT_GOVERNANCE)
            _git(repo, "checkout", "develop")

            with mock.patch.object(sdd_git, "ROOT_DIR", repo):
                # 1. create-branch --checkout updates ACTIVE_STATE.md & active_work_item.json
                args_cb = sdd_git.build_parser().parse_args(["create-branch", "--spec", "FEAT-010", "--checkout"])
                self.assertEqual(sdd_git.cmd_create_branch(args_cb, gov), 0)
                md = (repo / ".agents" / "ACTIVE_STATE.md").read_text(encoding="utf-8")
                self.assertIn("`FEAT-010`", md)
                self.assertIn("`feat/FEAT-010`", md)
                self.assertIn("`specs/features/FEAT-010-demo`", md)

                # 2. switch-branch back to develop resets to IDLE
                args_sw = sdd_git.build_parser().parse_args(["switch-branch", "--branch", "develop"])
                self.assertEqual(sdd_git.cmd_switch_branch(args_sw, gov), 0)
                md_idle = (repo / ".agents" / "ACTIVE_STATE.md").read_text(encoding="utf-8")
                self.assertIn("`IDLE (No Active Work Item)`", md_idle)
                self.assertIn("`develop`", md_idle)
                self.assertIn("`IDLE`", md_idle)

                # 3. worktree-create + worktree-remove syncs worktrees summary cleanly
                args_wc = sdd_git.build_parser().parse_args(["worktree-create", "--spec", "FEAT-010"])
                self.assertEqual(sdd_git.cmd_worktree_create(args_wc, gov), 0)
                wt_dir = repo / ".worktrees" / "feat-FEAT-010"
                self.assertIn("feat-FEAT-010", (repo / ".agents" / "ACTIVE_STATE.md").read_text(encoding="utf-8"))
                self.assertIn("`FEAT-010`", (wt_dir / ".agents" / "ACTIVE_STATE.md").read_text(encoding="utf-8"))

                args_wr = sdd_git.build_parser().parse_args(["worktree-remove", "--spec", "FEAT-010", "--force"])
                self.assertEqual(sdd_git.cmd_worktree_remove(args_wr, gov), 0)
                self.assertFalse(wt_dir.exists())
                self.assertFalse((repo / ".agents" / "worktree_states" / "feat-FEAT-010.json").exists())
                self.assertIn("- **Active Worktrees:** None", (repo / ".agents" / "ACTIVE_STATE.md").read_text(encoding="utf-8"))

                # 4. release-start + release-finish returns to develop with IDLE state
                _git(repo, "checkout", "develop")
                args_rs = sdd_git.build_parser().parse_args(["release-start", "--version", "1.2.0", "--worktree"])
                self.assertEqual(sdd_git.cmd_release_start(args_rs, gov), 0)
                _git(repo, "add", ".agents")
                _git(repo, "commit", "-m", "chore: sync state before release-finish")
                args_rf = sdd_git.build_parser().parse_args(["release-finish", "--version", "1.2.0", "--local-merge"])
                self.assertEqual(sdd_git.cmd_release_finish(args_rf, gov), 0)
                md_rel = (repo / ".agents" / "ACTIVE_STATE.md").read_text(encoding="utf-8")
                self.assertIn("`IDLE (No Active Work Item)`", md_rel)
                self.assertIn("`develop`", md_rel)

    def test_release_and_hotfix_finish_pr_first_default_and_push_guard(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = _init_temp_repo(pathlib.Path(tmp), initial_branch="main", with_develop=True)
            gov = copy.deepcopy(sdd_git.DEFAULT_GOVERNANCE)
            main_sha_before = _git(repo, "rev-parse", "main")

            _git(repo, "checkout", "-b", "release/v1.3.0", "develop")
            (repo / "CHANGELOG.md").write_text("## v1.3.0\n", encoding="utf-8")
            _git(repo, "add", "CHANGELOG.md")
            _git(repo, "commit", "-m", "chore: release notes")

            _git(repo, "checkout", "-b", "hotfix/BUG-404", "main")
            (repo / "hotfix.txt").write_text("patched\n", encoding="utf-8")
            _git(repo, "add", "hotfix.txt")
            _git(repo, "commit", "-m", "fix: hotfix 404")
            _git(repo, "checkout", "develop")

            with mock.patch.object(sdd_git, "ROOT_DIR", repo):
                # 1. Dirty working tree fails closed on release-finish without calling create_pr
                (repo / "dirty.tmp").write_text("uncommitted\n", encoding="utf-8")
                with mock.patch.object(sdd_git.GitProviderAdapter, "create_pr") as mock_dirty_pr:
                    args_dirty = sdd_git.build_parser().parse_args(["release-finish", "--version", "1.3.0"])
                    self.assertEqual(sdd_git.cmd_release_finish(args_dirty, gov), 1)
                    mock_dirty_pr.assert_not_called()
                (repo / "dirty.tmp").unlink()

                # 2. Default release-finish opens/prepares PR without checking out or merging main
                with mock.patch.object(
                    sdd_git.GitProviderAdapter, "create_pr", return_value="https://github.com/acme/repo/pull/42"
                ) as mock_pr:
                    args_rel = sdd_git.build_parser().parse_args(["release-finish", "--version", "1.3.0"])
                    self.assertFalse(args_rel.local_merge)
                    self.assertEqual(sdd_git.cmd_release_finish(args_rel, gov), 0)
                    mock_pr.assert_called_once_with(
                        "github",
                        "release/v1.3.0",
                        "main",
                        "chore(release): release v1.3.0 into main",
                        "Release v1.3.0 (release/v1.3.0 -> main)",
                    )
                self.assertEqual(_git(repo, "rev-parse", "main"), main_sha_before)
                self.assertEqual(_git(repo, "branch", "--show-current"), "develop")
                self.assertTrue(sdd_git.GitRunner.branch_exists("release/v1.3.0", cwd=repo))
                md_rel = (repo / ".agents" / "ACTIVE_STATE.md").read_text(encoding="utf-8")
                self.assertIn("`PR_OPENED:https://github.com/acme/repo/pull/42`", md_rel)
                state_rel = json.loads((repo / ".agents" / "active_work_item.json").read_text(encoding="utf-8"))
                self.assertEqual(state_rel["git"]["status"], "PR_OPENED:https://github.com/acme/repo/pull/42")

                # 3. Default hotfix-finish falls back to PR_READY when create_pr returns None
                with mock.patch.object(sdd_git.GitProviderAdapter, "create_pr", return_value=None) as mock_hf_pr:
                    args_hf = sdd_git.build_parser().parse_args(["hotfix-finish", "--bug", "BUG-404", "--version", "1.3.1"])
                    self.assertFalse(args_hf.local_merge)
                    self.assertEqual(sdd_git.cmd_hotfix_finish(args_hf, gov), 0)
                    mock_hf_pr.assert_called_once_with(
                        "github",
                        "hotfix/BUG-404",
                        "main",
                        "fix(hotfix): apply BUG-404 (v1.3.1)",
                        "Hotfix v1.3.1 (BUG-404: hotfix/BUG-404 -> main)",
                    )
                self.assertEqual(_git(repo, "rev-parse", "main"), main_sha_before)
                self.assertEqual(_git(repo, "branch", "--show-current"), "develop")
                self.assertTrue(sdd_git.GitRunner.branch_exists("hotfix/BUG-404", cwd=repo))
                md_hf = (repo / ".agents" / "ACTIVE_STATE.md").read_text(encoding="utf-8")
                self.assertIn("`PR_READY:hotfix/BUG-404->main`", md_hf)
                state_hf = json.loads((repo / ".agents" / "active_work_item.json").read_text(encoding="utf-8"))
                self.assertEqual(state_hf["git"]["status"], "PR_READY:hotfix/BUG-404->main")

                # 4. --local-merge --push refuses direct push to protected main (RN-SDD-BRANCH-SYNC)
                for cli_args, fn in (
                    (["release-finish", "--version", "1.3.0", "--local-merge", "--push"], sdd_git.cmd_release_finish),
                    (["hotfix-finish", "--bug", "BUG-404", "--version", "1.3.1", "--local-merge", "--push"], sdd_git.cmd_hotfix_finish),
                ):
                    with mock.patch("builtins.print") as mock_print:
                        rc = fn(sdd_git.build_parser().parse_args(cli_args), gov)
                    self.assertEqual(rc, 1)
                    printed = " ".join(" ".join(str(a) for a in call.args) for call in mock_print.call_args_list)
                    self.assertIn("RN-SDD-BRANCH-SYNC", printed)
                    self.assertEqual(_git(repo, "rev-parse", "main"), main_sha_before)
                    self.assertEqual(_git(repo, "branch", "--show-current"), "develop")

    def test_aud_021_containment_preserved_on_worktree_remove(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = pathlib.Path(tmp)
            repo = _init_temp_repo(base, initial_branch="main", with_develop=False)
            wt_root = repo / ".worktrees"
            wt_root.mkdir(exist_ok=True)
            outside = base / "outside_target"
            outside.mkdir()
            (outside / "keep.txt").write_text("safe\n", encoding="utf-8")

            link_escape = wt_root / "junction_escape"
            if os.name == "nt":
                subprocess.run(["cmd", "/c", "mklink", "/J", str(link_escape), str(outside)], capture_output=True, text=True, check=True)
            else:
                link_escape.symlink_to(outside, target_is_directory=True)

            mgr = sdd_git_worktree.WorktreeManager(sdd_git.DEFAULT_GOVERNANCE, root_dir=repo)
            for hostile in ("", " ", ".", "..", "../outside_target", "../../outside_target", str(wt_root), str(outside), "junction_escape"):
                self.assertFalse(mgr.remove(hostile, force=True), f"Hostile target should be rejected: {hostile!r}")
            self.assertTrue((outside / "keep.txt").exists())

            # Remove junction cleanly so TemporaryDirectory cleanup never fails
            if os.name == "nt":
                os.rmdir(link_escape)
            else:
                link_escape.unlink()

    def test_modularity_ceiling_500_lines_enforced(self):
        targets = [
            ROOT_DIR / "scripts" / "sdd_git.py",
            ROOT_DIR / "scripts" / "sdd_git_state.py",
            ROOT_DIR / "scripts" / "sdd_git_worktree.py",
            ROOT_DIR / "tests" / "test_sdd_governance.py",
            ROOT_DIR / "tests" / "test_sdd_git_concurrency.py",
        ]
        for path in targets:
            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertLessEqual(len(lines), 500, f"{path.name} exceeded 500 lines ({len(lines)})")


if __name__ == "__main__":
    unittest.main()
