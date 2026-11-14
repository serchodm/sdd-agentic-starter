#!/usr/bin/env python3
"""Rigorous offline tests for FWK-006: Ownership compiler, TX generator, DAG & boundaries."""

from __future__ import annotations

import contextlib, io, json, pathlib, sys, tempfile, unittest
from collections.abc import Sequence
from unittest import mock

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
for p in (ROOT_DIR, ROOT_DIR / ".agents" / "scripts"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import sdd_healthcheck
import verify_architecture_boundaries as arch_verify
from scripts import sdd_agent_generator, sdd_dag, sdd_generator_tx
from scripts.sdd_dag import DagCycleError, DagError
from scripts.sdd_generator_tx import (
    DEFAULT_CORE_AGENTS, atomic_write_json, build_deterministic_lock_payload,
    compute_content_digest, is_generic_dod_placeholder, parse_verification_commands, resolve_builder_dod,
)
from scripts.sdd_ownership import (
    OwnershipError, compile_ownership_builders, detect_zone_overlaps, parse_ownership_map, validate_repo_coverage,
)
from scripts.sdd_pack_registry import (
    PackCompatibilityError, StackConfigError, parse_stack_config, parse_yaml_subset, resolve_active_packs,
)

_VERIF_YAML = (
    "\n### 2.5. Comandos\n```yaml sdd:verification-commands\n"
    "lint: uv run ruff check .\nunit_test: uv run pytest tests/unit -q\n"
    "integration_test: uv run pytest tests/integration -q\nbuild: npm run build\n"
    "infra: alembic check\nbuilders:\n  custom-worker: uv run pytest tests/worker -q\n```\n"
)


def _w(path: pathlib.Path, text: str) -> pathlib.Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _snap(root: pathlib.Path) -> dict[str, bytes]:
    if not root.exists():
        return {}
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in sorted(root.rglob("*")) if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"
    }


def _stack(*, approved: bool = True, preset: str = "compact", packs: Sequence[str] = (),
           verif: str = _VERIF_YAML, ownership: str = "", extra_cfg: str = "") -> str:
    sign = "[x] Gate S0 Approved" if approved else "[ ] Gate S0 Approved"
    return (
        f"# Stack\n\n> **ESTADO:** `{sign} (Human Sign-off)`\n\n"
        f"```yaml sdd:stack-config\nstack_approved: {str(approved).lower()}\npreset: {preset}\n"
        f"packs: {json.dumps(list(packs))}\n{extra_cfg}```\n{verif}{ownership}"
    )


def _add_dummy_pack(packs_dir: pathlib.Path, name: str, *, pack_id: str | None = None, family: str = "language",
                    requires: Sequence[str] = (), targets: Sequence[str] = ()) -> None:
    pdir = packs_dir / name
    agent = f"{name.split('-', 1)[-1]}-helper"
    _w(pdir / "agents" / f"{agent}.md", f"---\nname: {agent}\nmode: subagent\n---\n{agent}\n")
    manifest: dict[str, object] = {
        "id": pack_id or name.replace("-", ":", 1), "family": family, "requires": list(requires),
        "description": name, "rules": [], "specialists": [f"agents/{agent}.md"], "skills": [], "workflows": [],
    }
    if targets:
        manifest["targets"] = list(targets)
    _w(pdir / "pack.json", json.dumps(manifest, indent=2))


def _run_gen(ws: pathlib.Path, argv: Sequence[str]) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with (mock.patch.object(sdd_agent_generator, "ROOT_DIR", ws),
          mock.patch.object(sys, "argv", ["sdd_agent_generator.py", *argv]),
          contextlib.redirect_stdout(out), contextlib.redirect_stderr(err)):
        code = sdd_agent_generator.main()
    return code, out.getvalue(), err.getvalue()


def _run_arch(ws: pathlib.Path) -> tuple[int, str]:
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        return arch_verify.main(["--repo-root", str(ws)]), out.getvalue()


