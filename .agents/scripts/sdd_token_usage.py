#!/usr/bin/env python3
"""
SDD Token & Cache Telemetry Tracker (Multi-IDE Agnostic Engine)
Universal token and context tracking across agentic environments:
- Google Antigravity
- GitHub Copilot (VS Code / JetBrains / CLI)
- OpenAI Codex & OpenAI Agents (API / CLI / Assistants / Canvas)
- Anthropic Claude Code
- Roo Code & Cline
- Cursor & Windsurf (Cascade)
- Aider
- Workspace SSOT (.agents/telemetry/tokens.json)
- Standard Environment Variables (SDD_TRANSCRIPT_PATH, SDD_TOKEN_USAGE_FILE, etc.)
"""

import argparse
import json
import os
import re
import sqlite3
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# UTF-8 encoding compatibility on Windows console
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass



def calc_cache_efficiency(total_cache: int, total_in: int) -> str:
    total_context = total_cache + total_in
    if total_context > 0:
        return f"{(total_cache / total_context * 100):.1f}%"
    return "0.0%"


def format_k(n: int) -> str:
    return f"{n / 1000:.1f}k"


def normalize_token_payload(data: Any) -> Tuple[int, int, int, int]:
    """
    Extracts (inp, out, cache, reasoning) from arbitrary JSON payloads
    emitted by Google, OpenAI, Anthropic, Copilot, Roo Code, etc.
    """
    if not isinstance(data, dict):
        return 0, 0, 0, 0

    usage = data.get("usage") if isinstance(data.get("usage"), dict) else data

    # 1. Input tokens
    inp = (
        usage.get("input_tokens")
        or usage.get("prompt_tokens")
        or usage.get("tokensIn")
        or usage.get("promptTokens")
        or usage.get("inputTokens")
        or usage.get("in")
        or 0
    )

    # 2. Output tokens
    out = (
        usage.get("output_tokens")
        or usage.get("completion_tokens")
        or usage.get("tokensOut")
        or usage.get("completionTokens")
        or usage.get("outputTokens")
        or usage.get("out")
        or 0
    )

    # 3. Cache tokens
    cache = (
        usage.get("cache_read_tokens")
        or usage.get("cache_read_input_tokens")
        or usage.get("cacheReads")
        or usage.get("cachedTokens")
        or usage.get("cached_tokens")
        or usage.get("cache")
        or 0
    )

    # Check nested prompt_tokens_details (OpenAI format)
    ptd = usage.get("prompt_tokens_details") or data.get("prompt_tokens_details")
    if isinstance(ptd, dict) and not cache:
        cache = ptd.get("cached_tokens", 0)

    # 4. Reasoning tokens (o1/o3/Claude thinking)
    reasoning = (
        usage.get("reasoning_tokens")
        or usage.get("thinking_tokens")
        or 0
    )
    ctd = usage.get("completion_tokens_details") or data.get("completion_tokens_details")
    if isinstance(ctd, dict) and not reasoning:
        reasoning = ctd.get("reasoning_tokens", 0)

    return int(inp), int(out), int(cache), int(reasoning)


def make_empty_metrics(ide: str = "unknown", source_path: Optional[str] = None) -> Dict[str, Any]:
    return {
        "ide": ide,
        "source_path": source_path,
        "is_available": False,
        "last_in": 0,
        "last_out": 0,
        "last_cache": 0,
        "last_reasoning": 0,
        "total_in": 0,
        "total_out": 0,
        "total_cache": 0,
        "total_reasoning": 0,
        "cache_efficiency": "0.0%",
    }


