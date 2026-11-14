#!/usr/bin/env python3
"""
SDD Token Telemetry Parsers & Payload Normalization (sdd_token_parsers.py)
Provides IDE-agnostic token payload normalization and log/database parsers
for Antigravity, Claude Code, OpenAI Codex, GitHub Copilot, Cursor, Windsurf,
Roo Code / Cline, Aider, and Workspace JSON telemetry.
"""

from __future__ import annotations

import json
import re
import sqlite3
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

_INPUT_KEYS = ("input_tokens", "prompt_tokens", "tokensIn", "promptTokens", "inputTokens", "in")
_OUTPUT_KEYS = ("output_tokens", "completion_tokens", "tokensOut", "completionTokens", "outputTokens", "out")
_CACHE_KEYS = ("cache_read_tokens", "cache_read_input_tokens", "cacheReads", "cachedTokens", "cached_tokens", "cache")
_REASONING_KEYS = ("reasoning_tokens", "thinking_tokens")

_COPILOT_TOKEN_RE = re.compile(
    r"tokens?:\s*(?:in[=:]\s*(\d+))?[,\s]*(?:out[=:]\s*(\d+))?[,\s]*(?:cache[=:]\s*(\d+))?",
    re.IGNORECASE,
)
_AIDER_TOKEN_RE = re.compile(
    r"tokens?:\s*([\d,]+)\s*(?:sent|prompt|in)[^\d]+([\d,]+)\s*(?:received|completion|out)",
    re.IGNORECASE,
)


def calc_cache_efficiency(total_cache: int, total_in: int) -> str:
    total_context = total_cache + total_in
    if total_context > 0:
        return f"{(total_cache / total_context * 100):.1f}%"
    return "0.0%"


def build_metrics(
    ide: str, source_path: Optional[str], is_available: bool, *,
    last_in: int = 0, last_out: int = 0, last_cache: int = 0, last_reasoning: int = 0,
    total_in: int = 0, total_out: int = 0, total_cache: int = 0, total_reasoning: int = 0,
    cache_efficiency: Optional[str] = None,
) -> Dict[str, Any]:
    return {
        "ide": ide, "source_path": source_path, "is_available": is_available,
        "last_in": last_in, "last_out": last_out, "last_cache": last_cache, "last_reasoning": last_reasoning,
        "total_in": total_in, "total_out": total_out, "total_cache": total_cache, "total_reasoning": total_reasoning,
        "cache_efficiency": cache_efficiency or calc_cache_efficiency(total_cache, total_in),
    }


def make_empty_metrics(ide: str = "unknown", source_path: Optional[str] = None) -> Dict[str, Any]:
    return build_metrics(ide=ide, source_path=source_path, is_available=False)


def _first_truthy(mapping: Dict[str, Any], keys: Tuple[str, ...]) -> Any:
    for key in keys:
        val = mapping.get(key)
        if val:
            return val
    return 0


def _coerce_int(value: Any, field_name: str) -> int:
    if value is None or value == 0:
        return 0
    if isinstance(value, bool):
        raise ValueError(f"Boolean value is not valid for token field '{field_name}'")
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str):
        return int(value.strip())
    raise TypeError(f"Unsupported type {type(value).__name__} for token field '{field_name}'")


def normalize_token_payload(data: Any) -> Tuple[int, int, int, int]:
    """
    Extracts (inp, out, cache, reasoning) from arbitrary JSON payloads
    emitted by Google, OpenAI, Anthropic, Copilot, Roo Code, etc.
    """
    if not isinstance(data, dict):
        return 0, 0, 0, 0

    usage = data.get("usage") if isinstance(data.get("usage"), dict) else data

    inp = _first_truthy(usage, _INPUT_KEYS)
    out = _first_truthy(usage, _OUTPUT_KEYS)
    cache = _first_truthy(usage, _CACHE_KEYS)

    ptd = usage.get("prompt_tokens_details") or data.get("prompt_tokens_details")
    if isinstance(ptd, dict) and not cache:
        cache = ptd.get("cached_tokens", 0)

    reasoning = _first_truthy(usage, _REASONING_KEYS)
    ctd = usage.get("completion_tokens_details") or data.get("completion_tokens_details")
    if isinstance(ctd, dict) and not reasoning:
        reasoning = ctd.get("reasoning_tokens", 0)

    return (
        _coerce_int(inp, "input_tokens"),
        _coerce_int(out, "output_tokens"),
        _coerce_int(cache, "cache_tokens"),
        _coerce_int(reasoning, "reasoning_tokens"),
    )


