#!/usr/bin/env python3
"""
Project Global SDD & Architecture Healthcheck (`sdd_healthcheck.py`)
Combines SDD governance invariants with `morluto/rea` and `affaan-m/ecc` verification checks:

1. Verifies spec triads (`01-spec.md`, `02-tech-spec.md`, `03-tasks.md` or bug equivalents) with
   strict Status/Estado column parsing (`AUD-024`), non-empty files, and orphan detection for
   `In Progress` / `In Review` / `Done` backlog items (`AUD-009`).
2. Verifies `RN-SDD-IMMUTABLE-DONE`: detects uncommitted and committed branch modifications to
   `specs/features/FEAT-XXX-*/` marked `Done` when no linked `CR-XXX` exists (`AUD-009`).
3. Verifies `RN-SDD-1-TO-1-CR` traceability in `specs/BACKLOG.md`.
4. Scans `.agents/scripts/*.py` and `scripts/*.py` via AST for `shell=True` / `os.system` /
   `os.popen`, and scans specs/inbox Markdown for hidden prompt-injection directives (`AUD-010`).
5. Runs `verify_architecture_boundaries.py` to validate architecture boundaries and modularity.
"""

from __future__ import annotations

import ast
import pathlib
import re
import subprocess
import sys

_SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from verify_architecture_boundaries import run_boundary_audit  # noqa: E402

GATE1_INITIAL_STATES = frozenset({"draft", "proposed", "propuesto", "gate 1"})
ACTIVE_WORK_STATES = frozenset({"in progress", "in review", "en progreso", "en revision", "en revisión"})
DONE_STATES = frozenset({"done", "completed", "completado", "completed / done"})
KNOWN_STATUS_VALUES = (
    GATE1_INITIAL_STATES | ACTIVE_WORK_STATES | DONE_STATES
    | frozenset({"candidate", "backlog", "cancelled", "canceled", "rejected", "blocked", "bloqueado"})
)

SPEC_CATEGORIES = (
    ("features", "FEAT", ("01-spec.md", "02-tech-spec.md", "03-tasks.md")),
    ("changes", "CR", ("01-spec.md", "02-tech-spec.md", "03-tasks.md")),
    ("bugs", "BUG", ("01-bug-report.md", "02-fix-spec.md", "03-tasks.md")),
)
PREFIX_TO_CATEGORY = {prefix: category for category, prefix, _ in SPEC_CATEGORIES}

BENIGN_COMMENT_RE = re.compile(r"^(?:GENERATED\s+by\s+sdd_agent_generator\b|Sourced\s+from\s+upstream\b)", re.I)
INJECTION_COMMENT_RE = re.compile(
    r"(?:\bsystem\s+override\b|\bignore\s+(?:all\s+|previous\s+|prior\s+)*instructions?\b"
    r"|\b(?:ignore|bypass)\s+(?:gate|guard|hook|rule|security|check)s?\b"
    r"|\bdisable\s+(?:hook|guard|check)s?\b|\bdisregard\b|\bjailbreak\b"
    r"|\brm\s+-rf\b|\binvoke-expression\b|\biex\s*\(|\bpowershell\b.*-enc"
    r"|\b(?:curl|wget)\b[^|]*\|\s*(?:ba)?sh\b|<\s*script\b)",
    re.I,
)
INJECTION_BODY_RE = re.compile(
    r"(?:\b(?:system|admin|developer)\s+override\b"
    r"|\bignore\s+(?:all\s+|previous\s+|prior\s+)+instructions?\b|<\s*script\b|[\u202a-\u202e\u2066-\u2069])",
    re.I,
)
DETAIL_SECTION_RE = re.compile(
    r"^#{2,6}\s+`?([A-Za-z]+-\d{3,4})`?[^\n]*\n(?:-[^\n]*\n){0,4}?-\s+\*\*Estado:\*\*\s+([^\n]+)",
    re.I | re.M,
)