def parse_jsonl_stream(path: Path, ide_name: str, filter_type: Optional[str] = None) -> Dict[str, Any]:
    """Generic parser for JSONL transcripts (Antigravity, Claude, OpenAI, etc.)."""
    total_in = 0
    total_out = 0
    total_cache = 0
    total_reasoning = 0
    last_in = 0
    last_out = 0
    last_cache = 0
    last_reasoning = 0
    has_records = False

    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    if filter_type and data.get("type") != filter_type:
                        continue

                    inp, out, cache, reasoning = normalize_token_payload(data)
                    if inp or out or cache or reasoning:
                        has_records = True
                        total_in += inp
                        total_out += out
                        total_cache += cache
                        total_reasoning += reasoning
                        last_in = inp
                        last_out = out
                        last_cache = cache
                        last_reasoning = reasoning
                except Exception:
                    continue
    except Exception:
        return make_empty_metrics(ide=ide_name, source_path=str(path))

    return {
        "ide": ide_name,
        "source_path": str(path),
        "is_available": has_records,
        "last_in": last_in,
        "last_out": last_out,
        "last_cache": last_cache,
        "last_reasoning": last_reasoning,
        "total_in": total_in,
        "total_out": total_out,
        "total_cache": total_cache,
        "total_reasoning": total_reasoning,
        "cache_efficiency": calc_cache_efficiency(total_cache, total_in),
    }


# =====================================================================
# PROVIDERS
# =====================================================================

class BaseProvider:
    name: str = "generic"

    def find_latest_session(self) -> Optional[Tuple[Path, float]]:
        """Returns (Path, mtime) or None if no session found."""
        raise NotImplementedError

    def extract_usage(self, session_path: Path) -> Dict[str, Any]:
        """Extracts token metrics from the session path."""
        raise NotImplementedError


class EnvVarProvider(BaseProvider):
    name = "env"

    def find_latest_session(self) -> Optional[Tuple[Path, float]]:
        # 1. Direct JSON file pointer
        usage_file = os.environ.get("SDD_TOKEN_USAGE_FILE") or os.environ.get("OPENAI_USAGE_FILE")
        if usage_file:
            p = Path(usage_file)
            if p.exists() and p.is_file():
                return p, p.stat().st_mtime

        # 2. Direct Transcript file pointer
        transcript = os.environ.get("SDD_TRANSCRIPT_PATH")
        if transcript:
            p = Path(transcript)
            if p.exists() and p.is_file():
                return p, p.stat().st_mtime

        # 3. Direct env vars override
        if os.environ.get("SDD_TOKENS_TOTAL_IN") or os.environ.get("SDD_TOKENS_IN"):
            # Synthetic session
            return Path("ENV_OVERRIDE"), 9999999999.0

        return None

    def extract_usage(self, session_path: Path) -> Dict[str, Any]:
        if str(session_path) == "ENV_OVERRIDE":
            total_in = int(os.environ.get("SDD_TOKENS_TOTAL_IN") or os.environ.get("SDD_TOKENS_IN") or 0)
            total_out = int(os.environ.get("SDD_TOKENS_TOTAL_OUT") or os.environ.get("SDD_TOKENS_OUT") or 0)
            total_cache = int(os.environ.get("SDD_TOKENS_TOTAL_CACHE") or os.environ.get("SDD_TOKENS_CACHE") or 0)
            last_in = int(os.environ.get("SDD_TOKENS_LAST_IN") or total_in)
            last_out = int(os.environ.get("SDD_TOKENS_LAST_OUT") or total_out)
            last_cache = int(os.environ.get("SDD_TOKENS_LAST_CACHE") or total_cache)

            return {
                "ide": "env",
                "source_path": "ENV_OVERRIDE",
                "is_available": True,
                "last_in": last_in,
                "last_out": last_out,
                "last_cache": last_cache,
                "last_reasoning": 0,
                "total_in": total_in,
                "total_out": total_out,
                "total_cache": total_cache,
                "total_reasoning": 0,
                "cache_efficiency": calc_cache_efficiency(total_cache, total_in),
            }

        if session_path.suffix.lower() == ".json":
            try:
                data = json.loads(session_path.read_text(encoding="utf-8", errors="ignore"))
                inp, out, cache, reasoning = normalize_token_payload(data)
                tot_in = data.get("total_in", inp)
                tot_out = data.get("total_out", out)
                tot_cache = data.get("total_cache", cache)
                tot_reasoning = data.get("total_reasoning", reasoning)
                return {
                    "ide": data.get("ide", "env"),
                    "source_path": str(session_path),
                    "is_available": True,
                    "last_in": data.get("last_in", inp),
                    "last_out": data.get("last_out", out),
                    "last_cache": data.get("last_cache", cache),
                    "last_reasoning": data.get("last_reasoning", reasoning),
                    "total_in": tot_in,
                    "total_out": tot_out,
                    "total_cache": tot_cache,
                    "total_reasoning": tot_reasoning,
                    "cache_efficiency": data.get("cache_efficiency") or calc_cache_efficiency(tot_cache, tot_in),
                }
            except Exception:
                pass

        return parse_jsonl_stream(session_path, ide_name="env")