class _WorkspaceMixin:
    _tmp_ctx: tempfile.TemporaryDirectory[str]
    _tmp_root: pathlib.Path
    _seq: int = 0

    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp_ctx = tempfile.TemporaryDirectory()
        cls._tmp_root = pathlib.Path(cls._tmp_ctx.name)

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp_ctx.cleanup()

    def _ws(self, stack_md: str, *, with_core: bool = False, packs: Sequence[str] = ()) -> pathlib.Path:
        type(self)._seq += 1
        ws = self._tmp_root / f"ws_{type(self)._seq}"
        _w(ws / "specs" / "STACK.md", stack_md)
        if with_core:
            for c in DEFAULT_CORE_AGENTS:
                _w(ws / ".agents" / "agents" / f"{c}.md", f"---\nname: {c}\n---\nCore agent {c}.\n")
        if packs:
            pdir = ws / ".sdd" / "catalog" / "packs"
            pdir.mkdir(parents=True, exist_ok=True)
            for name in packs:
                req = ("lang:python",) if name == "framework-fastapi" else ()
                fam = "framework" if name.startswith("framework-") else ("capability" if name.startswith("capability-") else "language")
                _add_dummy_pack(pdir, name, family=fam, requires=req)
        return ws


class TestOwnershipAndBoundaryEnforcement(_WorkspaceMixin, unittest.TestCase):
    """AUD-001: sdd:ownership-map compiler, overlaps, coverage, AST forbid_imports & coherence."""

    def test_ownership_map_compiles_custom_builders_and_coherence(self) -> None:
        own = (
            "\n```yaml sdd:ownership-map\nunowned_policy: error\nzones:\n"
            "  - id: domain-core\n    owner: \"@back-domain\"\n    archetype: layer-domain\n"
            "    paths: [\"src/{domain,shared}/**/*.py\"]\n    dod: unit_test\n    forbid_imports: [\"fastapi\", \"sqlalchemy\"]\n"
            "  - id: ui-surface\n    builder: front-ui\n    archetype: front-ui\n"
            "    zone_paths: [\"src/ui/**\"]\n    dod: build\n    forbid_imports: [\"src.backend\"]\n"
            "  - id: worker-jobs\n    owner: custom-worker\n    paths: [\"src/worker/**\"]\n```\n"
        )
        ws = self._ws(_stack(ownership=own), with_core=True)
        _w(ws / "src" / "domain" / "model.py", "class Entity: pass\n")
        _w(ws / "src" / "ui" / "view.tsx", "export const View = () => null;\n")
        _w(ws / "src" / "worker" / "job.py", "def run(): return 1\n")

        cfg = parse_ownership_map(ws / "specs" / "STACK.md")
        assert cfg is not None
        compiled = compile_ownership_builders(cfg, {"unit_test": "pytest -q", "build": "npm run build"})
        self.assertEqual([b["name"] for b in compiled], ["back-domain", "front-ui", "custom-worker"])

        lock = sdd_agent_generator.materialize_squad(repo_root=ws)
        self.assertEqual(lock["builders"], ["back-domain", "custom-worker", "front-ui"])
        self.assertFalse((ws / ".agents" / "agents" / "back-engineer.md").exists())
        self.assertEqual(sdd_agent_generator.verify_squad(repo_root=ws), [])

        dom_md = (ws / ".agents" / "agents" / "back-domain.md").read_text(encoding="utf-8")
        wrk_md = (ws / ".agents" / "agents" / "custom-worker.md").read_text(encoding="utf-8")
        for tok in (sdd_agent_generator.GENERATED_MARKER, "`src/{domain,shared}/**/*.py`", "uv run pytest tests/unit -q", "fastapi, sqlalchemy"):
            self.assertIn(tok, dom_md)
        self.assertIn("uv run pytest tests/worker -q", wrk_md)
        self.assertEqual(_run_arch(ws)[0], 0)

        for bad_own in (
            "\n```yaml sdd:ownership-map\nzones:\n  - id: z1\n    owner: a\n    archetype: tier-backend\n    paths: [\"src/a/**\"]\n  - id: z2\n    owner: a\n    archetype: layer-domain\n    paths: [\"src/b/**\"]\n```\n",
            "\n```yaml sdd:ownership-map\nzones:\n  - id: z1\n    owner: a\n    builder: b\n    paths: [\"src/a/**\"]\n```\n",
            "\n```yaml sdd:ownership-map\nzones:\n  - id: z1\n    owner: a\n    paths: [\"../escape/**\"]\n```\n",
            "\n```yaml sdd:ownership-map\nzones:\n  - id: z1\n    owner: a\n    paths: [\"/etc/passwd\"]\n```\n",
        ):
            bad_ws = self._ws(_stack(ownership=bad_own))
            with self.assertRaises(OwnershipError):
                cfg_bad = parse_ownership_map(bad_ws / "specs" / "STACK.md")
                assert cfg_bad is not None
                compile_ownership_builders(cfg_bad)

    def test_zone_overlap_detection_and_unowned_policy_enforcement(self) -> None:
        for p1, p2 in (("src/**", "src/backend/**"), ("src/*/api/*.py", "src/v1/**/*.py"), ("src/a?.py", "src/ab.py"), ("src/{api,web}/**", "src/web/routes/**")):
            with self.subTest(p1=p1, p2=p2):
                own = f"\n```yaml sdd:ownership-map\nzones:\n  z1:\n    owner: back-a\n    paths: [{json.dumps(p1)}]\n  z2:\n    owner: back-b\n    paths: [{json.dumps(p2)}]\n```\n"
                ws_ov = self._ws(_stack(ownership=own))
                cfg = parse_ownership_map(ws_ov / "specs" / "STACK.md")
                assert cfg is not None
                with self.assertRaises(OwnershipError):
                    detect_zone_overlaps(cfg)
                with self.assertRaises(OwnershipError):
                    sdd_agent_generator.materialize_squad(repo_root=ws_ov)
                self.assertFalse((ws_ov / ".agents").exists())
                code, out = _run_arch(ws_ov)
                self.assertEqual(code, 1)
                self.assertIn("[Ownership Overlap Error]", out)

        for policy in ("error", "fail-closed"):
            ws_err = self._ws(_stack(ownership=f"\n```yaml sdd:ownership-map\nunowned_policy: {policy}\nzones:\n  z1:\n    owner: back-a\n    paths: [\"src/owned/**\"]\n```\n"))
            _w(ws_err / "src" / "owned" / "ok.py", "X = 1\n")
            _w(ws_err / "src" / "rogue" / "orphan.py", "Y = 2\n")
            cfg_e = parse_ownership_map(ws_err / "specs" / "STACK.md")
            assert cfg_e is not None
            with self.assertRaises(OwnershipError):
                validate_repo_coverage(cfg_e, ws_err)
            with self.assertRaises(OwnershipError):
                sdd_agent_generator.materialize_squad(repo_root=ws_err)
            code, out = _run_arch(ws_err)
            self.assertEqual((code, "src/rogue/orphan.py" in out, "[Ownership Coverage Error]" in out), (1, True, True))

        ws_warn = self._ws(_stack(ownership="\n```yaml sdd:ownership-map\nunowned_policy: warn\nzones:\n  z1:\n    owner: back-a\n    paths: [\"src/owned/**\"]\n```\n"))
        _w(ws_warn / "src" / "owned" / "ok.py", "X = 1\n")
        _w(ws_warn / "DDBB" / "untracked.sql", "SELECT 1;\n")
        code_gen, _, err_gen = _run_gen(ws_warn, ["--materialize"])
        self.assertEqual(code_gen, 0, err_gen)
        self.assertIn("DDBB/untracked.sql", err_gen)
        code_arch, out_arch = _run_arch(ws_warn)
        self.assertEqual((code_arch, "[Ownership Coverage Warning]" in out_arch), (0, True))

    def test_ast_forbid_imports_normal_relative_and_dynamic(self) -> None:
        own = (
            "\n```yaml sdd:ownership-map\nunowned_policy: error\nzones:\n"
            "  backend-domain:\n    owner: back-domain\n    paths: [\"src/backend/domain/**\"]\n"
            "    forbid_imports: [\"fastapi\", \"sqlalchemy\", \"backend.infrastructure\"]\n"
            "  backend-api:\n    owner: back-api\n    paths: [\"src/backend/api/**\"]\n    forbid_imports: [\"sqlalchemy\"]\n```\n"
        )
        ws = self._ws(_stack(ownership=own))
        _w(ws / "src" / "backend" / "domain" / "clean.py", "from dataclasses import dataclass\n@dataclass\nclass Item:\n    id: int\n")
        _w(ws / "src" / "backend" / "api" / "routes.py", "import fastapi\napp = fastapi\n")
        self.assertEqual(_run_arch(ws)[0], 0)

        _w(
            ws / "src" / "backend" / "domain" / "bad_imports.py",
            "import importlib\nimport fastapi\nfrom sqlalchemy.orm import Session\n"
            "from . import fastapi as rel_f\nfrom backend import infrastructure\n"
            "m1 = importlib.import_module('fastapi')\nm2 = __import__('sqlalchemy')\n",
        )
        errors, _ = arch_verify.run_boundary_audit(ws)
        joined = "\n".join(errors)
        for token in ("fastapi", "sqlalchemy", "backend.infrastructure", "dynamically imports"):
            self.assertIn(token, joined)
        zone_errs = [e for e in errors if "[Zone:backend-domain (@back-domain) Boundary Violation]" in e]
        self.assertEqual(len(zone_errs), 6, zone_errs)
        self.assertFalse(any("routes.py" in e for e in errors))
        self.assertEqual(_run_arch(ws)[0], 1)


