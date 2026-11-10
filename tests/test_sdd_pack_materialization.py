#!/usr/bin/env python3
"""Offline unit and acceptance tests for FWK-001 pack materialization."""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import pathlib
import sys
import tempfile
import unittest
from collections.abc import Mapping, Sequence
from unittest import mock

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts import sdd_agent_generator, sdd_catalog_import, sdd_sync
from scripts.sdd_pack_registry import (
    CollisionError,
    InvalidManifestError,
    ManualModificationConflictError,
    PackDependencyError,
    StackConfigError,
    load_catalog_registry,
    parse_stack_config,
    resolve_pack_assets,
)

GENERATED_MARKER = sdd_agent_generator.GENERATED_MARKER


def _write_text(path: pathlib.Path, content: str) -> pathlib.Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _snapshot_tree(root: pathlib.Path) -> dict[str, bytes]:
    if not root.exists():
        return {}
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}


def _stack_doc(
    *,
    checkbox: bool = True,
    gate00_yaml: object = True,
    preset: str = "compact",
    packs: Sequence[str] = (),
    prose: str = "",
    include_block: bool = True,
    extra_yaml: str = "",
) -> str:
    signoff = "[x] Gate 00 Approved" if checkbox else "[ ] Gate 00 Approved"
    parts = [f"# Stack\n\n> **ESTADO DE LA PUERTA:** `{signoff} (Human Sign-off)`\n", prose]
    if include_block:
        gate_val = str(gate00_yaml).lower() if isinstance(gate00_yaml, bool) else repr(gate00_yaml)
        parts.append(
            f"```yaml sdd:stack-config\ngate00_approved: {gate_val}\npreset: {preset}\n"
            f"packs: {json.dumps(list(packs))}\n{extra_yaml}```\n"
        )
    return "\n".join(parts)


def _create_pack(
    packs_dir: pathlib.Path,
    dir_name: str,
    *,
    pack_id: str | None = None,
    family: str = "language",
    requires: Sequence[str] = (),
    agents: Mapping[str, str] | None = None,
    skills: Mapping[str, Mapping[str, str]] | None = None,
    rules: Mapping[str, str] | None = None,
    workflows: Mapping[str, str] | None = None,
    manifest_override: Mapping[str, object] | str | None = None,
    create_assets: bool = True,
) -> pathlib.Path:
    pack_dir = packs_dir / dir_name
    pack_dir.mkdir(parents=True, exist_ok=True)
    agents_map, skills_map, rules_map, wf_map = agents or {}, skills or {}, rules or {}, workflows or {}
    if create_assets:
        for rel, body in agents_map.items():
            _write_text(pack_dir / rel, body)
        for slug, files in skills_map.items():
            for fname, body in files.items():
                _write_text(pack_dir / "skills" / slug / fname, body)
        for rel, body in rules_map.items():
            _write_text(pack_dir / "rules" / pathlib.Path(rel).name, body)
        for rel, body in wf_map.items():
            _write_text(pack_dir / "workflows" / pathlib.Path(rel).name, body)
    if isinstance(manifest_override, str):
        return _write_text(pack_dir / "pack.json", manifest_override)

    manifest: dict[str, object] = {
        "id": pack_id or dir_name.replace("-", ":", 1),
        "family": family,
        "requires": list(requires),
        "description": f"Test pack {dir_name}",
        "rules": list(rules_map.keys()),
        "specialists": list(agents_map.keys()),
        "skills": [f"skills/{slug}" for slug in skills_map],
        "workflows": list(wf_map.keys()),
    }
    if manifest_override is not None:
        manifest.update(manifest_override)
    return _write_text(pack_dir / "pack.json", json.dumps(manifest, indent=2))