class WorkspaceTelemetryProvider(BaseProvider):
    name = "workspace"

    def find_latest_session(self) -> Optional[Tuple[Path, float]]:
        candidates = [
            Path(".agents/telemetry/tokens.json"),
            Path(".agents/telemetry/session_tokens.json"),
            Path(".agents/session_tokens.json"),
        ]
        for c in candidates:
            if c.exists() and c.is_file() and c.stat().st_size > 0:
                return c.resolve(), c.stat().st_mtime
        return None

    def extract_usage(self, session_path: Path) -> Dict[str, Any]:
        try:
            data = json.loads(session_path.read_text(encoding="utf-8", errors="ignore"))
            inp, out, cache, reasoning = normalize_token_payload(data)
            tot_in = data.get("total_in", inp)
            tot_out = data.get("total_out", out)
            tot_cache = data.get("total_cache", cache)
            tot_reasoning = data.get("total_reasoning", reasoning)

            return {
                "ide": data.get("ide", "workspace"),
                "source_path": str(session_path),
                "is_available": True,
                "last_in": data.get("last_in", inp),
                "last_out": data.get("last_out", out),
                "last_cache": data.get("last_cache", cache),
                "last_reasoning": data.get("last_reasoning", reasoning),
                "total_in": tot_in,
                "total_out": tot_out,
                "total_cache": tot_cache,
                "total_reasoning": tot_reasoning,
                "cache_efficiency": data.get("cache_efficiency") or calc_cache_efficiency(tot_cache, tot_in),
            }
        except Exception:
            return make_empty_metrics(ide="workspace", source_path=str(session_path))


class AntigravityProvider(BaseProvider):
    name = "antigravity"

    def find_latest_session(self) -> Optional[Tuple[Path, float]]:
        brain_dir = Path.home() / ".gemini" / "antigravity" / "brain"
        if not brain_dir.exists():
            return None
        transcripts = list(brain_dir.glob("*/.system_generated/logs/transcript.jsonl"))
        if not transcripts:
            return None
        transcripts.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return transcripts[0], transcripts[0].stat().st_mtime

    def extract_usage(self, session_path: Path) -> Dict[str, Any]:
        return parse_jsonl_stream(session_path, ide_name="antigravity", filter_type="PLANNER_RESPONSE")


class ClaudeCodeProvider(BaseProvider):
    name = "claude_code"

    def find_latest_session(self) -> Optional[Tuple[Path, float]]:
        candidates: List[Path] = []
        home_claude = Path.home() / ".claude"

        # Projects / sessions / history
        if home_claude.exists():
            candidates.extend(home_claude.glob("projects/**/*.jsonl"))
            candidates.extend(home_claude.glob("sessions/**/*.jsonl"))
            candidates.extend(home_claude.glob("*.jsonl"))

        local_claude = Path(".claude")
        if local_claude.exists():
            candidates.extend(local_claude.glob("**/*.jsonl"))

        if not candidates:
            return None

        candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return candidates[0], candidates[0].stat().st_mtime

    def extract_usage(self, session_path: Path) -> Dict[str, Any]:
        return parse_jsonl_stream(session_path, ide_name="claude_code")


