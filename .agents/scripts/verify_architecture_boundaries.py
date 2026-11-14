#!/usr/bin/env python3
"""
Clean / Hexagonal Architecture & Boundary Verifier
Inspired by `morluto/rea` (Boundary Ownership) and `affaan-m/ecc` (Modularity Checks).

Verifies:
1. Pure Domain layer isolation (no framework/ORM or infrastructure imports).
2. Application layer isolation (no direct transport/API imports).
3. Declarative `sdd:ownership-map` validation (overlaps, unowned coverage, custom `forbid_imports` AST checks).
4. File size modularity check across source directories (warning > 500 lines, error > 800 lines).
"""

from __future__ import annotations

import argparse
import ast
import pathlib
import sys

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
try:
    from scripts.sdd_ownership import (
        OwnershipError,
        detect_zone_overlaps,
        parse_ownership_map,
        validate_repo_coverage,
        zone_matches_path,
    )
except ImportError:
    _SCRIPTS_DIR = _REPO_ROOT / "scripts"
    if str(_SCRIPTS_DIR) not in sys.path:
        sys.path.insert(0, str(_SCRIPTS_DIR))
    from sdd_ownership import (
        OwnershipError,
        detect_zone_overlaps,
        parse_ownership_map,
        validate_repo_coverage,
        zone_matches_path,
    )