class TestTxGeneratorLifecycleAndCompatibility(_WorkspaceMixin, unittest.TestCase):
    """AUD-002..005, 012..014: Rematerialize, strict agents, drain, sanitize, compat, lock, rollback, verify."""

    def test_granular_to_compact_rematerialization_strict_agents_and_inbox_drain(self) -> None:
        ws = self._ws(_stack(preset="granular"), with_core=True)
        self.assertEqual(_run_gen(ws, ["--materialize"])[0], 0)
        granular = ("back-domain", "back-infra", "back-api", "db-specialist", "back-test", "front-logic", "front-ui", "front-test")
        for g in granular:
            self.assertTrue((ws / ".agents" / "agents" / f"{g}.md").is_file())
            self.assertTrue((ws / ".agent-inbox" / g / ".gitkeep").is_file())
        self.assertEqual(_run_gen(ws, ["--verify"])[0], 0)

        rogue = _w(ws / ".agents" / "agents" / "rogue-agent.md", "---\nname: rogue-agent\n---\nRogue.\n")
        code_strict, _, err_strict = _run_gen(ws, ["--materialize", "--strict-agents"])
        self.assertEqual((code_strict, "rogue-agent.md" in err_strict), (1, True))
        rogue.unlink()

        t1 = _w(ws / ".agent-inbox" / "back-domain" / "TASK-101.md", "Domain ticket payload\n")
        t2 = _w(ws / ".agent-inbox" / "front-ui" / "TASK-101.md", "UI collision ticket payload\n")
        _w(ws / "specs" / "STACK.md", _stack(preset="compact"))
        snap_before = _snap(ws / ".agents")
        code_fail, _, err_fail = _run_gen(ws, ["--materialize"])
        self.assertEqual((code_fail, "--drain-inboxes" in err_fail), (1, True))
        self.assertTrue(t1.is_file() and t2.is_file())
        self.assertEqual(_snap(ws / ".agents"), snap_before)

        code_ok, _, err_ok = _run_gen(ws, ["--materialize", "--drain-inboxes", "orchestrator"])
        self.assertEqual((code_ok, err_ok), (0, ""))
        for g in granular:
            self.assertFalse((ws / ".agents" / "agents" / f"{g}.md").exists())
            self.assertFalse((ws / ".agent-inbox" / g).exists())
        for c in ("back-engineer", "front-engineer"):
            self.assertTrue((ws / ".agents" / "agents" / f"{c}.md").is_file())
        self.assertEqual(
            sorted(p.read_text(encoding="utf-8") for p in (ws / ".agent-inbox" / "orchestrator").glob("*TASK-101.md")),
            ["Domain ticket payload\n", "UI collision ticket payload\n"],
        )
        self.assertEqual(_run_gen(ws, ["--verify"])[0], 0)

    def test_markdown_sanitization_bom_booleans_and_pack_compatibility(self) -> None:
        commented = (
            "\ufeff# Stack\n<!--\n[x] Gate S0 Approved\n"
            "```yaml sdd:stack-config\nstack_approved: true\npreset: api-only\npacks: [\"lang-java\"]\n```\n"
            "```yaml sdd:ownership-map\nzones: []\n```\n"
            "```yaml sdd:verification-commands\nunit_test: bad / cmd\n```\n-->\n"
            "~~[x] Gate S0 Approved~~ [ej: [x] Gate S0 Approved]\n```yaml\n[x] Gate S0 Approved\n```\n"
            "```yaml sdd:stack-config\nstack_approved: TRUE\ngate00_approved: True\n"
            "preset: compact\npacks: [\"lang-python\"]\nuiux:\n  enabled: False\n```\n" + _VERIF_YAML
        )
        p_unsigned = _w(self._tmp_root / "bom_unsigned.md", commented)
        cfg_u, eff_u = parse_stack_config(p_unsigned)
        self.assertEqual((eff_u, cfg_u.stack_approved, cfg_u.uiux), (False, True, {"enabled": False}))
        self.assertIsNone(parse_ownership_map(p_unsigned))
        self.assertEqual(parse_verification_commands(p_unsigned).unit_test, "uv run pytest tests/unit -q")

        p_signed = _w(self._tmp_root / "bom_signed.md", commented.replace("~~[x] Gate S0 Approved~~", "[x] Gate S0 Approved"))
        cfg_s, eff_s = parse_stack_config(p_signed)
        self.assertTrue(eff_s and cfg_s.stack_approved is True)
        self.assertEqual(parse_yaml_subset("a: TRUE\nb: False\nc: True\n"), {"a": True, "b": False, "c": True})

        ws = self._ws(_stack(preset="api-only", packs=[]), packs=("lang-python", "framework-fastapi", "capability-web-frontend"))
        _add_dummy_pack(ws / ".sdd" / "catalog" / "packs", "lang-sql", pack_id="lang:sql")
        _add_dummy_pack(ws / ".sdd" / "catalog" / "packs", "mobile-kit", pack_id="cap:mobile", family="capability", targets=("mobile",))
        for cli_pack in ("capability-web-frontend", "mobile-kit"):
            code, _, err = _run_gen(ws, ["--materialize", "--packs", cli_pack])
            self.assertEqual((code, "incompatible" in err.lower()), (1, True))
        for doc in (_stack(preset="api-only", extra_cfg="uiux:\n  enabled: true\n"), _stack(preset="api-only", packs=["capability-web-frontend"]),
                    _stack(preset="spa-only", packs=["lang-python", "framework-fastapi"]), _stack(preset="spa-only", packs=["lang-sql"])):
            with self.assertRaises(PackCompatibilityError):
                c, e = parse_stack_config(_w(self._tmp_root / f"compat_{hash(doc)}.md", doc))
                resolve_active_packs(c, e, None, ws / ".sdd" / "catalog" / "packs")
        c_spa, e_spa = parse_stack_config(_w(self._tmp_root / "spa_cli.md", _stack(preset="spa-only", packs=[])))
        with self.assertRaises(PackCompatibilityError):
            resolve_active_packs(c_spa, e_spa, ["lang-sql"], ws / ".sdd" / "catalog" / "packs")

    def test_deterministic_lock_rollback_on_oserror_and_readonly_verify_tampering(self) -> None:
        kw = dict(stack_approved=True, preset="compact", tech_stack="Py", timestamp="2026-01-01T00:00:00+00:00")
        p1 = build_deterministic_lock_payload(
            core_agents=["qa-tester", "architect"], builders=["front-engineer", "back-engineer"], specialists=["z", "a"],
            active_packs=[{"name": "b", "id": "b:1", "source": "manual"}, {"name": "a", "id": "a:1", "source": "stack-config"}],
            files={"z.md": {"sha256": "a" * 64, "owner": "x", "kind": "agent"}, "a.md": {"sha256": "b" * 64, "owner": "y", "kind": "agent"}}, **kw,
        )
        p2 = build_deterministic_lock_payload(
            core_agents=["architect", "qa-tester"], builders=["back-engineer", "front-engineer"], specialists=["a", "z"],
            active_packs=[{"name": "a", "id": "a:1", "source": "stack-config"}, {"name": "b", "id": "b:1", "source": "manual"}],
            files={"a.md": {"sha256": "b" * 64, "owner": "y", "kind": "agent"}, "z.md": {"sha256": "a" * 64, "owner": "x", "kind": "agent"}}, **kw,
        )
        self.assertEqual((p1, p1["content_digest"], list(p1["files"])), (p2, compute_content_digest(p1), ["a.md", "z.md"]))

        ws = self._ws(_stack(preset="compact", packs=["lang-python"]), with_core=True, packs=("lang-python",))
        self.assertEqual(_run_gen(ws, ["--materialize"])[0], 0)
        lock1 = json.loads((ws / ".agents" / "squad.lock.json").read_text(encoding="utf-8"))
        lock_bytes1 = (ws / ".agents" / "squad.lock.json").read_bytes()
        self.assertEqual(_run_gen(ws, ["--materialize"])[0], 0)
        lock2 = json.loads((ws / ".agents" / "squad.lock.json").read_text(encoding="utf-8"))
        self.assertEqual((lock1["content_digest"], lock1["timestamp"], lock_bytes1), (lock2["content_digest"], lock2["timestamp"], (ws / ".agents" / "squad.lock.json").read_bytes()))

        _w(ws / "specs" / "STACK.md", _stack(preset="granular", packs=[]))
        snap_ag, snap_in = _snap(ws / ".agents"), _snap(ws / ".agent-inbox")
        with mock.patch.object(sdd_generator_tx, "atomic_write_json", side_effect=OSError("Simulated disk full")):
            with self.assertRaises(OSError):
                sdd_agent_generator.materialize_squad(repo_root=ws)
        self.assertEqual((_snap(ws / ".agents"), _snap(ws / ".agent-inbox")), (snap_ag, snap_in))

        orig_wb, calls = pathlib.Path.write_bytes, 0
        def _boom_write(self_p: pathlib.Path, data: bytes) -> int:
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("Mid-write failure")
            return orig_wb(self_p, data)
        with mock.patch.object(pathlib.Path, "write_bytes", _boom_write), self.assertRaises(OSError):
            sdd_agent_generator.materialize_squad(repo_root=ws)
        self.assertEqual((_snap(ws / ".agents"), _snap(ws / ".agent-inbox")), (snap_ag, snap_in))

        _w(ws / "specs" / "STACK.md", _stack(preset="compact", packs=["lang-python"]))
        self.assertEqual(_run_gen(ws, ["--verify"])[0], 0)
        for target_path in (ws / ".agents" / "agents" / "back-engineer.md", ws / ".agents" / "agents" / "orchestrator.md"):
            orig = target_path.read_bytes()
            target_path.write_bytes(orig + b" ")
            tampered_snap = _snap(ws / ".agents")
            code, _, err = _run_gen(ws, ["--verify"])
            self.assertEqual((code, "Hash mismatch" in err, _snap(ws / ".agents")), (1, True, tampered_snap))
            target_path.write_bytes(orig)

        orig_lock = (ws / ".agents" / "squad.lock.json").read_bytes()
        atomic_write_json(ws / ".agents" / "squad.lock.json", {**lock1, "content_digest": "0" * 64})
        code_l, _, err_l = _run_gen(ws, ["--verify"])
        self.assertEqual((code_l, "content_digest" in err_l), (1, True))
        (ws / ".agents" / "squad.lock.json").write_bytes(orig_lock)

    def test_aud005_dod_placeholder_rejection_and_sec25_resolution(self) -> None:
        for ph in ("dotnet test / pytest / npm test", "migration check", "[ej: pytest]", "pytest <path/to/test.py>", "[comando]", "TBD", ""):
            self.assertTrue(is_generic_dod_placeholder(ph), ph)
            with self.assertRaises(StackConfigError):
                resolve_builder_dod("back-engineer", ph, None, gate_s0_approved=True)
            self.assertEqual(resolve_builder_dod("back-engineer", ph, None, gate_s0_approved=False), ph)

        bad_sec25 = _w(self._tmp_root / "bad_sec25.md", _stack(verif="\n```yaml sdd:verification-commands\nunit_test: \"[ej: pytest]\"\n```\n"))
        with self.assertRaises(StackConfigError):
            parse_verification_commands(bad_sec25)

        ws_no_25 = self._ws(_stack(verif=""))
        with self.assertRaises(StackConfigError):
            sdd_agent_generator.materialize_squad(repo_root=ws_no_25)
        self.assertFalse((ws_no_25 / ".agents").exists())

        cmds = parse_verification_commands(_w(self._tmp_root / "ok_sec25.md", _stack()))
        self.assertEqual(resolve_builder_dod("db-specialist", "migration check", cmds, gate_s0_approved=True), "alembic check")
        self.assertEqual(resolve_builder_dod("front-ui", "npm run build", cmds, gate_s0_approved=True), "npm run build")
        self.assertEqual(resolve_builder_dod("back-infra", "test", cmds, gate_s0_approved=True), "uv run pytest tests/integration -q")
        self.assertEqual(resolve_builder_dod("custom-worker", "test", cmds, gate_s0_approved=True), "uv run pytest tests/worker -q")