class OpenAICodexProvider(BaseProvider):
    name = "codex"

    def find_latest_session(self) -> Optional[Tuple[Path, float]]:
        candidates: List[Path] = []
        home_openai = Path.home() / ".openai"
        if home_openai.exists():
            candidates.extend(home_openai.glob("sessions/**/*.jsonl"))
            candidates.extend(home_openai.glob("*.jsonl"))
            candidates.extend(home_openai.glob("*.json"))

        local_openai = Path(".openai")
        if local_openai.exists():
            candidates.extend(local_openai.glob("**/*.jsonl"))
            candidates.extend(local_openai.glob("**/*.json"))

        if not candidates:
            return None

        candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return candidates[0], candidates[0].stat().st_mtime

    def extract_usage(self, session_path: Path) -> Dict[str, Any]:
        if session_path.suffix.lower() == ".json":
            try:
                data = json.loads(session_path.read_text(encoding="utf-8", errors="ignore"))
                inp, out, cache, reasoning = normalize_token_payload(data)
                return {
                    "ide": "codex",
                    "source_path": str(session_path),
                    "is_available": True,
                    "last_in": inp,
                    "last_out": out,
                    "last_cache": cache,
                    "last_reasoning": reasoning,
                    "total_in": inp,
                    "total_out": out,
                    "total_cache": cache,
                    "total_reasoning": reasoning,
                    "cache_efficiency": calc_cache_efficiency(cache, inp),
                }
            except Exception:
                return make_empty_metrics(ide="codex", source_path=str(session_path))

        return parse_jsonl_stream(session_path, ide_name="codex")


