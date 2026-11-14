import importlib
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

# Add project root to sys.path so we can import sdd_token_usage
ROOT_DIR = Path(__file__).resolve().parent.parent
SCRIPT_DIR = ROOT_DIR / ".agents" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import sdd_repo_map
import sdd_token_usage


class TestSddTokenUsage(unittest.TestCase):
    def test_normalize_token_payload_antigravity(self):
        data = {
            "type": "PLANNER_RESPONSE",
            "input_tokens": 1500,
            "output_tokens": 300,
            "cache_read_tokens": 25000,
        }
        inp, out, cache, reasoning = sdd_token_usage.normalize_token_payload(data)
        self.assertEqual(inp, 1500)
        self.assertEqual(out, 300)
        self.assertEqual(cache, 25000)
        self.assertEqual(reasoning, 0)

    def test_normalize_token_payload_claude_code(self):
        data = {
            "type": "assistant",
            "usage": {
                "input_tokens": 2000,
                "output_tokens": 400,
                "cache_read_input_tokens": 30000,
            },
        }
        inp, out, cache, reasoning = sdd_token_usage.normalize_token_payload(data)
        self.assertEqual(inp, 2000)
        self.assertEqual(out, 400)
        self.assertEqual(cache, 30000)
        self.assertEqual(reasoning, 0)

    def test_normalize_token_payload_openai_codex(self):
        data = {
            "id": "chatcmpl-123",
            "usage": {
                "prompt_tokens": 5000,
                "completion_tokens": 800,
                "prompt_tokens_details": {
                    "cached_tokens": 4000
                },
                "completion_tokens_details": {
                    "reasoning_tokens": 150
                }
            }
        }
        inp, out, cache, reasoning = sdd_token_usage.normalize_token_payload(data)
        self.assertEqual(inp, 5000)
        self.assertEqual(out, 800)
        self.assertEqual(cache, 4000)
        self.assertEqual(reasoning, 150)

    def test_normalize_token_payload_copilot(self):
        data = {
            "promptTokens": 1200,
            "completionTokens": 250,
            "cachedTokens": 800
        }
        inp, out, cache, reasoning = sdd_token_usage.normalize_token_payload(data)
        self.assertEqual(inp, 1200)
        self.assertEqual(out, 250)
        self.assertEqual(cache, 800)
        self.assertEqual(reasoning, 0)

    def test_normalize_token_payload_roo_code(self):
        data = {
            "tokensIn": 3500,
            "tokensOut": 450,
            "cacheReads": 12000
        }
        inp, out, cache, reasoning = sdd_token_usage.normalize_token_payload(data)
        self.assertEqual(inp, 3500)
        self.assertEqual(out, 450)
        self.assertEqual(cache, 12000)
        self.assertEqual(reasoning, 0)

    def test_workspace_telemetry_provider(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            telemetry_file = tmp_path / "tokens.json"
            telemetry_file.write_text(
                json.dumps({
                    "ide": "cursor",
                    "last_in": 1000,
                    "last_out": 200,
                    "last_cache": 5000,
                    "total_in": 10000,
                    "total_out": 2000,
                    "total_cache": 50000,
                }),
                encoding="utf-8"
            )

            provider = sdd_token_usage.WorkspaceTelemetryProvider()
            metrics = provider.extract_usage(telemetry_file)
            self.assertEqual(metrics["ide"], "cursor")
            self.assertTrue(metrics["is_available"])
            self.assertEqual(metrics["total_in"], 10000)
            self.assertEqual(metrics["cache_efficiency"], "83.3%")

    def test_env_var_override(self):
        old_env = os.environ.copy()
        try:
            os.environ["SDD_TOKENS_TOTAL_IN"] = "5000"
            os.environ["SDD_TOKENS_TOTAL_OUT"] = "1000"
            os.environ["SDD_TOKENS_TOTAL_CACHE"] = "20000"
            os.environ["SDD_TOKENS_LAST_IN"] = "500"
            os.environ["SDD_TOKENS_LAST_OUT"] = "100"
            os.environ["SDD_TOKENS_LAST_CACHE"] = "2000"

            provider = sdd_token_usage.EnvVarProvider()
            res = provider.find_latest_session()
            self.assertIsNotNone(res)
            session_path, _ = res
            metrics = provider.extract_usage(session_path)

            self.assertEqual(metrics["ide"], "env")
            self.assertEqual(metrics["total_in"], 5000)
            self.assertEqual(metrics["total_out"], 1000)
            self.assertEqual(metrics["total_cache"], 20000)
            self.assertEqual(metrics["last_in"], 500)
            self.assertEqual(metrics["cache_efficiency"], "80.0%")
        finally:
            os.environ.clear()
            os.environ.update(old_env)

    def test_copilot_log_stream_parser(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "copilot.log"
            log_file.write_text(
                "[INFO] Session started\n"
                "[INFO] [chat] turn completed - tokens: in=1200, out=300, cache=4000\n"
                "[INFO] [chat] turn completed - tokens: in=800, out=200, cache=3000\n",
                encoding="utf-8"
            )
            provider = sdd_token_usage.GitHubCopilotProvider()
            metrics = provider.extract_usage(log_file)
            self.assertEqual(metrics["ide"], "copilot")
            self.assertTrue(metrics["is_available"])
            self.assertEqual(metrics["total_in"], 2000)
            self.assertEqual(metrics["total_out"], 500)
            self.assertEqual(metrics["total_cache"], 7000)
            self.assertEqual(metrics["last_in"], 800)
            self.assertEqual(metrics["last_out"], 200)
            self.assertEqual(metrics["last_cache"], 3000)

    def test_roo_code_history_parser(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            hist_file = Path(tmpdir) / "api_conversation_history.json"
            hist_file.write_text(
                json.dumps([
                    {"tokensIn": 1000, "tokensOut": 150, "cacheReads": 5000},
                    {"tokensIn": 2000, "tokensOut": 300, "cacheReads": 10000},
                ]),
                encoding="utf-8"
            )
            provider = sdd_token_usage.RooCodeClineProvider()
            metrics = provider.extract_usage(hist_file)
            self.assertEqual(metrics["ide"], "roo_code")
            self.assertTrue(metrics["is_available"])
            self.assertEqual(metrics["total_in"], 3000)
            self.assertEqual(metrics["total_out"], 450)
            self.assertEqual(metrics["total_cache"], 15000)
            self.assertEqual(metrics["last_in"], 2000)

    def test_render_footer(self):
        metrics = {
            "ide": "copilot",
            "last_in": 1500,
            "last_out": 300,
            "last_cache": 10000,
            "total_in": 25000,
            "total_out": 4000,
            "total_cache": 75000,
            "cache_efficiency": "75.0%",
        }
        footer_green = sdd_token_usage.render_footer(metrics, turn=3, blocks=1, gate="2")
        self.assertIn("🟢 **Context Health (copilot):** Turn 3/15 | Blocks: 1/2 | Gate: 2", footer_green)
        self.assertIn("In 1.5k · Out 0.3k · Cache 10.0k", footer_green)
        self.assertIn("In 25.0k · Out 4.0k · Cache 75.0k (Hit: 75.0%)", footer_green)

        footer_red = sdd_token_usage.render_footer(metrics, turn=15, blocks=1, gate="4")
        self.assertIn("🔴 **Context Health (copilot):** Turn 15/15", footer_red)

        self.assertEqual(sdd_token_usage.evaluate_context_health(11, 0), ("🟡", "yellow"))
        self.assertEqual(sdd_token_usage.evaluate_context_health(1, 2), ("🟡", "yellow"))
        self.assertTrue(sdd_token_usage.evaluate_context_status(metrics, turn=15, blocks=1, gate="4")["should_handoff"])

    def test_sqlite_provider_and_explicit_transcript(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            db_path = tmp_path / "state.vscdb"
            conn = sqlite3.connect(db_path)
            conn.execute("CREATE TABLE ItemTable (key TEXT PRIMARY KEY, value TEXT)")
            conn.execute(
                "INSERT INTO ItemTable (key, value) VALUES (?, ?)",
                ("chatdata.session", json.dumps({"usage": {"promptTokens": 400, "completionTokens": 100, "cachedTokens": 500}})),
            )
            conn.execute(
                "INSERT INTO ItemTable (key, value) VALUES (?, ?)",
                (
                    "interactive.sessions",
                    json.dumps({"usage": {"prompt_tokens": 200, "completion_tokens": 50, "prompt_tokens_details": {"cached_tokens": 100}}}),
                ),
            )
            conn.commit()
            conn.close()

            cursor_metrics = sdd_token_usage.CursorProvider().extract_usage(db_path)
            self.assertEqual(cursor_metrics["ide"], "cursor")
            self.assertTrue(cursor_metrics["is_available"])
            self.assertEqual(cursor_metrics["total_in"], 600)
            self.assertEqual(cursor_metrics["total_out"], 150)
            self.assertEqual(cursor_metrics["total_cache"], 600)

            missing = sdd_token_usage.get_token_usage(transcript_path=str(tmp_path / "missing.jsonl"))
            self.assertFalse(missing["is_available"])

    def test_package_import_and_repo_map_contract(self):
        agents_dir = str(ROOT_DIR / ".agents")
        added = False
        if agents_dir not in sys.path:
            sys.path.insert(0, agents_dir)
            added = True
        try:
            pkg_tok = importlib.import_module("scripts.sdd_token_usage")
            pkg_map = importlib.import_module("scripts.sdd_repo_map")
            self.assertTrue(callable(pkg_tok.get_token_usage))
            self.assertIn(".py", pkg_map.EXTENSION_PARSERS)
        finally:
            if added and agents_dir in sys.path:
                sys.path.remove(agents_dir)

        with tempfile.TemporaryDirectory() as tmpdir:
            sample = Path(tmpdir) / "sample.py"
            sample.write_text("class Demo:\n    def greet(self, name: str) -> str:\n        return name\n", encoding="utf-8")
            lines, total_files, total_symbols = sdd_repo_map.build_repo_map_lines(sample)
            self.assertEqual(total_files, 1)
            self.assertEqual(total_symbols, 2)
            self.assertTrue(any("def greet(self, name: str) -> str" in ln for ln in lines))

        help_res = subprocess.run(
            [sys.executable, str(SCRIPT_DIR / "sdd_repo_map.py"), "--help"],
            capture_output=True, text=True, encoding="utf-8",
        )
        self.assertEqual(help_res.returncode, 0)
        self.assertIn("SDD Universal AST", help_res.stdout)

    def test_split_modules_within_500_lines(self):
        for rel in (
            ".agents/scripts/sdd_token_usage.py",
            ".agents/scripts/sdd_token_parsers.py",
            ".agents/scripts/sdd_token_report.py",
            ".agents/scripts/sdd_repo_map.py",
            ".agents/scripts/sdd_repo_map_parsers.py",
            "tests/test_sdd_token_usage.py",
        ):
            line_count = len((ROOT_DIR / rel).read_text(encoding="utf-8").splitlines())
            self.assertLessEqual(line_count, 500, f"{rel} exceeds 500-line ceiling ({line_count})")


if __name__ == "__main__":
    unittest.main()