def _add_standard_packs(packs_dir: pathlib.Path, names: Sequence[str]) -> None:
    if "lang-python" in names:
        _create_pack(
            packs_dir, "lang-python", pack_id="lang:python",
            agents={"agents/python-reviewer.md": "---\nname: python-reviewer\nmode: subagent\n---\nPython reviewer.\n"},
            skills={"python-patterns": {"SKILL.md": "---\nname: python-patterns\n---\nPatterns.\n", "helper.py": "VALUE = 42\n"},
                    "python-testing": {"SKILL.md": "# Python Testing\nPytest body.\n"}},
            rules={"rules/python/coding-style.md": "# Python Coding Style\nUse type hints.\n"},
            workflows={"commands/python-review.md": "---\ndescription: Python review\n---\nReview steps.\n"},
        )
    if "framework-fastapi" in names:
        _create_pack(
            packs_dir, "framework-fastapi", pack_id="framework:fastapi", family="framework", requires=("lang:python",),
            agents={"agents/fastapi-reviewer.md": "---\nname: fastapi-reviewer\nmode: subagent\n---\nFastAPI reviewer.\n"},
            skills={"fastapi-patterns": {"SKILL.md": "---\nname: fastapi-patterns\n---\nFastAPI.\n"}},
            rules={"rules/python/fastapi.md": "# FastAPI Rule\n"},
            workflows={"commands/fastapi-review.md": "# FastAPI Review\n"},
        )
    for name in names:
        if name in {"lang-java", "lang-typescript", "framework-react", "framework-vue"}:
            agent = f"{name.split('-', 1)[1]}-reviewer"
            req = ("lang:typescript",) if name.startswith("framework-") else ()
            _create_pack(
                packs_dir, name, requires=req,
                agents={f"agents/{agent}.md": f"---\nname: {agent}\nmode: subagent\n---\nBody.\n"},
                rules={f"rules/{name}/coding-style.md": f"# {name} rule\n"},
            )


