#!/usr/bin/env python3
"""
SDD Deterministic Terminal Output Trimmer (sdd_trim_exec.py)
Wraps DoD and verification commands to compress verbose terminal outputs.
- Success (exit 0): Compresses 100+ lines into a 1-line clean summary.
- Failure (exit != 0): Retains 100% of the failure traceback, assertion, file & line,
  while discarding environment noise, deprecation warnings, and ANSI junk.
"""

import os
import re
import subprocess
import sys

# Windows UTF-8 console output compatibility
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Regex to strip ANSI escape codes
ANSI_ESCAPE = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

# Ignorable noise patterns in test/build outputs
NOISE_PATTERNS = [
    re.compile(r".*DeprecationWarning:.*", re.IGNORECASE),
    re.compile(r".*UserWarning:.*", re.IGNORECASE),
    re.compile(r".*\[notice\] A new release of pip available.*", re.IGNORECASE),
    re.compile(r".*To update, run:.*pip install --upgrade.*", re.IGNORECASE),
    re.compile(r"^\s*$", re.IGNORECASE),
]


def clean_ansi(text: str) -> str:
    return ANSI_ESCAPE.sub("", text)


def filter_noise_lines(lines: list[str]) -> list[str]:
    cleaned = []
    for line in lines:
        stripped = line.strip()
        if any(pat.match(stripped) for pat in NOISE_PATTERNS):
            continue
        cleaned.append(line)
    return cleaned


def summarize_success(cmd_str: str, stdout: str, stderr: str, raw_line_count: int) -> str:
    output = clean_ansi(stdout + "\n" + stderr).strip()
    lines = [l for l in output.splitlines() if l.strip()]

    # Extract pytest / vitest summary if present
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
    raw_combined = clean_ansi(stdout + "\n" + stderr)
    raw_lines = raw_combined.splitlines()
    filtered = filter_noise_lines(raw_lines)

    # If failure trace is still excessively large (> 60 lines), keep the most relevant failure block (tail)
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


def main():
    if len(sys.argv) < 2:
        print("Usage: sdd_trim_exec.py <command-to-execute...>", file=sys.stderr)
        sys.exit(1)

    cmd = sys.argv[1:]
    cmd_str = " ".join(cmd)

    try:
        proc = subprocess.run(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except Exception as exc:
        print(f"❌ [DoD EXECUTION ERROR] Failed to spawn process '{cmd_str}': {exc}", file=sys.stderr)
        sys.exit(1)

    raw_output = proc.stdout + "\n" + proc.stderr
    raw_line_count = len(raw_output.splitlines())

    if proc.returncode == 0:
        print(summarize_success(cmd_str, proc.stdout, proc.stderr, raw_line_count))
        sys.exit(0)
    else:
        print(format_failure(cmd_str, proc.stdout, proc.stderr, proc.returncode), file=sys.stderr)
        sys.exit(proc.returncode)


if __name__ == "__main__":
    main()
