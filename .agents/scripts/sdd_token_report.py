#!/usr/bin/env python3
"""
SDD Token Telemetry Context Health Evaluator & Renderer (sdd_token_report.py)
Evaluates SDD context semaphore thresholds (green/yellow/red) and renders
footer, summary, and JSON reports for orchestrator and CLI telemetry.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Tuple

TURN_YELLOW_THRESHOLD = 11
TURN_RED_THRESHOLD = 15
BLOCK_YELLOW_THRESHOLD = 2
BLOCK_RED_THRESHOLD = 3


def format_k(n: int) -> str:
    return f"{n / 1000:.1f}k"


def evaluate_context_health(turn: int, blocks: int) -> Tuple[str, str]:
    """Returns (emoji_light, level_name) for SDD Context Semaphore thresholds."""
    if turn >= TURN_RED_THRESHOLD or blocks >= BLOCK_RED_THRESHOLD:
        return "🔴", "red"
    if turn >= TURN_YELLOW_THRESHOLD or blocks == BLOCK_YELLOW_THRESHOLD:
        return "🟡", "yellow"
    return "🟢", "green"


def evaluate_context_status(
    metrics: Dict[str, Any],
    turn: int,
    blocks: int,
    gate: Any,
) -> Dict[str, Any]:
    """Produces a structured context health evaluation summary."""
    status_light, status_level = evaluate_context_health(turn, blocks)
    return {
        "status_light": status_light,
        "status_level": status_level,
        "should_handoff": status_level == "red",
        "turn": turn,
        "blocks": blocks,
        "gate": gate,
        "ide": metrics.get("ide", "unknown"),
        "cache_efficiency": metrics.get("cache_efficiency", "0.0%"),
    }


def render_footer(metrics: Dict[str, Any], turn: int, blocks: int, gate: Any) -> str:
    """Renders the canonical SDD Context Health telemetry footer."""
    status_light, _ = evaluate_context_health(turn, blocks)

    last_in_k = format_k(metrics.get("last_in", 0))
    last_out_k = format_k(metrics.get("last_out", 0))
    last_cache_k = format_k(metrics.get("last_cache", 0))
    tot_in_k = format_k(metrics.get("total_in", 0))
    tot_out_k = format_k(metrics.get("total_out", 0))
    tot_cache_k = format_k(metrics.get("total_cache", 0))
    eff = metrics.get("cache_efficiency", "0.0%")
    ide_label = metrics.get("ide", "unknown")

    return (
        f"---\n"
        f"{status_light} **Context Health ({ide_label}):** Turn {turn}/15 | Blocks: {blocks}/2 | Gate: {gate}<br>\n"
        f"&emsp;&emsp;↳ **Tokens (Last Turn):** In {last_in_k} · Out {last_out_k} · Cache {last_cache_k}<br>\n"
        f"&emsp;&emsp;↳ **Tokens (Session Total):** In {tot_in_k} · Out {tot_out_k} · Cache {tot_cache_k} (Hit: {eff})"
    )


def format_summary(usage: Dict[str, Any]) -> str:
    """Formats a single-line human-readable telemetry summary."""
    return (
        f"[{usage.get('ide')}] In: {format_k(usage.get('total_in', 0))} | "
        f"Out: {format_k(usage.get('total_out', 0))} | "
        f"Cache: {format_k(usage.get('total_cache', 0))} ({usage.get('cache_efficiency', '0.0%')})"
    )


def format_json(usage: Dict[str, Any]) -> str:
    """Formats telemetry metrics as indented JSON."""
    return json.dumps(usage, indent=2)