class TestDagAndInboxStateEngine(_WorkspaceMixin, unittest.TestCase):
    """AUD-015: 03-tasks.md DAG waves, cycles/dangling errors, healthcheck & inbox transitions."""

    def _run_dag_cli(self, argv: Sequence[str]) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            return sdd_dag.main(list(argv)), out.getvalue(), err.getvalue()

    def test_dag_parallel_sequential_waves_and_cli_plan_json(self) -> None:
        tasks_md = _w(
            self._tmp_root / "dag_valid" / "03-tasks.md",
            "\ufeff# Tasks\n<!-- - [ ] T99: Commented cycle [Depends on: T99] -->\n"
            "```markdown\n- [ ] T98: Fenced [Depends on: T98]\n```\n"
            "## Bloque 1 [PARALLEL]\n- [ ] T1 (@back-domain): Domain entity\n- [ ] T2 (@front-logic): Client store\n\n"
            "## Bloque 2 [SEQUENTIAL]\n- [ ] T3 (@back-api): Endpoint\n- [ ] T4 (@front-ui): View\n  - Depends on: T3\n\n"
            "## Bloque 3 [PARALLEL: Requiere Bloque 2]\n- [ ] T5 (@qa-tester): E2E verification\n",
        )
        plan = sdd_dag.build_and_validate_dag(sdd_dag.parse_tasks_markdown(tasks_md))
        self.assertEqual([[t.task_id for t in w] for w in plan.waves], [["T1", "T2"], ["T3"], ["T4"], ["T5"]])
        self.assertEqual(plan.order, ("T1", "T2", "T3", "T4", "T5"))

        c_v, out_v, err_v = self._run_dag_cli(["--verify", str(tasks_md)])
        self.assertEqual((c_v, err_v, "DAG OK: 5 task(s) across 4 wave(s)." in out_v), (0, "", True))
        c_p, out_p, _ = self._run_dag_cli(["--plan", str(tasks_md), "--format", "json"])
        payload = json.loads(out_p)
        self.assertEqual((c_p, payload["task_count"], payload["wave_count"], payload["waves"]), (0, 5, 4, [["T1", "T2"], ["T3"], ["T4"], ["T5"]]))

    def test_dag_cycle_and_dangling_dependency_fail_cli_and_healthcheck(self) -> None:
        cyc2 = _w(self._tmp_root / "dag_c2" / "03-tasks.md", "- [ ] T1: A\n  - Depends on: T2\n- [ ] T2: B\n  - Depends on: T1\n")
        with self.assertRaises(DagCycleError) as ctx2:
            sdd_dag.build_and_validate_dag(sdd_dag.parse_tasks_markdown(cyc2))
        self.assertGreaterEqual(len(ctx2.exception.cycle), 2)
        c_cyc, _, err_cyc = self._run_dag_cli(["--verify", str(cyc2)])
        self.assertEqual((c_cyc, "[DAG ERROR]" in err_cyc), (1, True))

        for name, body in (("dang", "- [ ] T1: Ok\n- [ ] T2: Bad\n  - Depends on: T99\n"), ("dup", "- [ ] T1: A\n- [ ] T1: B\n")):
            p = _w(self._tmp_root / f"dag_{name}" / "03-tasks.md", body)
            with self.assertRaises(DagError):
                sdd_dag.build_and_validate_dag(sdd_dag.parse_tasks_markdown(p))
            self.assertEqual(self._run_dag_cli(["--verify", str(p)])[0], 1)

        ws = self._tmp_root / "hc_dag_ws"
        _w(ws / "specs" / "BACKLOG.md", "| ID | Nombre | Estado |\n| :--- | :--- | :--- |\n| FEAT-001 | Demo | In Progress |\n")
        _w(ws / "specs" / "features" / "FEAT-001-demo" / "01-spec.md", "# Spec\n")
        _w(ws / "specs" / "features" / "FEAT-001-demo" / "02-tech-spec.md", "# Tech\n")
        _w(ws / "specs" / "features" / "FEAT-001-demo" / "03-tasks.md", "- [ ] T1: A [Depends on: T2]\n- [ ] T2: B [Depends on: T1]\n")
        _w(ws / "specs" / "features" / "FEAT-002-prose" / "03-tasks.md", "# Prose-only tasks doc without IDs\n")
        dag_errs = sdd_healthcheck.check_task_dags(ws / "specs")
        self.assertEqual((len(dag_errs), "[SDD DAG Error]" in dag_errs[0], "FEAT-001-demo/03-tasks.md" in dag_errs[0]), (1, True, True))
        self.assertTrue(any("[SDD DAG Error]" in e for e in sdd_healthcheck.check_spec_triads(ws / "specs", ws / "specs" / "BACKLOG.md")))

    def test_inbox_transitions_block_unmet_deps_and_sync_markdown(self) -> None:
        ws = self._tmp_root / "inbox_dag_ws"
        tasks_md = _w(ws / "specs" / "features" / "FEAT-010-flow" / "03-tasks.md", "- [ ] T1 (@back-engineer): Build service\n- [ ] T2 (@front-engineer): Wire UI\n  - Depends on: T1\n")
        inbox = ws / ".agent-inbox"
        (inbox / "back-engineer").mkdir(parents=True, exist_ok=True)
        (inbox / "front-engineer").mkdir(parents=True, exist_ok=True)

        with self.assertRaises(DagError):
            sdd_dag.advance_inbox_task(tasks_md, "T2", "in_progress", inbox_root=inbox)
        self.assertFalse((inbox / "front-engineer" / "T2.md").exists())
        with self.assertRaises(DagError):
            sdd_dag.advance_inbox_task(tasks_md, "T1", "done", inbox_root=inbox)

        t1_prog = sdd_dag.advance_inbox_task(tasks_md, "T1", "in_progress", inbox_root=inbox)
        self.assertEqual((t1_prog.state, t1_prog.previous_state), ("in_progress", "pending"))
        with self.assertRaises(DagError):
            sdd_dag.advance_inbox_task(tasks_md, "T2", "in_progress", inbox_root=inbox)

        t1_done = sdd_dag.advance_inbox_task(tasks_md, "T1", "done", inbox_root=inbox, note="Verified")
        self.assertEqual((t1_done.state, t1_done.previous_state), ("done", "in_progress"))
        self.assertIn("- [x] T1 (@back-engineer): Build service", tasks_md.read_text(encoding="utf-8"))
        self.assertIn("- **Estado**: done", t1_done.ticket_path.read_text(encoding="utf-8"))
        with self.assertRaises(DagError):
            sdd_dag.update_inbox_ticket(t1_done.ticket_path, "in_progress", tasks_path=tasks_md, inbox_root=inbox)

        t2_prog = sdd_dag.advance_inbox_task(tasks_md, "T2", "in_progress", inbox_root=inbox)
        t2_done = sdd_dag.advance_inbox_task(tasks_md, "T2", "done", inbox_root=inbox)
        self.assertEqual((t2_prog.state, t2_done.state), ("in_progress", "done"))
        self.assertIn("- [x] T2 (@front-engineer): Wire UI", tasks_md.read_text(encoding="utf-8"))

        outside = _w(ws / "outside_ticket.md", "# T1\n- **Estado**: pending\n")
        with self.assertRaises(DagError):
            sdd_dag.update_inbox_ticket(outside, "in_progress", tasks_path=tasks_md, inbox_root=inbox)

    def test_fwk006_modularity_line_limits_strictly_under_500(self) -> None:
        for rel in (
            "scripts/sdd_ownership.py", "scripts/sdd_stack_parser.py", "scripts/sdd_generator_tx.py",
            "scripts/sdd_agent_generator.py", "scripts/sdd_pack_registry.py", "scripts/sdd_dag.py",
            ".agents/scripts/verify_architecture_boundaries.py", ".agents/scripts/sdd_healthcheck.py",
            "tests/test_sdd_pack_materialization.py", "tests/test_sdd_ui_design.py", "tests/test_sdd_ownership_dag.py",
        ):
            lines = len((ROOT_DIR / rel).read_text(encoding="utf-8").splitlines())
            self.assertLessEqual(lines, 500, f"{rel} exceeds 500 lines ({lines})")


if __name__ == "__main__":
    unittest.main()