class GitHubCopilotProvider(BaseProvider):
    name = "copilot"

    def _get_vscode_storage_dirs(self) -> List[Path]:
        dirs = []
        if sys.platform == "win32":
            appdata = os.environ.get("APPDATA")
            if appdata:
                dirs.append(Path(appdata) / "Code" / "User" / "workspaceStorage")
                dirs.append(Path(appdata) / "Code - Insiders" / "User" / "workspaceStorage")
        elif sys.platform == "darwin":
            dirs.append(Path.home() / "Library" / "Application Support" / "Code" / "User" / "workspaceStorage")
        else:
            dirs.append(Path.home() / ".config" / "Code" / "User" / "workspaceStorage")
        return [d for d in dirs if d.exists()]

    def find_latest_session(self) -> Optional[Tuple[Path, float]]:
        candidates: List[Path] = []

        # 1. SQLite state.vscdb in VS Code workspaceStorage
        for ws_dir in self._get_vscode_storage_dirs():
            for db in ws_dir.glob("*/state.vscdb"):
                candidates.append(db)

        # 2. Copilot CLI or local logs
        home_copilot = Path.home() / ".copilot-cli"
        if home_copilot.exists():
            candidates.extend(home_copilot.glob("**/*.jsonl"))
            candidates.extend(home_copilot.glob("**/*.log"))

        if not candidates:
            return None

        candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return candidates[0], candidates[0].stat().st_mtime

    def extract_usage(self, session_path: Path) -> Dict[str, Any]:
        if session_path.suffix.lower() == ".vscdb":
            return self._extract_from_sqlite(session_path)

        # Log or JSONL file
        total_in = 0
        total_out = 0
        total_cache = 0
        total_reasoning = 0
        last_in = 0
        last_out = 0
        last_cache = 0
        has_records = False

        token_re = re.compile(r"tokens?:\s*(?:in[=:]\s*(\d+))?[,\s]*(?:out[=:]\s*(\d+))?[,\s]*(?:cache[=:]\s*(\d+))?", re.IGNORECASE)

        try:
            with open(session_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    # Check JSON
                    if line.strip().startswith("{") and line.strip().endswith("}"):
                        try:
                            d = json.loads(line.strip())
                            inp, out, cache, r = normalize_token_payload(d)
                            if inp or out or cache:
                                has_records = True
                                total_in += inp
                                total_out += out
                                total_cache += cache
                                total_reasoning += r
                                last_in, last_out, last_cache = inp, out, cache
                                continue
                        except Exception:
                            pass

                    # Regex in log lines
                    match = token_re.search(line)
                    if match:
                        inp = int(match.group(1) or 0)
                        out = int(match.group(2) or 0)
                        cache = int(match.group(3) or 0)
                        if inp or out or cache:
                            has_records = True
                            total_in += inp
                            total_out += out
                            total_cache += cache
                            last_in, last_out, last_cache = inp, out, cache
        except Exception:
            pass

        return {
            "ide": "copilot",
            "source_path": str(session_path),
            "is_available": has_records,
            "last_in": last_in,
            "last_out": last_out,
            "last_cache": last_cache,
            "last_reasoning": total_reasoning,
            "total_in": total_in,
            "total_out": total_out,
            "total_cache": total_cache,
            "total_reasoning": total_reasoning,
            "cache_efficiency": calc_cache_efficiency(total_cache, total_in),
        }

    def _extract_from_sqlite(self, db_path: Path) -> Dict[str, Any]:
        total_in = 0
        total_out = 0
        total_cache = 0
        last_in = 0
        last_out = 0
        last_cache = 0
        has_records = False

        try:
            # Open SQLite in read-only URI mode to prevent locks
            uri = f"file:{db_path.as_posix()}?mode=ro"
            conn = sqlite3.connect(uri, uri=True, timeout=1.0)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT value FROM ItemTable WHERE key LIKE '%copilot%' OR key LIKE '%chatdata%' OR key LIKE '%interactive.sessions%'"
            )
            rows = cursor.fetchall()
            conn.close()

            for (val,) in rows:
                if not val:
                    continue
                try:
                    obj = json.loads(val) if isinstance(val, str) else json.loads(val.decode("utf-8", "ignore"))
                    # Recursively walk dictionary/list to find token payloads
                    stack = [obj]
                    while stack:
                        cur = stack.pop()
                        if isinstance(cur, dict):
                            inp, out, cache, _ = normalize_token_payload(cur)
                            if inp or out or cache:
                                has_records = True
                                total_in += inp
                                total_out += out
                                total_cache += cache
                                last_in, last_out, last_cache = inp, out, cache
                            for v in cur.values():
                                if isinstance(v, (dict, list)):
                                    stack.append(v)
                        elif isinstance(cur, list):
                            for item in cur:
                                if isinstance(item, (dict, list)):
                                    stack.append(item)
                except Exception:
                    continue
        except Exception:
            return make_empty_metrics(ide="copilot", source_path=str(db_path))

        return {
            "ide": "copilot",
            "source_path": str(db_path),
            "is_available": has_records,
            "last_in": last_in,
            "last_out": last_out,
            "last_cache": last_cache,
            "last_reasoning": 0,
            "total_in": total_in,
            "total_out": total_out,
            "total_cache": total_cache,
            "total_reasoning": 0,
            "cache_efficiency": calc_cache_efficiency(total_cache, total_in),
        }


