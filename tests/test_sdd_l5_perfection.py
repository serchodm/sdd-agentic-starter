#!/usr/bin/env python3
"""Deterministic unit tests for FWK-010 L5 Perfection Hardening (RF-1001..RF-1004)."""

from __future__ import annotations

import contextlib
import inspect
import io
import json
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
for _p in (str(ROOT_DIR), str(ROOT_DIR / "scripts"), str(ROOT_DIR / ".agents" / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import sdd_ci  # noqa: E402
import sdd_code_gate_guard  # noqa: E402
import sdd_dag  # noqa: E402
import sdd_gate_seal  # noqa: E402
import verify_architecture_boundaries as arch_bounds  # noqa: E402


def _write(path: pathlib.Path, content: str) -> pathlib.Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content.encode("utf-8"))
    return path


def _seed_approved_workspace(base: pathlib.Path) -> tuple[pathlib.Path, pathlib.Path]:
    _write(
        base / "specs" / "STACK.md",
        "# Stack\n\n- [x] Gate S0 Approved (Authorized by PO on 2026-11-15)\n",
    )
    _write(
        base / "specs" / "BACKLOG.md",
        "| ID | Tipo | Titulo | Gate 0 | Estado |\n|---|---|---|---|---|\n| `FEAT-001` | Feature | Auth | [x] | In Progress |\n",
    )
    spec_dir = base / "specs" / "features" / "FEAT-001-auth"
    _write(
        spec_dir / "01-spec.md",
        "# Spec FEAT-001\n\n- [x] Gate 1 Approved\n\nWHEN user logs in, THE SYSTEM SHALL issue a JWT token.\n",
    )
    _write(
        spec_dir / "02-tech-spec.md",
        "# Tech Spec FEAT-001\n\n- [x] Gate 2 Approved\n\nEndpoint POST /api/v1/login returns 200 OK with token.\n",
    )
    _write(
        spec_dir / "03-tasks.md",
        "# Tasks FEAT-001\n\n- [x] Gate 3 Approved\n\n- [ ] `T1.1` [`@back-engineer`]: Implement login\n",
    )
    _write(
        base / ".agents" / "active_work_item.json",
        json.dumps(
            {
                "active_work_item_id": "FEAT-001-auth",
                "spec_dir": "specs/features/FEAT-001-auth",
                "status": "IN_PROGRESS",
                "gate_1_approved": True,
                "gate_2_approved": True,
                "gate_3_approved": True,
                "approved_by_human": True,
            },
            indent=2,
        ),
    )
    return base, spec_dir


def _run_code_gate_guard(repo_root: pathlib.Path, rel_target: str, content: str = "x = 1\n") -> dict:
    payload = {"tool_name": "write_file", "tool_input": {"Path": rel_target, "Content": content}}
    buf = io.StringIO()
    with (
        mock.patch.object(sdd_code_gate_guard, "get_repo_root", return_value=repo_root),
        mock.patch.object(sdd_code_gate_guard, "read_hook_payload", return_value=payload),
        contextlib.redirect_stdout(buf),
    ):
        sdd_code_gate_guard.main()
    return json.loads(buf.getvalue().strip())


class TestGateCryptographicSeal(unittest.TestCase):
    """RF-1001: Cryptographic SHA-256 Gate Seals & Tamper Detection."""

    def test_seal_and_verify_gates_roundtrip_and_inline_embedding(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ws, spec_dir = _seed_approved_workspace(pathlib.Path(tmp))
            raw_02 = (spec_dir / "02-tech-spec.md").read_text(encoding="utf-8")
            digest_lf = sdd_gate_seal.compute_gate_doc_sha256(raw_02)
            digest_crlf = sdd_gate_seal.compute_gate_doc_sha256(raw_02.replace("\n", "\r\n"))
            self.assertEqual(digest_lf, digest_crlf)

            seals = sdd_gate_seal.seal_work_item_gates(ws, embed_inline=True)
            self.assertEqual(set(seals.keys()), {"1", "2", "3"})
            self.assertEqual(seals["2"], digest_lf)

            for gate_num, fname in ((1, "01-spec.md"), (2, "02-tech-spec.md"), (3, "03-tasks.md")):
                embedded_text = (spec_dir / fname).read_text(encoding="utf-8")
                self.assertIn(f"<!-- sdd:gate-seal gate={gate_num} sha256=", embedded_text)
                self.assertEqual(sdd_gate_seal.compute_gate_doc_sha256(embedded_text), seals[str(gate_num)])
                self.assertEqual(sdd_gate_seal.extract_inline_gate_seal(embedded_text, gate_num), seals[str(gate_num)])

            ok, msg = sdd_gate_seal.verify_work_item_gate_seals(ws, require_seals=True)
            self.assertTrue(ok, msg)
            self.assertEqual(msg, "OK")
            decision = _run_code_gate_guard(ws, "src/app.py")
            self.assertEqual(decision["decision"], "allow")

    def test_post_approval_tampering_blocks_code_gate_guard(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ws, spec_dir = _seed_approved_workspace(pathlib.Path(tmp))
            sdd_gate_seal.seal_work_item_gates(ws, embed_inline=True)

            tech_path = spec_dir / "02-tech-spec.md"
            tampered = tech_path.read_text(encoding="utf-8").replace("200 OK", "201 Created")
            self.assertIn("[x] Gate 2 Approved", tampered)
            _write(tech_path, tampered)

            ok, msg = sdd_gate_seal.verify_work_item_gate_seals(ws)
            self.assertFalse(ok)
            self.assertIn("SDD Gate Cryptographic Seal Violation", msg)
            self.assertIn("02-tech-spec.md", msg)

            decision = _run_code_gate_guard(ws, "src/app.py")
            self.assertEqual(decision["decision"], "deny")
            self.assertIn("SDD Gate Cryptographic Seal Violation", decision["reason"])

    def test_malformed_inline_seal_and_missing_required_seal_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ws, spec_dir = _seed_approved_workspace(pathlib.Path(tmp))
            ok_req, msg_req = sdd_gate_seal.verify_work_item_gate_seals(ws, require_seals=True)
            self.assertFalse(ok_req)
            self.assertIn("Missing SHA-256 seal for Gate 1", msg_req)

            state_path = ws / ".agents" / "active_work_item.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["enforce_gate_seals"] = True
            _write(state_path, json.dumps(state))
            decision_missing = _run_code_gate_guard(ws, "src/app.py")
            self.assertEqual(decision_missing["decision"], "deny")
            self.assertIn("Missing SHA-256 seal", decision_missing["reason"])

            state["enforce_gate_seals"] = False
            _write(state_path, json.dumps(state))
            spec01 = spec_dir / "01-spec.md"
            _write(spec01, spec01.read_text(encoding="utf-8") + "\n<!-- sdd:gate-seal sha256=bad_digest -->\n")
            decision_malformed = _run_code_gate_guard(ws, "src/app.py")
            self.assertEqual(decision_malformed["decision"], "deny")
            self.assertIn("Malformed inline sdd:gate-seal", decision_malformed["reason"])

    def test_cli_approve_gate_and_verify_gates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ws, spec_dir = _seed_approved_workspace(pathlib.Path(tmp))
            with contextlib.redirect_stdout(io.StringIO()):
                rc_approve = sdd_gate_seal.main(["--repo-root", str(ws), "--approve", "--embed-inline", "--verify"])
                rc_verify_ok = sdd_gate_seal.main(["--repo-root", str(ws), "--verify"])
            self.assertEqual(rc_approve, 0)
            self.assertEqual(rc_verify_ok, 0)

            _write(
                spec_dir / "03-tasks.md",
                (spec_dir / "03-tasks.md").read_text(encoding="utf-8").replace("Implement login", "Implement OAuth"),
            )
            with contextlib.redirect_stdout(io.StringIO()):
                rc_verify_bad = sdd_gate_seal.main(["--repo-root", str(ws), "--verify"])
            self.assertEqual(rc_verify_bad, 1)


class TestPolyglotBoundaryImports(unittest.TestCase):
    """RF-1002: Polyglot Boundary & Ownership Import Scanner (TS/JS/C#/Go/Rust/Java/Kotlin)."""

    def test_polyglot_forbid_imports_across_ts_cs_go_rust_java_kotlin(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ws = pathlib.Path(tmp)
            stack_md = """# Stack
```yaml sdd:ownership-map
unowned_policy: warn
zones:
  - id: domain-core
    owner: back-engineer
    paths: ["src/domain/**"]
    forbid_imports:
      - "@infra/sqlalchemy"
      - "Microsoft.EntityFrameworkCore"
      - "database/sql"
      - "sqlx::postgres"
      - "jakarta.persistence"
```
"""
            _write(ws / "specs" / "STACK.md", stack_md)
            domain = ws / "src" / "domain"

            _write(
                domain / "Order.ts",
                "// import { x } from '@infra/sqlalchemy';\n"
                "/*\nimport { y } from '@infra/sqlalchemy';\n*/\n"
                "export const label = 'import @infra/sqlalchemy';\n"
                "import { db } from '@infra/sqlalchemy';\n",
            )
            _write(domain / "View.tsx", "const lazy = await import('@infra/sqlalchemy');\n")
            _write(
                domain / "Entity.cs",
                "// using Microsoft.EntityFrameworkCore;\n"
                "using System;\n"
                "using Microsoft.EntityFrameworkCore.Metadata;\n",
            )
            _write(
                domain / "repo.go",
                "package domain\n"
                "// import \"database/sql\"\n"
                "import (\n"
                "    \"fmt\"\n"
                "    \"database/sql\"\n"
                ")\n",
            )
            _write(
                domain / "model.rs",
                "/* use sqlx::postgres::PgPool; */\n"
                "use std::collections::HashMap;\n"
                "use sqlx::postgres::PgPool;\n",
            )
            _write(
                domain / "User.java",
                "package com.app.domain;\n"
                "// import jakarta.persistence.Entity;\n"
                "import jakarta.persistence.Entity;\n",
            )
            _write(
                domain / "Account.kt",
                "package com.app.domain\n"
                "import jakarta.persistence.Column as JpaColumn\n",
            )

            errors, _ = arch_bounds.run_boundary_audit(ws)
            joined = "\n".join(errors)
            self.assertIn("src/domain/Order.ts:6 imports forbidden module '@infra/sqlalchemy'", joined)
            self.assertNotIn("Order.ts:1", joined)
            self.assertNotIn("Order.ts:3", joined)
            self.assertNotIn("Order.ts:5", joined)
            self.assertIn("src/domain/View.tsx:1 imports forbidden module '@infra/sqlalchemy'", joined)
            self.assertIn("src/domain/Entity.cs:3 imports forbidden module 'Microsoft.EntityFrameworkCore.Metadata'", joined)
            self.assertIn("src/domain/repo.go:5 imports forbidden module 'database/sql'", joined)
            self.assertIn("src/domain/model.rs:3 imports forbidden module 'sqlx::postgres::PgPool'", joined)
            self.assertIn("src/domain/User.java:3 imports forbidden module 'jakarta.persistence.Entity'", joined)
            self.assertIn("src/domain/Account.kt:2 imports forbidden module 'jakarta.persistence.Column'", joined)


class TestDagWriteSetCollisions(unittest.TestCase):
    """RF-1003: Parallel Wave Write-Set Collision Detection & Auto-Split."""

    def test_parallel_wave_write_set_collision_raises_by_default(self) -> None:
        md_exact = """# Tasks
- [ ] `T1.1` [`@back-engineer`] `[PARALLEL: BLOCK_A]`: Edit auth service
  - *Archivos exactos*: `src/auth/service.py`, `src/auth/dto.py`
- [ ] `T1.2` [`@back-engineer`] `[PARALLEL: BLOCK_A]`: Refactor auth service
  - *Archivos exactos*: `src/auth/service.py`
"""
        tasks_exact = sdd_dag.parse_tasks_text(md_exact)
        self.assertEqual(tasks_exact[0].target_paths, ("src/auth/service.py", "src/auth/dto.py"))
        with self.assertRaises(sdd_dag.DagWriteSetCollisionError) as ctx1:
            sdd_dag.build_and_validate_dag(tasks_exact)
        self.assertIn("T1.1", str(ctx1.exception))
        self.assertIn("T1.2", str(ctx1.exception))

        md_prefix = """# Tasks
- [ ] `T2.1` [`@back-engineer`] `[PARALLEL: BLOCK_A]`: Touch auth dir
  - *Archivos*: `src/auth`
- [ ] `T2.2` [`@back-engineer`] `[PARALLEL: BLOCK_A]`: Touch nested file
  - *Target paths*: `src/auth/handlers/login.py`
"""
        with self.assertRaises(sdd_dag.DagWriteSetCollisionError):
            sdd_dag.build_and_validate_dag(sdd_dag.parse_tasks_text(md_prefix))

        md_glob = """# Tasks
- [ ] `T3.1` [`@back-engineer`] `[PARALLEL: BLOCK_A]`: Format all python
  - *Write-set*: `src/**/*.py`
- [ ] `T3.2` [`@back-engineer`] `[PARALLEL: BLOCK_A]`: Edit API routes
  - *Files*: `src/api/routes.py`
"""
        with self.assertRaises(sdd_dag.DagWriteSetCollisionError):
            sdd_dag.build_and_validate_dag(sdd_dag.parse_tasks_text(md_glob))

    def test_parallel_wave_auto_split_resolves_write_set_collisions(self) -> None:
        md = """# Tasks
- [ ] `T1.1` [`@back-engineer`] `[PARALLEL: BLOCK_A]`: Task A
  - *Archivos exactos*: `src/shared.py`
- [ ] `T1.2` [`@back-engineer`] `[PARALLEL: BLOCK_A]`: Task B (collides with T1.1)
  - *Archivos exactos*: `src/shared.py`
- [ ] `T1.3` [`@front-engineer`] `[PARALLEL: BLOCK_A]`: Task C (disjoint)
  - *Archivos exactos*: `src/ui/button.tsx`
"""
        tasks = sdd_dag.parse_tasks_text(md)
        plan = sdd_dag.build_and_validate_dag(tasks, auto_split_waves=True)
        self.assertEqual(len(plan.waves), 2)
        self.assertEqual([t.task_id for t in plan.waves[0]], ["T1.1", "T1.3"])
        self.assertEqual([t.task_id for t in plan.waves[1]], ["T1.2"])
        for wave in plan.waves:
            self.assertEqual(sdd_dag.find_wave_write_set_collisions(wave), [])

        with tempfile.TemporaryDirectory() as tmp:
            tasks_file = _write(pathlib.Path(tmp) / "03-tasks.md", md)
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(sdd_dag.main(["--verify", str(tasks_file)]), 1)
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = sdd_dag.main(["--plan", str(tasks_file), "--auto-split", "--format", "json"])
            self.assertEqual(rc, 0)
            payload = json.loads(buf.getvalue())
            self.assertEqual(payload["waves"], [["T1.1", "T1.3"], ["T1.2"]])


class TestCiDagAndThresholdEnforcement(unittest.TestCase):
    """RF-1004: CI DAG Verification Step & Minimum Test Count Threshold (>= 120)."""

    def test_ci_workflow_verifies_all_dags_and_enforces_min_120_tests(self) -> None:
        ci_text = (ROOT_DIR / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        self.assertIn("scripts/sdd_cli.py ci-verify", ci_text)
        self.assertIn("--mode auto", ci_text)
        self.assertEqual(inspect.signature(sdd_ci.check_framework_unittest).parameters["min_tests"].default, 120)
        self.assertEqual(sdd_ci.build_parser().parse_args([]).min_tests, 120)
        dag_res = sdd_ci.check_dags(ROOT_DIR, mode="framework")
        self.assertEqual(dag_res.status, "PASS", dag_res.detail)

        task_files = sorted(ROOT_DIR.glob(".sdd/framework/work-items/*/03-tasks.md")) + sorted(
            ROOT_DIR.glob("specs/*/*/03-tasks.md")
        )
        self.assertGreaterEqual(len(task_files), 10)
        for tf in task_files:
            tasks = sdd_dag.parse_tasks_markdown(tf)
            self.assertGreater(len(tasks), 0, f"No tasks parsed in {tf}")
            plan = sdd_dag.build_and_validate_dag(tasks)
            for wave in plan.waves:
                self.assertEqual(sdd_dag.find_wave_write_set_collisions(wave), [], f"Collision in {tf}")


if __name__ == "__main__":
    unittest.main()