class TestSddPackMaterialization(unittest.TestCase):
    """Offline verification for all 9 groups (02-tech-spec §7) and 7 BDD scenarios."""

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

    def _new_ws(
        self, stack_content: str, packs: Sequence[str] = (), *, with_catalog: bool = True, with_archetype: bool = False
    ) -> pathlib.Path:
        type(self)._ws_seq += 1
        root = self._tmp_root / f"ws_{type(self)._ws_seq}"
        _write_text(root / "specs" / "STACK.md", stack_content)
        if with_archetype:
            _write_text(root / ".sdd" / "catalog" / "archetypes" / "tier-backend.archetype.md", "---\nname: {{AGENT_NAME}}\n---\n{{TECH_STACK}}\n")
        if with_catalog:
            (packs_dir := root / ".sdd" / "catalog" / "packs").mkdir(parents=True, exist_ok=True)
            _add_standard_packs(packs_dir, packs)
        return root

    def _materialize(self, root: pathlib.Path, *, requested_packs: list[str] | None = None) -> dict[str, object]:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            return sdd_agent_generator.materialize_squad(requested_packs=requested_packs, repo_root=root)

    def _run_cli(self, root: pathlib.Path, argv: list[str]) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with (
            mock.patch.object(sdd_agent_generator, "ROOT_DIR", root),
            mock.patch.object(sys, "argv", ["sdd_agent_generator.py", *argv]),
            contextlib.redirect_stdout(out),
            contextlib.redirect_stderr(err),
        ):
            code = sdd_agent_generator.main()
        return code, out.getvalue(), err.getvalue()

    def _assert_generated_header(self, path: pathlib.Path, owner: str, *, has_frontmatter: bool) -> None:
        lines = path.read_text(encoding="utf-8").splitlines()
        expected = f"<!-- {GENERATED_MARKER} ({owner}). Do not edit directly. -->"
        if has_frontmatter:
            self.assertEqual(lines[0], "---")
            self.assertEqual(lines[lines.index("---", 1) + 1], expected)
        else:
            self.assertEqual(lines[0], expected)

    # Group 1 / Scenario 1: Strict selection from sdd:stack-config & lazy pack-rules
    def test_scenario_1_strict_stack_config_selection_and_lazy_rules(self) -> None:
        stack = _stack_doc(
            checkbox=True, gate00_yaml=True, packs=["lang-python"],
            prose="Ejemplos de stack: React / Vue / Java / TypeScript / FastAPI / PostgreSQL.",
            extra_yaml="uiux:\n  mode: strict\n",
        )
        ws = self._new_ws(stack, packs=("lang-python", "lang-java", "framework-react", "framework-vue"), with_archetype=True)
        _write_text(ws / ".sdd" / "catalog" / "specialists" / "code-explorer.md", "---\nname: code-explorer\n---\nExplorer.\n")
        _write_text(ws / ".agents" / "overrides" / "back-engineer.md", "---\nname: back-engineer\n---\nCustom builder.\n")
        lock = self._materialize(ws)

        self.assertEqual(lock["schema_version"], 2)
        self.assertTrue(lock["gate00_approved"])
        self.assertEqual(lock["active_packs"], [{"name": "lang-python", "id": "lang:python", "source": "stack-config"}])

        py_agent = ws / ".agents" / "agents" / "python-reviewer.md"
        py_skill_md = ws / ".agents" / "skills" / "python-patterns" / "SKILL.md"
        py_skill_py = ws / ".agents" / "skills" / "python-patterns" / "helper.py"
        py_rule = ws / ".agents" / "pack-rules" / "lang-python" / "coding-style.md"
        py_wf = ws / ".agents" / "workflows" / "python-review.md"
        for p in (py_agent, py_skill_md, py_skill_py, py_rule, py_wf, ws / ".agent-inbox" / "python-reviewer" / ".gitkeep"):
            self.assertTrue(p.is_file(), f"Missing materialized file: {p}")

        self.assertFalse((ws / ".agents" / "rules").exists())
        for phantom in ("java-reviewer.md", "react-reviewer.md", "vue-reviewer.md", "fastapi-reviewer.md"):
            self.assertFalse((ws / ".agents" / "agents" / phantom).exists())

        self._assert_generated_header(py_agent, "pack:lang-python", has_frontmatter=True)
        self._assert_generated_header(py_skill_md, "pack:lang-python", has_frontmatter=True)
        self._assert_generated_header(py_wf, "pack:lang-python", has_frontmatter=True)
        self._assert_generated_header(py_rule, "pack:lang-python", has_frontmatter=False)
        self.assertEqual(py_skill_py.read_text(encoding="utf-8"), "VALUE = 42\n")
        self.assertIn("Custom builder.", (ws / ".agents" / "agents" / "back-engineer.md").read_text(encoding="utf-8"))

        managed = sdd_sync.load_managed_lock_paths(ws)
        for rel in (
            ".agents/agents/python-reviewer.md", ".agents/skills/python-patterns/helper.py",
            ".agents/pack-rules/lang-python/coding-style.md", ".agents/workflows/python-review.md", ".agents/squad.lock.json",
        ):
            self.assertFalse(sdd_sync.is_syncable_framework_file(rel, ws / rel, managed))

    def test_stack_config_yaml_parsing_and_invalid_blocks(self) -> None:
        valid_block = _stack_doc(
            checkbox=True, gate00_yaml=True, packs=["lang-python"],
            extra_yaml="uiux:\n  enabled: true\n  palette:\n    - warm\n    - editorial\n",
        )
        cfg, approved = parse_stack_config(_write_text(self._tmp_root / "yaml_valid.md", valid_block))
        self.assertTrue(approved)
        self.assertEqual(cfg.packs, ("lang-python",))
        self.assertEqual(cfg.uiux, {"enabled": True, "palette": ["warm", "editorial"]})

        bad_cases = (
            _stack_doc(checkbox=True, gate00_yaml="yes"),
            _stack_doc(checkbox=True, gate00_yaml=True, preset="unknown-mode"),
            _stack_doc(checkbox=True, gate00_yaml=True, extra_yaml="gate00_approved: false\n"),
            _stack_doc(checkbox=True, gate00_yaml=True, extra_yaml="\tbad_indent: 1\n"),
            valid_block + "\n```yaml sdd:stack-config\ngate00_approved: true\n```\n",
            "# Stack\n```yaml sdd:stack-config\ngate00_approved: true\n",
        )
        for idx, content in enumerate(bad_cases):
            with self.subTest(case=idx), self.assertRaises(StackConfigError):
                parse_stack_config(_write_text(self._tmp_root / f"yaml_bad_{idx}.md", content))

    # Group 2 / Scenario 2: Gate 00 lock, --packs manual, mismatch & missing block
    def test_scenario_2_gate00_lock_and_manual_packs(self) -> None:
        ws = self._new_ws(_stack_doc(checkbox=False, gate00_yaml=False, packs=["lang-python"]), packs=("lang-python",))
        self.assertEqual(self._run_cli(ws, ["--materialize"])[0], 0)
        lock = json.loads((ws / ".agents" / "squad.lock.json").read_text(encoding="utf-8"))
        self.assertEqual((lock["gate00_approved"], lock["active_packs"]), (False, []))
        self.assertFalse((ws / ".agents" / "agents" / "python-reviewer.md").exists())

        self.assertEqual(self._run_cli(ws, ["--materialize", "--packs", "lang-python"])[0], 0)
        lock2 = json.loads((ws / ".agents" / "squad.lock.json").read_text(encoding="utf-8"))
        self.assertEqual(lock2["active_packs"], [{"name": "lang-python", "id": "lang:python", "source": "manual"}])
        self.assertTrue((ws / ".agents" / "agents" / "python-reviewer.md").is_file())

    def test_gate00_mismatch_and_missing_block_behavior(self) -> None:
        ws = self._new_ws(_stack_doc(checkbox=True, gate00_yaml=False, packs=["lang-python"]), packs=("lang-python",))
        lock = self._materialize(ws)
        self.assertEqual((lock["gate00_approved"], lock["active_packs"]), (False, []))

        ws_rev = self._new_ws(_stack_doc(checkbox=False, gate00_yaml=True, packs=["lang-python"]), with_catalog=False)
        self.assertFalse(parse_stack_config(ws_rev / "specs" / "STACK.md")[1])

        ws_nb_u = self._new_ws(_stack_doc(checkbox=False, include_block=False), with_catalog=False)
        cfg, eff = parse_stack_config(ws_nb_u / "specs" / "STACK.md")
        self.assertEqual((eff, cfg.preset, cfg.packs), (False, "compact", ()))

        ws_nb_a = self._new_ws(_stack_doc(checkbox=True, include_block=False), with_catalog=False)
        with self.assertRaises(StackConfigError):
            parse_stack_config(ws_nb_a / "specs" / "STACK.md")
        code, _, err = self._run_cli(ws_nb_a, ["--materialize"])
        self.assertEqual(code, 1)
        self.assertIn("[ERROR SDD]", err)

    # Group 3: Pack dependencies `requires` (AMB-004)
    def test_requires_dependency_missing_fails_closed_atomically(self) -> None:
        ws = self._new_ws(_stack_doc(checkbox=True, gate00_yaml=True, packs=["framework-fastapi"]), packs=("lang-python", "framework-fastapi"))
        with self.assertRaises(PackDependencyError):
            self._materialize(ws)
        code, _, err = self._run_cli(ws, ["--materialize"])
        self.assertEqual(code, 1)
        self.assertIn("lang:python", err)
        self.assertFalse((ws / ".agents").exists())
        self.assertFalse((ws / ".agent-inbox").exists())

        lock = self._materialize(ws, requested_packs=["lang-python", "framework-fastapi"])
        self.assertEqual(
            lock["active_packs"],
            [{"name": "framework-fastapi", "id": "framework:fastapi", "source": "stack-config"},
             {"name": "lang-python", "id": "lang:python", "source": "manual"}],
        )

    # Group 4 / Scenario 3: Double materialize idempotency
    def test_scenario_3_idempotency_preserves_files_hashes_and_timestamp(self) -> None:
        ws = self._new_ws(_stack_doc(checkbox=True, gate00_yaml=True, packs=["lang-python"]), packs=("lang-python",))
        lock1 = self._materialize(ws)
        snap1, lock_bytes1 = _snapshot_tree(ws / ".agents"), (ws / ".agents" / "squad.lock.json").read_bytes()

        lock2 = self._materialize(ws)
        self.assertEqual(snap1, _snapshot_tree(ws / ".agents"))
        self.assertEqual((lock1["files"], lock1["timestamp"]), (lock2["files"], lock2["timestamp"]))
        self.assertEqual(lock_bytes1, (ws / ".agents" / "squad.lock.json").read_bytes())

    # Group 5 / Scenario 4: Safe deactivation cleanup & manual modification conflict
    def test_scenario_4_deactivation_cleanup_and_inbox_preservation(self) -> None:
        ws = self._new_ws(_stack_doc(checkbox=True, gate00_yaml=True, packs=["lang-python", "lang-java"]), packs=("lang-python", "lang-java"))
        self._materialize(ws)
        ticket = _write_text(ws / ".agent-inbox" / "python-reviewer" / "TASK-1.md", "Pending work\n")
        _write_text(ws / "specs" / "STACK.md", _stack_doc(checkbox=True, gate00_yaml=True, packs=[]))
        code, _, err = self._run_cli(ws, ["--materialize"])
        self.assertEqual(code, 0)
        self.assertIn("[WARN]", err)
        self.assertTrue(ticket.is_file())
        self.assertFalse((ws / ".agent-inbox" / "java-reviewer").exists())
        for removed in (
            ws / ".agents" / "agents" / "python-reviewer.md", ws / ".agents" / "agents" / "java-reviewer.md",
            ws / ".agents" / "skills" / "python-patterns", ws / ".agents" / "pack-rules", ws / ".agents" / "workflows" / "python-review.md",
        ):
            self.assertFalse(removed.exists(), f"Expected pruned path: {removed}")

    def test_scenario_4_manual_edit_conflict_blocks_rematerialize_and_deactivation(self) -> None:
        ws = self._new_ws(_stack_doc(checkbox=True, gate00_yaml=True, packs=["lang-python"]), packs=("lang-python",))
        self._materialize(ws)
        agent_file = ws / ".agents" / "agents" / "python-reviewer.md"
        custom = "---\nname: python-reviewer\n---\nUser manual edit.\n"
        _write_text(agent_file, custom)

        with self.assertRaises(ManualModificationConflictError):
            self._materialize(ws)
        self.assertEqual(agent_file.read_text(encoding="utf-8"), custom)

        _write_text(ws / "specs" / "STACK.md", _stack_doc(checkbox=True, gate00_yaml=True, packs=[]))
        snap_before = _snapshot_tree(ws / ".agents")
        with self.assertRaises(ManualModificationConflictError):
            self._materialize(ws)
        self.assertEqual(_snapshot_tree(ws / ".agents"), snap_before)

    # Group 6 / Scenario 5: Collisions (intra-packs & unmanaged artisanal destinations)
    def test_scenario_5_intra_pack_and_unmanaged_destination_collisions(self) -> None:
        ws_col = self._new_ws(_stack_doc(checkbox=True, gate00_yaml=True, packs=["pack-a", "pack-b"]))
        packs = ws_col / ".sdd" / "catalog" / "packs"
        _create_pack(packs, "pack-a", skills={"shared-skill": {"SKILL.md": "# A\n"}}, rules={"rules/a/coding-style.md": "# A\n"})
        _create_pack(packs, "pack-b", skills={"shared-skill": {"SKILL.md": "# B\n"}}, rules={"rules/b/coding-style.md": "# B\n"})
        with self.assertRaises(CollisionError) as ctx:
            self._materialize(ws_col)
        self.assertIn("pack:pack-a", str(ctx.exception))
        self.assertIn("pack:pack-b", str(ctx.exception))
        self.assertFalse((ws_col / ".agents").exists())

        ws_unmanaged = self._new_ws(_stack_doc(checkbox=True, gate00_yaml=True, packs=["lang-python", "framework-fastapi"]), packs=("lang-python", "framework-fastapi"))
        artisanal = _write_text(ws_unmanaged / ".agents" / "skills" / "fastapi-patterns" / "SKILL.md", "Artisanal skill\n")
        before_unmanaged = _snapshot_tree(ws_unmanaged / ".agents")
        with self.assertRaises(CollisionError):
            self._materialize(ws_unmanaged)
        self.assertEqual(_snapshot_tree(ws_unmanaged / ".agents"), before_unmanaged)
        self.assertEqual(artisanal.read_text(encoding="utf-8"), "Artisanal skill\n")

        ws_rules = self._new_ws(_stack_doc(checkbox=True, gate00_yaml=True, packs=["rule-a", "rule-b"]))
        packs_r = ws_rules / ".sdd" / "catalog" / "packs"
        _create_pack(packs_r, "rule-a", rules={"rules/a/coding-style.md": "# A\n"})
        _create_pack(packs_r, "rule-b", rules={"rules/b/coding-style.md": "# B\n"})
        self._materialize(ws_rules)
        self.assertTrue((ws_rules / ".agents" / "pack-rules" / "rule-a" / "coding-style.md").is_file())
        self.assertTrue((ws_rules / ".agents" / "pack-rules" / "rule-b" / "coding-style.md").is_file())

    # Group 7 / Scenario 6: Invalid pack.json, path traversal, unknown pack & corrupt lock
    def test_scenario_6_invalid_manifests_traversal_and_corrupt_lock(self) -> None:
        ws = self._new_ws(_stack_doc(checkbox=True, gate00_yaml=True, packs=["bad-pack"]))
        packs_dir = ws / ".sdd" / "catalog" / "packs"
        bad_dir = packs_dir / "bad-pack"
        builders = {
            "broken_json": lambda d: _create_pack(d, "bad-pack", manifest_override="{invalid json"),
            "missing_id": lambda d: _create_pack(d, "bad-pack", manifest_override={"id": ""}),
            "missing_asset": lambda d: _create_pack(d, "bad-pack", rules={"rules/python/missing.md": ""}, create_assets=False),
            "missing_skill_md": lambda d: _create_pack(d, "bad-pack", skills={"broken-skill": {"README.md": "no skill"}}),
            "traversal_rule": lambda d: _create_pack(d, "bad-pack", manifest_override={"rules": ["../outside.md"]}),
            "abs_workflow": lambda d: _create_pack(d, "bad-pack", manifest_override={"workflows": ["/etc/passwd"]}),
            "win_abs_skill": lambda d: _create_pack(d, "bad-pack", manifest_override={"skills": ["C:\\escape\\skill"]}),
        }
        for label, build in builders.items():
            with self.subTest(case=label):
                if bad_dir.exists():
                    for p in sorted(bad_dir.rglob("*"), reverse=True):
                        p.unlink() if p.is_file() else p.rmdir()
                build(packs_dir)
                with self.assertRaises(InvalidManifestError):
                    self._materialize(ws)
                self.assertFalse((ws / ".agents").exists())

        _write_text(ws / "specs" / "STACK.md", _stack_doc(checkbox=True, gate00_yaml=True, packs=["nonexistent-pack"]))
        with self.assertRaises(InvalidManifestError):
            self._materialize(ws)

        _write_text(ws / "specs" / "STACK.md", _stack_doc(checkbox=True, gate00_yaml=True, packs=[]))
        _write_text(ws / ".agents" / "squad.lock.json", "{corrupt-lock")
        with self.assertRaises(InvalidManifestError):
            self._materialize(ws)
        self.assertEqual((ws / ".agents" / "squad.lock.json").read_text(encoding="utf-8"), "{corrupt-lock")

    # Group 8 / Scenario 7: Offline catalog importer & external pack preservation
    def test_scenario_7_offline_importer_workflows_and_external_preservation(self) -> None:
        root = self._tmp_root / "importer_case"
        packs_dir, spec_dir = root / "packs", root / "specialists"
        ext_manifest = _write_text(
            packs_dir / "capability-ui-design" / "pack.json",
            json.dumps({"id": "capability:ui-design", "family": "capability", "requires": [], "description": "External", "rules": [], "specialists": [], "skills": [], "workflows": []}),
        )
        ext_skill = _write_text(packs_dir / "capability-ui-design" / "skills" / "ui-ux-pro-max" / "SKILL.md", "SENTINEL_EXTERNAL_PACK_BYTES\n")
        ext_before = {ext_manifest: ext_manifest.read_bytes(), ext_skill: ext_skill.read_bytes()}

        def fake_fetcher(rel_url: str) -> str | None:
            if rel_url == "agents/code-explorer.md":
                return "---\nname: code-explorer\ndescription: Custom desc\n---\nBody text.\n"
            if rel_url == "agents/build-error-resolver.md" or rel_url.startswith("commands/"):
                return f"---\ndescription: {rel_url}\n---\nMock content for {rel_url}\n"
            return None

        out, err = io.StringIO(), io.StringIO()
        with (mock.patch("urllib.request.urlopen", side_effect=AssertionError("Network call forbidden in tests")),
              contextlib.redirect_stdout(out), contextlib.redirect_stderr(err)):
            pack_warnings = sdd_catalog_import.import_packs(fetcher=fake_fetcher, packs_dir=packs_dir)
            spec_warnings = sdd_catalog_import.import_specialists(fetcher=fake_fetcher, specialists_dir=spec_dir)

        self.assertGreater(len(pack_warnings), 0)
        self.assertEqual(len(spec_warnings), len(sdd_catalog_import.UNIVERSAL_SPECIALISTS) - 2)
        for path, expected_bytes in ext_before.items():
            self.assertEqual(path.read_bytes(), expected_bytes)

        total_wf = 0
        for pack_name, meta in sdd_catalog_import.STACK_PACKS.items():
            wf_dir = packs_dir / pack_name / "workflows"
            if meta["workflows"]:
                self.assertTrue(wf_dir.is_dir())
                for wf in meta["workflows"]:
                    self.assertIn(f"Mock content for {wf}", (wf_dir / pathlib.Path(wf).name).read_text(encoding="utf-8"))
                    total_wf += 1
            else:
                self.assertFalse(wf_dir.exists())
        self.assertEqual(total_wf, 22)
        self.assertIn("write: false", (spec_dir / "code-explorer.md").read_text(encoding="utf-8"))
        self.assertIn("write: true", (spec_dir / "build-error-resolver.md").read_text(encoding="utf-8"))

    # Group 9: Real workspace template sanity, catalog validity & modularity thresholds
    def test_real_template_sanitization_catalog_integrity_and_line_limits(self) -> None:
        lock = json.loads((ROOT_DIR / ".agents" / "squad.lock.json").read_text(encoding="utf-8"))
        self.assertEqual((lock["schema_version"], lock["gate00_approved"], lock["active_packs"]), (2, False, []))
        self.assertEqual(lock["builders"], ["back-engineer", "front-engineer"])
        self.assertEqual((len(lock["specialists"]), len(lock["files"])), (20, 22))
        for rel, meta in lock["files"].items():
            disk = ROOT_DIR / rel
            self.assertTrue(disk.is_file(), f"Lock file missing on disk: {rel}")
            self.assertEqual(hashlib.sha256(disk.read_bytes()).hexdigest(), meta["sha256"])

        agent_stems = sorted(p.stem for p in (ROOT_DIR / ".agents" / "agents").glob("*.md"))
        inbox_names = sorted(p.name for p in (ROOT_DIR / ".agent-inbox").iterdir() if p.is_dir())
        expected_agents = sorted([*sdd_agent_generator.CORE_AGENTS, *lock["builders"], *lock["specialists"]])
        self.assertEqual((agent_stems, inbox_names), (expected_agents, expected_agents))
        self.assertFalse((ROOT_DIR / ".agents" / "pack-rules").exists())

        cfg, effective = parse_stack_config(ROOT_DIR / "specs" / "STACK.md")
        self.assertFalse(effective)
        self.assertEqual((cfg.gate00_approved, cfg.preset, cfg.packs), (False, "compact", ()))

        registry = load_catalog_registry(ROOT_DIR / ".sdd" / "catalog" / "packs")
        self.assertTrue(set(sdd_catalog_import.STACK_PACKS.keys()).issubset(registry.keys()))
        for name, manifest in registry.items():
            resolved = resolve_pack_assets(manifest, ROOT_DIR / ".sdd" / "catalog" / "packs" / name)
            self.assertEqual(len(resolved.workflow_files), len(manifest.workflows))

        for rel in (
            "scripts/sdd_pack_registry.py", "scripts/sdd_agent_generator.py",
            "scripts/sdd_catalog_import.py", "scripts/sdd_sync.py", "tests/test_sdd_pack_materialization.py",
        ):
            lines = len((ROOT_DIR / rel).read_text(encoding="utf-8").splitlines())
            self.assertLessEqual(lines, 500, f"{rel} exceeds 500-line warning limit ({lines})")


if __name__ == "__main__":
    unittest.main()
