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

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError, OSError):
        pass

if __package__:
    from .sdd_token_parsers import (
        build_metrics, calc_cache_efficiency, make_empty_metrics, normalize_token_payload,
        parse_aider_history, parse_copilot_log, parse_json_summary, parse_jsonl_stream,
        parse_roo_code_history, parse_vscode_sqlite,
    )
    from .sdd_token_report import (
        evaluate_context_health, evaluate_context_status, format_json, format_k,
        format_summary, render_footer,
    )
else:
    _SCRIPT_DIR = Path(__file__).resolve().parent
    if str(_SCRIPT_DIR) not in sys.path:
        sys.path.insert(0, str(_SCRIPT_DIR))
    from sdd_token_parsers import (
        build_metrics, calc_cache_efficiency, make_empty_metrics, normalize_token_payload,
        parse_aider_history, parse_copilot_log, parse_json_summary, parse_jsonl_stream,
        parse_roo_code_history, parse_vscode_sqlite,
    )
    from sdd_token_report import (
        evaluate_context_health, evaluate_context_status, format_json, format_k,
        format_summary, render_footer,
    )


def _latest_session_from_paths(candidates: Iterable[Path]) -> Optional[Tuple[Path, float]]:
    best_path: Optional[Path] = None
    best_mtime = -1.0
    for candidate in candidates:
        try:
            if candidate.is_file():
                mtime = candidate.stat().st_mtime
                if mtime > best_mtime:
                    best_mtime = mtime
                    best_path = candidate
        except OSError:
            continue
    if best_path is None:
        return None
    return best_path, best_mtime


def _vscode_user_dirs(app_names: Tuple[str, ...], leaf: str) -> List[Path]:
    bases: List[Path] = []
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        if appdata:
            for app in app_names:
                bases.append(Path(appdata) / app / "User" / leaf)
    elif sys.platform == "darwin":
        support = Path.home() / "Library" / "Application Support"
        for app in app_names:
            bases.append(support / app / "User" / leaf)
    else:
        cfg = Path.home() / ".config"
        for app in app_names:
            bases.append(cfg / app / "User" / leaf)
    return [d for d in bases if d.exists()]


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
        usage_file = os.environ.get("SDD_TOKEN_USAGE_FILE") or os.environ.get("OPENAI_USAGE_FILE")
        if usage_file:
            p = Path(usage_file)
            if p.exists() and p.is_file():
                return p, p.stat().st_mtime

        transcript = os.environ.get("SDD_TRANSCRIPT_PATH")
        if transcript:
            p = Path(transcript)
            if p.exists() and p.is_file():
                return p, p.stat().st_mtime

        if os.environ.get("SDD_TOKENS_TOTAL_IN") or os.environ.get("SDD_TOKENS_IN"):
            return Path("ENV_OVERRIDE"), 9999999999.0

        return None

    def extract_usage(self, session_path: Path) -> Dict[str, Any]:
        if str(session_path) == "ENV_OVERRIDE":
            total_in = int(os.environ.get("SDD_TOKENS_TOTAL_IN") or os.environ.get("SDD_TOKENS_IN") or 0)
            total_out = int(os.environ.get("SDD_TOKENS_TOTAL_OUT") or os.environ.get("SDD_TOKENS_OUT") or 0)
            total_cache = int(os.environ.get("SDD_TOKENS_TOTAL_CACHE") or os.environ.get("SDD_TOKENS_CACHE") or 0)
            return build_metrics(
                ide="env",
                source_path="ENV_OVERRIDE",
                is_available=True,
                last_in=int(os.environ.get("SDD_TOKENS_LAST_IN") or total_in),
                last_out=int(os.environ.get("SDD_TOKENS_LAST_OUT") or total_out),
                last_cache=int(os.environ.get("SDD_TOKENS_LAST_CACHE") or total_cache),
                total_in=total_in,
                total_out=total_out,
                total_cache=total_cache,
            )

        if session_path.suffix.lower() == ".json":
            parsed = parse_json_summary(session_path, default_ide="env")
            if parsed is not None:
                return parsed

        return parse_jsonl_stream(session_path, ide_name="env")


class WorkspaceTelemetryProvider(BaseProvider):
    name = "workspace"

    def find_latest_session(self) -> Optional[Tuple[Path, float]]:
        candidates = (
            Path(".agents/telemetry/tokens.json"),
            Path(".agents/telemetry/session_tokens.json"),
            Path(".agents/session_tokens.json"),
        )
        for candidate in candidates:
            if candidate.exists() and candidate.is_file() and candidate.stat().st_size > 0:
                return candidate.resolve(), candidate.stat().st_mtime
        return None

    def extract_usage(self, session_path: Path) -> Dict[str, Any]:
        parsed = parse_json_summary(session_path, default_ide="workspace")
        if parsed is not None:
            return parsed
        return make_empty_metrics(ide="workspace", source_path=str(session_path))