def parse_json_summary(
    path: Path,
    default_ide: str,
    ide_override: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Parses a single JSON object containing summary and/or normalized usage fields."""
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError(f"Expected JSON object, got {type(data).__name__}")
        inp, out, cache, reasoning = normalize_token_payload(data)
        tot_in = _coerce_int(data.get("total_in", inp), "total_in")
        tot_out = _coerce_int(data.get("total_out", out), "total_out")
        tot_cache = _coerce_int(data.get("total_cache", cache), "total_cache")
        tot_reasoning = _coerce_int(data.get("total_reasoning", reasoning), "total_reasoning")
        return build_metrics(
            ide=ide_override or data.get("ide", default_ide),
            source_path=str(path),
            is_available=True,
            last_in=_coerce_int(data.get("last_in", inp), "last_in"),
            last_out=_coerce_int(data.get("last_out", out), "last_out"),
            last_cache=_coerce_int(data.get("last_cache", cache), "last_cache"),
            last_reasoning=_coerce_int(data.get("last_reasoning", reasoning), "last_reasoning"),
            total_in=tot_in,
            total_out=tot_out,
            total_cache=tot_cache,
            total_reasoning=tot_reasoning,
            cache_efficiency=data.get("cache_efficiency"),
        )
    except (OSError, json.JSONDecodeError, ValueError, TypeError) as exc:
        print(f"[WARN] Failed to parse JSON summary '{path}': {exc}", file=sys.stderr)
        return None


def parse_jsonl_stream(path: Path, ide_name: str, filter_type: Optional[str] = None) -> Dict[str, Any]:
    """Generic parser for JSONL transcripts (Antigravity, Claude, OpenAI, etc.)."""
    total_in = total_out = total_cache = total_reasoning = 0
    last_in = last_out = last_cache = last_reasoning = 0
    has_records = False

    try:
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    data = json.loads(stripped)
                except json.JSONDecodeError:
                    continue
                if not isinstance(data, dict):
                    continue
                if filter_type and data.get("type") != filter_type:
                    continue
                try:
                    inp, out, cache, reasoning = normalize_token_payload(data)
                except (ValueError, TypeError) as exc:
                    print(f"[WARN] Skipping malformed record in '{path}': {exc}", file=sys.stderr)
                    continue
                if inp or out or cache or reasoning:
                    has_records = True
                    total_in += inp
                    total_out += out
                    total_cache += cache
                    total_reasoning += reasoning
                    last_in, last_out, last_cache, last_reasoning = inp, out, cache, reasoning
    except OSError as exc:
        print(f"[WARN] Failed to read JSONL transcript '{path}': {exc}", file=sys.stderr)
        return make_empty_metrics(ide=ide_name, source_path=str(path))

    return build_metrics(
        ide=ide_name, source_path=str(path), is_available=has_records,
        last_in=last_in, last_out=last_out, last_cache=last_cache, last_reasoning=last_reasoning,
        total_in=total_in, total_out=total_out, total_cache=total_cache, total_reasoning=total_reasoning,
    )


def parse_copilot_log(path: Path) -> Dict[str, Any]:
    """Parses GitHub Copilot CLI JSONL or plain-text log streams."""
    total_in = total_out = total_cache = total_reasoning = 0
    last_in = last_out = last_cache = last_reasoning = 0
    has_records = False

    try:
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                stripped = line.strip()
                if stripped.startswith("{") and stripped.endswith("}"):
                    try:
                        data = json.loads(stripped)
                        inp, out, cache, reasoning = normalize_token_payload(data)
                        if inp or out or cache or reasoning:
                            has_records = True
                            total_in += inp
                            total_out += out
                            total_cache += cache
                            total_reasoning += reasoning
                            last_in, last_out, last_cache, last_reasoning = inp, out, cache, reasoning
                            continue
                    except (json.JSONDecodeError, ValueError, TypeError):
                        pass

                match = _COPILOT_TOKEN_RE.search(line)
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
    except OSError as exc:
        print(f"[WARN] Failed to read Copilot log '{path}': {exc}", file=sys.stderr)
        return make_empty_metrics(ide="copilot", source_path=str(path))

    return build_metrics(
        ide="copilot", source_path=str(path), is_available=has_records,
        last_in=last_in, last_out=last_out, last_cache=last_cache, last_reasoning=last_reasoning,
        total_in=total_in, total_out=total_out, total_cache=total_cache, total_reasoning=total_reasoning,
    )


_CONSUMED_DETAIL_KEYS = frozenset({"usage", "prompt_tokens_details", "completion_tokens_details"})


def _walk_json_tokens(root: Any) -> Tuple[int, int, int, int, int, int, bool]:
    total_in = total_out = total_cache = 0
    last_in = last_out = last_cache = 0
    has_records = False
    stack = [root]
    while stack:
        cur = stack.pop()
        if isinstance(cur, dict):
            try:
                inp, out, cache, _ = normalize_token_payload(cur)
            except (ValueError, TypeError) as exc:
                print(f"[WARN] Skipping malformed SQLite token payload: {exc}", file=sys.stderr)
                inp = out = cache = 0
            found_here = bool(inp or out or cache)
            if found_here:
                has_records = True
                total_in += inp
                total_out += out
                total_cache += cache
                last_in, last_out, last_cache = inp, out, cache
            for key, val in cur.items():
                if found_here and key in _CONSUMED_DETAIL_KEYS:
                    continue
                if isinstance(val, (dict, list)):
                    stack.append(val)
        elif isinstance(cur, list):
            for item in cur:
                if isinstance(item, (dict, list)):
                    stack.append(item)
    return total_in, total_out, total_cache, last_in, last_out, last_cache, has_records


def parse_vscode_sqlite(db_path: Path, ide: str = "copilot") -> Dict[str, Any]:
    """Extracts chat token usage from VS Code / Cursor / Windsurf state.vscdb SQLite."""
    total_in = total_out = total_cache = 0
    last_in = last_out = last_cache = 0
    has_records = False
    conn: Optional[sqlite3.Connection] = None

    try:
        uri = f"file:{db_path.as_posix()}?mode=ro"
        conn = sqlite3.connect(uri, uri=True, timeout=1.0)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT value FROM ItemTable WHERE key LIKE '%copilot%' OR key LIKE '%chatdata%' OR key LIKE '%interactive.sessions%'"
        )
        rows = cursor.fetchall()
    except (sqlite3.Error, OSError) as exc:
        print(f"[WARN] Failed to read SQLite telemetry '{db_path}': {exc}", file=sys.stderr)
        return make_empty_metrics(ide=ide, source_path=str(db_path))
    finally:
        if conn is not None:
            conn.close()

    for (val,) in rows:
        if not val:
            continue
        try:
            text = val if isinstance(val, str) else val.decode("utf-8", "replace")
            obj = json.loads(text)
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        t_in, t_out, t_cache, l_in, l_out, l_cache, found = _walk_json_tokens(obj)
        if found:
            has_records = True
            total_in += t_in
            total_out += t_out
            total_cache += t_cache
            last_in, last_out, last_cache = l_in, l_out, l_cache

    return build_metrics(
        ide=ide, source_path=str(db_path), is_available=has_records,
        last_in=last_in, last_out=last_out, last_cache=last_cache,
        total_in=total_in, total_out=total_out, total_cache=total_cache,
    )


def parse_roo_code_history(session_path: Path) -> Dict[str, Any]:
    """Parses Roo Code / Cline api_conversation_history.json arrays."""
    total_in = total_out = total_cache = 0
    last_in = last_out = last_cache = 0
    has_records = False

    try:
        items = json.loads(session_path.read_text(encoding="utf-8", errors="replace"))
        if not isinstance(items, list):
            raise ValueError(f"Expected JSON array in '{session_path}'")
        for item in items:
            inp, out, cache, _ = normalize_token_payload(item)
            if inp or out or cache:
                has_records = True
                total_in += inp
                total_out += out
                total_cache += cache
                last_in, last_out, last_cache = inp, out, cache
    except (OSError, json.JSONDecodeError, ValueError, TypeError) as exc:
        print(f"[WARN] Failed to parse Roo Code history '{session_path}': {exc}", file=sys.stderr)
        return make_empty_metrics(ide="roo_code", source_path=str(session_path))

    ide_id = "cline" if "claude-dev" in str(session_path).lower() else "roo_code"
    return build_metrics(
        ide=ide_id, source_path=str(session_path), is_available=has_records,
        last_in=last_in, last_out=last_out, last_cache=last_cache,
        total_in=total_in, total_out=total_out, total_cache=total_cache,
    )


def parse_aider_history(session_path: Path) -> Dict[str, Any]:
    """Parses token counters from .aider.chat.history.md."""
    total_in = total_out = 0
    has_records = False

    try:
        with open(session_path, "r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                match = _AIDER_TOKEN_RE.search(line)
                if match:
                    total_in += int(match.group(1).replace(",", ""))
                    total_out += int(match.group(2).replace(",", ""))
                    has_records = True
    except OSError as exc:
        print(f"[WARN] Failed to read Aider history '{session_path}': {exc}", file=sys.stderr)
        return make_empty_metrics(ide="aider", source_path=str(session_path))

    return build_metrics(
        ide="aider",
        source_path=str(session_path),
        is_available=has_records,
        last_in=total_in,
        last_out=total_out,
        total_in=total_in,
        total_out=total_out,
        cache_efficiency="0.0%",
    )