def _strip_fenced_blocks(text: str) -> str:
    out: list[str] = []
    in_fence, fence_char = False, ""
    for line in text.splitlines():
        stripped = line.lstrip()
        if not in_fence and (stripped.startswith("```") or stripped.startswith("~~~")):
            in_fence, fence_char = True, stripped[:3]
        elif in_fence and stripped.startswith(fence_char):
            in_fence, fence_char = False, ""
        elif not in_fence:
            out.append(line)
    return "\n".join(out)


def _clean_cell(cell: str) -> str:
    return re.sub(r"[`*_]+", "", cell).strip()


def _normalize_status(cell: str) -> str:
    return re.sub(r"\s+", " ", _clean_cell(cell)).lower()


def _split_markdown_row(line: str) -> list[str]:
    stripped = line.strip()
    if not stripped.startswith("|") or "|" not in stripped[1:]:
        return []
    parts = re.split(r"(?<!\\)\|", stripped)
    if parts and parts[0] == "":
        parts = parts[1:]
    if parts and parts[-1] == "":
        parts = parts[:-1]
    return [part.strip() for part in parts]


def _is_separator_row(cells: list[str]) -> bool:
    return bool(cells) and all(bool(re.match(r"^:?-{2,}:?$", c.replace(" ", ""))) for c in cells)


def _find_col_index(headers: list[str], exact_names: set[str], partial_tokens: tuple[str, ...]) -> int | None:
    normalized = [_normalize_status(h) for h in headers]
    for idx, name in enumerate(normalized):
        if name in exact_names:
            return idx
    for idx, name in enumerate(normalized):
        if any(tok in name for tok in partial_tokens):
            return idx
    return None


def _infer_headerless_status(cells: list[str]) -> str:
    if len(cells) < 2:
        return ""
    last_norm = _normalize_status(cells[-1])
    if last_norm in KNOWN_STATUS_VALUES:
        return last_norm
    if len(cells) >= 4:
        prev_norm = _normalize_status(cells[-2])
        looks_non_status = last_norm in {"", "-", "n/a"} or bool(re.match(r"^\d{4}-\d{2}-\d{2}$", last_norm))
        if looks_non_status and prev_norm in KNOWN_STATUS_VALUES:
            return prev_norm
    return last_norm


def _parse_backlog_entries(backlog_text: str) -> tuple[dict[str, str], dict[str, set[str]]]:
    """Parse Markdown tables and detail sections in BACKLOG.md strictly by Status column."""
    statuses: dict[str, str] = {}
    cr_links: dict[str, set[str]] = {}
    cleaned = re.sub(r"<!--.*?-->", "", _strip_fenced_blocks(backlog_text), flags=re.S)
    lines = cleaned.splitlines()
    status_idx: int | None = None
    id_idx, affected_idx, in_table = 0, None, False

    for i, line in enumerate(lines):
        cells = _split_markdown_row(line)
        if not cells:
            status_idx, id_idx, affected_idx, in_table = None, 0, None, False
            continue
        if _is_separator_row(cells):
            in_table = True
            continue
        next_is_sep = i + 1 < len(lines) and _is_separator_row(_split_markdown_row(lines[i + 1]))
        looks_header = (
            not in_table
            and not re.search(r"\b(?:FEAT|CR|BUG|FWK|RFC)-\d+\b", _clean_cell(cells[0]), re.I)
            and any(_normalize_status(c) in {"estado", "estado final", "status", "final status"} for c in cells)
        )
        if next_is_sep or looks_header:
            in_table = True
            status_idx = _find_col_index(cells, {"estado", "estado final", "status", "final status", "state"}, ("estado", "status"))
            found_id = _find_col_index(cells, {"id", "id cr", "id bug"}, ("id",))
            id_idx = found_id if found_id is not None else 0
            affected_idx = _find_col_index(cells, {"feature afectada", "affected feature", "feature"}, ("afectada", "affected", "feature"))
            continue

        in_table = True
        if id_idx >= len(cells):
            continue
        id_match = re.search(r"\b([A-Za-z]+-\d{3,4})\b", _clean_cell(cells[id_idx]))
        if not id_match:
            continue
        item_id = id_match.group(1).upper()
        statuses[item_id] = (
            (_normalize_status(cells[status_idx]) if status_idx < len(cells) else "")
            if status_idx is not None
            else _infer_headerless_status(cells)
        )
        if item_id.startswith("CR-"):
            aff_cell = cells[affected_idx] if affected_idx is not None and affected_idx < len(cells) else (cells[1] if len(cells) >= 2 else "")
            linked = {m.upper() for m in re.findall(r"\bFEAT-\d{3,4}\b", _clean_cell(aff_cell), re.I)}
            if linked:
                cr_links.setdefault(item_id, set()).update(linked)

    for match in DETAIL_SECTION_RE.finditer(cleaned):
        statuses.setdefault(match.group(1).upper(), _normalize_status(match.group(2)))
    return statuses, cr_links


