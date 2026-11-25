#!/usr/bin/env python3
"""Offline acceptance tests for FWK-020 enterprise packs (CA-2004..CA-2008)."""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import pathlib
import re
import shutil
import sys
import tempfile
import unittest
from collections.abc import Sequence
from unittest import mock

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts import sdd_agent_generator, sdd_catalog_import  # noqa: E402
from scripts.sdd_pack_registry import (  # noqa: E402
    PackCompatibilityError,
    PackDependencyError,
    StackConfigError,
    load_catalog_registry,
)

REAL_PACKS_DIR = ROOT_DIR / ".sdd" / "catalog" / "packs"
BOOTSTRAP_REFS_DIR = ROOT_DIR / ".sdd" / "catalog" / "bootstrap-references"
NEW_NON_ECC_PACKS = (
    "capability-event-driven",
    "capability-api-governance",
    "capability-iac-cloud",
    "framework-nextjs",
    "framework-nestjs",
    "capability-data-engineering",
)
_VERIF_BLOCK = (
    "\n```yaml sdd:verification-commands\n"
    "lint: uv run ruff check .\n"
    "unit_test: uv run pytest tests -q\n"
    "```\n"
)


def _write(path: pathlib.Path, content: str) -> pathlib.Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _stack_md(packs: Sequence[str], *, preset: str = "compact") -> str:
    return (
        "# Stack\n\n> **ESTADO:** `[x] Gate S0 Approved (Human Sign-off)`\n\n"
        f"```yaml sdd:stack-config\nstack_approved: true\ngate00_approved: true\n"
        f"preset: {preset}\npacks: {json.dumps(list(packs))}\n```\n"
        + _VERIF_BLOCK
    )


def _seed_ws(base: pathlib.Path, name: str, packs_to_copy: Sequence[str], stack_packs: Sequence[str], *, preset: str = "compact") -> pathlib.Path:
    ws = base / name
    _write(ws / "specs" / "STACK.md", _stack_md(stack_packs, preset=preset))
    target_packs = ws / ".sdd" / "catalog" / "packs"
    target_packs.mkdir(parents=True, exist_ok=True)
    for pack_dir in packs_to_copy:
        shutil.copytree(REAL_PACKS_DIR / pack_dir, target_packs / pack_dir)
    return ws


def _materialize_silent(ws: pathlib.Path) -> dict[str, object]:
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        return sdd_agent_generator.materialize_squad(repo_root=ws)