class RooCodeClineProvider(BaseProvider):
    name = "roo_code"

    def _get_storage_roots(self) -> List[Path]:
        roots = []
        if sys.platform == "win32":
            appdata = os.environ.get("APPDATA")
            if appdata:
                roots.append(Path(appdata) / "Code" / "User" / "globalStorage")
                roots.append(Path(appdata) / "Cursor" / "User" / "globalStorage")
                roots.append(Path(appdata) / "Windsurf" / "User" / "globalStorage")
        elif sys.platform == "darwin":
            roots.append(Path.home() / "Library" / "Application Support" / "Code" / "User" / "globalStorage")
            roots.append(Path.home() / "Library" / "Application Support" / "Cursor" / "User" / "globalStorage")
        else:
            roots.append(Path.home() / ".config" / "Code" / "User" / "globalStorage")
            roots.append(Path.home() / ".config" / "Cursor" / "User" / "globalStorage")

        return [r for r in roots if r.exists()]

    def find_latest_session(self) -> Optional[Tuple[Path, float]]:
        candidates: List[Path] = []
        ext_names = ["rooveterinaryinc.roo-cline", "saoudrizwan.claude-dev"]

        for storage_root in self._get_storage_roots():
            for ext in ext_names:
                tasks_dir = storage_root / ext / "tasks"
                if tasks_dir.exists():
                    for hist in tasks_dir.glob("*/api_conversation_history.json"):
                        candidates.append(hist)

        if not candidates:
            return None

        candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return candidates[0], candidates[0].stat().st_mtime

    def extract_usage(self, session_path: Path) -> Dict[str, Any]:
        total_in = 0
        total_out = 0
        total_cache = 0
        last_in = 0
        last_out = 0
        last_cache = 0
        has_records = False

        try:
            items = json.loads(session_path.read_text(encoding="utf-8", errors="ignore"))
            if isinstance(items, list):
                for item in items:
                    inp, out, cache, _ = normalize_token_payload(item)
                    if inp or out or cache:
                        has_records = True
                        total_in += inp
                        total_out += out
                        total_cache += cache
                        last_in, last_out, last_cache = inp, out, cache
        except Exception:
            return make_empty_metrics(ide="roo_code", source_path=str(session_path))

        ide_id = "cline" if "claude-dev" in str(session_path).lower() else "roo_code"
        return {
            "ide": ide_id,
            "source_path": str(session_path),
            "is_available": has_records,
            "last_in": last_in,
            "last_out": last_out,
            "last_cache": last_cache,
            "last_reasoning": 0,
            "total_in": total_in,
            "total_out": total_out,
            "total_cache": total_cache,
            "total_reasoning": 0,
            "cache_efficiency": calc_cache_efficiency(total_cache, total_in),
        }


class CursorProvider(BaseProvider):
    name = "cursor"

    def find_latest_session(self) -> Optional[Tuple[Path, float]]:
        candidates: List[Path] = []
        if sys.platform == "win32":
            appdata = os.environ.get("APPDATA")
            if appdata:
                ws_dir = Path(appdata) / "Cursor" / "User" / "workspaceStorage"
                if ws_dir.exists():
                    candidates.extend(ws_dir.glob("*/state.vscdb"))
        elif sys.platform == "darwin":
            ws_dir = Path.home() / "Library" / "Application Support" / "Cursor" / "User" / "workspaceStorage"
            if ws_dir.exists():
                candidates.extend(ws_dir.glob("*/state.vscdb"))
        else:
            ws_dir = Path.home() / ".config" / "Cursor" / "User" / "workspaceStorage"
            if ws_dir.exists():
                candidates.extend(ws_dir.glob("*/state.vscdb"))

        if not candidates:
            return None

        candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return candidates[0], candidates[0].stat().st_mtime

    def extract_usage(self, session_path: Path) -> Dict[str, Any]:
        # Uses Copilot SQLite logic adapted for Cursor
        copilot_prov = GitHubCopilotProvider()
        res = copilot_prov._extract_from_sqlite(session_path)
        res["ide"] = "cursor"
        return res


class WindsurfProvider(BaseProvider):
    name = "windsurf"

    def find_latest_session(self) -> Optional[Tuple[Path, float]]:
        candidates: List[Path] = []
        if sys.platform == "win32":
            appdata = os.environ.get("APPDATA")
            if appdata:
                ws_dir = Path(appdata) / "Windsurf" / "User" / "workspaceStorage"
                if ws_dir.exists():
                    candidates.extend(ws_dir.glob("*/state.vscdb"))
        elif sys.platform == "darwin":
            ws_dir = Path.home() / "Library" / "Application Support" / "Windsurf" / "User" / "workspaceStorage"
            if ws_dir.exists():
                candidates.extend(ws_dir.glob("*/state.vscdb"))
        else:
            ws_dir = Path.home() / ".config" / "Windsurf" / "User" / "workspaceStorage"
            if ws_dir.exists():
                candidates.extend(ws_dir.glob("*/state.vscdb"))

        if not candidates:
            return None

        candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return candidates[0], candidates[0].stat().st_mtime

    def extract_usage(self, session_path: Path) -> Dict[str, Any]:
        copilot_prov = GitHubCopilotProvider()
        res = copilot_prov._extract_from_sqlite(session_path)
        res["ide"] = "windsurf"
        return res


