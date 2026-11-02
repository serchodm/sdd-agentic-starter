#!/usr/bin/env python3
"""
SDD Universal AST & Signature Repo-Map Generator (sdd_repo_map.py)
Generates an ultra-compact, token-efficient interface map of codebases.
Supports 20+ top programming languages across all major software ecosystems:
- Python (.py): Native ast parser (classes, methods, signatures, return types).
- TypeScript & JavaScript (.ts, .tsx, .js, .jsx, .mjs, .cjs): Classes, interfaces, types, functions, React.FC.
- C# (.cs): Namespaces, classes, interfaces, records, structs, methods, properties.
- Java (.java): Packages, classes, interfaces, records, enums, methods.
- Kotlin (.kt, .kts): Packages, classes, objects, interfaces, top-level/member funs.
- Go (.go): Packages, structs, interfaces, type defs, methods with receivers, funcs.
- Rust (.rs): Structs, enums, traits, impl blocks, functions with return types.
- C & C++ (.c, .h, .cpp, .hpp, .cc, .cxx): Classes, structs, functions, namespaces.
- PHP (.php): Namespaces, classes, interfaces, traits, methods.
- Ruby (.rb): Modules, classes, def methods.
- Swift (.swift): Classes, structs, protocols, enums, funcs.
- Dart (.dart): Classes, abstract classes, mixins, enums, functions.
- Scala (.scala): Packages, objects, classes, traits, case classes, defs.
- Elixir (.ex, .exs): Defmodule, def, defp macros.
- Shell & Bash (.sh, .bash): Function definitions.
- PowerShell (.ps1, .psm1): Functions, classes.
- SQL (.sql): CREATE TABLE, VIEW, PROCEDURE, FUNCTION.
- Solidity (.sol): Contracts, interfaces, libraries, functions.
- Lua (.lua): Functions and table functions.
- Zig (.zig): Pub const struct/enum/union, pub fn.

Reduces token cost by 90-95% when agents only need to know what signatures exist.
Zero external dependencies (uses standard library only: ast, re, pathlib, sys).
"""

import ast
import os
import pathlib
import re
import sys

# Windows UTF-8 console output compatibility
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Standard build / dependency folders to ignore across all ecosystems
IGNORED_DIRS = {
    ".git", ".venv", "venv", "env", "node_modules", "dist", "build",
    "__pycache__", ".pytest_cache", ".mypy_cache",
    "bin", "obj",             # .NET
    "target",                 # Rust / Maven
    ".gradle",                # Gradle
    "vendor",                 # Go / PHP / Ruby
    "out", ".next", ".nuxt",  # Frontend frameworks
    ".angular", ".svelte-kit",
    "coverage", ".turbo"
}


# ============================================================================
# 1. PYTHON PARSER (Native AST)
# ============================================================================
def format_py_arg(arg: ast.arg) -> str:
    name = arg.arg
    if arg.annotation:
        try:
            ann = ast.unparse(arg.annotation)
            return f"{name}: {ann}"
        except Exception:
            pass
    return name