class TestSddEnterprisePacks(unittest.TestCase):
    """Offline verification of FWK-020 enterprise packs, compatibility, and attribution."""

    def test_ca2004_event_driven_and_api_governance_materialization(self) -> None:
        """CA-2004: Clean materialization of event-driven + api-governance (6 skills, SHA-256, 0 rules)."""
        with tempfile.TemporaryDirectory() as tmp:
            ws = _seed_ws(
                pathlib.Path(tmp),
                "ca2004",
                ("capability-event-driven", "capability-api-governance"),
                ("capability:event-driven", "capability:api-governance"),
            )
            lock = _materialize_silent(ws)
            expected_skills = (
                "kafka-streaming-patterns",
                "async-messaging-patterns",
                "microservices-boundaries",
                "openapi-contract-governance",
                "grpc-protobuf-patterns",
                "asyncapi-event-contracts",
            )
            skill_dirs = sorted(p.name for p in (ws / ".agents" / "skills").iterdir() if p.is_dir())
            self.assertEqual(skill_dirs, sorted(expected_skills))
            files_map = lock["files"]
            assert isinstance(files_map, dict)
            for slug in expected_skills:
                rel = f".agents/skills/{slug}/SKILL.md"
                disk = ws / rel
                self.assertTrue(disk.is_file(), f"Missing {rel}")
                self.assertIn(rel, files_map)
                self.assertEqual(hashlib.sha256(disk.read_bytes()).hexdigest(), files_map[rel]["sha256"])
            pack_rules = ws / ".agents" / "pack-rules"
            rule_files = list(pack_rules.rglob("*.md")) if pack_rules.exists() else []
            self.assertEqual(rule_files, [])
            self.assertEqual(sdd_agent_generator.verify_squad(repo_root=ws), [])

    def test_ca2005_dependencies_fail_closed_and_full_enterprise_materialization(self) -> None:
        """CA-2005: PackDependencyError on missing requires + clean materialization of 8 new skills."""
        all_needed = (
            "lang-typescript",
            "framework-react",
            "framework-nextjs",
            "framework-nestjs",
            "capability-iac-cloud",
            "capability-data-engineering",
        )
        with tempfile.TemporaryDirectory() as tmp:
            base = pathlib.Path(tmp)
            missing_cases = (
                ("nextjs_no_deps", ("framework:nextjs",)),
                ("nextjs_no_react", ("framework:nextjs", "lang:typescript")),
                ("nextjs_no_ts", ("framework:nextjs", "framework:react")),
                ("nestjs_no_ts", ("framework:nestjs",)),
            )
            for case_name, req_packs in missing_cases:
                with self.subTest(case=case_name):
                    ws_bad = _seed_ws(base, case_name, all_needed, req_packs)
                    with self.assertRaises(PackDependencyError):
                        _materialize_silent(ws_bad)
                    self.assertFalse((ws_bad / ".agents").exists())

            ws_ok = _seed_ws(
                base,
                "ca2005_ok",
                all_needed,
                (
                    "lang:typescript",
                    "framework:react",
                    "framework:nextjs",
                    "framework:nestjs",
                    "capability:iac-cloud",
                    "capability:data-engineering",
                ),
            )
            lock = _materialize_silent(ws_ok)
            self.assertEqual(sdd_agent_generator.verify_squad(repo_root=ws_ok), [])
            expected_new = (
                "nextjs-patterns",
                "nestjs-patterns",
                "terraform-opentofu-patterns",
                "cloud-iam-security",
                "cloud-finops-guardrails",
                "dbt-modeling-patterns",
                "airflow-dag-patterns",
                "data-quality-governance",
            )
            files_map = lock["files"]
            assert isinstance(files_map, dict)
            for slug in expected_new:
                rel = f".agents/skills/{slug}/SKILL.md"
                self.assertTrue((ws_ok / rel).is_file(), f"Missing {rel}")
                self.assertIn(rel, files_map)

    def test_ca2006_devops_and_database_expanded_packs_and_cli_verify(self) -> None:
        """CA-2006: capability:devops (5 skills) + capability:database (7 skills) + CLI --verify."""
        with tempfile.TemporaryDirectory() as tmp:
            ws = _seed_ws(
                pathlib.Path(tmp),
                "ca2006",
                ("capability-devops", "capability-database"),
                ("capability:devops", "capability:database"),
            )
            _materialize_silent(ws)
            reg = load_catalog_registry(ws / ".sdd" / "catalog" / "packs")
            devops_slugs = [pathlib.PurePosixPath(s).name for s in reg["capability-devops"].skills]
            db_slugs = [pathlib.PurePosixPath(s).name for s in reg["capability-database"].skills]
            self.assertEqual(len(devops_slugs), 5)
            self.assertIn("helm-gitops-patterns", devops_slugs)
            self.assertEqual(len(db_slugs), 7)
            self.assertIn("multi-tenant-isolation", db_slugs)

            materialized = sorted(p.name for p in (ws / ".agents" / "skills").iterdir() if p.is_dir())
            self.assertEqual(materialized, sorted(devops_slugs + db_slugs))

            out, err = io.StringIO(), io.StringIO()
            with (
                mock.patch.object(sdd_agent_generator, "ROOT_DIR", ws),
                mock.patch.object(sys, "argv", ["sdd_agent_generator.py", "--verify"]),
                contextlib.redirect_stdout(out),
                contextlib.redirect_stderr(err),
            ):
                rc = sdd_agent_generator.main()
            self.assertEqual((rc, err.getvalue()), (0, ""), out.getvalue())
            self.assertIn("0 mismatches", out.getvalue())

    def test_ca2007_preset_incompatibility_and_bootstrap_parity(self) -> None:
        """CA-2007: PackCompatibilityError (StackConfigError) + ES/EN bootstrap parity & pruning."""
        packs_needed = (
            "lang-typescript",
            "framework-react",
            "framework-nextjs",
            "framework-nestjs",
            "capability-event-driven",
            "capability-data-engineering",
        )
        with tempfile.TemporaryDirectory() as tmp:
            base = pathlib.Path(tmp)
            incompatible_cases = (
                ("api_nextjs", "api-only", ("lang:typescript", "framework:react", "framework:nextjs")),
                ("spa_nestjs", "spa-only", ("lang:typescript", "framework:nestjs")),
                ("spa_event", "spa-only", ("capability:event-driven",)),
                ("spa_data", "spa-only", ("capability:data-engineering",)),
            )
            for label, preset, req_packs in incompatible_cases:
                with self.subTest(case=label):
                    ws = _seed_ws(base, label, packs_needed, req_packs, preset=preset)
                    with self.assertRaises(PackCompatibilityError) as ctx:
                        _materialize_silent(ws)
                    self.assertIsInstance(ctx.exception, StackConfigError)

        es_text = (BOOTSTRAP_REFS_DIR / "question-catalog-es.md").read_text(encoding="utf-8")
        en_text = (BOOTSTRAP_REFS_DIR / "question-catalog-en.md").read_text(encoding="utf-8")
        pruning_text = (BOOTSTRAP_REFS_DIR / "stack-config-and-pruning.md").read_text(encoding="utf-8")

        def _round_question_counts(text: str) -> list[int]:
            rounds = re.split(r"^##\s+", text, flags=re.MULTILINE)[1:]
            return [len(re.findall(r"^\d+\.\s+\*\*", r, flags=re.MULTILINE)) for r in rounds]

        self.assertEqual(_round_question_counts(es_text), [7, 12, 11])
        self.assertEqual(_round_question_counts(en_text), [7, 12, 11])
        for token in (*NEW_NON_ECC_PACKS, "capability-devops", "multi-tenant-isolation"):
            self.assertIn(token, es_text)
            self.assertIn(token, en_text)
            self.assertIn(token, pruning_text)
        for pruned_rule in ("framework-nextjs", "framework-nestjs", "capability-event-driven", "capability-data-engineering"):
            self.assertIn(pruned_rule, pruning_text)

    def test_ca2008_catalog_inventory_attribution_and_importer_preservation(self) -> None:
        """CA-2008: 25 packs (86 skills), uniform upstream/licenses, 1:1 notices, offline importer & fail-closed."""
        registry = load_catalog_registry(REAL_PACKS_DIR)
        self.assertEqual(len(registry), 25)
        self.assertEqual(sum(len(m.skills) for m in registry.values()), 86)

        upstream_md = (ROOT_DIR / ".sdd" / "catalog" / "UPSTREAM.md").read_text(encoding="utf-8")
        notices_md = (ROOT_DIR / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")
        allowed_licenses = {"MIT", "Apache-2.0"}
        seen_repos: set[str] = set()

        for pack_name in sorted(registry):
            raw = json.loads((REAL_PACKS_DIR / pack_name / "pack.json").read_text(encoding="utf-8"))
            up = raw.get("upstream")
            self.assertIsInstance(up, dict, f"{pack_name}: missing upstream dict")
            self.assertIn(up.get("license"), allowed_licenses, f"{pack_name}: invalid license {up.get('license')}")
            repo = up.get("repo")
            self.assertIsInstance(repo, str)
            self.assertTrue(bool(repo and "/" in repo), f"{pack_name}: invalid upstream.repo {repo!r}")
            seen_repos.add(repo)
            self.assertIn(pack_name, upstream_md)
            if "references" in up:
                self.assertIsInstance(up["references"], list)
                for ref in up["references"]:
                    self.assertIsInstance(ref, str)
                    m = re.match(r"^([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)\s+\((MIT|Apache-2\.0)\)$", ref)
                    self.assertIsNotNone(m, f"{pack_name}: invalid upstream.references entry {ref!r}")
                    assert m is not None
                    seen_repos.add(m.group(1))

        for repo_slug in sorted(seen_repos):
            self.assertIn(repo_slug, upstream_md, f"{repo_slug} missing from UPSTREAM.md")
            self.assertIn(repo_slug, notices_md, f"{repo_slug} missing from THIRD_PARTY_NOTICES.md")

        # Offline importer simulation: preserves 6 non-ECC packs + 2 extra SDD skills + upstream.references
        with tempfile.TemporaryDirectory() as tmp:
            packs_dir = pathlib.Path(tmp) / "packs"
            sentinels: dict[pathlib.Path, bytes] = {}
            for p_name in NEW_NON_ECC_PACKS:
                shutil.copytree(REAL_PACKS_DIR / p_name, packs_dir / p_name)
                pj = packs_dir / p_name / "pack.json"
                sentinels[pj] = pj.read_bytes()
            for expanded in ("capability-devops", "capability-database"):
                shutil.copytree(REAL_PACKS_DIR / expanded, packs_dir / expanded)

            def fake_fetcher(rel_url: str) -> str | None:
                return f"# Mock {rel_url}\n" if rel_url.endswith(".md") else None

            with (
                mock.patch("urllib.request.urlopen", side_effect=AssertionError("Network forbidden")),
                contextlib.redirect_stdout(io.StringIO()),
                contextlib.redirect_stderr(io.StringIO()),
            ):
                sdd_catalog_import.import_packs(fetcher=fake_fetcher, packs_dir=packs_dir)

            for pj, before_bytes in sentinels.items():
                self.assertEqual(pj.read_bytes(), before_bytes, f"Non-ECC pack mutated: {pj}")

            devops_raw = json.loads((packs_dir / "capability-devops" / "pack.json").read_text(encoding="utf-8"))
            self.assertIn("skills/helm-gitops-patterns", devops_raw["skills"])
            self.assertEqual(devops_raw["upstream"]["references"], ["wshobson/agents (MIT)"])

            db_raw = json.loads((packs_dir / "capability-database" / "pack.json").read_text(encoding="utf-8"))
            self.assertIn("skills/multi-tenant-isolation", db_raw["skills"])
            self.assertEqual(
                db_raw["upstream"]["references"],
                ["supabase/agent-skills (MIT)", "agamm/claude-code-owasp (MIT)"],
            )

            # Fail-closed negative tests: malformed pack.json and path traversal outside pack_dir
            for label, payload in (
                ("malformed_json", "{not valid json"),
                ("escape_path", json.dumps({"skills": ["../outside-skill"]})),
            ):
                with self.subTest(case=label):
                    bad_dir = pathlib.Path(tmp) / f"bad_{label}"
                    _write(bad_dir / "capability-devops" / "pack.json", payload)
                    with (
                        self.assertRaises(ValueError),
                        contextlib.redirect_stdout(io.StringIO()),
                        contextlib.redirect_stderr(io.StringIO()),
                    ):
                        sdd_catalog_import.import_packs(fetcher=fake_fetcher, packs_dir=bad_dir)


if __name__ == "__main__":
    unittest.main()
