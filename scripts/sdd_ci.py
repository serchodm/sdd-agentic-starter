#!/usr/bin/env python3
"""CI-agnostic SDD governance and stack verification engine (FWK-013)."""

from __future__ import annotations

import argparse, json, os, re, shlex, subprocess, sys, time
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any

_FRAMEWORK_ROOT = Path(__file__).resolve().parent.parent
for _p in (str(_FRAMEWORK_ROOT), str(_FRAMEWORK_ROOT / "scripts"), str(_FRAMEWORK_ROOT / ".agents" / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from sdd_healthcheck import (  # noqa: E402
    check_cr_backlog_registration, check_done_features_git_clean, check_inbox_and_stack_safety,
    check_spec_triads, check_subprocess_shell_safety, parse_done_features_from_text,
)

try:
    from scripts.sdd_drift import run_drift_check
    from scripts.sdd_generator_tx import VerificationCommands, parse_verification_commands
    from scripts.sdd_git_state import is_link_or_junction
    from scripts.sdd_ownership import OwnershipError, parse_ownership_map
    from scripts.sdd_pack_registry import StackConfigError, parse_stack_config
    from scripts.sdd_portfolio import run_portfolio_ci_check
except ImportError:
    from sdd_drift import run_drift_check
    from sdd_generator_tx import VerificationCommands, parse_verification_commands
    from sdd_git_state import is_link_or_junction
    from sdd_ownership import OwnershipError, parse_ownership_map
    from sdd_pack_registry import StackConfigError, parse_stack_config
    from sdd_portfolio import run_portfolio_ci_check

VALID_CHECK_STATUSES: frozenset[str] = frozenset({"PASS", "FAIL", "SKIPPED_OPT_IN", "SKIPPED_NO_APPLICABLE"})
VALID_CI_MODES: frozenset[str] = frozenset({"auto", "framework", "project"})
DEFAULT_STACK_SLOTS: tuple[str, ...] = ("lint", "unit_test", "build", "infra")
ALL_STACK_SLOTS: tuple[str, ...] = ("lint", "unit_test", "integration_test", "build", "infra", "full_suite")
_FORBIDDEN_SHELL_TOKENS: tuple[str, ...] = (";", "|", "`", "$(", ">", "<", "\n", "\r", "\x00")
_SINGLE_AMP_RE = re.compile(r"(?<!&)&(?!&)|&&&")
_TEST_RAN_RE = re.compile(r"^Ran\s+(\d+)\s+tests?\s+in\s+", re.MULTILINE)
_SCRIPT_EXTS: tuple[str, ...] = (".py", ".sh", ".ps1", ".cmd")
_ODD_REQUIRED_FILES: tuple[str, ...] = ("docs/knowledge/ADRS.md", "docs/knowledge/API_CATALOG.md", "docs/knowledge/DATA_MODELS.md", "docs/knowledge/SYSTEM_TOPOLOGY.md", "docs/traceability/TRACEABILITY-MATRIX.md")


@dataclass(frozen=True)
class CheckResult:
    """Single deterministic verification check outcome."""

    name: str; status: str; detail: str; duration_ms: int
    data: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.status not in VALID_CHECK_STATUSES:
            raise ValueError(f"Invalid check status {self.status!r} for '{self.name}'.")


@dataclass(frozen=True)
class CiVerifyReport:
    """Aggregated CI verification report across governance and mode checks."""

    mode: str; overall_status: str; checks: tuple[CheckResult, ...]; repo_root: str

    def __post_init__(self) -> None:
        if self.mode not in {"framework", "project"}:
            raise ValueError(f"Invalid resolved CI mode {self.mode!r}.")
        if self.overall_status not in {"PASS", "FAIL"}:
            raise ValueError(f"Invalid overall_status {self.overall_status!r}.")


def _res(name: str, status: str, detail: str, t0: float, data: dict[str, Any] | None = None) -> CheckResult:
    return CheckResult(name=name, status=status, detail=detail, duration_ms=max(0, int((time.monotonic() - t0) * 1000)), data=data or {})


def _run_subprocess(argv: Sequence[str], cwd: Path, extra_env: Mapping[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "PYTHONIOENCODING": "utf-8", **(dict(extra_env) if extra_env else {})}
    return subprocess.run(list(argv), cwd=str(cwd), env=env, capture_output=True, text=True, encoding="utf-8", errors="replace", shell=False)


def _resolve_script(repo_root: Path, *parts: str) -> tuple[Path, bool]:
    local = repo_root.joinpath(*parts)
    return (local, True) if local.is_file() else (_FRAMEWORK_ROOT.joinpath(*parts), False)


def _run_script_check(name: str, script: Path, args: Sequence[str], cwd: Path, ok_msg: str, t0: float) -> CheckResult:
    res = _run_subprocess([sys.executable, str(script), *args], cwd=cwd)
    if res.returncode != 0:
        return _res(name, "FAIL", (res.stderr or res.stdout).strip() or f"{script.name} exited with {res.returncode}", t0)
    return _res(name, "PASS", ok_msg, t0)


def _load_json_object(path: Path, label: str, *, forbid_bom: bool = False) -> tuple[dict[str, Any] | None, str | None]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        return None, f"Cannot read {label}: {exc}"
    if forbid_bom and raw.startswith(b"\xef\xbb\xbf"):
        return None, f"{label} must not contain a UTF-8 BOM (\\xef\\xbb\\xbf)."
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return None, f"Invalid UTF-8 JSON in {label}: {exc}"
    if not isinstance(data, dict):
        return None, f"{label} must be a JSON object."
    return data, None


def detect_ci_mode(repo_root: Path, requested: str = "auto") -> str:
    """Resolve effective CI mode (`framework` or `project`) from request and `STACK.md`."""
    if requested not in VALID_CI_MODES:
        raise ValueError(f"Invalid CI mode {requested!r}; expected one of {sorted(VALID_CI_MODES)}.")
    if requested != "auto":
        return requested
    _, stack_approved = parse_stack_config(repo_root / "specs" / "STACK.md")
    if stack_approved:
        return "project"
    has_fwk = (repo_root / ".sdd" / "framework" / "BACKLOG.md").is_file() and (repo_root / ".sdd" / "framework" / "work-items").is_dir() and (repo_root / "tests" / "test_sdd_governance.py").is_file()
    return "framework" if has_fwk else "project"


def _validate_hook_cmd(cmd: object, event_name: str, root_res: Path) -> str | None:
    if not isinstance(cmd, str) or not cmd.strip():
        return f"Empty or invalid hook command under '{event_name}'."
    try:
        tokens = [t.strip("\"'").replace("\\", "/") for t in shlex.split(cmd, posix=False)]
    except ValueError as exc:
        return f"Malformed hook command under '{event_name}': {exc}"
    scripts = [t for t in tokens if t.endswith(_SCRIPT_EXTS)]
    if not scripts:
        return f"No script target found in hook command: {cmd!r}"
    for rel in scripts:
        if not rel or ":" in rel or rel.startswith("/") or ".." in PurePosixPath(rel).parts:
            return f"Unsafe or escaping hook script path: {rel}"
        agents_res = (root_res / ".agents").resolve()
        cand = (agents_res / rel) if (agents_res / rel).exists() else (root_res / rel)
        if is_link_or_junction(cand) or not cand.resolve().is_relative_to(root_res) or not cand.resolve().is_file():
            return f"Hook script path missing or escapes repo: {rel}"
    return None


def check_hooks_json(repo_root: Path) -> CheckResult:
    """Validate `.agents/hooks.json` existence, no UTF-8 BOM, valid JSON, and safe script paths."""
    t0, root_res = time.monotonic(), repo_root.resolve()
    hooks_path = repo_root / ".agents" / "hooks.json"
    if is_link_or_junction(hooks_path) or not hooks_path.is_file() or not hooks_path.resolve().is_relative_to(root_res):
        return _res("hooks", "FAIL", f"Missing or unsafe hooks file: {hooks_path}", t0)
    data, err = _load_json_object(hooks_path, ".agents/hooks.json", forbid_bom=True)
    if err or data is None:
        return _res("hooks", "FAIL", err or "Invalid .agents/hooks.json", t0)
    hooks_section = data.get("hooks")
    if not isinstance(hooks_section, dict) or not hooks_section:
        return _res("hooks", "FAIL", ".agents/hooks.json must define a non-empty 'hooks' object.", t0)
    checked = 0
    for event_name, entries in hooks_section.items():
        if not isinstance(entries, list):
            return _res("hooks", "FAIL", f"Hook event '{event_name}' must be a list.", t0)
        for entry in entries:
            if not isinstance(entry, dict) or not isinstance(entry.get("hooks", []), list):
                return _res("hooks", "FAIL", f"Invalid hook entry under '{event_name}'.", t0)
            for hook in entry.get("hooks", []):
                if cmd_err := _validate_hook_cmd(hook.get("command") if isinstance(hook, dict) else None, event_name, root_res):
                    return _res("hooks", "FAIL", cmd_err, t0)
                checked += 1
    return _res("hooks", "PASS", f"Verified .agents/hooks.json ({checked} command(s)).", t0, {"commands": checked}) if checked else _res("hooks", "FAIL", "No hook commands verified in .agents/hooks.json.", t0)


def check_healthcheck(repo_root: Path) -> CheckResult:
    """Run SDD integrity and Done-immutability healthcheck on `repo_root`."""
    t0 = time.monotonic()
    local_hc, is_local = _resolve_script(repo_root, ".agents", "scripts", "sdd_healthcheck.py")
    if is_local:
        return _run_script_check("healthcheck", local_hc, (), repo_root, "SDD healthcheck passed.", t0)
    specs_root, backlog_path = repo_root / "specs", repo_root / "specs" / "BACKLOG.md"
    backlog_text = backlog_path.read_text(encoding="utf-8", errors="ignore") if backlog_path.is_file() else ""
    done = parse_done_features_from_text(backlog_text)
    errors = [*check_spec_triads(specs_root, backlog_path), *check_done_features_git_clean(repo_root, done, backlog_text),
              *check_cr_backlog_registration(repo_root, backlog_text), *check_subprocess_shell_safety(repo_root), *check_inbox_and_stack_safety(repo_root)]
    return _res("healthcheck", "FAIL", "; ".join(errors), t0, {"errors": errors}) if errors else _res("healthcheck", "PASS", "SDD healthcheck passed.", t0)


def check_odd_compliance(repo_root: Path) -> CheckResult:
    """Validate 0DD knowledge artifacts, bilingual docs (`es`/`en`), and Done feature traceability."""
    t0 = time.monotonic()
    if missing := [rel for rel in _ODD_REQUIRED_FILES if not (repo_root / rel).is_file() or not (repo_root / rel).read_text(encoding="utf-8", errors="replace").strip()]:
        return _res("odd_compliance", "FAIL", f"Missing or empty 0DD artifacts: {', '.join(missing)}", t0)
    for lang in ("es", "en"):
        lang_dir = repo_root / "docs" / lang
        if not (lang_dir.is_dir() and any(p.is_file() and p.read_text(encoding="utf-8", errors="replace").strip() for p in lang_dir.rglob("*.md"))):
            return _res("odd_compliance", "FAIL", f"Missing bilingual 0DD Markdown documentation under docs/{lang}/.", t0)
    backlog_path = repo_root / "specs" / "BACKLOG.md"
    done_features = sorted(parse_done_features_from_text(backlog_path.read_text(encoding="utf-8", errors="replace") if backlog_path.is_file() else ""))
    matrix_text = (repo_root / "docs" / "traceability" / "TRACEABILITY-MATRIX.md").read_text(encoding="utf-8", errors="replace")
    if untraced := [feat for feat in done_features if not re.search(rf"\b{re.escape(feat)}\b", matrix_text)]:
        return _res("odd_compliance", "FAIL", f"0DD Violation: Done feature(s) missing from TRACEABILITY-MATRIX.md: {', '.join(untraced)}", t0, {"untraced": untraced})
    return _res("odd_compliance", "PASS", f"0DD compliance verified ({len(done_features)} Done feature(s) traced).", t0, {"done_features_count": len(done_features)})


def check_architecture_boundaries(repo_root: Path) -> CheckResult:
    """Run `verify_architecture_boundaries.py --repo-root <repo_root>`."""
    t0 = time.monotonic()
    script, _ = _resolve_script(repo_root, ".agents", "scripts", "verify_architecture_boundaries.py")
    return _run_script_check("boundaries", script, ("--repo-root", str(repo_root)), repo_root, "Architecture boundaries verified (0 errors).", t0)


def check_catalog_and_squad_lock(repo_root: Path, mode: str = "project") -> CheckResult:
    """Run `sdd_agent_generator.py --list` and `--verify` (or equivalent API check)."""
    t0 = time.monotonic()
    script, is_local = _resolve_script(repo_root, "scripts", "sdd_agent_generator.py")
    if is_local:
        for flag in ("--list", "--verify"):
            if (r := _run_script_check("catalog_verify", script, (flag,), repo_root, "ok", t0)).status == "FAIL":
                return r
        return _res("catalog_verify", "PASS", "Catalog and squad.lock.json verified cleanly.", t0)
    if (repo_root / ".agents" / "squad.lock.json").exists() or (repo_root / ".sdd" / "catalog").is_dir():
        try:
            from scripts import sdd_agent_generator
        except ImportError:
            import sdd_agent_generator
        try:
            sdd_agent_generator.list_catalog(repo_root=repo_root)
            mismatches = sdd_agent_generator.verify_squad(repo_root=repo_root, strict_agents=True)
        except Exception as exc:
            return _res("catalog_verify", "FAIL", str(exc), t0)
        return _res("catalog_verify", "FAIL", "; ".join(mismatches), t0) if mismatches else _res("catalog_verify", "PASS", "Catalog and squad.lock.json verified cleanly.", t0)
    return _res("catalog_verify", "FAIL" if mode == "framework" else "SKIPPED_NO_APPLICABLE", "Catalog and squad.lock.json not present in workspace.", t0)


def check_dags(repo_root: Path, mode: str = "project") -> CheckResult:
    """Validate all `03-tasks.md` DAGs under `.sdd/framework/work-items/*/` and `specs/*/*/`."""
    t0 = time.monotonic()
    task_files = sorted(repo_root.glob(".sdd/framework/work-items/*/03-tasks.md")) + sorted(repo_root.glob("specs/*/*/03-tasks.md"))
    if not task_files:
        return _res("dag_verify", "FAIL" if mode == "framework" else "SKIPPED_NO_APPLICABLE", "No 03-tasks.md files found to verify.", t0)
    dag_script, _ = _resolve_script(repo_root, "scripts", "sdd_dag.py")
    for tf in task_files:
        res = _run_subprocess([sys.executable, str(dag_script), "--verify", str(tf)], cwd=repo_root)
        if res.returncode != 0:
            msg = (res.stderr or res.stdout).strip() or f"exit {res.returncode}"
            return _res("dag_verify", "FAIL", f"DAG verification failed for {tf.relative_to(repo_root).as_posix()}: {msg}", t0)
    return _res("dag_verify", "PASS", f"Verified {len(task_files)} DAG specification(s).", t0, {"dag_count": len(task_files)})


def check_gate_seals(repo_root: Path) -> CheckResult:
    """Verify Gate 1..3 cryptographic seals when an active work item is configured."""
    t0, state_file = time.monotonic(), repo_root / ".agents" / "active_work_item.json"
    if is_link_or_junction(state_file):
        return _res("gate_seals", "FAIL", "State file .agents/active_work_item.json cannot be a symlink or junction.", t0)
    if not state_file.exists():
        return _res("gate_seals", "PASS", "No active work item (.agents/active_work_item.json absent).", t0)
    state, err = _load_json_object(state_file, ".agents/active_work_item.json")
    if err or state is None:
        return _res("gate_seals", "FAIL", err or "Invalid .agents/active_work_item.json", t0)
    active_id = str(state.get("active_work_item_id") or "").strip()
    if not active_id or active_id.upper() == "IDLE":
        return _res("gate_seals", "PASS", "Active work item is IDLE; gate seals clean.", t0)
    if active_id.upper().startswith("REL-"):
        return _res("gate_seals", "PASS", f"Release work item '{active_id}' uses Gate 6; Gate 1..3 seals exempt.", t0)
    seal_script, _ = _resolve_script(repo_root, "scripts", "sdd_gate_seal.py")
    return _run_script_check("gate_seals", seal_script, ("--verify", "--repo-root", str(repo_root)), repo_root, f"Verified gate seals for {active_id}.", t0)


def check_git_and_instincts(repo_root: Path) -> CheckResult:
    """Run `sdd_git.py status` and `sdd_instincts.py list` checks."""
    t0 = time.monotonic()
    git_script, has_local_git = _resolve_script(repo_root, "scripts", "sdd_git.py")
    if has_local_git:
        if (r := _run_script_check("git_and_instincts", git_script, ("status",), repo_root, "ok", t0)).status == "FAIL":
            return r
    elif (repo_root / ".git").exists() and (res := _run_subprocess(["git", "status", "--porcelain"], cwd=repo_root)).returncode != 0:
        return _res("git_and_instincts", "FAIL", res.stderr.strip() or "git status failed.", t0)
    inst_script, has_local_inst = _resolve_script(repo_root, "scripts", "sdd_instincts.py")
    if has_local_inst:
        if (r := _run_script_check("git_and_instincts", inst_script, ("list",), repo_root, "ok", t0)).status == "FAIL":
            return r
    elif (inst_file := repo_root / ".agents" / "instincts.json").is_file() and (err := _load_json_object(inst_file, ".agents/instincts.json")[1]):
        return _res("git_and_instincts", "FAIL", err, t0)
    return _res("git_and_instincts", "PASS", "Git orchestrator and atomic instincts verified.", t0)


def check_design_tokens(repo_root: Path) -> CheckResult:
    """Run `sdd_tokens_validator.py --allow-missing` in `repo_root`."""
    t0 = time.monotonic()
    tok_script, _ = _resolve_script(repo_root, "scripts", "sdd_tokens_validator.py")
    return _run_script_check("tokens", tok_script, ("--allow-missing",), repo_root, "Design tokens consistency verified.", t0)


def check_spec_drift(repo_root: Path, mode: str = "project") -> CheckResult:
    """Run offline Spec Drift verification in `project` mode when features or governed zones exist."""
    t0 = time.monotonic()
    if mode == "framework": return _res("spec_drift", "SKIPPED_NO_APPLICABLE", "Spec drift check skipped in framework mode.", t0)
    try:
        stack_path = repo_root / "specs" / "STACK.md"
        if is_link_or_junction(repo_root / "specs") or is_link_or_junction(stack_path): raise OwnershipError("Refusing symlink or junction on specs/STACK.md.")
        cfg = parse_ownership_map(stack_path) if stack_path.exists() else None
        if not (cfg and any(z.governance == "governed" for z in cfg.zones)) and not any((repo_root / "specs" / "features").glob("FEAT-*")):
            return _res("spec_drift", "SKIPPED_NO_APPLICABLE", "No FEAT-* specs or governed ownership zones found.", t0)
        r = run_drift_check(repo_root)
    except (OwnershipError, ValueError, OSError) as exc: return _res("spec_drift", "FAIL", f"Spec drift check failed closed: {exc}", t0)
    data = {"findings": [asdict(f) for f in r.findings], "warnings": list(r.warnings), "governed_files": r.governed_files, "legacy_readonly_files": r.legacy_readonly_files, "covered_files": r.covered_files, "citations_checked": r.citations_checked}
    return _res("spec_drift", r.status, f"Spec drift verified ({r.citations_checked} citation(s), {r.governed_files} governed file(s))." if r.status == "PASS" else f"Spec drift detected {len(r.findings)} finding(s).", t0, data)


def check_portfolio(repo_root: Path) -> CheckResult:
    """Validate portfolio epics (`EPIC-*.md`) and feature dependencies via `sdd_portfolio`."""
    t0 = time.monotonic()
    try:
        status, detail, data = run_portfolio_ci_check(repo_root)
    except (ValueError, OSError) as exc:
        return _res("portfolio", "FAIL", f"Portfolio check failed closed: {exc}", t0)
    return _res("portfolio", status, detail, t0, data)


def check_framework_unittest(repo_root: Path, min_tests: int = 120, *, tests_dir: str = "tests", skip_tests: bool = False) -> CheckResult:
    """Execute deterministic `unittest discover` suite and enforce `tests_run >= min_tests`."""
    t0 = time.monotonic()
    if skip_tests or os.environ.get("SDD_CI_NESTED_TEST") == "1":
        why = "--skip-tests requested" if skip_tests else "SDD_CI_NESTED_TEST=1 recursion guard active"
        return _res("framework_tests", "SKIPPED_OPT_IN", f"Framework unittest skipped ({why}).", t0, {"tests_run": 0, "min_tests": min_tests, "skipped": True})
    if not (target_dir := repo_root / tests_dir).is_dir():
        return _res("framework_tests", "FAIL", f"Missing tests directory: {target_dir}", t0, {"tests_run": 0, "min_tests": min_tests})
    res = _run_subprocess([sys.executable, "-m", "unittest", "discover", "-s", tests_dir, "-v"], cwd=repo_root, extra_env={"SDD_CI_NESTED_TEST": "1"})
    combined = f"{res.stdout}\n{res.stderr}"
    match = _TEST_RAN_RE.search(combined)
    tests_run = int(match.group(1)) if match else 0
    data = {"tests_run": tests_run, "min_tests": min_tests}
    if res.returncode != 0:
        return _res("framework_tests", "FAIL", f"Unit test suite failed (tests_run={tests_run}):\n" + "\n".join(combined.strip().splitlines()[-15:]), t0, data)
    if tests_run < min_tests:
        return _res("framework_tests", "FAIL", f"Test count regression: ran {tests_run} tests, expected >= {min_tests}.", t0, data)
    return _res("framework_tests", "PASS", f"{tests_run} deterministic tests passed (>= {min_tests} required).", t0, data)


def split_safe_chained_command(cmd: str) -> list[list[str]]:
    """Validate and split a safe `&&`-chained command into argv lists without shell metacharacters."""
    if not isinstance(cmd, str) or not cmd.strip(): raise ValueError("Verification command cannot be empty.")
    if bad := next((tok for tok in _FORBIDDEN_SHELL_TOKENS if tok in cmd), None): raise ValueError(f"Forbidden shell metacharacter {bad!r} in verification command.")
    if _SINGLE_AMP_RE.search(cmd): raise ValueError("Isolated '&' or '&&&' is forbidden in verification command.")
    segments, buf, quote, i, n = [], [], None, 0, len(cmd)
    while i < n:
        ch = cmd[i]
        if quote != "'" and ch == "\\" and i + 1 < n:
            buf.append(cmd[i : i + 2]); i += 2; continue
        if quote:
            quote = None if ch == quote else quote; buf.append(ch)
        elif ch in ("'", '"'):
            quote = ch; buf.append(ch)
        elif cmd[i : i + 2] == "&&":
            segments.append("".join(buf)); buf.clear(); i += 2; continue
        else:
            buf.append(ch)
        i += 1
    if quote is not None: raise ValueError("Unclosed quote in verification command.")
    segments.append("".join(buf))
    argv_list: list[list[str]] = []
    for seg in segments:
        if not (clean_seg := seg.strip()) or not (tokens := shlex.split(clean_seg, posix=True)): raise ValueError("Empty command segment around '&&'.")
        argv_list.append(tokens)
    return argv_list


def _resolve_requested_slots(include_integration: bool, stack_slots: Sequence[str] | None) -> tuple[str, ...]:
    if not stack_slots: return (*DEFAULT_STACK_SLOTS, "integration_test", "full_suite") if include_integration else DEFAULT_STACK_SLOTS
    parsed: list[str] = []
    for slot in (s.strip() for raw in stack_slots for s in raw.split(",") if s.strip()):
        if slot not in ALL_STACK_SLOTS: raise ValueError(f"Unknown stack verification slot {slot!r}; expected one of {ALL_STACK_SLOTS}.")
        if slot not in parsed: parsed.append(slot)
    if not parsed: raise ValueError("--stack-slots provided without valid slot names.")
    return tuple(parsed)


def check_stack_commands(
    repo_root: Path, mode: str, *, run_stack: bool = False, run_stack_if_approved: bool = False,
    include_integration: bool = False, stack_slots: Sequence[str] | None = None,
) -> CheckResult:
    """Opt-in fail-closed execution of `specs/STACK.md §2.5` commands with `shell=False`."""
    t0 = time.monotonic()
    try:
        _, stack_approved = parse_stack_config(repo_root / "specs" / "STACK.md")
    except StackConfigError as exc:
        return _res("stack_commands", "FAIL", f"Invalid specs/STACK.md: {exc}", t0)
    skip_status = "SKIPPED_NO_APPLICABLE" if mode == "framework" else "SKIPPED_OPT_IN"
    if (not run_stack and not run_stack_if_approved) or (run_stack_if_approved and not run_stack and not stack_approved):
        return _res("stack_commands", skip_status, "Stack verification commands skipped.", t0)
    if not stack_approved:
        return _res("stack_commands", "FAIL", "Gate S0 is not approved in specs/STACK.md; --run-stack refused (fail-closed).", t0)
    try:
        slots = _resolve_requested_slots(include_integration, stack_slots)
        verif: VerificationCommands = parse_verification_commands(repo_root / "specs" / "STACK.md")
        planned: list[tuple[str, list[list[str]]]] = []
        for slot in slots:
            if (raw_cmd := getattr(verif, slot, None)) is None:
                if stack_slots:
                    return _res("stack_commands", "FAIL", f"Requested verification slot '{slot}' is missing in specs/STACK.md §2.5.", t0)
                continue
            planned.append((slot, split_safe_chained_command(raw_cmd)))
    except (ValueError, StackConfigError) as exc:
        return _res("stack_commands", "FAIL", str(exc), t0)
    if not planned:
        return _res("stack_commands", "FAIL", "No verification commands configured in specs/STACK.md §2.5.", t0)
    executed: list[str] = []
    for slot, argv_chain in planned:
        for argv in argv_chain:
            try:
                res = _run_subprocess(argv, cwd=repo_root)
            except OSError as exc:
                return _res("stack_commands", "FAIL", f"Slot '{slot}' failed to start ({argv[0]}): {exc}", t0)
            if res.returncode != 0:
                return _res("stack_commands", "FAIL", f"Slot '{slot}' command {argv!r} failed: {(res.stderr or res.stdout).strip() or res.returncode}", t0, {"failed_slot": slot})
        executed.append(slot)
    return _res("stack_commands", "PASS", f"Executed stack slots cleanly: {', '.join(executed)}.", t0, {"slots": executed})


def run_ci_verify(
    repo_root: Path, *, mode: str = "auto", run_stack: bool = False, run_stack_if_approved: bool = False,
    include_integration: bool = False, stack_slots: Sequence[str] | None = None,
    min_tests: int = 120, skip_tests: bool = False, tests_dir: str = "tests",
) -> CiVerifyReport:
    """Execute full CI verification pipeline and return structured `CiVerifyReport`."""
    root = repo_root.resolve()
    resolved_mode = detect_ci_mode(root, requested=mode)
    checks: list[CheckResult] = [
        check_hooks_json(root), check_healthcheck(root), check_odd_compliance(root), check_architecture_boundaries(root),
        check_catalog_and_squad_lock(root, mode=resolved_mode), check_dags(root, mode=resolved_mode), check_gate_seals(root),
        check_git_and_instincts(root), check_design_tokens(root), check_spec_drift(root, mode=resolved_mode), check_portfolio(root),
    ]
    if resolved_mode == "framework":
        checks.append(check_framework_unittest(root, min_tests=min_tests, tests_dir=tests_dir, skip_tests=skip_tests))
    checks.append(check_stack_commands(root, resolved_mode, run_stack=run_stack, run_stack_if_approved=run_stack_if_approved, include_integration=include_integration, stack_slots=stack_slots))
    overall = "FAIL" if any(c.status == "FAIL" for c in checks) else "PASS"
    return CiVerifyReport(mode=resolved_mode, overall_status=overall, checks=tuple(checks), repo_root=str(root))


def report_to_dict(report: CiVerifyReport) -> dict[str, Any]:
    """Serialize `CiVerifyReport` to a JSON-compatible dictionary."""
    return {
        "mode": report.mode, "overall_status": report.overall_status, "repo_root": report.repo_root,
        "checks": [{"name": c.name, "status": c.status, "detail": c.detail, "duration_ms": c.duration_ms, "data": c.data} for c in report.checks],
    }


def format_report_text(report: CiVerifyReport) -> str:
    """Render human-readable CI verification summary."""
    lines = [f"=== SDD CI Verify ({report.mode} mode) [{report.overall_status}] ===", f"Repo Root: {report.repo_root}"]
    lines.extend(f"  [{c.status}] {c.name} ({c.duration_ms}ms): {c.detail}" for c in report.checks)
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    """Build CLI argument parser for `scripts/sdd_ci.py`."""
    p = argparse.ArgumentParser(description="CI-agnostic SDD governance and stack verification engine.")
    for flag, kw in (
        ("--repo-root", {"type": Path, "default": _FRAMEWORK_ROOT, "help": "Repository root directory."}),
        ("--mode", {"choices": ("auto", "framework", "project"), "default": "auto", "help": "CI verification mode."}),
        ("--run-stack", {"action": "store_true", "help": "Execute STACK.md §2.5 commands (fail-closed if S0 unapproved)."}),
        ("--run-stack-if-approved", {"action": "store_true", "help": "Execute STACK.md §2.5 commands only if Gate S0 is approved."}),
        ("--include-integration", {"action": "store_true", "help": "Also run integration_test and full_suite stack slots."}),
        ("--stack-slots", {"nargs": "+", "default": None, "help": "Explicit stack slots to execute."}),
        ("--min-tests", {"type": int, "default": 120, "help": "Minimum unit test count in framework mode."}),
        ("--skip-tests", {"action": "store_true", "help": "Skip framework unittest execution."}),
        ("--format", {"dest": "output_format", "choices": ("text", "json"), "default": "text", "help": "Output format."}),
    ):
        p.add_argument(flag, **kw)
    return p


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint returning `0` on PASS and `1` on FAIL."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except (AttributeError, OSError, ValueError) as exc:
                print(f"[WARN] UTF-8 stream reconfigure failed: {exc}", file=sys.stderr)
    args = build_parser().parse_args(argv)
    if args.min_tests < 0:
        print("[FAIL] --min-tests must be >= 0.", file=sys.stderr)
        return 1
    try:
        report = run_ci_verify(args.repo_root, mode=args.mode, run_stack=args.run_stack, run_stack_if_approved=args.run_stack_if_approved,
                               include_integration=args.include_integration, stack_slots=args.stack_slots, min_tests=args.min_tests, skip_tests=args.skip_tests)
    except (ValueError, StackConfigError, OSError) as exc:
        print(json.dumps({"overall_status": "FAIL", "error": str(exc)}, indent=2, ensure_ascii=False) if args.output_format == "json" else f"[FAIL] {exc}",
              file=sys.stdout if args.output_format == "json" else sys.stderr)
        return 1
    print(json.dumps(report_to_dict(report), indent=2, ensure_ascii=False) if args.output_format == "json" else format_report_text(report))
    return 0 if report.overall_status == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
