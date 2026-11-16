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
import re
import sys

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


def _load_sdd_ownership():
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
        scripts_dir = _REPO_ROOT / "scripts"
        if str(scripts_dir) not in sys.path:
            sys.path.insert(0, str(scripts_dir))
        from sdd_ownership import (
            OwnershipError,
            detect_zone_overlaps,
            parse_ownership_map,
            validate_repo_coverage,
            zone_matches_path,
        )
    return OwnershipError, detect_zone_overlaps, parse_ownership_map, validate_repo_coverage, zone_matches_path

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


_COMMENT_OR_STR_RE = re.compile(r'("(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|`(?:\\.|[^`\\])*`)|(/\*[\s\S]*?\*/|//[^\n]*)')
_TS_IMPORT_RE = re.compile(
    r"\b(?:import|export)\s+(?:type\s+)?(?:[\w*{}\s,$]+\s+from\s+)?[\"']([^\"']+)[\"']"
    r"|\b(?:require|import)\s*\(\s*[\"']([^\"']+)[\"']\s*\)"
)
_CS_USING_RE = re.compile(r"^[ \t]*(?:global\s+)?using\s+(?:static\s+)?(?:[A-Za-z_]\w*\s*=\s*)?([A-Za-z_][\w.]*)\s*;", re.M)
_GO_SINGLE_RE = re.compile(r'\bimport\s+(?:[A-Za-z_.]\w*\s+)?["`]([^"`]+)["`]')
_GO_BLOCK_RE = re.compile(r"\bimport\s*\(([\s\S]*?)\)")
_GO_SPEC_RE = re.compile(r'["`]([^"`]+)["`]')
_RS_USE_RE = re.compile(r"^[ \t]*(?:pub(?:\s*\([^)]*\))?\s+)?(?:use\s+([^;]+)|extern\s+crate\s+([A-Za-z_]\w*))\s*;", re.M)
_JVM_IMPORT_RE = re.compile(r"^[ \t]*import\s+(?:static\s+)?([A-Za-z_][\w.*]*)(?:\s+as\s+[A-Za-z_]\w*)?\s*;?", re.M)


def _strip_c_style_comments(source: str) -> str:
    return _COMMENT_OR_STR_RE.sub(lambda m: m.group(1) if m.group(1) else "\n" * m.group(2).count("\n"), source)


def _canon_import_path(raw: str, *, strip_at: bool = False) -> str:
    s = re.sub(r"^(?:(?:\.\.?/)+|/)+", "", raw.strip())
    s = re.sub(r"^(?:crate|super|self)::", "", s)
    if strip_at:
        s = s.lstrip("@")
    return re.sub(r"(?:::|[/\\])+", ".", s).strip(".")


def _matches_polyglot_forbidden(raw_target: str, forbidden_roots: set[str]) -> bool:
    t_canon = _canon_import_path(raw_target, strip_at=False)
    t_no_at = _canon_import_path(raw_target, strip_at=True)
    tokens = {tok for part in re.split(r"[./:\\,{}\s*]+", raw_target.strip()) if part for tok in (part, part.lstrip("@"))}
    for rule in forbidden_roots:
        r = rule.strip()
        if not r:
            continue
        if any(sep in r for sep in (".", "/", "\\", ":")):
            for tc, rc in ((t_canon, _canon_import_path(r, strip_at=False)), (t_no_at, _canon_import_path(r, strip_at=True))):
                if rc and (tc == rc or tc.startswith(rc + ".") or f".{rc}." in f".{tc}."):
                    return True
            r_parts = [p for p in _canon_import_path(r, strip_at=True).split(".") if p]
            if r_parts and all(p in tokens for p in r_parts):
                return True
        elif r in tokens or r.lstrip("@") in tokens:
            return True
    return False


def check_polyglot_imports(
    code_file: pathlib.Path,
    forbidden_roots: set[str],
    layer_name: str,
    display_path: str | None = None,
) -> tuple[list[str], list[str]]:
    """Verify forbidden imports across Python (AST) and TS/JS/C#/Go/Rust/Java/Kotlin."""
    ext = code_file.suffix.lower()
    if ext == ".py":
        return check_python_ast_imports(code_file, forbidden_roots, layer_name, display_path=display_path)
    label = display_path or code_file.name
    if ext not in _CODE_EXTENSIONS:
        return [], []
    try:
        raw_source = code_file.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return [f"[{layer_name}] Read error in {label}: {exc}"], []

    stripped = _strip_c_style_comments(raw_source.replace("\r\n", "\n").replace("\r", "\n"))
    extracted: list[tuple[int, str]] = []
    if ext in {".ts", ".tsx", ".js", ".jsx"}:
        for m in _TS_IMPORT_RE.finditer(stripped):
            target = m.group(1) or m.group(2) or ""
            extracted.append((stripped.count("\n", 0, m.start()) + 1, target))
    elif ext == ".cs":
        for m in _CS_USING_RE.finditer(stripped):
            extracted.append((stripped.count("\n", 0, m.start()) + 1, m.group(1)))
    elif ext == ".go":
        for m in _GO_SINGLE_RE.finditer(stripped):
            extracted.append((stripped.count("\n", 0, m.start()) + 1, m.group(1)))
        for bm in _GO_BLOCK_RE.finditer(stripped):
            base_off = bm.start(1)
            for sm in _GO_SPEC_RE.finditer(bm.group(1)):
                extracted.append((stripped.count("\n", 0, base_off + sm.start()) + 1, sm.group(1)))
    elif ext == ".rs":
        for m in _RS_USE_RE.finditer(stripped):
            extracted.append((stripped.count("\n", 0, m.start()) + 1, (m.group(1) or m.group(2) or "").strip()))
    elif ext in {".java", ".kt"}:
        for m in _JVM_IMPORT_RE.finditer(stripped):
            extracted.append((stripped.count("\n", 0, m.start()) + 1, m.group(1)))

    errors: list[str] = []
    for lineno, target in extracted:
        if target and _matches_polyglot_forbidden(target, forbidden_roots):
            errors.append(f"[{layer_name} Boundary Violation] {label}:{lineno} imports forbidden module '{target}'")
    return errors, []


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


