#!/usr/bin/env python3
"""
SDD Token & Cache Telemetry Tracker
Reads the conversation transcript to extract input, output, and cache read tokens.
"""

import json
import os
import sys
from pathlib import Path


def find_latest_transcript() -> Path | None:
    brain_dir = Path.home() / ".gemini" / "antigravity" / "brain"
    if not brain_dir.exists():
        return None
    transcripts = list(brain_dir.glob("*/.system_generated/logs/transcript.jsonl"))
    if not transcripts:
        return None
    transcripts.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return transcripts[0]


def get_token_usage(transcript_path: str = None) -> dict:
    if transcript_path:
        path = Path(transcript_path)
    else:
        path = find_latest_transcript()

    if not path or not path.exists():
        return {
            "last_in": 0,
            "last_out": 0,
            "last_cache": 0,
            "total_in": 0,
            "total_out": 0,
            "total_cache": 0,
            "cache_efficiency": "0.0%",
        }

    total_in = 0
    total_out = 0
    total_cache = 0
    last_in = 0
    last_out = 0
    last_cache = 0

    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                if data.get("type") == "PLANNER_RESPONSE":
                    inp = data.get("input_tokens", 0)
                    out = data.get("output_tokens", 0)
                    cache = data.get("cache_read_tokens", 0)
                    total_in += inp
                    total_out += out
                    total_cache += cache
                    last_in = inp
                    last_out = out
                    last_cache = cache
            except Exception:
                continue

    total_context_read = total_in + total_cache
    efficiency = (
        f"{(total_cache / total_context_read * 100):.1f}%"
        if total_context_read > 0
        else "0.0%"
    )

    return {
        "last_in": last_in,
        "last_out": last_out,
        "last_cache": last_cache,
        "total_in": total_in,
        "total_out": total_out,
        "total_cache": total_cache,
        "cache_efficiency": efficiency,
    }


if __name__ == "__main__":
    t_path = sys.argv[1] if len(sys.argv) > 1 else None
    usage = get_token_usage(t_path)
    print(json.dumps(usage, indent=2))
