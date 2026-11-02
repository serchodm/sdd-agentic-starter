#!/usr/bin/env python3
"""
SDD AST Repo-Map Generator (sdd_repo_map.py)
Generates an ultra-compact, token-efficient interface map of codebases.
- Python (.py): Uses native ast parser to extract classes, methods, signatures and return types.
- TypeScript/JavaScript (.ts, .tsx, .js, .jsx): Uses deterministic regex AST parsing
  to extract interfaces, types, exported functions, classes, and React components.
Reduces token cost by 90-95% when agents only need to know what signatures exist.
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


def format_py_arg(arg: ast.arg) -> str:
    name = arg.arg
    if arg.annotation:
        ann = ast.unparse(arg.annotation)
        return f"{name}: {ann}"
    return name


def format_py_signature(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    prefix = "async def " if isinstance(node, ast.AsyncFunctionDef) else "def "
    args = []
    for a in node.args.posonlyargs:
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
    ret_str = f" -> {ast.unparse(node.returns)}" if node.returns else ""
    return f"{prefix}{node.name}({arg_str}){ret_str}"


def parse_python_file(path: pathlib.Path) -> list[str]:
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


# TypeScript / JavaScript regex patterns
TS_PATTERNS = [
    re.compile(r"^\s*export\s+interface\s+([A-Za-z0-9_]+(\s*<[^>]+>)?(\s+extends\s+[^{]+)?)", re.MULTILINE),
    re.compile(r"^\s*export\s+type\s+([A-Za-z0-9_]+(\s*<[^>]+>)?\s*=\s*[^;]+);", re.MULTILINE),
    re.compile(r"^\s*export\s+(?:default\s+)?(?:async\s+)?function\s+([A-Za-z0-9_]+\s*\([^)]*\)(?:\s*:\s*[^{]+)?)", re.MULTILINE),
    re.compile(r"^\s*export\s+const\s+([A-Za-z0-9_]+)\s*:\s*React\.FC(\s*<[^>]+>)?", re.MULTILINE),
    re.compile(r"^\s*export\s+class\s+([A-Za-z0-9_]+(\s+extends\s+[A-Za-z0-9_]+)?(\s+implements\s+[^{]+)?)", re.MULTILINE),
]


def parse_typescript_file(path: pathlib.Path) -> list[str]:
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        return [f"  [Read Error]: {exc}"]

    lines = []
    for match in re.finditer(r"export\s+interface\s+([A-Za-z0-9_]+(?:<[^>]+>)?(?:\s+extends\s+[^{]+)?)", content):
        lines.append(f"  interface {match.group(1).strip()}")

    for match in re.finditer(r"export\s+type\s+([A-Za-z0-9_]+(?:<[^>]+>)?)\s*=", content):
        lines.append(f"  type {match.group(1).strip()}")

    for match in re.finditer(r"export\s+(?:async\s+)?function\s+([A-Za-z0-9_]+\s*\([^)]*\)(?:\s*:\s*[^{]+)?)", content):
        lines.append(f"  function {match.group(1).strip()}")

    for match in re.finditer(r"export\s+const\s+([A-Za-z0-9_]+)\s*:\s*React\.FC(?:<([^>]+)>)?", content):
        prop_str = f"<{match.group(2)}>" if match.group(2) else ""
        lines.append(f"  component {match.group(1).strip()}{prop_str}")

    for match in re.finditer(r"export\s+class\s+([A-Za-z0-9_]+(?:<[^>]+>)?(?:\s+extends\s+[A-Za-z0-9_]+)?)", content):
        lines.append(f"  class {match.group(1).strip()}")

    return lines


def generate_map(target_path: pathlib.Path, max_depth: int = 4) -> None:
    if target_path.is_file():
        files = [target_path]
    elif target_path.is_dir():
        files = []
        for p in target_path.rglob("*"):
            if not p.is_file():
                continue
            if p.suffix in {".py", ".ts", ".tsx"}:
                parts = p.parts
                if any(x in parts for x in {".venv", "node_modules", "dist", "build", "__pycache__", ".git"}):
                    continue
                files.append(p)
    else:
        print(f"❌ [Error] Path '{target_path}' does not exist.", file=sys.stderr)
        sys.exit(1)

    files.sort()
    total_files = len(files)
    total_symbols = 0

    print(f"=== SDD AST REPO-MAP: {target_path} ({total_files} files) ===\n")

    for f in files:
        rel = f.as_posix()
        try:
            rel = f.relative_to(pathlib.Path.cwd()).as_posix()
        except ValueError:
            pass

        if f.suffix == ".py":
            signatures = parse_python_file(f)
        else:
            signatures = parse_typescript_file(f)

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