def format_py_signature(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    prefix = "async def " if isinstance(node, ast.AsyncFunctionDef) else "def "
    args = []
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

    arg_str = ", ".join(args)
    ret_str = ""
    if node.returns:
        try:
            ret_str = f" -> {ast.unparse(node.returns)}"
        except Exception:
            pass
    return f"{prefix}{node.name}({arg_str}){ret_str}"


def parse_python(path: pathlib.Path) -> list[str]:
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(content, filename=str(path))
    except Exception as exc:
        return [f"  [Parse Error]: {exc}"]

    lines = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            bases = [ast.unparse(b) for b in node.bases]
            base_str = f"({', '.join(bases)})" if bases else ""
            lines.append(f"  class {node.name}{base_str}:")
            for sub in node.body:
                if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    sig = format_py_signature(sub)
                    lines.append(f"    {sig}")
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            sig = format_py_signature(node)
            lines.append(f"  {sig}")
    return lines


# ============================================================================
# 2. TYPESCRIPT & JAVASCRIPT PARSER
# ============================================================================
def parse_ts_js(path: pathlib.Path) -> list[str]:
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        return [f"  [Read Error]: {exc}"]

    lines = []
    for m in re.finditer(r"export\s+interface\s+([A-Za-z0-9_]+(?:<[^>]+>)?(?:\s+extends\s+[^{]+)?)", content):
        lines.append(f"  interface {m.group(1).strip()}")

    for m in re.finditer(r"export\s+type\s+([A-Za-z0-9_]+(?:<[^>]+>)?)\s*=", content):
        lines.append(f"  type {m.group(1).strip()}")

    for m in re.finditer(r"export\s+(?:default\s+)?(?:async\s+)?function\s+([A-Za-z0-9_]+\s*\([^)]*\)(?:\s*:\s*[^{]+)?)", content):
        lines.append(f"  function {m.group(1).strip()}")

    for m in re.finditer(r"export\s+const\s+([A-Za-z0-9_]+)\s*:\s*React\.FC(?:<([^>]+)>)?", content):
        props = f"<{m.group(2)}>" if m.group(2) else ""
        lines.append(f"  component {m.group(1).strip()}{props}")

    for m in re.finditer(r"export\s+(?:default\s+)?class\s+([A-Za-z0-9_]+(?:<[^>]+>)?(?:\s+extends\s+[A-Za-z0-9_<>]+)?(?:\s+implements\s+[^{]+)?)", content):
        lines.append(f"  class {m.group(1).strip()}")

    return lines


# ============================================================================
# 3. C# (.NET) PARSER
# ============================================================================
def parse_csharp(path: pathlib.Path) -> list[str]:
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        return [f"  [Read Error]: {exc}"]

    lines = []
    # Namespaces
    for m in re.finditer(r"^\s*namespace\s+([A-Za-z0-9_.]+)", content, re.MULTILINE):
        lines.append(f"  namespace {m.group(1).strip()}")

    # Classes, Interfaces, Records, Structs
    type_pat = re.compile(
        r"^\s*(?:\[[^\]]+\]\s*)*(?:public|protected|internal)?\s*(?:static|abstract|sealed|partial)?\s*"
        r"(class|interface|record|struct)\s+([A-Za-z0-9_]+(?:<[^>]+>)?(?:\s*:\s*[^{]+)?)",
        re.MULTILINE
    )
    for m in type_pat.finditer(content):
        kind, name = m.group(1), m.group(2).strip()
        lines.append(f"  {kind} {name}")

    # Public/Protected Methods
    method_pat = re.compile(
        r"^\s*(?:\[[^\]]+\]\s*)*(?:public|protected)\s+(?:static|virtual|override|async|sealed)?\s*"
        r"([A-Za-z0-9_<>,.\[\]\?]+)\s+([A-Za-z0-9_]+(?:<[^>]+>)?\s*\([^)]*\))",
        re.MULTILINE
    )
    for m in method_pat.finditer(content):
        ret_type, sig = m.group(1).strip(), m.group(2).strip()
        if ret_type not in {"class", "interface", "record", "struct", "namespace", "get", "set"}:
            lines.append(f"    {ret_type} {sig}")

    return lines


# ============================================================================
# 4. JAVA PARSER
# ============================================================================
def parse_java(path: pathlib.Path) -> list[str]:
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        return [f"  [Read Error]: {exc}"]

    lines = []
    # Package
    for m in re.finditer(r"^\s*package\s+([A-Za-z0-9_.]+);", content, re.MULTILINE):
        lines.append(f"  package {m.group(1).strip()}")

    # Classes, Interfaces, Records, Enums
    type_pat = re.compile(
        r"^\s*(?:@[A-Za-z0-9_]+(?:\([^)]*\))?\s*)*(?:public|protected)?\s*(?:static|abstract|final)?\s*"
        r"(class|interface|record|enum)\s+([A-Za-z0-9_]+(?:<[^>]+>)?(?:\s+(?:extends|implements)\s+[^{]+)?)",
        re.MULTILINE
    )
    for m in type_pat.finditer(content):
        kind, name = m.group(1), m.group(2).strip()
        lines.append(f"  {kind} {name}")

    # Methods
    method_pat = re.compile(
        r"^\s*(?:@[A-Za-z0-9_]+(?:\([^)]*\))?\s*)*(?:public|protected)\s+(?:static|final|synchronized|abstract)?\s*"
        r"([A-Za-z0-9_<>,.\[\]]+)\s+([A-Za-z0-9_]+\s*\([^)]*\))",
        re.MULTILINE
    )
    for m in method_pat.finditer(content):
        ret_type, sig = m.group(1).strip(), m.group(2).strip()
        if ret_type not in {"class", "interface", "record", "enum"}:
            lines.append(f"    {ret_type} {sig}")

    return lines


# ============================================================================
# 5. KOTLIN PARSER
# ============================================================================
def parse_kotlin(path: pathlib.Path) -> list[str]:
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        return [f"  [Read Error]: {exc}"]

    lines = []
    for m in re.finditer(r"^\s*package\s+([A-Za-z0-9_.]+)", content, re.MULTILINE):
        lines.append(f"  package {m.group(1).strip()}")

    type_pat = re.compile(
        r"^\s*(?:data\s+|sealed\s+|abstract\s+|open\s+|enum\s+)*(class|interface|object)\s+([A-Za-z0-9_]+(?:<[^>]+>)?(?:\s*:\s*[^{]+)?)",
        re.MULTILINE
    )
    for m in type_pat.finditer(content):
        lines.append(f"  {m.group(1)} {m.group(2).strip()}")

    fun_pat = re.compile(
        r"^\s*(?:override\s+|suspend\s+|inline\s+|private\s+|protected\s+|public\s+|internal\s+)*fun\s+([A-Za-z0-9_.<>]+\s*\([^)]*\)(?:\s*:\s*[^{=]+)?)",
        re.MULTILINE
    )
    for m in fun_pat.finditer(content):
        lines.append(f"    fun {m.group(1).strip()}")

    return lines


# ============================================================================
# 6. GO PARSER
# ============================================================================
def parse_go(path: pathlib.Path) -> list[str]:
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        return [f"  [Read Error]: {exc}"]

    lines = []
    for m in re.finditer(r"^\s*package\s+([A-Za-z0-9_]+)", content, re.MULTILINE):
        lines.append(f"  package {m.group(1).strip()}")

    # Types: struct, interface, aliases
    for m in re.finditer(r"^\s*type\s+([A-Za-z0-9_]+)\s+(struct|interface|[A-Za-z0-9_\[\]]+)", content, re.MULTILINE):
        lines.append(f"  type {m.group(1)} {m.group(2)}")

    # Functions & Methods with receivers
    for m in re.finditer(r"^\s*func\s+(?:\(([^)]+)\)\s+)?([A-Za-z0-9_]+\s*\([^)]*\)(?:\s*[^{]+)?)", content, re.MULTILINE):
        receiver = f"({m.group(1)}) " if m.group(1) else ""
        sig = m.group(2).strip()
        lines.append(f"  func {receiver}{sig}")

    return lines


# ============================================================================
# 7. RUST PARSER
# ============================================================================
def parse_rust(path: pathlib.Path) -> list[str]:
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        return [f"  [Read Error]: {exc}"]

    lines = []
    # Structs, Enums, Traits
    type_pat = re.compile(r"^\s*(?:pub(?:\([^)]+\))?\s+)?(struct|enum|trait|union)\s+([A-Za-z0-9_]+(?:<[^>]+>)?(?:\s*:\s*[^{;]+)?)", re.MULTILINE)
    for m in type_pat.finditer(content):
        lines.append(f"  {m.group(1)} {m.group(2).strip()}")

    # Impl blocks
    for m in re.finditer(r"^\s*impl(?:<[^>]+>)?\s+(?:([A-Za-z0-9_<>:]+)\s+for\s+)?([A-Za-z0-9_<>:]+)", content, re.MULTILINE):
        trait_part = f"{m.group(1)} for " if m.group(1) else ""
        lines.append(f"  impl {trait_part}{m.group(2)}")

    # Functions
    fn_pat = re.compile(r"^\s*(?:pub(?:\([^)]+\))?\s+)?(?:async\s+)?(?:const\s+)?fn\s+([A-Za-z0-9_]+\s*(?:<[^>]+>)?\s*\([^)]*\)(?:\s*->\s*[^{;]+)?)", re.MULTILINE)
    for m in fn_pat.finditer(content):
        lines.append(f"    fn {m.group(1).strip()}")

    return lines


# ============================================================================
# 8. C & C++ PARSER
# ============================================================================
def parse_c_cpp(path: pathlib.Path) -> list[str]:
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        return [f"  [Read Error]: {exc}"]

    lines = []
    # Namespaces
    for m in re.finditer(r"^\s*namespace\s+([A-Za-z0-9_:]+)", content, re.MULTILINE):
        lines.append(f"  namespace {m.group(1)}")

    # Classes, Structs
    for m in re.finditer(r"^\s*(?:template\s*<[^>]+>\s*)?(class|struct)\s+([A-Za-z0-9_]+(?:\s*:\s*[^{]+)?)", content, re.MULTILINE):
        lines.append(f"  {m.group(1)} {m.group(2).strip()}")

    # Function declarations/definitions (heuristic)
    func_pat = re.compile(r"^\s*(?:[A-Za-z0-9_:<>]+\s+)?([A-Za-z0-9_~]+(?:::?[A-Za-z0-9_~]+)*\s*\([^;)]*\))\s*(?:const)?(?:\s*override)?\s*[{;]", re.MULTILINE)
    for m in func_pat.finditer(content):
        sig = m.group(1).strip()
        if not any(sig.startswith(k) for k in ["if", "for", "while", "switch", "catch"]):
            lines.append(f"    {sig}")

    return lines


# ============================================================================
# 9. PHP PARSER
# ============================================================================
def parse_php(path: pathlib.Path) -> list[str]:
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        return [f"  [Read Error]: {exc}"]

    lines = []
    for m in re.finditer(r"^\s*namespace\s+([A-Za-z0-9_\\]+);", content, re.MULTILINE):
        lines.append(f"  namespace {m.group(1)}")

    type_pat = re.compile(r"^\s*(?:abstract\s+|final\s+)?(class|interface|trait|enum)\s+([A-Za-z0-9_]+(?:\s+(?:extends|implements)\s+[^{]+)?)", re.MULTILINE)
    for m in type_pat.finditer(content):
        lines.append(f"  {m.group(1)} {m.group(2).strip()}")

    fn_pat = re.compile(r"^\s*(?:public|protected|private)?\s*(?:static)?\s*function\s+([A-Za-z0-9_]+\s*\([^)]*\)(?:\s*:\s*[^{;]+)?)", re.MULTILINE)
    for m in fn_pat.finditer(content):
        lines.append(f"    function {m.group(1).strip()}")

    return lines


# ============================================================================
# 10. RUBY PARSER
# ============================================================================
def parse_ruby(path: pathlib.Path) -> list[str]:
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        return [f"  [Read Error]: {exc}"]

    lines = []
    for m in re.finditer(r"^\s*module\s+([A-Za-z0-9_:]+)", content, re.MULTILINE):
        lines.append(f"  module {m.group(1)}")

    for m in re.finditer(r"^\s*class\s+([A-Za-z0-9_:]+(?:\s*<\s*[A-Za-z0-9_:]+)?)", content, re.MULTILINE):
        lines.append(f"  class {m.group(1)}")

    for m in re.finditer(r"^\s*def\s+([A-Za-z0-9_.]+(?:\([^)]*\))?)", content, re.MULTILINE):
        lines.append(f"    def {m.group(1)}")

    return lines


# ============================================================================
# 11. SWIFT PARSER
# ============================================================================
def parse_swift(path: pathlib.Path) -> list[str]:
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        return [f"  [Read Error]: {exc}"]

    lines = []
    type_pat = re.compile(r"^\s*(?:public\s+|open\s+|final\s+)*(class|struct|protocol|enum|actor)\s+([A-Za-z0-9_]+(?:\s*:\s*[^{]+)?)", re.MULTILINE)
    for m in type_pat.finditer(content):
        lines.append(f"  {m.group(1)} {m.group(2).strip()}")

    fn_pat = re.compile(r"^\s*(?:public\s+|open\s+|override\s+|static\s+|mutating\s+)*func\s+([A-Za-z0-9_]+\s*\([^)]*\)(?:\s*(?:async|throws)?\s*(?:->\s*[^{]+)?)?)", re.MULTILINE)
    for m in fn_pat.finditer(content):
        lines.append(f"    func {m.group(1).strip()}")

    return lines


# ============================================================================
# 12. DART PARSER (Flutter)
# ============================================================================
def parse_dart(path: pathlib.Path) -> list[str]:
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        return [f"  [Read Error]: {exc}"]

    lines = []
    type_pat = re.compile(r"^\s*(?:abstract\s+)?(class|mixin|enum)\s+([A-Za-z0-9_]+(?:\s+(?:extends|with|implements)\s+[^{]+)?)", re.MULTILINE)
    for m in type_pat.finditer(content):
        lines.append(f"  {m.group(1)} {m.group(2).strip()}")

    fn_pat = re.compile(r"^\s*(?:[A-Za-z0-9_<>,?]+\s+)?([A-Za-z0-9_]+\s*\([^)]*\)\s*(?:async\*?|sync\*?)?)\s*[{=>]", re.MULTILINE)
    for m in fn_pat.finditer(content):
        sig = m.group(1).strip()
        if not any(sig.startswith(k) for k in ["if", "for", "while", "switch", "catch", "return"]):
            lines.append(f"    {sig}")

    return lines


# ============================================================================
# 13. SCALA PARSER
# ============================================================================
def parse_scala(path: pathlib.Path) -> list[str]:
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        return [f"  [Read Error]: {exc}"]

    lines = []
    for m in re.finditer(r"^\s*(?:case\s+)?(class|object|trait)\s+([A-Za-z0-9_]+(?:\[[^\]]+\])?(?:\s+(?:extends|with)\s+[^{]+)?)", content, re.MULTILINE):
        lines.append(f"  {m.group(1)} {m.group(2).strip()}")

    for m in re.finditer(r"^\s*def\s+([A-Za-z0-9_]+\s*(?:\[[^\]]+\])?\s*\([^)]*\)(?:\s*:\s*[^{=]+)?)", content, re.MULTILINE):
        lines.append(f"    def {m.group(1).strip()}")

    return lines


# ============================================================================
# 14. ELIXIR PARSER
# ============================================================================
def parse_elixir(path: pathlib.Path) -> list[str]:
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        return [f"  [Read Error]: {exc}"]

    lines = []
    for m in re.finditer(r"^\s*defmodule\s+([A-Za-z0-9_.]+)", content, re.MULTILINE):
        lines.append(f"  defmodule {m.group(1)}")

    for m in re.finditer(r"^\s*(def|defp)\s+([A-Za-z0-9_!?]+(?:\([^)]*\))?)", content, re.MULTILINE):
        lines.append(f"    {m.group(1)} {m.group(2)}")

    return lines


# ============================================================================
# 15. SHELL & BASH PARSER
# ============================================================================
def parse_shell(path: pathlib.Path) -> list[str]:
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        return [f"  [Read Error]: {exc}"]

    lines = []
    for m in re.finditer(r"^\s*(?:function\s+)?([A-Za-z0-9_:-]+)\s*\(\)\s*\{", content, re.MULTILINE):
        lines.append(f"  function {m.group(1)}()")
    return lines


# ============================================================================
# 16. POWERSHELL PARSER
# ============================================================================
def parse_powershell(path: pathlib.Path) -> list[str]:
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        return [f"  [Read Error]: {exc}"]

    lines = []
    for m in re.finditer(r"^\s*class\s+([A-Za-z0-9_]+(?:\s*:\s*[A-Za-z0-9_]+)?)", content, re.MULTILINE):
        lines.append(f"  class {m.group(1)}")

    for m in re.finditer(r"^\s*function\s+([A-Za-z0-9_-]+)", content, re.MULTILINE):
        lines.append(f"  function {m.group(1)}")
    return lines


# ============================================================================
# 17. SQL (DDL / Schemas) PARSER
# ============================================================================
def parse_sql(path: pathlib.Path) -> list[str]:
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        return [f"  [Read Error]: {exc}"]

    lines = []
    pat = re.compile(
        r"^\s*CREATE\s+(?:OR\s+REPLACE\s+)?(TABLE|VIEW|PROCEDURE|FUNCTION|INDEX|TRIGGER)\s+(?:IF\s+NOT\s+EXISTS\s+)?([A-Za-z0-9_\".]+)",
        re.MULTILINE | re.IGNORECASE
    )
    for m in pat.finditer(content):
        kind, name = m.group(1).upper(), m.group(2).strip()
        lines.append(f"  CREATE {kind} {name}")
    return lines


# ============================================================================
# 18. SOLIDITY PARSER (Smart Contracts)
# ============================================================================
def parse_solidity(path: pathlib.Path) -> list[str]:
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        return [f"  [Read Error]: {exc}"]

    lines = []
    for m in re.finditer(r"^\s*(contract|interface|library)\s+([A-Za-z0-9_]+(?:\s+is\s+[^{]+)?)", content, re.MULTILINE):
        lines.append(f"  {m.group(1)} {m.group(2).strip()}")

    for m in re.finditer(r"^\s*function\s+([A-Za-z0-9_]+\s*\([^)]*\)[^{;]*)", content, re.MULTILINE):
        lines.append(f"    function {m.group(1).strip()}")
    return lines


# ============================================================================
# 19. LUA PARSER
# ============================================================================
def parse_lua(path: pathlib.Path) -> list[str]:
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        return [f"  [Read Error]: {exc}"]

    lines = []
    for m in re.finditer(r"^\s*function\s+([A-Za-z0-9_:.]+\s*\([^)]*\))", content, re.MULTILINE):
        lines.append(f"  function {m.group(1)}")
    return lines


# ============================================================================
# 20. ZIG PARSER
# ============================================================================
def parse_zig(path: pathlib.Path) -> list[str]:
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        return [f"  [Read Error]: {exc}"]

    lines = []
    for m in re.finditer(r"^\s*pub\s+const\s+([A-Za-z0-9_]+)\s*=\s*(struct|enum|union)", content, re.MULTILINE):
        lines.append(f"  pub const {m.group(1)} = {m.group(2)}")

    for m in re.finditer(r"^\s*pub\s+fn\s+([A-Za-z0-9_]+\s*\([^)]*\)[^{]+)", content, re.MULTILINE):
        lines.append(f"  pub fn {m.group(1).strip()}")
    return lines


# ============================================================================
# EXTENSION DISPATCH TABLE
# ============================================================================
EXTENSION_PARSERS = {
    # 1. Python
    ".py": parse_python,
    # 2. TypeScript & JavaScript
    ".ts": parse_ts_js,
    ".tsx": parse_ts_js,
    ".js": parse_ts_js,
    ".jsx": parse_ts_js,
    ".mjs": parse_ts_js,
    ".cjs": parse_ts_js,
    # 3. C# (.NET)
    ".cs": parse_csharp,
    # 4. Java
    ".java": parse_java,
    # 5. Kotlin
    ".kt": parse_kotlin,
    ".kts": parse_kotlin,
    # 6. Go
    ".go": parse_go,
    # 7. Rust
    ".rs": parse_rust,
    # 8. C & C++
    ".c": parse_c_cpp,
    ".h": parse_c_cpp,
    ".cpp": parse_c_cpp,
    ".hpp": parse_c_cpp,
    ".cc": parse_c_cpp,
    ".cxx": parse_c_cpp,
    # 9. PHP
    ".php": parse_php,
    # 10. Ruby
    ".rb": parse_ruby,
    # 11. Swift
    ".swift": parse_swift,
    # 12. Dart (Flutter)
    ".dart": parse_dart,
    # 13. Scala
    ".scala": parse_scala,
    # 14. Elixir
    ".ex": parse_elixir,
    ".exs": parse_elixir,
    # 15. Shell & Bash
    ".sh": parse_shell,
    ".bash": parse_shell,
    # 16. PowerShell
    ".ps1": parse_powershell,
    ".psm1": parse_powershell,
    # 17. SQL
    ".sql": parse_sql,
    # 18. Solidity
    ".sol": parse_solidity,
    # 19. Lua
    ".lua": parse_lua,
    # 20. Zig
    ".zig": parse_zig,
}


def generate_map(target_path: pathlib.Path) -> None:
    if target_path.is_file():
        files = [target_path]
    elif target_path.is_dir():
        files = []
        for p in target_path.rglob("*"):
            if not p.is_file():
                continue
            if p.suffix.lower() in EXTENSION_PARSERS:
                parts = p.parts
                if any(x in parts for x in IGNORED_DIRS):
                    continue
                files.append(p)
    else:
        print(f"❌ [Error] Path '{target_path}' does not exist.", file=sys.stderr)
        sys.exit(1)

    files.sort()
    total_files = len(files)
    total_symbols = 0

    print(f"=== SDD AST REPO-MAP: {target_path} ({total_files} files scanned) ===\n")

    for f in files:
        parser = EXTENSION_PARSERS.get(f.suffix.lower())
        if not parser:
            continue

        rel = f.as_posix()
        try:
            rel = f.relative_to(pathlib.Path.cwd()).as_posix()
        except ValueError:
            pass

        signatures = parser(f)
        if signatures:
            print(f"📄 {rel}:")
            for sig in signatures:
                print(f"  {sig}")
                total_symbols += 1
            print()

    print(f"--- Map complete: {total_symbols} symbols extracted across {total_files} files ---")


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    generate_map(pathlib.Path(target))


if __name__ == "__main__":
    main()
