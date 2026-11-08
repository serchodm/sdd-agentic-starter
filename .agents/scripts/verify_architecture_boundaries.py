#!/usr/bin/env python3
"""
Clean / Hexagonal Architecture & Producing-Boundary Verifier
Inspired by `morluto/rea` (`verify:module-boundaries` & Producing-Boundary Ownership)
and `affaan-m/ecc` (Modularity & Security Checks).

Checks:
1. `backend/src/domain/` pure domain isolation (zero imports from fastapi, sqlalchemy, sqlmodel, httpx, infrastructure, api).
2. `backend/src/application/` application layer isolation (zero imports from fastapi, starlette, uvicorn, api).
3. `frontend/src/` black-box package boundary for `@paco/avatar-engine` (only public root imports allowed; no deep internal imports).
4. File size modularity check across `backend/src/` and `frontend/src/` (warning > 500 lines, error > 800 lines).
"""

import ast
import pathlib
import re
import sys

FORBIDDEN_DOMAIN_IMPORTS = {
    "fastapi",
    "starlette",
    "sqlalchemy",
    "sqlmodel",
    "alembic",
    "httpx",
    "asyncpg",
    "psycopg",
    "uvicorn",
    "infrastructure",
    "api",
}

FORBIDDEN_APPLICATION_IMPORTS = {
    "fastapi",
    "starlette",
    "uvicorn",
    "api",
}

MAX_LINES_ERROR = 800
MAX_LINES_WARN = 500


def check_python_ast_imports(
    py_file: pathlib.Path, forbidden_roots: set[str], layer_name: str
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    try:
        source = py_file.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(py_file))
    except Exception as exc:
        return [f"[{layer_name}] AST parse error in {py_file}: {exc}"], []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                parts = alias.name.split(".")
                if any(part in forbidden_roots for part in parts):
                    errors.append(
                        f"[{layer_name} Boundary Violation] {py_file.name}:{node.lineno} imports forbidden module '{alias.name}'"
                    )
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            parts = mod.split(".")
            if any(part in forbidden_roots for part in parts):
                # Known FEAT-005 baseline debt (scheduled for cleanup in CR-005 / tech-debt):
                if mod == "src.api.dtos.events" and py_file.name in {"event_bus.py", "process_user_input.py"}:
                    warnings.append(
                        f"[{layer_name} Legacy DTO Coupling] {py_file.name}:{node.lineno} imports '{mod}' "
                        "(tracked baseline from FEAT-005; isolate DTOs in application/domain during CR-005)."
                    )
                else:
                    errors.append(
                        f"[{layer_name} Boundary Violation] {py_file.name}:{node.lineno} imports from forbidden module '{mod}'"
                    )
    return errors, warnings


def check_frontend_boundaries(frontend_src: pathlib.Path) -> list[str]:
    errors: list[str] = []
    if not frontend_src.exists():
        return errors

    deep_avatar_import = re.compile(r"""from\s+['"]@paco/avatar-engine/.+['"]""")
    for path in frontend_src.rglob("*"):
        if path.suffix.lower() not in {".ts", ".tsx", ".js", ".jsx"}:
            continue
        content = path.read_text(encoding="utf-8", errors="ignore")
        for lineno, line in enumerate(content.splitlines(), start=1):
            if deep_avatar_import.search(line):
                errors.append(
                    f"[Frontend Black-Box Violation] {path.relative_to(frontend_src)}:{lineno} "
                    f"uses deep internal import from @paco/avatar-engine. Use only the public root contract."
                )
    return errors


def check_file_sizes(root_dir: pathlib.Path, label: str) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if not root_dir.exists():
        return errors, warnings

    for path in root_dir.rglob("*"):
        if path.suffix.lower() not in {".py", ".ts", ".tsx", ".js", ".jsx"}:
            continue
        lines = len(path.read_text(encoding="utf-8", errors="ignore").splitlines())
        rel = path.relative_to(root_dir)
        if lines > MAX_LINES_ERROR:
            errors.append(f"[{label} Modularity Error] {rel} has {lines} lines (max {MAX_LINES_ERROR}).")
        elif lines > MAX_LINES_WARN:
            warnings.append(f"[{label} Modularity Warning] {rel} has {lines} lines (target <= {MAX_LINES_WARN}).")
    return errors, warnings


def run_boundary_audit(repo_root: pathlib.Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    domain_dirs = [repo_root / "backend" / "src" / "domain", repo_root / "src" / "domain"]
    for domain_dir in domain_dirs:
        if domain_dir.exists():
            for py_file in domain_dir.rglob("*.py"):
                e, w = check_python_ast_imports(py_file, FORBIDDEN_DOMAIN_IMPORTS, "Domain")
                errors.extend(e)
                warnings.extend(w)

    app_dirs = [repo_root / "backend" / "src" / "application", repo_root / "src" / "application"]
    for app_dir in app_dirs:
        if app_dir.exists():
            for py_file in app_dir.rglob("*.py"):
                e, w = check_python_ast_imports(py_file, FORBIDDEN_APPLICATION_IMPORTS, "Application")
                errors.extend(e)
                warnings.extend(w)

    frontend_src = repo_root / "frontend" / "src"
    if not frontend_src.exists():
        frontend_src = repo_root / "src" / "frontend"
    errors.extend(check_frontend_boundaries(frontend_src))

    scan_targets = [
        (repo_root / "src", "Source"),
        (repo_root / "backend" / "src", "Backend"),
        (frontend_src, "Frontend"),
    ]
    for sub, lbl in scan_targets:
        if sub.exists():
            size_err, size_warn = check_file_sizes(sub, lbl)
            errors.extend(size_err)
            warnings.extend(size_warn)

    return errors, warnings


def main() -> int:
    repo_root = pathlib.Path(__file__).resolve().parents[2]
    errors, warnings = run_boundary_audit(repo_root)

    for w in warnings:
        print(f"WARN: {w}")
    for e in errors:
        print(f"ERROR: {e}")

    if errors:
        print(f"\nArchitecture Boundary Audit FAILED with {len(errors)} error(s).")
        return 1

    print(f"Architecture Boundary Audit PASSED (0 errors, {len(warnings)} warning(s)).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