class AntigravityProvider(BaseProvider):
    name = "antigravity"

    def find_latest_session(self) -> Optional[Tuple[Path, float]]:
        brain_dir = Path.home() / ".gemini" / "antigravity" / "brain"
        if not brain_dir.exists():
            return None
        return _latest_session_from_paths(brain_dir.glob("*/.system_generated/logs/transcript.jsonl"))

    def extract_usage(self, session_path: Path) -> Dict[str, Any]:
        return parse_jsonl_stream(session_path, ide_name="antigravity", filter_type="PLANNER_RESPONSE")


class ClaudeCodeProvider(BaseProvider):
    name = "claude_code"

    def find_latest_session(self) -> Optional[Tuple[Path, float]]:
        candidates: List[Path] = []
        home_claude = Path.home() / ".claude"
        if home_claude.exists():
            candidates.extend(home_claude.glob("projects/**/*.jsonl"))
            candidates.extend(home_claude.glob("sessions/**/*.jsonl"))
            candidates.extend(home_claude.glob("*.jsonl"))
        local_claude = Path(".claude")
        if local_claude.exists():
            candidates.extend(local_claude.glob("**/*.jsonl"))
        return _latest_session_from_paths(candidates)

    def extract_usage(self, session_path: Path) -> Dict[str, Any]:
        return parse_jsonl_stream(session_path, ide_name="claude_code")


class OpenAICodexProvider(BaseProvider):
    name = "codex"

    def find_latest_session(self) -> Optional[Tuple[Path, float]]:
        candidates: List[Path] = []
        for root, patterns in (
            (Path.home() / ".openai", ("sessions/**/*.jsonl", "*.jsonl", "*.json")),
            (Path(".openai"), ("**/*.jsonl", "**/*.json")),
        ):
            if root.exists():
                for pat in patterns:
                    candidates.extend(root.glob(pat))
        return _latest_session_from_paths(candidates)

    def extract_usage(self, session_path: Path) -> Dict[str, Any]:
        if session_path.suffix.lower() == ".json":
            parsed = parse_json_summary(session_path, default_ide="codex", ide_override="codex")
            if parsed is not None:
                return parsed
            return make_empty_metrics(ide="codex", source_path=str(session_path))
        return parse_jsonl_stream(session_path, ide_name="codex")


class GitHubCopilotProvider(BaseProvider):
    name = "copilot"

    def _get_vscode_storage_dirs(self) -> List[Path]:
        return _vscode_user_dirs(("Code", "Code - Insiders"), "workspaceStorage")

    def find_latest_session(self) -> Optional[Tuple[Path, float]]:
        candidates: List[Path] = []
        for ws_dir in self._get_vscode_storage_dirs():
            candidates.extend(ws_dir.glob("*/state.vscdb"))
        home_copilot = Path.home() / ".copilot-cli"
        if home_copilot.exists():
            candidates.extend(home_copilot.glob("**/*.jsonl"))
            candidates.extend(home_copilot.glob("**/*.log"))
        return _latest_session_from_paths(candidates)

    def _extract_from_sqlite(self, db_path: Path) -> Dict[str, Any]:
        return parse_vscode_sqlite(db_path, ide="copilot")

    def extract_usage(self, session_path: Path) -> Dict[str, Any]:
        if session_path.suffix.lower() == ".vscdb":
            return self._extract_from_sqlite(session_path)
        return parse_copilot_log(session_path)


class RooCodeClineProvider(BaseProvider):
    name = "roo_code"

    def _get_storage_roots(self) -> List[Path]:
        apps = ("Code", "Cursor", "Windsurf") if sys.platform == "win32" else ("Code", "Cursor")
        return _vscode_user_dirs(apps, "globalStorage")

    def find_latest_session(self) -> Optional[Tuple[Path, float]]:
        candidates: List[Path] = []
        for storage_root in self._get_storage_roots():
            for ext in ("rooveterinaryinc.roo-cline", "saoudrizwan.claude-dev"):
                tasks_dir = storage_root / ext / "tasks"
                if tasks_dir.exists():
                    candidates.extend(tasks_dir.glob("*/api_conversation_history.json"))
        return _latest_session_from_paths(candidates)

    def extract_usage(self, session_path: Path) -> Dict[str, Any]:
        return parse_roo_code_history(session_path)