def parse_done_features_from_text(backlog_text: str) -> set[str]:
    statuses, _ = _parse_backlog_entries(backlog_text)
    return {item_id for item_id, status in statuses.items() if item_id.startswith("FEAT-") and status in DONE_STATES}


def _safe_rel(path: pathlib.Path, base: pathlib.Path) -> str:
    try:
        return str(path.relative_to(base)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def check_prompt_injection_risks(md_path: pathlib.Path, display_path: str) -> list[str]:
    """Detect hidden HTML override comments and prompt-injection directives outside fenced code blocks."""
    try:
        raw_text = md_path.read_text(encoding="utf-8")
    except Exception as exc:
        return [f"[Prompt Injection Audit Error] Failed to read '{display_path}': {exc}"]

    no_fences = _strip_fenced_blocks(raw_text)
    for match in re.finditer(r"<!--(.*?)-->", no_fences, flags=re.S):
        body = match.group(1).strip()
        if not BENIGN_COMMENT_RE.match(body) and INJECTION_COMMENT_RE.search(body):
            return [f"[Prompt Injection Risk] '{display_path}' contains suspicious hidden HTML directive."]

    no_comments = re.sub(r"<!--.*?-->", "", no_fences, flags=re.S)
    if INJECTION_BODY_RE.search(no_comments):
        return [f"[Prompt Injection Risk] '{display_path}' contains forbidden override/script directive."]
    return []


def check_spec_triads(specs_root: pathlib.Path, backlog_path: pathlib.Path) -> list[str]:
    """Validate spec triads, non-empty artifacts, backlog orphan items, and prompt-injection safety."""
    errors: list[str] = []
    backlog_text = backlog_path.read_text(encoding="utf-8", errors="ignore") if backlog_path.exists() else ""
    statuses, _ = _parse_backlog_entries(backlog_text)
    found_dirs_by_id: dict[str, list[pathlib.Path]] = {}

    if backlog_path.exists():
        errors.extend(check_prompt_injection_risks(backlog_path, _safe_rel(backlog_path, specs_root.parent)))

    for category, _prefix, required_files in SPEC_CATEGORIES:
        cat_dir = specs_root / category
        if not cat_dir.exists():
            continue
        for item_dir in sorted(cat_dir.iterdir()):
            if not item_dir.is_dir():
                continue
            m = re.match(r"^([A-Za-z]+-\d{3,4})", item_dir.name)
            item_id = m.group(1).upper() if m else item_dir.name.upper()
            found_dirs_by_id.setdefault(item_id, []).append(item_dir)

            files_to_check = (required_files[0],) if statuses.get(item_id, "") in GATE1_INITIAL_STATES else required_files
            rel_item = _safe_rel(item_dir, specs_root.parent)
            for req in files_to_check:
                req_path = item_dir / req
                if not req_path.exists():
                    errors.append(f"[SDD Triad Incomplete] '{rel_item}' is missing '{req}'.")
                    continue
                try:
                    content = req_path.read_text(encoding="utf-8")
                except Exception as exc:
                    errors.append(f"[SDD Triad Error] Failed to read '{rel_item}/{req}': {exc}")
                    continue
                if not content.strip():
                    errors.append(f"[SDD Triad Incomplete] '{rel_item}' has empty '{req}'.")

            for md_file in sorted(item_dir.glob("*.md")):
                errors.extend(check_prompt_injection_risks(md_file, _safe_rel(md_file, specs_root.parent)))

    for item_id, status in sorted(statuses.items()):
        prefix = item_id.split("-", 1)[0]
        if prefix in PREFIX_TO_CATEGORY and status in (ACTIVE_WORK_STATES | DONE_STATES) and item_id not in found_dirs_by_id:
            errors.append(
                f"[SDD Backlog Orphan] '{item_id}' is marked '{status}' in specs/BACKLOG.md "
                f"but has no folder under 'specs/{PREFIX_TO_CATEGORY[prefix]}/'."
            )
    return errors


def _run_git(repo_root: pathlib.Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=str(repo_root), capture_output=True, text=True, encoding="utf-8", errors="replace")


def _cr_linked_features(repo_root: pathlib.Path, backlog_text: str) -> set[str]:
    _, cr_links = _parse_backlog_entries(backlog_text)
    changes_dir = repo_root / "specs" / "changes"
    if not changes_dir.exists():
        return set()
    existing_crs = {
        m.group(1).upper()
        for d in changes_dir.iterdir()
        if d.is_dir()
        for m in [re.match(r"^(CR-\d{3,4})(?:-|$)", d.name, re.I)]
        if m
    }
    return {feat for cr_id, feats in cr_links.items() if cr_id in existing_crs for feat in feats}


def _resolve_base_commit(repo_root: pathlib.Path, head_sha: str) -> tuple[str | None, set[str]]:
    for ref in ("origin/develop", "develop", "origin/main", "main"):
        if _run_git(repo_root, ["rev-parse", "--verify", "--quiet", ref]).returncode != 0:
            continue
        mb = _run_git(repo_root, ["merge-base", ref, "HEAD"])
        base = mb.stdout.strip()
        if mb.returncode == 0 and base and base != head_sha:
            show_base = _run_git(repo_root, ["show", f"{base}:specs/BACKLOG.md"])
            return base, (parse_done_features_from_text(show_base.stdout) if show_base.returncode == 0 else set())
    return None, set()


def _check_committed_done_mutations(
    repo_root: pathlib.Path, feat_id: str, rel_dir: str, base_commit: str | None, done_at_base: set[str]
) -> list[str]:
    if base_commit and feat_id in done_at_base:
        diff_res = _run_git(repo_root, ["diff", "--name-only", base_commit, "HEAD", "--", rel_dir])
        if diff_res.returncode != 0:
            return [f"[RN-SDD-IMMUTABLE-DONE Error] git diff failed for '{rel_dir}': {diff_res.stderr.strip()}"]
        if diff_res.stdout.strip():
            return [
                f"[RN-SDD-IMMUTABLE-DONE Violation] Completed feature '{rel_dir}' has committed modifications "
                f"vs base {base_commit[:8]} without a linked CR-XXX:\n{diff_res.stdout.strip()}"
            ]

    log_range = [f"{base_commit}..HEAD"] if base_commit else ["-n", "20", "HEAD"]
    log_res = _run_git(repo_root, ["log", "--no-merges", "--format=%H", *log_range, "--", rel_dir])
    if log_res.returncode != 0:
        return [f"[RN-SDD-IMMUTABLE-DONE Error] git log failed for '{rel_dir}': {log_res.stderr.strip()}"]
    for sha in (line.strip() for line in log_res.stdout.splitlines() if line.strip()):
        if _run_git(repo_root, ["rev-parse", "--verify", "--quiet", f"{sha}^"]).returncode != 0:
            continue
        prev_bl = _run_git(repo_root, ["show", f"{sha}^:specs/BACKLOG.md"])
        if prev_bl.returncode == 0 and feat_id in parse_done_features_from_text(prev_bl.stdout):
            return [
                f"[RN-SDD-IMMUTABLE-DONE Violation] Completed feature '{rel_dir}' was modified after "
                f"being marked Done (commit {sha[:8]}) without a linked CR-XXX."
            ]
    return []


def check_done_features_git_clean(
    repo_root: pathlib.Path, done_features: set[str], backlog_text: str | None = None
) -> list[str]:
    errors: list[str] = []
    features_dir = repo_root / "specs" / "features"
    if not features_dir.exists():
        return errors
    if _run_git(repo_root, ["rev-parse", "--is-inside-work-tree"]).returncode != 0:
        if (repo_root / ".git").exists() or done_features:
            errors.append("[RN-SDD-IMMUTABLE-DONE Error] Unable to verify git immutability for Done features.")
        return errors
    if not done_features:
        return errors

    if backlog_text is None:
        bp = repo_root / "specs" / "BACKLOG.md"
        backlog_text = bp.read_text(encoding="utf-8", errors="ignore") if bp.exists() else ""
    cr_backed = _cr_linked_features(repo_root, backlog_text)
    head_res = _run_git(repo_root, ["rev-parse", "--verify", "--quiet", "HEAD"])
    head_sha = head_res.stdout.strip() if head_res.returncode == 0 else None
    base_commit, done_at_base = _resolve_base_commit(repo_root, head_sha) if head_sha else (None, set())

    for item_dir in sorted(features_dir.iterdir()):
        if not item_dir.is_dir():
            continue
        m = re.match(r"^(FEAT-\d{3,4})", item_dir.name, re.I)
        if not m or m.group(1).upper() not in done_features:
            continue
        feat_id, rel_dir = m.group(1).upper(), _safe_rel(item_dir, repo_root)
        st = _run_git(repo_root, ["status", "--porcelain", "--", rel_dir])
        if st.returncode != 0:
            errors.append(f"[RN-SDD-IMMUTABLE-DONE Error] git status failed for '{rel_dir}': {st.stderr.strip()}")
            continue
        if st.stdout.strip():
            errors.append(f"[RN-SDD-IMMUTABLE-DONE Violation] Completed feature '{rel_dir}' has uncommitted modifications:\n{st.stdout.strip()}")
        if head_sha and feat_id not in cr_backed:
            errors.extend(_check_committed_done_mutations(repo_root, feat_id, rel_dir, base_commit, done_at_base))
    return errors


def check_cr_backlog_registration(repo_root: pathlib.Path, backlog_text: str | None = None) -> list[str]:
    errors: list[str] = []
    backlog_path = repo_root / "specs" / "BACKLOG.md"
    changes_dir = repo_root / "specs" / "changes"
    if not backlog_path.exists() or not changes_dir.exists():
        return errors
    if backlog_text is None:
        backlog_text = backlog_path.read_text(encoding="utf-8", errors="ignore")
    statuses, _ = _parse_backlog_entries(backlog_text)
    for cr_dir in sorted(changes_dir.iterdir()):
        if not cr_dir.is_dir():
            continue
        m = re.match(r"^(CR-\d{3,4})", cr_dir.name, re.I)
        if m and m.group(1).upper() not in statuses:
            errors.append(f"[Backlog Traceability Error] Change Request '{cr_dir.name}' ({m.group(1).upper()}) is not registered in specs/BACKLOG.md.")
    return errors


def _audit_call_node(node: ast.Call, rel_path: str) -> list[str]:
    errs: list[str] = []
    if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name) and node.func.value.id == "os" and node.func.attr in {"system", "popen"}:
        errs.append(f"[Static Security Error] '{rel_path}:{node.lineno}' calls forbidden 'os.{node.func.attr}()'.")
    for kw in node.keywords:
        if kw.arg == "shell" and not (isinstance(kw.value, ast.Constant) and kw.value.value in {False, None}):
            errs.append(f"[Static Security Error] '{rel_path}:{node.lineno}' uses unsafe 'shell=...' argument.")
        elif kw.arg is None and isinstance(kw.value, ast.Dict):
            for k_node, v_node in zip(kw.value.keys, kw.value.values):
                if isinstance(k_node, ast.Constant) and k_node.value == "shell" and not (isinstance(v_node, ast.Constant) and v_node.value in {False, None}):
                    errs.append(f"[Static Security Error] '{rel_path}:{node.lineno}' passes unsafe 'shell' in **kwargs.")
    return errs