class AiderProvider(BaseProvider):
    name = "aider"

    def find_latest_session(self) -> Optional[Tuple[Path, float]]:
        c = Path(".aider.chat.history.md")
        if c.exists() and c.is_file():
            return c.resolve(), c.stat().st_mtime
        return None

    def extract_usage(self, session_path: Path) -> Dict[str, Any]:
        total_in = 0
        total_out = 0
        token_re = re.compile(r"tokens?:\s*([\d,]+)\s*(?:sent|prompt|in)[^\d]+([\d,]+)\s*(?:received|completion|out)", re.IGNORECASE)
        has_records = False
        try:
            with open(session_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    m = token_re.search(line)
                    if m:
                        inp = int(m.group(1).replace(",", ""))
                        out = int(m.group(2).replace(",", ""))
                        total_in += inp
                        total_out += out
                        has_records = True
        except Exception:
            pass

        return {
            "ide": "aider",
            "source_path": str(session_path),
            "is_available": has_records,
            "last_in": total_in,
            "last_out": total_out,
            "last_cache": 0,
            "last_reasoning": 0,
            "total_in": total_in,
            "total_out": total_out,
            "total_cache": 0,
            "total_reasoning": 0,
            "cache_efficiency": "0.0%",
        }


# =====================================================================
# ENGINE ORCHESTRATION & AUTO-DISCOVERY
# =====================================================================

ALL_PROVIDERS: List[BaseProvider] = [
    EnvVarProvider(),
    WorkspaceTelemetryProvider(),
    AntigravityProvider(),
    ClaudeCodeProvider(),
    OpenAICodexProvider(),
    GitHubCopilotProvider(),
    RooCodeClineProvider(),
    CursorProvider(),
    WindsurfProvider(),
    AiderProvider(),
]


def get_token_usage(
    transcript_path: Optional[str] = None,
    ide_override: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Main entry point for retrieving token usage.
    Maintains 100% backward compatibility with legacy caller signature while
    adding universal multi-IDE resolution.
    """
    # 1. Explicit transcript path passed
    if transcript_path:
        p = Path(transcript_path)
        if p.exists() and p.is_file():
            if p.suffix.lower() == ".json":
                try:
                    data = json.loads(p.read_text(encoding="utf-8", errors="ignore"))
                    inp, out, cache, reasoning = normalize_token_payload(data)
                    tot_in = data.get("total_in", inp)
                    tot_out = data.get("total_out", out)
                    tot_cache = data.get("total_cache", cache)
                    tot_reasoning = data.get("total_reasoning", reasoning)
                    return {
                        "ide": ide_override or data.get("ide", "file"),
                        "source_path": str(p),
                        "is_available": True,
                        "last_in": data.get("last_in", inp),
                        "last_out": data.get("last_out", out),
                        "last_cache": data.get("last_cache", cache),
                        "last_reasoning": data.get("last_reasoning", reasoning),
                        "total_in": tot_in,
                        "total_out": tot_out,
                        "total_cache": tot_cache,
                        "total_reasoning": tot_reasoning,
                        "cache_efficiency": data.get("cache_efficiency") or calc_cache_efficiency(tot_cache, tot_in),
                    }
                except Exception:
                    pass
            return parse_jsonl_stream(p, ide_name=ide_override or "file")
        return make_empty_metrics(ide=ide_override or "unknown", source_path=str(p))

    # 2. Check environment variable override for IDE
    target_ide = (ide_override or os.environ.get("SDD_AGENT_IDE") or os.environ.get("AGENT_IDE") or "").strip().lower()

    # 3. Find candidates
    candidates: List[Tuple[float, BaseProvider, Path]] = []
    for provider in ALL_PROVIDERS:
        if target_ide and provider.name != target_ide:
            # If user explicitly requested an IDE, skip others
            continue
        try:
            res = provider.find_latest_session()
            if res:
                path, mtime = res
                candidates.append((mtime, provider, path))
        except Exception:
            continue

    if not candidates:
        return make_empty_metrics(ide=target_ide or "unknown")

    # Sort by mtime descending (most recently modified session wins!)
    candidates.sort(key=lambda c: c[0], reverse=True)
    best_mtime, best_provider, best_path = candidates[0]

    try:
        metrics = best_provider.extract_usage(best_path)
        return metrics
    except Exception:
        return make_empty_metrics(ide=best_provider.name, source_path=str(best_path))


def render_footer(metrics: Dict[str, Any], turn: int, blocks: int, gate: Any) -> str:
    # Traffic light indicator
    if turn >= 15 or blocks >= 3:
        status_light = "🔴"
    elif turn >= 11 or blocks == 2:
        status_light = "🟡"
    else:
        status_light = "🟢"

    last_in_k = format_k(metrics.get("last_in", 0))
    last_out_k = format_k(metrics.get("last_out", 0))
    last_cache_k = format_k(metrics.get("last_cache", 0))
    tot_in_k = format_k(metrics.get("total_in", 0))
    tot_out_k = format_k(metrics.get("total_out", 0))
    tot_cache_k = format_k(metrics.get("total_cache", 0))
    eff = metrics.get("cache_efficiency", "0.0%")
    ide_label = metrics.get("ide", "unknown")

    footer = (
        f"---\n"
        f"{status_light} **Context Health ({ide_label}):** Turn {turn}/15 | Blocks: {blocks}/2 | Gate: {gate}<br>\n"
        f"&emsp;&emsp;↳ **Tokens (Last Turn):** In {last_in_k} · Out {last_out_k} · Cache {last_cache_k}<br>\n"
        f"&emsp;&emsp;↳ **Tokens (Session Total):** In {tot_in_k} · Out {tot_out_k} · Cache {tot_cache_k} (Hit: {eff})"
    )
    return footer


def main():
    parser = argparse.ArgumentParser(description="SDD Token & Cache Telemetry Tracker (Multi-IDE Agnostic)")
    parser.add_argument("transcript_path", nargs="?", default=None, help="Optional direct path to transcript file")
    parser.add_argument("--transcript", type=str, default=None, help="Explicit path to transcript file")
    parser.add_argument("--ide", type=str, default=None, help="Force specific IDE provider (antigravity, claude_code, copilot, codex, roo_code, cursor, windsurf, aider, workspace, env)")
    parser.add_argument("--format", choices=["json", "footer", "summary"], default="json", help="Output format")
    parser.add_argument("--turn", type=int, default=1, help="Current turn number for footer format (default: 1)")
    parser.add_argument("--blocks", type=int, default=0, help="Current blocks completed for footer format (default: 0)")
    parser.add_argument("--gate", type=str, default="0", help="Current Gate for footer format (default: 0)")

    args = parser.parse_args()

    t_path = args.transcript or args.transcript_path
    usage = get_token_usage(transcript_path=t_path, ide_override=args.ide)

    if args.format == "footer":
        print(render_footer(usage, turn=args.turn, blocks=args.blocks, gate=args.gate))
    elif args.format == "summary":
        print(
            f"[{usage.get('ide')}] In: {format_k(usage.get('total_in', 0))} | "
            f"Out: {format_k(usage.get('total_out', 0))} | "
            f"Cache: {format_k(usage.get('total_cache', 0))} ({usage.get('cache_efficiency', '0.0%')})"
        )
    else:
        print(json.dumps(usage, indent=2))


if __name__ == "__main__":
    main()