class _WorkspaceSqliteProvider(BaseProvider):
    _app_name: str = ""

    def find_latest_session(self) -> Optional[Tuple[Path, float]]:
        candidates: List[Path] = []
        for ws_dir in _vscode_user_dirs((self._app_name,), "workspaceStorage"):
            candidates.extend(ws_dir.glob("*/state.vscdb"))
        return _latest_session_from_paths(candidates)

    def extract_usage(self, session_path: Path) -> Dict[str, Any]:
        return parse_vscode_sqlite(session_path, ide=self.name)


class CursorProvider(_WorkspaceSqliteProvider):
    name = "cursor"
    _app_name = "Cursor"


class WindsurfProvider(_WorkspaceSqliteProvider):
    name = "windsurf"
    _app_name = "Windsurf"


class AiderProvider(BaseProvider):
    name = "aider"

    def find_latest_session(self) -> Optional[Tuple[Path, float]]:
        candidate = Path(".aider.chat.history.md")
        if candidate.exists() and candidate.is_file():
            return candidate.resolve(), candidate.stat().st_mtime
        return None

    def extract_usage(self, session_path: Path) -> Dict[str, Any]:
        return parse_aider_history(session_path)


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
    Main entry point for retrieving token usage across all supported IDEs.
    """
    if transcript_path:
        p = Path(transcript_path)
        if p.exists() and p.is_file():
            if p.suffix.lower() == ".json":
                parsed = parse_json_summary(p, default_ide="file", ide_override=ide_override)
                if parsed is not None:
                    return parsed
            return parse_jsonl_stream(p, ide_name=ide_override or "file")
        print(f"[WARN] Transcript file not found: '{p}'", file=sys.stderr)
        return make_empty_metrics(ide=ide_override or "unknown", source_path=str(p))

    target_ide = (ide_override or os.environ.get("SDD_AGENT_IDE") or os.environ.get("AGENT_IDE") or "").strip().lower()

    candidates: List[Tuple[float, BaseProvider, Path]] = []
    for provider in ALL_PROVIDERS:
        if target_ide and provider.name != target_ide:
            continue
        try:
            res = provider.find_latest_session()
        except (OSError, RuntimeError, ValueError) as exc:
            print(f"[WARN] Provider '{provider.name}' discovery failed: {exc}", file=sys.stderr)
            continue
        if res:
            path, mtime = res
            candidates.append((mtime, provider, path))

    if not candidates:
        return make_empty_metrics(ide=target_ide or "unknown")

    candidates.sort(key=lambda c: c[0], reverse=True)
    _, best_provider, best_path = candidates[0]

    try:
        return best_provider.extract_usage(best_path)
    except (OSError, RuntimeError, ValueError, TypeError) as exc:
        print(f"[WARN] Provider '{best_provider.name}' extraction failed: {exc}", file=sys.stderr)
        return make_empty_metrics(ide=best_provider.name, source_path=str(best_path))


def main() -> int:
    parser = argparse.ArgumentParser(description="SDD Token & Cache Telemetry Tracker (Multi-IDE Agnostic)")
    parser.add_argument("transcript_path", nargs="?", default=None, help="Optional direct path to transcript file")
    parser.add_argument("--transcript", type=str, default=None, help="Explicit path to transcript file")
    parser.add_argument(
        "--ide",
        type=str,
        default=None,
        help="Force specific IDE provider (antigravity, claude_code, copilot, codex, roo_code, cursor, windsurf, aider, workspace, env)",
    )
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
        print(format_summary(usage))
    else:
        print(format_json(usage))
    return 0


__all__ = [
    "ALL_PROVIDERS", "AiderProvider", "AntigravityProvider", "BaseProvider", "ClaudeCodeProvider",
    "CursorProvider", "EnvVarProvider", "GitHubCopilotProvider", "OpenAICodexProvider",
    "RooCodeClineProvider", "WindsurfProvider", "WorkspaceTelemetryProvider",
    "build_metrics", "calc_cache_efficiency", "evaluate_context_health", "evaluate_context_status",
    "format_json", "format_k", "format_summary", "get_token_usage", "main", "make_empty_metrics",
    "normalize_token_payload", "parse_aider_history", "parse_copilot_log", "parse_json_summary",
    "parse_jsonl_stream", "parse_roo_code_history", "parse_vscode_sqlite", "render_footer",
]

if __name__ == "__main__":
    sys.exit(main())
