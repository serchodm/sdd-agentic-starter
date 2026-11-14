#!/usr/bin/env python3
"""
SDD Deterministic Terminal Output Trimmer (sdd_trim_exec.py)
Wraps DoD and verification commands with shell=False to compress verbose terminal outputs.
- Success (exit 0): Compresses 100+ lines into a 1-line clean summary.
- Failure (exit != 0): Retains the failure traceback, assertion, file & line,
  while discarding environment noise, deprecation warnings, and ANSI junk.
"""

from __future__ import annotations

import os
import re
import shlex
import subprocess
import sys

# Windows UTF-8 console output compatibility
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

ANSI_ESCAPE = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

NOISE_PATTERNS = [
    re.compile(r".*DeprecationWarning:.*", re.IGNORECASE),
    re.compile(r".*UserWarning:.*", re.IGNORECASE),
    re.compile(r".*\[notice\] A new release of pip available.*", re.IGNORECASE),
    re.compile(r".*To update, run:.*pip install --upgrade.*", re.IGNORECASE),
    re.compile(r"^\s*$", re.IGNORECASE),
]

FORBIDDEN_SINGLE_STR_TOKENS: tuple[str, ...] = (
    "&&",
    "||",
    "&",
    "|",
    ";",
    ">",
    "<",
    "`",
    "$(",
    "\n",
    "\r",
    "\x00",
)

FORBIDDEN_ARGV_OPERATORS: frozenset[str] = frozenset(
    {"&", "&&", "|", "||", ";", ">", ">>", "<", "<<", "1>", "2>", "2>&1"}
)


def clean_ansi(text: str) -> str:
    """Strip ANSI escape sequences from command output."""
    return ANSI_ESCAPE.sub("", text)


def filter_noise_lines(lines: list[str]) -> list[str]:
    """Filter ignorable warning and blank lines from failure output."""
    cleaned = []
    for line in lines:
        stripped = line.strip()
        if any(pat.match(stripped) for pat in NOISE_PATTERNS):
            continue
        cleaned.append(line)
    return cleaned


def _unwrap_nt_quotes(tokens: list[str]) -> list[str]:
    unwrapped: list[str] = []
    for tok in tokens:
        if len(tok) >= 2 and tok[0] == tok[-1] and tok[0] in ('"', "'"):
            unwrapped.append(tok[1:-1])
        else:
            unwrapped.append(tok)
    return unwrapped


def parse_command_args(raw_args: list[str]) -> list[str]:
    """
    Parse command arguments safely for shell=False execution.
    Supports:
      1. Explicit `-- <executable> [args...]`
      2. Single command string parsed via shlex.split after rejecting shell operators
      3. Pre-split argv list without standalone shell chaining/redirection operators
    """
    if not raw_args:
        raise ValueError("Usage: sdd_trim_exec.py [--] <command-to-execute...>")

    if raw_args[0] == "--":
        cmd = raw_args[1:]
        if not cmd or not cmd[0].strip():
            raise ValueError("No command provided after '--'.")
        if any("\x00" in arg for arg in cmd):
            raise ValueError("Null byte disallowed in command arguments.")
        return cmd

    if len(raw_args) == 1:
        raw_cmd = raw_args[0]
        if not raw_cmd.strip():
            raise ValueError("Command string cannot be empty.")
        for bad in FORBIDDEN_SINGLE_STR_TOKENS:
            if bad in raw_cmd:
                raise ValueError(
                    f"Unsafe shell metacharacter or operator {bad!r} rejected in single command string. "
                    "Use '-- <executable> <args...>' to pass literal arguments safely."
                )
        is_posix = os.name != "nt"
        tokens = shlex.split(raw_cmd, posix=is_posix)
        if not is_posix:
            tokens = _unwrap_nt_quotes(tokens)
        if not tokens or not tokens[0].strip():
            raise ValueError("Parsed command is empty.")
        return tokens

    for arg in raw_args:
        if "\x00" in arg:
            raise ValueError("Null byte disallowed in command arguments.")
        if arg in FORBIDDEN_ARGV_OPERATORS:
            raise ValueError(
                f"Unsafe shell operator token {arg!r} rejected. "
                "Use '-- <executable> <args...>' if literal arguments are intended."
            )
    if not raw_args[0].strip():
        raise ValueError("Command executable cannot be empty.")
    return list(raw_args)


def summarize_success(cmd_str: str, stdout: str, stderr: str, raw_line_count: int) -> str:
    """Summarize passing command output into a compact single-line status."""
    output = clean_ansi(stdout + "\n" + stderr).strip()
    lines = [line for line in output.splitlines() if line.strip()]

    summary_line = ""
    for line in reversed(lines):
        if re.search(r"(\d+\s+passed|\d+\s+failed|test files|tests)", line, re.IGNORECASE):
            summary_line = line.strip()
            break

    if not summary_line and lines:
        summary_line = lines[-1].strip()

    saved_lines = max(0, raw_line_count - 1)
    if summary_line:
        return f"✅ [DoD OK] {summary_line} (Trimmed {saved_lines} verbose lines)"
    return f"✅ [DoD OK] Command finished successfully (Trimmed {saved_lines} lines)"


def format_failure(cmd_str: str, stdout: str, stderr: str, return_code: int) -> str:
    """Format failing command output while keeping relevant tracebacks."""
    raw_combined = clean_ansi(stdout + "\n" + stderr)
    raw_lines = raw_combined.splitlines()
    filtered = filter_noise_lines(raw_lines)

    if len(filtered) > 60:
        header = filtered[:5]
        tail = filtered[-50:]
        filtered = header + [f"\n... [Trimmed {len(filtered) - 55} intermediate setup lines] ...\n"] + tail

    formatted_trace = "\n".join(filtered).strip()
    return (
        f"❌ [DoD FAILED - Exit Code {return_code}]\n"
        f"Command: {cmd_str}\n"
        f"--- Targeted Failure Trace ---\n"
        f"{formatted_trace}"
    )


def main(argv: list[str] | None = None) -> int:
    """Execute wrapped command with shell=False and compress output."""
    raw_args = sys.argv[1:] if argv is None else list(argv)
    try:
        cmd = parse_command_args(raw_args)
    except ValueError as exc:
        print(f"❌ [DoD REJECTED] {exc}", file=sys.stderr)
        return 1

    cmd_str = " ".join(cmd)
    try:
        proc = subprocess.run(
            cmd,
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except Exception as exc:
        print(f"❌ [DoD EXECUTION ERROR] Failed to spawn process '{cmd_str}': {exc}", file=sys.stderr)
        return 1

    raw_output = proc.stdout + "\n" + proc.stderr
    raw_line_count = len(raw_output.splitlines())

    if proc.returncode == 0:
        print(summarize_success(cmd_str, proc.stdout, proc.stderr, raw_line_count))
        return 0

    print(format_failure(cmd_str, proc.stdout, proc.stderr, proc.returncode), file=sys.stderr)
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main())
