#!/usr/bin/env python3
"""Offline unit and acceptance tests for FWK-002 capability-ui-design."""

from __future__ import annotations

import contextlib
import io
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest
from collections.abc import Sequence
from unittest import mock

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts import sdd_agent_generator, sdd_catalog_import, sdd_sync, sdd_vendor_update
from scripts.sdd_pack_registry import (
    InvalidManifestError,
    PackDependencyError,
    StackConfigError,
    load_pack_manifest,
    parse_stack_config,
    resolve_active_packs,
    resolve_pack_assets,
)
from scripts.sdd_vendor_update import VendorIntegrityError, update_vendor, verify_vendor_lock

CATALOG_PACKS_DIR = ROOT_DIR / ".sdd" / "catalog" / "packs"
UI_PACK_DIR = CATALOG_PACKS_DIR / "capability-ui-design"
UI_VENDOR_DIR = UI_PACK_DIR / "vendor" / "ui-ux-pro-max"
GENERATED_MARKER = sdd_agent_generator.GENERATED_MARKER
_IGNORE_PYCACHE = shutil.ignore_patterns("__pycache__", "*.pyc")


def _write_text(path: pathlib.Path, content: str) -> pathlib.Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _snapshot_tree(root: pathlib.Path) -> dict[str, bytes]:
    if not root.exists():
        return {}
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in sorted(root.rglob("*"))
        if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"
    }


def _stack_doc(
    *, checkbox: bool = True, gate00_yaml: object = True, preset: str = "spa-only",
    packs: Sequence[str] = (), uiux_yaml: str = "",
) -> str:
    signoff = "[x] Gate 00 Approved" if checkbox else "[ ] Gate 00 Approved"
    gate_val = str(gate00_yaml).lower() if isinstance(gate00_yaml, bool) else repr(gate00_yaml)
    return (
        f"# Stack\n\n> **ESTADO DE LA PUERTA:** `{signoff} (Human Sign-off)`\n\n"
        f"```yaml sdd:stack-config\ngate00_approved: {gate_val}\npreset: {preset}\n"
        f"packs: {json.dumps(list(packs))}\n{uiux_yaml}```\n"
    )


def _add_dummy_pack(packs_dir: pathlib.Path, dir_name: str, pack_id: str, family: str, requires: Sequence[str], agent: str) -> None:
    pack_dir = packs_dir / dir_name
    _write_text(pack_dir / "agents" / f"{agent}.md", f"---\nname: {agent}\nmode: subagent\n---\n{agent}\n")
    manifest = {
        "id": pack_id, "family": family, "requires": list(requires), "description": dir_name,
        "rules": [], "specialists": [f"agents/{agent}.md"], "skills": [], "workflows": [],
    }
    _write_text(pack_dir / "pack.json", json.dumps(manifest, indent=2))