def check_subprocess_shell_safety(repo_root: pathlib.Path) -> list[str]:
    errors: list[str] = []
    for target_dir in (repo_root / ".agents" / "scripts", repo_root / "scripts"):
        if not target_dir.exists():
            continue
        for py_file in sorted(target_dir.rglob("*.py")):
            if "__pycache__" in py_file.parts or ".venv" in py_file.parts:
                continue
            rel_path = _safe_rel(py_file, repo_root)
            try:
                tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
            except Exception as exc:
                errors.append(f"[Static Security Error] Failed to parse '{rel_path}': {exc}")
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    errors.extend(_audit_call_node(node, rel_path))
    return errors


def check_inbox_and_stack_safety(repo_root: pathlib.Path) -> list[str]:
    errors: list[str] = []
    stack_path = repo_root / "specs" / "STACK.md"
    if stack_path.exists():
        errors.extend(check_prompt_injection_risks(stack_path, "specs/STACK.md"))
    inbox_dir = repo_root / ".agent-inbox"
    if inbox_dir.exists():
        for md_file in sorted(inbox_dir.rglob("*.md")):
            errors.extend(check_prompt_injection_risks(md_file, _safe_rel(md_file, repo_root)))
    return errors


def check_git_sync_status(repo_root: pathlib.Path) -> list[str]:
    warnings: list[str] = []
    res_curr_branch = _run_git(repo_root, ["branch", "--show-current"])
    current_branch = res_curr_branch.stdout.strip() if res_curr_branch.returncode == 0 else "main"
    target_push = f"origin {current_branch}" if current_branch else "origin <branch>"

    res_status = _run_git(repo_root, ["status", "--porcelain"])
    if res_status.returncode == 0 and res_status.stdout.strip():
        count = len(res_status.stdout.strip().splitlines())
        warnings.append(
            f"[RN-SDD-BRANCH-SYNC Reminder] Working tree has {count} uncommitted file(s)/folder(s). "
            f"Remember to run `git add`, `git commit`, and `git push {target_push}` once validated."
        )
    res_branch = _run_git(repo_root, ["status", "-sb"])
    if res_branch.returncode == 0 and "ahead" in res_branch.stdout:
        warnings.append(
            f"[RN-SDD-BRANCH-SYNC Reminder] Local branch '{current_branch}' is ahead of remote. Remember to run `git push {target_push}`."
        )
    return warnings


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    repo_root = pathlib.Path(__file__).resolve().parents[2]
    specs_root = repo_root / "specs"
    backlog_path = specs_root / "BACKLOG.md"
    backlog_text = backlog_path.read_text(encoding="utf-8", errors="ignore") if backlog_path.exists() else ""
    done_features = parse_done_features_from_text(backlog_text)
    errors: list[str] = []
    warnings: list[str] = []

    print("=== Project SDD & Agent Harness 2.0 Healthcheck ===")
    print(f"Detected Done/Immutable Features ({len(done_features)}): {', '.join(sorted(done_features))}")

    errors.extend(check_spec_triads(specs_root, backlog_path))
    errors.extend(check_done_features_git_clean(repo_root, done_features, backlog_text))
    errors.extend(check_cr_backlog_registration(repo_root, backlog_text))
    errors.extend(check_subprocess_shell_safety(repo_root))
    errors.extend(check_inbox_and_stack_safety(repo_root))

    arch_errors, arch_warnings = run_boundary_audit(repo_root)
    errors.extend(arch_errors)
    warnings.extend(arch_warnings)
    warnings.extend(check_git_sync_status(repo_root))

    for w in warnings:
        print(f"  [WARN]  {w}")
    for e in errors:
        print(f"  [ERROR] {e}")

    if errors:
        print(f"\n❌ SDD Healthcheck FAILED with {len(errors)} error(s) and {len(warnings)} warning(s).")
        return 1

    print(f"\n✅ SDD Healthcheck PASSED (0 errors, {len(warnings)} warning(s)).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
