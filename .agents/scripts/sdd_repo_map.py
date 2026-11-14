#!/usr/bin/env python3
"""
SDD Universal AST & Signature Repo-Map Generator (sdd_repo_map.py)
Generates an ultra-compact, token-efficient interface map of codebases
across 20+ programming languages using standard library parsers only.
"""

from __future__ import annotations

import argparse
import pathlib
import sys

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError, OSError):
        pass

if __package__:
    from .sdd_repo_map_parsers import (
        EXTENSION_PARSERS,
        format_py_arg,
        format_py_signature,
        parse_c_cpp,
        parse_csharp,
        parse_dart,
        parse_elixir,
        parse_go,
        parse_java,
        parse_kotlin,
        parse_lua,
        parse_php,
        parse_powershell,
        parse_python,
        parse_ruby,
        parse_rust,
        parse_scala,
        parse_shell,
        parse_solidity,
        parse_sql,
        parse_swift,
        parse_ts_js,
        parse_zig,
    )
else:
    _SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
    if str(_SCRIPT_DIR) not in sys.path:
        sys.path.insert(0, str(_SCRIPT_DIR))
    from sdd_repo_map_parsers import (
        EXTENSION_PARSERS,
        format_py_arg,
        format_py_signature,
        parse_c_cpp,
        parse_csharp,
        parse_dart,
        parse_elixir,
        parse_go,
        parse_java,
        parse_kotlin,
        parse_lua,
        parse_php,
        parse_powershell,
        parse_python,
        parse_ruby,
        parse_rust,
        parse_scala,
        parse_shell,
        parse_solidity,
        parse_sql,
        parse_swift,
        parse_ts_js,
        parse_zig,
    )

# Standard build / dependency folders to ignore across all ecosystems
IGNORED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "dist",
    "build",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "bin",
    "obj",
    "target",
    ".gradle",
    "vendor",
    "out",
    ".next",
    ".nuxt",
    ".angular",
    ".svelte-kit",
    "coverage",
    ".turbo",
}


def collect_source_files(
    target_path: pathlib.Path,
    ignored_dirs: set[str] | frozenset[str] = IGNORED_DIRS,
) -> list[pathlib.Path]:
    """Collects supported source files under target_path, failing closed on missing path."""
    if target_path.is_file():
        return [target_path]
    if target_path.is_dir():
        files: list[pathlib.Path] = []
        for entry in target_path.rglob("*"):
            if not entry.is_file():
                continue
            if entry.suffix.lower() in EXTENSION_PARSERS:
                if any(part in ignored_dirs for part in entry.parts):
                    continue
                files.append(entry)
        files.sort()
        return files
    raise FileNotFoundError(f"Path '{target_path}' does not exist.")


def build_repo_map_lines(target_path: pathlib.Path) -> tuple[list[str], int, int]:
    """Builds formatted repo-map output lines along with (total_files, total_symbols)."""
    files = collect_source_files(target_path)
    total_files = len(files)
    total_symbols = 0
    output: list[str] = [f"=== SDD AST REPO-MAP: {target_path} ({total_files} files scanned) ===\n"]

    cwd = pathlib.Path.cwd()
    for src_file in files:
        parser = EXTENSION_PARSERS.get(src_file.suffix.lower())
        if not parser:
            continue
        rel = src_file.as_posix()
        try:
            rel = src_file.relative_to(cwd).as_posix()
        except ValueError:
            pass

        signatures = parser(src_file)
        if signatures:
            output.append(f"📄 {rel}:")
            for sig in signatures:
                output.append(f"  {sig}")
                total_symbols += 1
            output.append("")

    output.append(f"--- Map complete: {total_symbols} symbols extracted across {total_files} files ---")
    return output, total_files, total_symbols


def generate_map(target_path: pathlib.Path) -> None:
    try:
        output_lines, _, _ = build_repo_map_lines(target_path)
    except FileNotFoundError:
        print(f"❌ [Error] Path '{target_path}' does not exist.", file=sys.stderr)
        sys.exit(1)

    for line in output_lines:
        print(line)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="SDD Universal AST & Signature Repo-Map Generator (20+ languages)"
    )
    parser.add_argument(
        "target",
        nargs="?",
        default=".",
        help="File or directory to scan (default: .)",
    )
    args = parser.parse_args(argv)
    generate_map(pathlib.Path(args.target))
    return 0


__all__ = [
    "EXTENSION_PARSERS",
    "IGNORED_DIRS",
    "build_repo_map_lines",
    "collect_source_files",
    "format_py_arg",
    "format_py_signature",
    "generate_map",
    "main",
    "parse_c_cpp",
    "parse_csharp",
    "parse_dart",
    "parse_elixir",
    "parse_go",
    "parse_java",
    "parse_kotlin",
    "parse_lua",
    "parse_php",
    "parse_powershell",
    "parse_python",
    "parse_ruby",
    "parse_rust",
    "parse_scala",
    "parse_shell",
    "parse_solidity",
    "parse_sql",
    "parse_swift",
    "parse_ts_js",
    "parse_zig",
]

if __name__ == "__main__":
    sys.exit(main())
