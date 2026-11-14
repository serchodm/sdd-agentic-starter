#!/usr/bin/env python3
"""
SDD Repo-Map Language Parsers (sdd_repo_map_parsers.py)
AST and regex skeleton extractors for 20+ programming languages.
"""

from __future__ import annotations

import ast
import pathlib
import re
from typing import Callable

Rule = tuple[re.Pattern[str], Callable[[re.Match[str]], str | None]]
ParserFn = Callable[[pathlib.Path], list[str]]


# ============================================================================
# 1. PYTHON PARSER (Native AST)
# ============================================================================
def format_py_arg(arg: ast.arg) -> str:
    name = arg.arg
    if arg.annotation:
        try:
            return f"{name}: {ast.unparse(arg.annotation)}"
        except (ValueError, TypeError, AttributeError):
            pass
    return name


def format_py_signature(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    prefix = "async def " if isinstance(node, ast.AsyncFunctionDef) else "def "
    args: list[str] = []
    for a in getattr(node.args, "posonlyargs", []):
        args.append(format_py_arg(a))
    for a in node.args.args:
        args.append(format_py_arg(a))
    if node.args.vararg:
        args.append(f"*{format_py_arg(node.args.vararg)}")
    for a in node.args.kwonlyargs:
        args.append(format_py_arg(a))
    if node.args.kwarg:
        args.append(f"**{format_py_arg(node.args.kwarg)}")

    ret_str = ""
    if node.returns:
        try:
            ret_str = f" -> {ast.unparse(node.returns)}"
        except (ValueError, TypeError, AttributeError):
            pass
    return f"{prefix}{node.name}({', '.join(args)}){ret_str}"


def parse_python(path: pathlib.Path) -> list[str]:
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(content, filename=str(path))
    except (OSError, SyntaxError, ValueError) as exc:
        return [f"  [Parse Error]: {exc}"]

    lines: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            bases = [ast.unparse(b) for b in node.bases]
            base_str = f"({', '.join(bases)})" if bases else ""
            lines.append(f"  class {node.name}{base_str}:")
            for sub in node.body:
                if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    lines.append(f"    {format_py_signature(sub)}")
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            lines.append(f"  {format_py_signature(node)}")
    return lines


# ============================================================================
# 2. REGEX EXTRACTION ENGINE & LANGUAGE RULES
# ============================================================================
def _extract_by_rules(path: pathlib.Path, rules: tuple[Rule, ...]) -> list[str]:
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return [f"  [Read Error]: {exc}"]

    lines: list[str] = []
    for pattern, formatter in rules:
        for match in pattern.finditer(content):
            formatted = formatter(match)
            if formatted is not None:
                lines.append(formatted)
    return lines


def _rule(pattern: str, formatter: Callable[[re.Match[str]], str | None], flags: int = re.MULTILINE) -> Rule:
    return re.compile(pattern, flags), formatter


def _skip_keywords(sig: str, prefixes: tuple[str, ...], indent: str = "    ") -> str | None:
    if any(sig.startswith(k) for k in prefixes):
        return None
    return f"{indent}{sig}"


def _skip_ret_types(ret_type: str, sig: str, excluded: frozenset[str]) -> str | None:
    if ret_type in excluded:
        return None
    return f"    {ret_type} {sig}"


_RULES_TS_JS: tuple[Rule, ...] = (
    _rule(r"export\s+interface\s+([A-Za-z0-9_]+(?:<[^>]+>)?(?:\s+extends\s+[^{]+)?)", lambda m: f"  interface {m.group(1).strip()}", 0),
    _rule(r"export\s+type\s+([A-Za-z0-9_]+(?:<[^>]+>)?)\s*=", lambda m: f"  type {m.group(1).strip()}", 0),
    _rule(r"export\s+(?:default\s+)?(?:async\s+)?function\s+([A-Za-z0-9_]+\s*\([^)]*\)(?:\s*:\s*[^{]+)?)", lambda m: f"  function {m.group(1).strip()}", 0),
    _rule(r"export\s+const\s+([A-Za-z0-9_]+)\s*:\s*React\.FC(?:<([^>]+)>)?", lambda m: f"  component {m.group(1).strip()}{f'<{m.group(2)}>' if m.group(2) else ''}", 0),
    _rule(r"export\s+(?:default\s+)?class\s+([A-Za-z0-9_]+(?:<[^>]+>)?(?:\s+extends\s+[A-Za-z0-9_<>]+)?(?:\s+implements\s+[^{]+)?)", lambda m: f"  class {m.group(1).strip()}", 0),
)

_CSHARP_EXCLUDED = frozenset({"class", "interface", "record", "struct", "namespace", "get", "set"})
_RULES_CSHARP: tuple[Rule, ...] = (
    _rule(r"^\s*namespace\s+([A-Za-z0-9_.]+)", lambda m: f"  namespace {m.group(1).strip()}"),
    _rule(
        r"^\s*(?:\[[^\]]+\]\s*)*(?:public|protected|internal)?\s*(?:static|abstract|sealed|partial)?\s*"
        r"(class|interface|record|struct)\s+([A-Za-z0-9_]+(?:<[^>]+>)?(?:\s*:\s*[^{]+)?)",
        lambda m: f"  {m.group(1)} {m.group(2).strip()}",
    ),
    _rule(
        r"^\s*(?:\[[^\]]+\]\s*)*(?:public|protected)\s+(?:static|virtual|override|async|sealed)?\s*"
        r"([A-Za-z0-9_<>,.\[\]\?]+)\s+([A-Za-z0-9_]+(?:<[^>]+>)?\s*\([^)]*\))",
        lambda m: _skip_ret_types(m.group(1).strip(), m.group(2).strip(), _CSHARP_EXCLUDED),
    ),
)

_JAVA_EXCLUDED = frozenset({"class", "interface", "record", "enum"})
_RULES_JAVA: tuple[Rule, ...] = (
    _rule(r"^\s*package\s+([A-Za-z0-9_.]+);", lambda m: f"  package {m.group(1).strip()}"),
    _rule(
        r"^\s*(?:@[A-Za-z0-9_]+(?:\([^)]*\))?\s*)*(?:public|protected)?\s*(?:static|abstract|final)?\s*"
        r"(class|interface|record|enum)\s+([A-Za-z0-9_]+(?:<[^>]+>)?(?:\s+(?:extends|implements)\s+[^{]+)?)",
        lambda m: f"  {m.group(1)} {m.group(2).strip()}",
    ),
    _rule(
        r"^\s*(?:@[A-Za-z0-9_]+(?:\([^)]*\))?\s*)*(?:public|protected)\s+(?:static|final|synchronized|abstract)?\s*"
        r"([A-Za-z0-9_<>,.\[\]]+)\s+([A-Za-z0-9_]+\s*\([^)]*\))",
        lambda m: _skip_ret_types(m.group(1).strip(), m.group(2).strip(), _JAVA_EXCLUDED),
    ),
)

_RULES_KOTLIN: tuple[Rule, ...] = (
    _rule(r"^\s*package\s+([A-Za-z0-9_.]+)", lambda m: f"  package {m.group(1).strip()}"),
    _rule(
        r"^\s*(?:data\s+|sealed\s+|abstract\s+|open\s+|enum\s+)*(class|interface|object)\s+([A-Za-z0-9_]+(?:<[^>]+>)?(?:\s*:\s*[^{]+)?)",
        lambda m: f"  {m.group(1)} {m.group(2).strip()}",
    ),
    _rule(
        r"^\s*(?:override\s+|suspend\s+|inline\s+|private\s+|protected\s+|public\s+|internal\s+)*fun\s+([A-Za-z0-9_.<>]+\s*\([^)]*\)(?:\s*:\s*[^{=]+)?)",
        lambda m: f"    fun {m.group(1).strip()}",
    ),
)

_RULES_GO: tuple[Rule, ...] = (
    _rule(r"^\s*package\s+([A-Za-z0-9_]+)", lambda m: f"  package {m.group(1).strip()}"),
    _rule(r"^\s*type\s+([A-Za-z0-9_]+)\s+(struct|interface|[A-Za-z0-9_\[\]]+)", lambda m: f"  type {m.group(1)} {m.group(2)}"),
    _rule(
        r"^\s*func\s+(?:\(([^)]+)\)\s+)?([A-Za-z0-9_]+\s*\([^)]*\)(?:\s*[^{]+)?)",
        lambda m: f"  func {f'({m.group(1)}) ' if m.group(1) else ''}{m.group(2).strip()}",
    ),
)

_RULES_RUST: tuple[Rule, ...] = (
    _rule(
        r"^\s*(?:pub(?:\([^)]+\))?\s+)?(struct|enum|trait|union)\s+([A-Za-z0-9_]+(?:<[^>]+>)?(?:\s*:\s*[^{;]+)?)",
        lambda m: f"  {m.group(1)} {m.group(2).strip()}",
    ),
    _rule(
        r"^\s*impl(?:<[^>]+>)?\s+(?:([A-Za-z0-9_<>:]+)\s+for\s+)?([A-Za-z0-9_<>:]+)",
        lambda m: f"  impl {f'{m.group(1)} for ' if m.group(1) else ''}{m.group(2)}",
    ),
    _rule(
        r"^\s*(?:pub(?:\([^)]+\))?\s+)?(?:async\s+)?(?:const\s+)?fn\s+([A-Za-z0-9_]+\s*(?:<[^>]+>)?\s*\([^)]*\)(?:\s*->\s*[^{;]+)?)",
        lambda m: f"    fn {m.group(1).strip()}",
    ),
)

_C_SKIP = ("if", "for", "while", "switch", "catch")
_RULES_C_CPP: tuple[Rule, ...] = (
    _rule(r"^\s*namespace\s+([A-Za-z0-9_:]+)", lambda m: f"  namespace {m.group(1)}"),
    _rule(r"^\s*(?:template\s*<[^>]+>\s*)?(class|struct)\s+([A-Za-z0-9_]+(?:\s*:\s*[^{]+)?)", lambda m: f"  {m.group(1)} {m.group(2).strip()}"),
    _rule(
        r"^\s*(?:[A-Za-z0-9_:<>]+\s+)?([A-Za-z0-9_~]+(?:::?[A-Za-z0-9_~]+)*\s*\([^;)]*\))\s*(?:const)?(?:\s*override)?\s*[{;]",
        lambda m: _skip_keywords(m.group(1).strip(), _C_SKIP),
    ),
)

_RULES_PHP: tuple[Rule, ...] = (
    _rule(r"^\s*namespace\s+([A-Za-z0-9_\\]+);", lambda m: f"  namespace {m.group(1)}"),
    _rule(r"^\s*(?:abstract\s+|final\s+)?(class|interface|trait|enum)\s+([A-Za-z0-9_]+(?:\s+(?:extends|implements)\s+[^{]+)?)", lambda m: f"  {m.group(1)} {m.group(2).strip()}"),
    _rule(r"^\s*(?:public|protected|private)?\s*(?:static)?\s*function\s+([A-Za-z0-9_]+\s*\([^)]*\)(?:\s*:\s*[^{;]+)?)", lambda m: f"    function {m.group(1).strip()}"),
)

_RULES_RUBY: tuple[Rule, ...] = (
    _rule(r"^\s*module\s+([A-Za-z0-9_:]+)", lambda m: f"  module {m.group(1)}"),
    _rule(r"^\s*class\s+([A-Za-z0-9_:]+(?:\s*<\s*[A-Za-z0-9_:]+)?)", lambda m: f"  class {m.group(1)}"),
    _rule(r"^\s*def\s+([A-Za-z0-9_.]+(?:\([^)]*\))?)", lambda m: f"    def {m.group(1)}"),
)

_RULES_SWIFT: tuple[Rule, ...] = (
    _rule(r"^\s*(?:public\s+|open\s+|final\s+)*(class|struct|protocol|enum|actor)\s+([A-Za-z0-9_]+(?:\s*:\s*[^{]+)?)", lambda m: f"  {m.group(1)} {m.group(2).strip()}"),
    _rule(r"^\s*(?:public\s+|open\s+|override\s+|static\s+|mutating\s+)*func\s+([A-Za-z0-9_]+\s*\([^)]*\)(?:\s*(?:async|throws)?\s*(?:->\s*[^{]+)?)?)", lambda m: f"    func {m.group(1).strip()}"),
)

_DART_SKIP = ("if", "for", "while", "switch", "catch", "return")
_RULES_DART: tuple[Rule, ...] = (
    _rule(r"^\s*(?:abstract\s+)?(class|mixin|enum)\s+([A-Za-z0-9_]+(?:\s+(?:extends|with|implements)\s+[^{]+)?)", lambda m: f"  {m.group(1)} {m.group(2).strip()}"),
    _rule(r"^\s*(?:[A-Za-z0-9_<>,?]+\s+)?([A-Za-z0-9_]+\s*\([^)]*\)\s*(?:async\*?|sync\*?)?)\s*[{=>]", lambda m: _skip_keywords(m.group(1).strip(), _DART_SKIP)),
)

_RULES_SCALA: tuple[Rule, ...] = (
    _rule(r"^\s*(?:case\s+)?(class|object|trait)\s+([A-Za-z0-9_]+(?:\[[^\]]+\])?(?:\s+(?:extends|with)\s+[^{]+)?)", lambda m: f"  {m.group(1)} {m.group(2).strip()}"),
    _rule(r"^\s*def\s+([A-Za-z0-9_]+\s*(?:\[[^\]]+\])?\s*\([^)]*\)(?:\s*:\s*[^{=]+)?)", lambda m: f"    def {m.group(1).strip()}"),
)

_RULES_ELIXIR: tuple[Rule, ...] = (
    _rule(r"^\s*defmodule\s+([A-Za-z0-9_.]+)", lambda m: f"  defmodule {m.group(1)}"),
    _rule(r"^\s*(def|defp)\s+([A-Za-z0-9_!?]+(?:\([^)]*\))?)", lambda m: f"    {m.group(1)} {m.group(2)}"),
)

_RULES_SHELL: tuple[Rule, ...] = (
    _rule(r"^\s*(?:function\s+)?([A-Za-z0-9_:-]+)\s*\(\)\s*\{", lambda m: f"  function {m.group(1)}()"),
)

_RULES_POWERSHELL: tuple[Rule, ...] = (
    _rule(r"^\s*class\s+([A-Za-z0-9_]+(?:\s*:\s*[A-Za-z0-9_]+)?)", lambda m: f"  class {m.group(1)}"),
    _rule(r"^\s*function\s+([A-Za-z0-9_-]+)", lambda m: f"  function {m.group(1)}"),
)

_RULES_SQL: tuple[Rule, ...] = (
    _rule(
        r"^\s*CREATE\s+(?:OR\s+REPLACE\s+)?(TABLE|VIEW|PROCEDURE|FUNCTION|INDEX|TRIGGER)\s+(?:IF\s+NOT\s+EXISTS\s+)?([A-Za-z0-9_\".]+)",
        lambda m: f"  CREATE {m.group(1).upper()} {m.group(2).strip()}",
        re.MULTILINE | re.IGNORECASE,
    ),
)

_RULES_SOLIDITY: tuple[Rule, ...] = (
    _rule(r"^\s*(contract|interface|library)\s+([A-Za-z0-9_]+(?:\s+is\s+[^{]+)?)", lambda m: f"  {m.group(1)} {m.group(2).strip()}"),
    _rule(r"^\s*function\s+([A-Za-z0-9_]+\s*\([^)]*\)[^{;]*)", lambda m: f"    function {m.group(1).strip()}"),
)

_RULES_LUA: tuple[Rule, ...] = (
    _rule(r"^\s*function\s+([A-Za-z0-9_:.]+\s*\([^)]*\))", lambda m: f"  function {m.group(1)}"),
)

_RULES_ZIG: tuple[Rule, ...] = (
    _rule(r"^\s*pub\s+const\s+([A-Za-z0-9_]+)\s*=\s*(struct|enum|union)", lambda m: f"  pub const {m.group(1)} = {m.group(2)}"),
    _rule(r"^\s*pub\s+fn\s+([A-Za-z0-9_]+\s*\([^)]*\)[^{]+)", lambda m: f"  pub fn {m.group(1).strip()}"),
)


def parse_ts_js(path: pathlib.Path) -> list[str]:
    return _extract_by_rules(path, _RULES_TS_JS)


def parse_csharp(path: pathlib.Path) -> list[str]:
    return _extract_by_rules(path, _RULES_CSHARP)


def parse_java(path: pathlib.Path) -> list[str]:
    return _extract_by_rules(path, _RULES_JAVA)


def parse_kotlin(path: pathlib.Path) -> list[str]:
    return _extract_by_rules(path, _RULES_KOTLIN)


def parse_go(path: pathlib.Path) -> list[str]:
    return _extract_by_rules(path, _RULES_GO)


def parse_rust(path: pathlib.Path) -> list[str]:
    return _extract_by_rules(path, _RULES_RUST)


def parse_c_cpp(path: pathlib.Path) -> list[str]:
    return _extract_by_rules(path, _RULES_C_CPP)


def parse_php(path: pathlib.Path) -> list[str]:
    return _extract_by_rules(path, _RULES_PHP)


def parse_ruby(path: pathlib.Path) -> list[str]:
    return _extract_by_rules(path, _RULES_RUBY)


def parse_swift(path: pathlib.Path) -> list[str]:
    return _extract_by_rules(path, _RULES_SWIFT)


def parse_dart(path: pathlib.Path) -> list[str]:
    return _extract_by_rules(path, _RULES_DART)


def parse_scala(path: pathlib.Path) -> list[str]:
    return _extract_by_rules(path, _RULES_SCALA)


def parse_elixir(path: pathlib.Path) -> list[str]:
    return _extract_by_rules(path, _RULES_ELIXIR)


def parse_shell(path: pathlib.Path) -> list[str]:
    return _extract_by_rules(path, _RULES_SHELL)


def parse_powershell(path: pathlib.Path) -> list[str]:
    return _extract_by_rules(path, _RULES_POWERSHELL)


def parse_sql(path: pathlib.Path) -> list[str]:
    return _extract_by_rules(path, _RULES_SQL)


def parse_solidity(path: pathlib.Path) -> list[str]:
    return _extract_by_rules(path, _RULES_SOLIDITY)


def parse_lua(path: pathlib.Path) -> list[str]:
    return _extract_by_rules(path, _RULES_LUA)


def parse_zig(path: pathlib.Path) -> list[str]:
    return _extract_by_rules(path, _RULES_ZIG)


EXTENSION_PARSERS: dict[str, ParserFn] = {
    ".py": parse_python,
    ".ts": parse_ts_js,
    ".tsx": parse_ts_js,
    ".js": parse_ts_js,
    ".jsx": parse_ts_js,
    ".mjs": parse_ts_js,
    ".cjs": parse_ts_js,
    ".cs": parse_csharp,
    ".java": parse_java,
    ".kt": parse_kotlin,
    ".kts": parse_kotlin,
    ".go": parse_go,
    ".rs": parse_rust,
    ".c": parse_c_cpp,
    ".h": parse_c_cpp,
    ".cpp": parse_c_cpp,
    ".hpp": parse_c_cpp,
    ".cc": parse_c_cpp,
    ".cxx": parse_c_cpp,
    ".php": parse_php,
    ".rb": parse_ruby,
    ".swift": parse_swift,
    ".dart": parse_dart,
    ".scala": parse_scala,
    ".ex": parse_elixir,
    ".exs": parse_elixir,
    ".sh": parse_shell,
    ".bash": parse_shell,
    ".ps1": parse_powershell,
    ".psm1": parse_powershell,
    ".sql": parse_sql,
    ".sol": parse_solidity,
    ".lua": parse_lua,
    ".zig": parse_zig,
}