DEFAULT_FORBIDDEN_DOMAIN_IMPORTS = {
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

DEFAULT_FORBIDDEN_APPLICATION_IMPORTS = {
    "fastapi",
    "starlette",
    "uvicorn",
    "api",
}

MAX_LINES_ERROR = 800
MAX_LINES_WARN = 500
_SKIP_WALK_DIRS = frozenset(
    {".git", ".worktrees", ".venv", "venv", "node_modules", "__pycache__", ".mypy_cache", ".pytest_cache", ".ruff_cache"}
)
_CODE_EXTENSIONS = frozenset({".py", ".ts", ".tsx", ".js", ".jsx", ".cs", ".go", ".rs", ".java", ".kt"})


def _matches_forbidden(module_name: str, exact_roots: set[str], dotted_rules: set[str]) -> bool:
    if not module_name:
        return False
    if any(module_name == rule or module_name.startswith(rule + ".") for rule in dotted_rules):
        return True
    return any(part in exact_roots for part in module_name.split("."))


def check_python_ast_imports(
    py_file: pathlib.Path,
    forbidden_roots: set[str],
    layer_name: str,
    display_path: str | None = None,
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    label = display_path or py_file.name
    try:
        source = py_file.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(py_file))
    except (OSError, UnicodeDecodeError, SyntaxError, ValueError) as exc:
        return [f"[{layer_name}] AST parse error in {label}: {exc}"], []

    exact_roots = {entry for entry in forbidden_roots if "." not in entry}
    dotted_rules = {entry for entry in forbidden_roots if "." in entry}

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if _matches_forbidden(alias.name, exact_roots, dotted_rules):
                    errors.append(
                        f"[{layer_name} Boundary Violation] {label}:{node.lineno} imports forbidden module '{alias.name}'"
                    )
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if mod and _matches_forbidden(mod, exact_roots, dotted_rules):
                errors.append(
                    f"[{layer_name} Boundary Violation] {label}:{node.lineno} imports from forbidden module '{mod}'"
                )
            elif not mod:
                for alias in node.names:
                    if _matches_forbidden(alias.name, exact_roots, dotted_rules):
                        errors.append(
                            f"[{layer_name} Boundary Violation] {label}:{node.lineno} imports forbidden module '{alias.name}'"
                        )
            elif dotted_rules:
                for alias in node.names:
                    qualified = f"{mod}.{alias.name}"
                    if _matches_forbidden(qualified, set(), dotted_rules):
                        errors.append(
                            f"[{layer_name} Boundary Violation] {label}:{node.lineno} imports forbidden module '{qualified}'"
                        )
        elif isinstance(node, ast.Call) and node.args:
            func = node.func
            is_dyn_import = (
                (isinstance(func, ast.Name) and func.id in {"__import__", "import_module"})
                or (isinstance(func, ast.Attribute) and func.attr == "import_module")
            )
            if is_dyn_import and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                target = node.args[0].value
                if _matches_forbidden(target, exact_roots, dotted_rules):
                    errors.append(
                        f"[{layer_name} Boundary Violation] {label}:{node.lineno} dynamically imports forbidden module '{target}'"
                    )
    return errors, warnings


def check_file_sizes(root_dir: pathlib.Path, label: str) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if not root_dir.exists():
        return errors, warnings

    for path in sorted(root_dir.rglob("*"), key=lambda p: p.as_posix()):
        if any(part in _SKIP_WALK_DIRS for part in path.parts) or not path.is_file():
            continue
        if path.suffix.lower() not in _CODE_EXTENSIONS:
            continue
        rel = path.relative_to(root_dir).as_posix()
        try:
            lines = len(path.read_text(encoding="utf-8").splitlines())
        except (OSError, UnicodeDecodeError) as exc:
            errors.append(f"[{label} Read Error] Cannot inspect {rel}: {exc}")
            continue
        if lines > MAX_LINES_ERROR:
            errors.append(f"[{label} Modularity Error] {rel} has {lines} lines (max {MAX_LINES_ERROR}).")
        elif lines > MAX_LINES_WARN:
            warnings.append(f"[{label} Modularity Warning] {rel} has {lines} lines (target <= {MAX_LINES_WARN}).")
    return errors, warnings


def _iter_repo_python_files(repo_root: pathlib.Path) -> tuple[list[tuple[pathlib.Path, str]], list[str]]:
    root_resolved = repo_root.resolve()
    collected: list[tuple[pathlib.Path, str]] = []
    errors: list[str] = []
    seen_dirs: set[pathlib.Path] = {root_resolved}

    def _walk(current: pathlib.Path) -> None:
        try:
            entries = sorted(current.iterdir(), key=lambda p: p.name)
        except OSError as exc:
            errors.append(f"[Ownership Scan Error] Cannot read directory '{current}': {exc}")
            return
        for entry in entries:
            if entry.name in _SKIP_WALK_DIRS:
                continue
            if entry.is_symlink():
                res = entry.resolve()
                if not entry.exists() or not res.is_relative_to(root_resolved):
                    errors.append(f"[Ownership Scan Error] Unsafe or broken symlink '{entry}'.")
                    continue
            if entry.is_dir():
                res = entry.resolve()
                if res not in seen_dirs:
                    seen_dirs.add(res)
                    _walk(entry)
            elif entry.is_file() and entry.suffix == ".py":
                collected.append((entry, entry.relative_to(root_resolved).as_posix()))

    _walk(root_resolved)
    return collected, errors


def _run_ownership_audit(repo_root: pathlib.Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    stack_path = repo_root / "specs" / "STACK.md"
    try:
        ownership_cfg = parse_ownership_map(stack_path)
    except OwnershipError as exc:
        return [f"[Ownership Map Error] {exc}"], []
    if ownership_cfg is None:
        return [], []

    try:
        detect_zone_overlaps(ownership_cfg)
    except OwnershipError as exc:
        errors.append(f"[Ownership Overlap Error] {exc}")

    try:
        cov_warnings = validate_repo_coverage(ownership_cfg, repo_root)
        warnings.extend(f"[Ownership Coverage Warning] {w}" for w in cov_warnings)
    except OwnershipError as exc:
        errors.append(f"[Ownership Coverage Error] {exc}")

    if any(zone.forbid_imports for zone in ownership_cfg.zones):
        py_files, walk_errors = _iter_repo_python_files(repo_root)
        errors.extend(walk_errors)
        for zone in ownership_cfg.zones:
            if not zone.forbid_imports:
                continue
            forbidden = set(zone.forbid_imports)
            label = f"Zone:{zone.zone_id} (@{zone.owner})"
            for py_file, rel_posix in py_files:
                if zone_matches_path(zone, rel_posix):
                    e, w = check_python_ast_imports(py_file, forbidden, label, display_path=rel_posix)
                    errors.extend(e)
                    warnings.extend(w)
    return errors, warnings


def run_boundary_audit(repo_root: pathlib.Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    domain_dirs = [repo_root / "src" / "backend" / "domain", repo_root / "src" / "domain", repo_root / "backend" / "src" / "domain"]
    for domain_dir in domain_dirs:
        if domain_dir.exists():
            for py_file in sorted(domain_dir.rglob("*.py"), key=lambda p: p.as_posix()):
                e, w = check_python_ast_imports(py_file, DEFAULT_FORBIDDEN_DOMAIN_IMPORTS, "Domain")
                errors.extend(e)
                warnings.extend(w)

    app_dirs = [repo_root / "src" / "backend" / "application", repo_root / "src" / "application", repo_root / "backend" / "src" / "application"]
    for app_dir in app_dirs:
        if app_dir.exists():
            for py_file in sorted(app_dir.rglob("*.py"), key=lambda p: p.as_posix()):
                e, w = check_python_ast_imports(py_file, DEFAULT_FORBIDDEN_APPLICATION_IMPORTS, "Application")
                errors.extend(e)
                warnings.extend(w)

    own_err, own_warn = _run_ownership_audit(repo_root)
    errors.extend(own_err)
    warnings.extend(own_warn)

    scan_targets = [
        (repo_root / "src", "Source"),
    ]
    for sub, lbl in scan_targets:
        if sub.exists():
            size_err, size_warn = check_file_sizes(sub, lbl)
            errors.extend(size_err)
            warnings.extend(size_warn)

    return errors, warnings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Clean / Hexagonal Architecture & Ownership Boundary Verifier")
    parser.add_argument(
        "--repo-root",
        type=pathlib.Path,
        default=pathlib.Path(__file__).resolve().parents[2],
        help="Repository root to audit (defaults to current repository).",
    )
    args = parser.parse_args(argv)
    repo_root = args.repo_root.resolve()
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
