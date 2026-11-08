import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

# Add project root to sys.path so we can import sdd_token_usage
SCRIPT_DIR = Path(__file__).resolve().parent.parent / ".agents" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

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


if __name__ == "__main__":
    unittest.main()