def _iter_repo_code_files(
    repo_root: pathlib.Path, extensions: frozenset[str] = _CODE_EXTENSIONS
) -> tuple[list[tuple[pathlib.Path, str]], list[str]]:
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
            elif entry.is_file() and entry.suffix.lower() in extensions:
                collected.append((entry, entry.relative_to(root_resolved).as_posix()))

    _walk(root_resolved)
    return collected, errors


def _iter_repo_python_files(repo_root: pathlib.Path) -> tuple[list[tuple[pathlib.Path, str]], list[str]]:
    return _iter_repo_code_files(repo_root, frozenset({".py"}))


def _run_ownership_audit(repo_root: pathlib.Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    stack_path = repo_root / "specs" / "STACK.md"
    if not stack_path.exists() and not stack_path.is_symlink():
        return [], []
    try:
        (
            ownership_error_cls,
            detect_zone_overlaps,
            parse_ownership_map,
            validate_repo_coverage,
            zone_matches_path,
        ) = _load_sdd_ownership()
    except ImportError as exc:
        if not stack_path.is_file():
            return [f"[Ownership Map Error] Cannot inspect '{stack_path}' without 'scripts.sdd_ownership': {exc}"], []
        try:
            stack_text = stack_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as read_exc:
            return [f"[Ownership Map Error] Cannot read '{stack_path}' without 'scripts.sdd_ownership': {read_exc}"], []
        if "sdd:ownership-map" in stack_text.lower():
            return [f"[Ownership Map Error] Missing 'scripts.sdd_ownership' to validate sdd:ownership-map: {exc}"], []
        return [], []

    try:
        ownership_cfg = parse_ownership_map(stack_path)
    except ownership_error_cls as exc:
        return [f"[Ownership Map Error] {exc}"], []
    if ownership_cfg is None:
        return [], []

    try:
        detect_zone_overlaps(ownership_cfg)
    except ownership_error_cls as exc:
        errors.append(f"[Ownership Overlap Error] {exc}")

    try:
        cov_warnings = validate_repo_coverage(ownership_cfg, repo_root)
        warnings.extend(f"[Ownership Coverage Warning] {w}" for w in cov_warnings)
    except ownership_error_cls as exc:
        errors.append(f"[Ownership Coverage Error] {exc}")

    if any(zone.forbid_imports for zone in ownership_cfg.zones):
        code_files, walk_errors = _iter_repo_code_files(repo_root)
        errors.extend(walk_errors)
        for zone in ownership_cfg.zones:
            if not zone.forbid_imports:
                continue
            forbidden = set(zone.forbid_imports)
            label = f"Zone:{zone.zone_id} (@{zone.owner})"
            for code_file, rel_posix in code_files:
                if zone_matches_path(zone, rel_posix):
                    e, w = check_polyglot_imports(code_file, forbidden, label, display_path=rel_posix)
                    errors.extend(e)
                    warnings.extend(w)
    return errors, warnings


def run_boundary_audit(repo_root: pathlib.Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    domain_dirs = [repo_root / "src" / "backend" / "domain", repo_root / "src" / "domain", repo_root / "backend" / "src" / "domain"]
    for domain_dir in domain_dirs:
        if domain_dir.exists():
            for code_file in sorted(domain_dir.rglob("*"), key=lambda p: p.as_posix()):
                if code_file.is_file() and code_file.suffix.lower() in _CODE_EXTENSIONS:
                    e, w = check_polyglot_imports(code_file, DEFAULT_FORBIDDEN_DOMAIN_IMPORTS, "Domain")
                    errors.extend(e)
                    warnings.extend(w)

    app_dirs = [repo_root / "src" / "backend" / "application", repo_root / "src" / "application", repo_root / "backend" / "src" / "application"]
    for app_dir in app_dirs:
        if app_dir.exists():
            for code_file in sorted(app_dir.rglob("*"), key=lambda p: p.as_posix()):
                if code_file.is_file() and code_file.suffix.lower() in _CODE_EXTENSIONS:
                    e, w = check_polyglot_imports(code_file, DEFAULT_FORBIDDEN_APPLICATION_IMPORTS, "Application")
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