class TestSddUiDesign(unittest.TestCase):
    """Offline verification for FWK-002 (02-tech-spec §6 groups 1-7 & BDD scenarios 1-7)."""

    _tmp_ctx: tempfile.TemporaryDirectory[str]
    _tmp_root: pathlib.Path
    _ws_seq: int = 0

    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp_ctx = tempfile.TemporaryDirectory()
        cls._tmp_root = pathlib.Path(cls._tmp_ctx.name)

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp_ctx.cleanup()

    def _new_ws(self, stack_content: str, *, copy_packs: Sequence[str] = (), dummy_packs: Sequence[str] = ()) -> pathlib.Path:
        type(self)._ws_seq += 1
        ws = self._tmp_root / f"ui_ws_{type(self)._ws_seq}"
        _write_text(ws / "specs" / "STACK.md", stack_content)
        packs_dir = ws / ".sdd" / "catalog" / "packs"
        packs_dir.mkdir(parents=True, exist_ok=True)
        for name in copy_packs:
            shutil.copytree(CATALOG_PACKS_DIR / name, packs_dir / name, ignore=_IGNORE_PYCACHE)
        dummy_defs = {
            "lang-python": ("lang:python", "language", (), "python-reviewer"),
            "framework-fastapi": ("framework:fastapi", "framework", ("lang:python",), "fastapi-reviewer"),
            "lang-typescript": ("lang:typescript", "language", (), "typescript-reviewer"),
            "framework-react": ("framework:react", "framework", ("lang:typescript",), "react-reviewer"),
        }
        for name in dummy_packs:
            _add_dummy_pack(packs_dir, name, *dummy_defs[name])
        return ws

    def _materialize(self, ws: pathlib.Path, *, requested_packs: list[str] | None = None) -> dict[str, object]:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            return sdd_agent_generator.materialize_squad(requested_packs=requested_packs, repo_root=ws)

    def _run_gen_cli(self, ws: pathlib.Path, argv: list[str]) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with (
            mock.patch.object(sdd_agent_generator, "ROOT_DIR", ws),
            mock.patch.object(sys, "argv", ["sdd_agent_generator.py", *argv]),
            contextlib.redirect_stdout(out),
            contextlib.redirect_stderr(err),
        ):
            code = sdd_agent_generator.main()
        return code, out.getvalue(), err.getvalue()

    def _assert_generated_header(self, path: pathlib.Path, owner: str) -> None:
        lines = path.read_text(encoding="utf-8").splitlines()
        self.assertEqual(lines[0], "---")
        self.assertEqual(lines[lines.index("---", 1) + 1], f"<!-- {GENERATED_MARKER} ({owner}). Do not edit directly. -->")

    # Group 1 / BDD Scenario 1 (RFC-001 #6): Real catalog validation, offline scripts & importer preservation
    def test_group1_real_catalog_offline_scripts_and_importer_preservation(self) -> None:
        self.assertNotIn("capability-ui-design", sdd_catalog_import.STACK_PACKS)
        manifest = load_pack_manifest(UI_PACK_DIR)
        self.assertEqual(
            (manifest.pack_id, manifest.family, manifest.requires, manifest.targets, manifest.rules),
            ("capability:ui-design", "capability", ("capability:web-frontend",), ("web",), ()),
        )
        self.assertEqual(manifest.specialists, ("agents/ui-ux-designer.md",))
        self.assertEqual(manifest.skills, ("skills/sdd-ui-design", "vendor/ui-ux-pro-max"))
        self.assertEqual(manifest.workflows, ("workflows/ui-design-review.md",))
        assert manifest.upstream is not None
        self.assertEqual(
            (manifest.upstream["repo"], manifest.upstream["package"], manifest.upstream["license"], manifest.upstream["version"], manifest.upstream["vendor_lock"]),
            ("nextlevelbuilder/ui-ux-pro-max-skill", "ui-ux-pro-max-cli", "MIT", "2.15.0", "vendor/ui-ux-pro-max/VENDOR.lock.json"),
        )

        notice = (UI_PACK_DIR / "NOTICE.md").read_text(encoding="utf-8")
        for needle in ("nextlevelbuilder/ui-ux-pro-max-skill", "ui-ux-pro-max-cli@2.15.0", "MIT License", "affaan-m/ecc"):
            self.assertIn(needle, notice)
        lic = (UI_VENDOR_DIR / "LICENSE").read_text(encoding="utf-8")
        self.assertIn("MIT License", lic)
        self.assertIn("Next Level Builder", lic)

        lock = verify_vendor_lock(UI_VENDOR_DIR)
        self.assertEqual((lock["schema_version"], lock["package"], lock["version"], lock["license"]), (1, "ui-ux-pro-max-cli", "2.15.0", "MIT"))
        self.assertGreaterEqual(len(lock["files"]), 40)
        for req_entry in ("LICENSE", "SKILL.md", "scripts/search.py", "scripts/validate_data.py"):
            self.assertIn(req_entry, lock["files"])
        self.assertFalse(any(k.startswith("scripts/tests") for k in lock["files"]))
        self.assertFalse((UI_VENDOR_DIR / "scripts" / "tests").exists())
        disk_rel = {p.relative_to(UI_VENDOR_DIR).as_posix() for p in UI_VENDOR_DIR.rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"}
        self.assertEqual(disk_rel - {"VENDOR.lock.json"}, set(lock["files"]))

        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(sdd_vendor_update.main(["--verify"]), 0)

        resolved = resolve_pack_assets(manifest, UI_PACK_DIR)
        self.assertEqual([s for s, _ in resolved.skill_dirs], ["sdd-ui-design", "ui-ux-pro-max"])
        self.assertEqual([p.name for p in resolved.agent_files], ["ui-ux-designer.md"])
        self.assertEqual([p.name for p in resolved.workflow_files], ["ui-design-review.md"])

        env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
        val_proc = subprocess.run([sys.executable, "-B", str(UI_VENDOR_DIR / "scripts" / "validate_data.py")], capture_output=True, text=True, encoding="utf-8", env=env, check=False)
        self.assertEqual(val_proc.returncode, 0, val_proc.stderr)
        self.assertIn("OK: validated", val_proc.stdout)

        search_proc = subprocess.run(
            [sys.executable, "-B", str(UI_VENDOR_DIR / "scripts" / "search.py"), "fintech dashboard", "--design-system", "-p", "Test", "--json"],
            capture_output=True, text=True, encoding="utf-8", env=env, check=False,
        )
        self.assertEqual(search_proc.returncode, 0, search_proc.stderr)
        payload = json.loads(search_proc.stdout)
        self.assertEqual(payload["design_system"]["project_name"], "Test")
        for section in ("colors", "typography", "style", "anti_patterns"):
            self.assertTrue(payload["design_system"][section])

        tmp_packs = self._tmp_root / "importer_packs"
        if tmp_packs.exists():
            shutil.rmtree(tmp_packs)
        tmp_ui_pack = tmp_packs / "capability-ui-design"
        shutil.copytree(UI_PACK_DIR, tmp_ui_pack, ignore=_IGNORE_PYCACHE)
        before_snap = _snapshot_tree(tmp_ui_pack)

        def fake_fetcher(rel_url: str) -> str | None:
            return f"---\ndescription: {rel_url}\n---\nMock ECC {rel_url}\n" if rel_url.startswith("commands/") else None

        with mock.patch("urllib.request.urlopen", side_effect=AssertionError("Network forbidden")), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            sdd_catalog_import.import_packs(fetcher=fake_fetcher, packs_dir=tmp_packs)
        self.assertTrue((tmp_packs / "lang-python" / "pack.json").is_file())
        self.assertEqual(_snapshot_tree(tmp_ui_pack), before_snap)

    # Group 2 / BDD Scenarios 2, 3, 4 (RFC-001 #7, #8, #9): Topology activation & pruning
    def test_group2_topology_activation_and_pruning(self) -> None:
        ws = self._new_ws(
            _stack_doc(preset="api-only", packs=["lang-python", "framework-fastapi"]),
            copy_packs=("capability-web-frontend", "capability-ui-design"),
            dummy_packs=("lang-python", "framework-fastapi"),
        )
        lock_api = self._materialize(ws)
        self.assertEqual([a["name"] for a in lock_api["active_packs"]], ["lang-python", "framework-fastapi"])
        for absent in ("agents/ui-ux-designer.md", "skills/sdd-ui-design", "skills/ui-ux-pro-max", "workflows/ui-design-review.md"):
            self.assertFalse((ws / ".agents" / absent).exists(), f"Should not materialize on api-only: {absent}")
        self.assertFalse((ws / ".agent-inbox" / "ui-ux-designer").exists())

        _write_text(ws / "specs" / "STACK.md", _stack_doc(
            preset="spa-only", packs=["capability-web-frontend", "capability-ui-design"],
            uiux_yaml="uiux:\n  enabled: true\n  provider: ui-ux-pro-max\n  version: \"2.15.0\"\n  hifi_format: html\n  brand_constraints: null\n",
        ))
        self.assertEqual(self._run_gen_cli(ws, ["--materialize"])[0], 0)
        lock_spa = json.loads((ws / ".agents" / "squad.lock.json").read_text(encoding="utf-8"))
        self.assertEqual({a["name"] for a in lock_spa["active_packs"]}, {"capability-web-frontend", "capability-ui-design"})
        for rel_md in ("agents/ui-ux-designer.md", "skills/sdd-ui-design/SKILL.md", "skills/ui-ux-pro-max/SKILL.md", "workflows/ui-design-review.md"):
            self._assert_generated_header(ws / ".agents" / rel_md, "pack:capability-ui-design")
        for expected in (
            ws / ".agents" / "skills" / "ui-ux-pro-max" / "scripts" / "search.py",
            ws / ".agents" / "skills" / "ui-ux-pro-max" / "LICENSE",
            ws / ".agents" / "skills" / "ui-ux-pro-max" / "data" / "styles.csv",
            ws / ".agent-inbox" / "ui-ux-designer" / ".gitkeep",
            ws / ".agents" / "agents" / "a11y-architect.md",
            ws / ".agents" / "agents" / "front-ui.md",
        ):
            self.assertTrue(expected.is_file(), f"Missing materialized UI asset: {expected}")
        managed = sdd_sync.load_managed_lock_paths(ws)
        for rel in (".agents/agents/ui-ux-designer.md", ".agents/skills/ui-ux-pro-max/scripts/search.py", ".agents/workflows/ui-design-review.md"):
            self.assertFalse(sdd_sync.is_syncable_framework_file(rel, ws / rel, managed))

        _write_text(ws / "specs" / "STACK.md", _stack_doc(preset="spa-only", packs=["capability-web-frontend"], uiux_yaml="uiux:\n  enabled: false\n"))
        self._materialize(ws)
        for pruned in (ws / ".agents" / "agents" / "ui-ux-designer.md", ws / ".agents" / "skills" / "sdd-ui-design", ws / ".agents" / "skills" / "ui-ux-pro-max", ws / ".agents" / "workflows" / "ui-design-review.md", ws / ".agent-inbox" / "ui-ux-designer"):
            self.assertFalse(pruned.exists())
        self.assertTrue((ws / ".agents" / "agents" / "a11y-architect.md").is_file())

        ws_ecc = self._new_ws(
            _stack_doc(preset="spa-only", packs=["lang-typescript", "framework-react", "capability-web-frontend"], uiux_yaml="uiux:\n  enabled: false\n"),
            copy_packs=("capability-web-frontend",),
            dummy_packs=("lang-typescript", "framework-react"),
        )
        self._materialize(ws_ecc)
        for ecc_rel in ("agents/a11y-architect.md", "skills/design-system/SKILL.md", "skills/accessibility/SKILL.md", "skills/browser-qa/SKILL.md"):
            self.assertTrue((ws_ecc / ".agents" / ecc_rel).is_file(), f"Missing ECC asset: {ecc_rel}")
        for no_ui in ("agents/ui-ux-designer.md", "skills/sdd-ui-design", "skills/ui-ux-pro-max", "workflows/ui-design-review.md"):
            self.assertFalse((ws_ecc / ".agents" / no_ui).exists())

    # Group 3: Fail-closed validation of `uiux` config, pack dependencies & manifest extensions
    def test_group3_fail_closed_uiux_and_pack_manifest_validation(self) -> None:
        for fmt in ("html", "figma", "html+figma"):
            for bc in ("null", "docs/design-system/BRAND.md"):
                with self.subTest(fmt=fmt, bc=bc):
                    doc = _stack_doc(uiux_yaml=f"uiux:\n  enabled: true\n  provider: ui-ux-pro-max\n  hifi_format: {fmt}\n  brand_constraints: {bc}\n")
                    cfg, eff = parse_stack_config(_write_text(self._tmp_root / f"ok_{fmt}_{bc.replace('/', '_')}.md", doc))
                    self.assertTrue(eff)
                    assert cfg.uiux is not None
                    self.assertEqual((cfg.uiux["hifi_format"], cfg.uiux["brand_constraints"]), (fmt, None if bc == "null" else bc))

        bad_uiux_cases = {
            "api_only_enabled": _stack_doc(preset="api-only", uiux_yaml="uiux:\n  enabled: true\n"),
            "unknown_key": _stack_doc(uiux_yaml="uiux:\n  enabled: true\n  mode: strict\n"),
            "non_mapping": _stack_doc(uiux_yaml="uiux: enabled\n"),
            "missing_enabled": _stack_doc(uiux_yaml="uiux:\n  provider: ui-ux-pro-max\n"),
            "non_bool_enabled": _stack_doc(uiux_yaml="uiux:\n  enabled: \"true\"\n"),
            "bad_provider": _stack_doc(uiux_yaml="uiux:\n  enabled: true\n  provider: custom-ai\n"),
            "empty_version": _stack_doc(uiux_yaml="uiux:\n  enabled: true\n  version: \"\"\n"),
            "bad_hifi_format": _stack_doc(uiux_yaml="uiux:\n  enabled: true\n  hifi_format: sketch\n"),
            "abs_posix_brand": _stack_doc(uiux_yaml="uiux:\n  enabled: true\n  brand_constraints: /etc/passwd\n"),
            "abs_win_brand": _stack_doc(uiux_yaml="uiux:\n  enabled: true\n  brand_constraints: C:\\brand.md\n"),
            "traversal_brand": _stack_doc(uiux_yaml="uiux:\n  enabled: true\n  brand_constraints: ../BRAND.md\n"),
            "dot_brand": _stack_doc(uiux_yaml="uiux:\n  enabled: true\n  brand_constraints: .\n"),
        }
        for label, content in bad_uiux_cases.items():
            with self.subTest(bad_uiux=label), self.assertRaises(StackConfigError):
                parse_stack_config(_write_text(self._tmp_root / f"bad_uiux_{label}.md", content))

        for idx, (packs, uiux_yaml) in enumerate((
            (["capability-web-frontend"], "uiux:\n  enabled: true\n"),
            (["capability-web-frontend", "capability-ui-design"], "uiux:\n  enabled: false\n"),
            (["capability-web-frontend", "capability-ui-design"], ""),
            (["capability-web-frontend", "capability:ui-design"], "uiux:\n  enabled: false\n"),
        )):
            with self.subTest(mismatch=idx), self.assertRaises(StackConfigError):
                cfg, eff = parse_stack_config(_write_text(self._tmp_root / f"mismatch_{idx}.md", _stack_doc(packs=packs, uiux_yaml=uiux_yaml)))
                resolve_active_packs(cfg, eff, None, CATALOG_PACKS_DIR)

        ws_dep = self._new_ws(_stack_doc(packs=["capability-ui-design"], uiux_yaml="uiux:\n  enabled: true\n"))
        _write_text(ws_dep / ".sdd" / "catalog" / "packs" / "capability-ui-design" / "pack.json", (UI_PACK_DIR / "pack.json").read_text(encoding="utf-8"))
        with self.assertRaises(PackDependencyError) as dep_ctx:
            self._materialize(ws_dep)
        self.assertIn("capability:web-frontend", str(dep_ctx.exception))

        base_m = {"id": "custom:test", "family": "capability", "requires": [], "description": "d", "rules": [], "specialists": [], "skills": [], "workflows": []}
        for label, patch in (("bad_targets_type", {"targets": "web"}), ("empty_target", {"targets": [""]}), ("bad_upstream_type", {"upstream": "nope"}), ("empty_vendor_lock", {"upstream": {"vendor_lock": ""}})):
            with self.subTest(manifest_case=label), self.assertRaises(InvalidManifestError):
                pdir = self._tmp_root / f"bad_m_{label}"
                _write_text(pdir / "pack.json", json.dumps({**base_m, **patch}))
                load_pack_manifest(pdir)

        pdir_trav = self._tmp_root / "bad_m_traversal_lock"
        _write_text(pdir_trav / "pack.json", json.dumps({**base_m, "upstream": {"vendor_lock": "../VENDOR.lock.json"}}))
        with self.assertRaises(InvalidManifestError):
            resolve_pack_assets(load_pack_manifest(pdir_trav), pdir_trav)

    # Group 4 / BDD Scenario 5 (RFC-001 #10): Vendor tampering fails closed before touching .agents/
    def test_group4_vendor_tampering_aborts_verify_and_materialize(self) -> None:
        ws = self._new_ws(
            _stack_doc(preset="spa-only", packs=["capability-web-frontend", "capability-ui-design"], uiux_yaml="uiux:\n  enabled: true\n  provider: ui-ux-pro-max\n  hifi_format: html\n"),
            copy_packs=("capability-web-frontend", "capability-ui-design"),
        )
        pack_dir = ws / ".sdd" / "catalog" / "packs" / "capability-ui-design"
        vdir = pack_dir / "vendor" / "ui-ux-pro-max"
        orig_skill = (vdir / "SKILL.md").read_bytes()
        orig_colors = (vdir / "data" / "colors.csv").read_bytes()

        for mode in ("modified_byte", "missing_file", "extra_file"):
            with self.subTest(tamper=mode):
                try:
                    if mode == "modified_byte":
                        (vdir / "SKILL.md").write_bytes(orig_skill + b" ")
                        expected_fragment = "SKILL.md"
                    elif mode == "missing_file":
                        (vdir / "data" / "colors.csv").unlink()
                        expected_fragment = "data/colors.csv"
                    else:
                        _write_text(vdir / "extra_undeclared.txt", "unexpected\n")
                        expected_fragment = "extra_undeclared.txt"

                    with self.assertRaises(VendorIntegrityError) as v_ctx:
                        verify_vendor_lock(vdir)
                    self.assertIn(expected_fragment, str(v_ctx.exception))
                    if mode == "modified_byte":
                        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                            self.assertEqual(sdd_vendor_update.main(["--verify", "--pack-dir", str(pack_dir)]), 1)
                    with self.assertRaises(InvalidManifestError):
                        self._materialize(ws)
                    self.assertFalse((ws / ".agents").exists())
                    if mode == "missing_file":
                        self.assertEqual(self._run_gen_cli(ws, ["--materialize"])[0], 1)
                        self.assertFalse((ws / ".agents").exists())
                finally:
                    (vdir / "SKILL.md").write_bytes(orig_skill)
                    (vdir / "data" / "colors.csv").write_bytes(orig_colors)
                    if (vdir / "extra_undeclared.txt").exists():
                        (vdir / "extra_undeclared.txt").unlink()

    # Group 5: Isolated update_vendor() with mocked npx runner
    def test_group5_vendor_update_isolated_runner_and_apply(self) -> None:
        pack_dir = self._tmp_root / "upd_pack"
        if pack_dir.exists():
            shutil.rmtree(pack_dir)
        _write_text(pack_dir / "pack.json", json.dumps({"id": "capability:ui-design", "upstream": {"version": "2.14.0"}}, indent=2))
        old_vendor = pack_dir / "vendor" / "ui-ux-pro-max"
        _write_text(old_vendor / "LICENSE", "MIT License — Preserved\n")
        _write_text(old_vendor / "SKILL.md", "---\nname: ui-ux-pro-max\n---\nOld\n")
        _write_text(old_vendor / "old_obsolete.csv", "a,b\n")

        def make_runner(val_exit: int = 0, runner_exit: int = 0) -> object:
            def _runner(cmd: Sequence[str], staging_dir: pathlib.Path) -> int:
                self.assertEqual(list(cmd), ["npx", "--yes", "ui-ux-pro-max-cli@2.15.0", "init", "--ai", "antigravity", "--offline"])
                self.assertFalse(staging_dir.is_relative_to(pack_dir))
                if runner_exit != 0:
                    return runner_exit
                skills_root = staging_dir / ".agents" / "skills"
                for sibling in ("banner-design", "brand", "design", "design-system", "slides", "ui-styling"):
                    _write_text(skills_root / sibling / "SKILL.md", f"# {sibling}\n")
                _write_text(skills_root / "ui-styling" / "LICENSE.txt", "Apache License 2.0\n")
                target = skills_root / "ui-ux-pro-max"
                (target / "data").mkdir(parents=True, exist_ok=True)
                (target / "scripts" / "tests").mkdir(parents=True, exist_ok=True)
                (target / "SKILL.md").write_bytes(b"---\r\nname: ui-ux-pro-max\r\n---\r\nNew\r\n")
                (target / "data" / "styles.csv").write_bytes(b"id,name\r\n1,Minimal\r\n")
                _write_text(target / "scripts" / "validate_data.py", f"import sys\nsys.exit({val_exit})\n")
                _write_text(target / "scripts" / "tests" / "test_upstream.py", "assert False\n")
                return 0
            return _runner

        with self.assertRaises(ValueError):
            update_vendor("2.15", pack_dir, runner=make_runner())
        snap_before = _snapshot_tree(pack_dir)
        with self.assertRaises(VendorIntegrityError):
            update_vendor("2.15.0", pack_dir, apply=True, runner=make_runner(runner_exit=1))
        self.assertEqual(_snapshot_tree(pack_dir), snap_before)

        preview = update_vendor("2.15.0", pack_dir, apply=False, runner=make_runner(0))
        self.assertFalse(preview["applied"])
        self.assertEqual(preview["removed"], ["old_obsolete.csv"])
        self.assertIn("data/styles.csv", preview["added"])
        self.assertIn("SKILL.md", preview["modified"])
        self.assertEqual(preview["pack_version_change"], {"from": "2.14.0", "to": "2.15.0", "changed": True})
        self.assertEqual(_snapshot_tree(pack_dir), snap_before)

        with self.assertRaises(VendorIntegrityError):
            update_vendor("2.15.0", pack_dir, apply=True, runner=make_runner(val_exit=1))
        self.assertEqual(_snapshot_tree(pack_dir), snap_before)

        applied = update_vendor("2.15.0", pack_dir, apply=True, runner=make_runner(0))
        self.assertTrue(applied["applied"])
        self.assertEqual(json.loads((pack_dir / "pack.json").read_text(encoding="utf-8"))["upstream"]["version"], "2.15.0")
        self.assertEqual((old_vendor / "LICENSE").read_text(encoding="utf-8"), "MIT License — Preserved\n")
        self.assertFalse((old_vendor / "old_obsolete.csv").exists())
        self.assertFalse((old_vendor / "scripts" / "tests").exists())
        self.assertNotIn(b"\r", (old_vendor / "SKILL.md").read_bytes())
        self.assertNotIn(b"\r", (old_vendor / "data" / "styles.csv").read_bytes())
        for sibling in ("banner-design", "brand", "design", "design-system", "slides", "ui-styling", "LICENSE.txt"):
            self.assertFalse((old_vendor / sibling).exists())
        self.assertEqual(verify_vendor_lock(old_vendor)["version"], "2.15.0")

    # Group 6 / BDD Scenarios 6 & 7 (RFC-001 #11, #12): Contractual assertions on real governance artefacts
    def test_group6_contractual_assertions_on_real_artefacts(self) -> None:
        checks = {
            UI_PACK_DIR / "agents" / "ui-ux-designer.md": (
                "name: ui-ux-designer", "Gate 1", "wireframe.excalidraw", "screen-spec.md", "BLOCKED_DOR_", "BLOCKED_",
                "src/**", "tests/**", "RN-SDD-IMMUTABLE-DONE", "npx", "--force", "@a11y-architect", "@architect", "[ ] Visual Sign-off (Human)",
            ),
            UI_PACK_DIR / "skills" / "sdd-ui-design" / "SKILL.md": (
                ".agents/skills/ui-ux-pro-max/scripts/search.py", "--json", "--output-dir", "--force",
                "MASTER.md", "design-tokens.json", "CHANGELOG.md", "pages/SCR-XXX.md",
                "MAJOR", "MINOR", "PATCH", "Design System Foundation", "CR-XXX", "RN-SDD-IMMUTABLE-DONE", "RN-SDD-1-TO-1-CR",
            ),
            UI_PACK_DIR / "workflows" / "ui-design-review.md": (
                "BLOCKED_DOR_", "sdd-ui-design", "search.py", "@a11y-architect", "WCAG 2.2 AA", "@architect", "§6.1", "Stop-the-Line", "Visual Sign-off (Human)",
            ),
            ROOT_DIR / ".agents" / "skills" / "sdd-bootstrap" / "SKILL.md": (
                "Solo Backend / API Only", "CLI / Herramienta Local", "Enable ui-ux-pro-max",
                "uiux.hifi_format", "uiux.brand_constraints", "capability-ui-design", "Design System Foundation", "Gate 0 (Intake)", "specs/BACKLOG.md",
            ),
            ROOT_DIR / "specs" / "templates" / "02-technical-spec.template.md": (
                "### 6.1. Diseño Visual", "MASTER@<versión>", "docs/design-system/pages/SCR-XXX.md", "docs/design-system/design-tokens.json", "@a11y-architect", "- [ ] **Visual Sign-off (Human)**",
            ),
            ROOT_DIR / ".agents" / "agents" / "orchestrator.md": (
                "ui-design-review.md", "@ui-ux-designer", "@a11y-architect", "Visual Sign-off (Human)", "MASTER@versión", "pages/SCR-XXX.md",
            ),
        }
        for path, tokens in checks.items():
            text = path.read_text(encoding="utf-8")
            for tok in tokens:
                self.assertIn(tok, text, f"Missing {tok!r} in {path.name}")
        designer = (UI_PACK_DIR / "agents" / "ui-ux-designer.md").read_text(encoding="utf-8")
        self.assertLess(designer.index("@a11y-architect"), designer.index("@architect"))
        self.assertLess(designer.index("@architect"), designer.index("[ ] Visual Sign-off (Human)"))

        tpl_cfg, tpl_eff = parse_stack_config(ROOT_DIR / "specs" / "templates" / "00-stack.template.md")
        self.assertFalse(tpl_eff)
        self.assertEqual((tpl_cfg.gate00_approved, tpl_cfg.packs, tpl_cfg.uiux), (False, (), {"enabled": False, "provider": "ui-ux-pro-max", "version": "2.15.0", "hifi_format": "html"}))
        stack_cfg, stack_eff = parse_stack_config(ROOT_DIR / "specs" / "STACK.md")
        self.assertFalse(stack_eff)
        self.assertEqual((stack_cfg.gate00_approved, stack_cfg.preset, stack_cfg.packs, stack_cfg.uiux), (False, "compact", (), {"enabled": False}))
        self.assertFalse((ROOT_DIR / "docs" / "design-system").exists())

        for arch_name in ("front-ui.archetype.md", "front-engineer.archetype.md", "tier-frontend.archetype.md"):
            arch = (ROOT_DIR / ".sdd" / "catalog" / "archetypes" / arch_name).read_text(encoding="utf-8")
            for tok in ("SCR-XXX", "MASTER@versión", "docs/design-system/pages/SCR-XXX.md", "docs/design-system/design-tokens.json"):
                self.assertIn(tok, arch, f"Missing {tok} in {arch_name}")

    # Group 7: Modularity threshold <= 500 lines
    def test_group7_modularity_line_limit_500(self) -> None:
        for rel in (
            "scripts/sdd_pack_registry.py", "scripts/sdd_agent_generator.py", "scripts/sdd_vendor_update.py",
            "tests/test_sdd_pack_materialization.py", "tests/test_sdd_ui_design.py",
        ):
            count = len((ROOT_DIR / rel).read_text(encoding="utf-8").splitlines())
            self.assertLessEqual(count, 500, f"{rel} exceeds 500-line ceiling ({count})")


if __name__ == "__main__":
    unittest.main()
