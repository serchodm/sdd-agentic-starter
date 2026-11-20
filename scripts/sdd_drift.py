#!/usr/bin/env python3
"""Deterministic offline Spec Drift detector and Strangler Fig zone inspector (FWK-016)."""

from __future__ import annotations

import argparse, json, re, subprocess, sys
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError, OSError):
            pass

_FRAMEWORK_ROOT = Path(__file__).resolve().parent.parent
for _p in (str(_FRAMEWORK_ROOT), str(_FRAMEWORK_ROOT / "scripts"), str(_FRAMEWORK_ROOT / ".agents" / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from sdd_healthcheck import DONE_STATES, _parse_backlog_entries, _split_markdown_row, _strip_fenced_blocks  # noqa: E402
from sdd_immutable_feature_guard import resolve_repo_relative_path  # noqa: E402
from sdd_repo_map import EXTENSION_PARSERS, IGNORED_DIRS, collect_source_files  # noqa: E402

try:  # noqa: E402
    from scripts.sdd_git_state import is_link_or_junction
    from scripts.sdd_ownership import OwnershipError, OwnershipMapConfig, derive_candidate_roots, parse_ownership_map, resolve_path_zone
except ImportError:
    from sdd_git_state import is_link_or_junction
    from sdd_ownership import OwnershipError, OwnershipMapConfig, derive_candidate_roots, parse_ownership_map, resolve_path_zone

VALID_FINDING_KINDS: frozenset[str] = frozenset({"UNCOVERED_FILE", "MISSING_SOURCE_FILE", "MISSING_SYMBOL", "UNLINKED_CODE_DRIFT"})
VALID_SEVERITIES: frozenset[str] = frozenset({"error", "warning"})
_FALLBACK_ROOTS: tuple[str, ...] = ("src", "app", "lib", "backend", "frontend", "api", "web", "services", "packages", "cmd", "internal", "DDBB")
_TEST_DIRS: frozenset[str] = frozenset({"tests", "test", "__tests__"})
_SCAN_IGNORED: frozenset[str] = frozenset(IGNORED_DIRS) | {".agents", ".worktrees", ".sdd", "specs", "docs"}
_CLOSED_STATES: frozenset[str] = DONE_STATES | frozenset({"done / completed", "cancelled", "canceled", "rejected"})
_INACTIVE_BUG_STATES: frozenset[str] = _CLOSED_STATES | frozenset({"candidate", "backlog"})
_TS_JS_EXTS: frozenset[str] = frozenset({".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"})
_SRC_TAG_RE = re.compile(r"\b(SRC-\d{3,4})\b", re.IGNORECASE)
_FEAT_ID_RE = re.compile(r"\b(FEAT-\d{3,4})\b", re.IGNORECASE)
_DIR_ID_RE = re.compile(r"^((?:FEAT|CR|BUG|HOTFIX)-\d{3,4})(?:-|$)", re.IGNORECASE)
_HEADER_STATUS_RE = re.compile(r"^\s*(?:[-*]\s*)?(?:\*\*)?(?:Estado|Status)(?:\*\*)?\s*:\s*`?([^`\n]+?)`?\s*$", re.IGNORECASE | re.MULTILINE)
_PATH_SYM_RE = re.compile(r"(?<![A-Za-z0-9_./\\-])([A-Za-z0-9_./\\-]+?\.[A-Za-z0-9]+)::([A-Za-z_][A-Za-z0-9_.:]*)(?:\(\))?")
_BARE_PATH_RE = re.compile(r"(?<![A-Za-z0-9_./\\:-])([A-Za-z0-9_./\\-]+?\.[A-Za-z0-9]+)(?![A-Za-z0-9_./\\:-])")
_SHA_TOKEN_RE = re.compile(r"(?<![A-Za-z0-9_./-])([0-9a-f]{7,40})(?![A-Za-z0-9_./-])", re.IGNORECASE)
_SAFE_GIT_REF_RE = re.compile(r"^[A-Za-z0-9_./@^~-]+$")
_CR_REF_HINT_RE = re.compile(r"(?:feature|afectada|affected|parent|vinculad|linked|FEAT-\d{3,4})", re.IGNORECASE)
_DECL_KW_RE = re.compile(r"^(?:interface|type|class|record|struct|enum|trait|union|object|module|defmodule|namespace|package|contract|library|actor|mixin|async\s+def|def|defp|fn|fun|function|component|pub\s+fn)\s+([A-Za-z_][A-Za-z0-9_:.]*)")

@dataclass(frozen=True)
class SrcCitation:
    """Single source citation parsed from a FEAT-XXX or CR-XXX specification."""
    feature_id: str; src_id: str; rel_path: str; symbol: str | None; commit_sha: str | None

@dataclass(frozen=True)
class DriftFinding:
    """Single deterministic Spec Drift or coverage finding."""
    kind: str; severity: str; feature_id: str; path: str; symbol: str | None; detail: str
    def __post_init__(self) -> None:
        if self.kind not in VALID_FINDING_KINDS or self.severity not in VALID_SEVERITIES:
            raise ValueError(f"Invalid drift finding ({self.kind!r}, {self.severity!r}).")

@dataclass(frozen=True)
class DriftReport:
    """Aggregated offline Spec Drift verification report."""
    repo_root: str; status: str; findings: tuple[DriftFinding, ...]
    governed_files: int; legacy_readonly_files: int; covered_files: int; citations_checked: int; warnings: tuple[str, ...]
    def __post_init__(self) -> None:
        if self.status not in ("PASS", "FAIL"):
            raise ValueError(f"Invalid drift report status: {self.status!r}")

@dataclass
class _WorkState:
    statuses: dict[str, str]; cr_links: dict[str, set[str]]; item_dirs: dict[str, Path]; citations_by_owner: dict[str, list[SrcCitation]]
    open_crs_by_feat: dict[str, set[str]]; closed_crs_by_feat: dict[str, list[str]]; has_active_bug: bool; active_cr_id: str | None; active_cr_links: set[str]

def _norm_rel(raw_path: str) -> str:
    return re.sub(r"^(?:\./)+", "", raw_path.strip().strip("`'\"()[]").replace("\\", "/")).lstrip("/")

def _supported_rel(raw_path: str) -> str | None:
    norm = _norm_rel(raw_path) if raw_path and "://" not in raw_path else ""
    return norm if norm and ".." not in PurePosixPath(norm).parts and PurePosixPath(norm).suffix.lower() in EXTENSION_PARSERS else None

def _safe_read_text(path: Path, root: Path, label: str) -> str:
    resolve_repo_relative_path(str(path), root)
    if not path.is_file():
        raise ValueError(f"Expected regular file for {label}: '{path}'.")
    return path.read_text(encoding="utf-8", errors="replace")

def inspect_ownership_path(repo_root: Path, rel_posix: str) -> tuple[bool, str | None]:
    """Inspect `specs/STACK.md` ownership-map for `rel_posix`, returning `(matched, legacy_zone_id)`."""
    stack_path = repo_root / "specs" / "STACK.md"
    if is_link_or_junction(repo_root) or is_link_or_junction(stack_path.parent) or is_link_or_junction(stack_path):
        raise OwnershipError("Refusing symlink or junction on specs/STACK.md.")
    config = parse_ownership_map(stack_path) if stack_path.exists() else None
    norm_rel = _norm_rel(rel_posix)
    zone = resolve_path_zone(config, norm_rel) if (config is not None and norm_rel) else None
    return (False, None) if zone is None else (True, zone.id if zone.governance == "legacy-readonly" else None)

def _run_git(root: Path, args: list[str], *, timeout: int = 10) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=str(root), capture_output=True, text=True, encoding="utf-8", errors="replace", shell=False, timeout=timeout)

def _verify_commit(root: Path, ref: str) -> str | None:
    res = _run_git(root, ["rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"])
    return res.stdout.strip() if res.returncode == 0 and res.stdout.strip() else None

def _newest_commit(root: Path, shas: list[str]) -> str | None:
    newest = shas[0] if shas else None
    for cand in shas[1:]:
        if cand != newest and _run_git(root, ["merge-base", "--is-ancestor", newest, cand]).returncode == 0:  # type: ignore[arg-type]
            newest = cand
    return newest

def _line_sha(line: str) -> str | None:
    return next((m.group(1).lower() for m in _SHA_TOKEN_RE.finditer(line) if any(ch.isdigit() for ch in m.group(1))), None)

def _extract_citations(owner_id: str, raw_text: str) -> list[SrcCitation]:
    out: list[SrcCitation] = []
    for line in re.sub(r"<!--.*?-->", "", _strip_fenced_blocks(raw_text), flags=re.DOTALL).splitlines():
        if not (src_m := _SRC_TAG_RE.search(line)):
            continue
        src_id, line_sha, occupied = src_m.group(1).upper(), _line_sha(line), []
        for m in _PATH_SYM_RE.finditer(line):
            if rel := _supported_rel(m.group(1)):
                occupied.append(m.span())
                out.append(SrcCitation(owner_id, src_id, rel, m.group(2).rstrip("()"), _line_sha(line[m.end() : m.end() + 48]) or line_sha))
        for m in _BARE_PATH_RE.finditer(line):
            if not any(s <= m.start() < e for s, e in occupied) and (rel := _supported_rel(m.group(1))):
                out.append(SrcCitation(owner_id, src_id, rel, None, _line_sha(line[m.end() : m.end() + 48]) or line_sha))
    return out

def _collect_work_state(root: Path, warnings: list[str]) -> _WorkState:
    backlog_path = root / "specs" / "BACKLOG.md"
    statuses, cr_links = (_parse_backlog_entries(_safe_read_text(backlog_path, root, "specs/BACKLOG.md")) if (backlog_path.exists() or is_link_or_junction(backlog_path)) else ({}, {}))
    item_dirs: dict[str, Path] = {}
    cits_by_owner: dict[str, list[SrcCitation]] = {}
    for bucket, files in (("features", ("01-spec.md", "02-tech-spec.md")), ("changes", ("01-spec.md", "02-tech-spec.md")), ("bugs", ("01-bug-report.md", "02-fix-spec.md"))):
        bdir = root / "specs" / bucket
        if not bdir.exists():
            continue
        resolve_repo_relative_path(f"specs/{bucket}", root)
        for entry in sorted(bdir.iterdir()):
            if is_link_or_junction(entry):
                raise ValueError(f"Refusing symlink or junction spec dir: '{entry}'.")
            if not entry.is_dir() or not (m := _DIR_ID_RE.match(entry.name)):
                continue
            item_id = m.group(1).upper()
            item_dirs[item_id] = entry
            for fname in files:
                fpath = entry / fname
                if not fpath.exists() and not is_link_or_junction(fpath):
                    continue
                text = _safe_read_text(fpath, root, f"specs/{bucket}/{entry.name}/{fname}")
                cleaned = re.sub(r"<!--.*?-->", "", _strip_fenced_blocks(text), flags=re.DOTALL)
                if fname in ("01-spec.md", "01-bug-report.md") and not statuses.get(item_id):
                    if hm := _HEADER_STATUS_RE.search("\n".join(cleaned.splitlines()[:35])):
                        statuses[item_id] = re.sub(r"\s+", " ", hm.group(1)).strip().lower()
                if item_id.startswith(("FEAT-", "CR-")):
                    cits_by_owner.setdefault(item_id, []).extend(_extract_citations(item_id, text))
                if item_id.startswith("CR-") and fname == "01-spec.md":
                    for idx, ln in enumerate(cleaned.splitlines()):
                        if idx < 30 or _CR_REF_HINT_RE.search(ln):
                            cr_links.setdefault(item_id, set()).update(fm.group(1).upper() for fm in _FEAT_ID_RE.finditer(ln))

    open_crs: dict[str, set[str]] = {}
    closed_crs: dict[str, list[str]] = {}
    for cr_id in sorted({k for k in (*statuses, *item_dirs) if k.startswith("CR-")}, key=lambda s: int(s.partition("-")[2]) if s.partition("-")[2].isdigit() else 0):
        st = statuses.get(cr_id, "")
        if st not in {"cancelled", "canceled", "rejected"}:
            for fid in cr_links.get(cr_id, set()):
                (closed_crs.setdefault(fid, []).append(cr_id) if st in DONE_STATES else open_crs.setdefault(fid, set()).add(cr_id))

    has_bug = any(k.startswith(("BUG-", "HOTFIX-")) and st not in _INACTIVE_BUG_STATES for k, st in statuses.items())
    active_cr_id, active_cr_links = None, set()
    active_json = root / ".agents" / "active_work_item.json"
    if active_json.exists() or is_link_or_junction(active_json):
        try:
            raw = json.loads(_safe_read_text(active_json, root, ".agents/active_work_item.json"))
            if isinstance(raw, dict) and (wm := _DIR_ID_RE.match(str(raw.get("active_work_item_id") or "").strip())) and str(raw.get("status") or "").strip().lower() not in (_CLOSED_STATES | {"idle"}):
                wid = wm.group(1).upper()
                if wid.startswith(("BUG-", "HOTFIX-")):
                    has_bug = True
                elif wid.startswith("CR-") and statuses.get(wid, "") not in _CLOSED_STATES:
                    active_cr_id, active_cr_links = wid, set(cr_links.get(wid, set()))
        except Exception as exc:
            warnings.append(f"Could not parse .agents/active_work_item.json: {exc}")
    return _WorkState(statuses, cr_links, item_dirs, cits_by_owner, open_crs, closed_crs, has_bug, active_cr_id, active_cr_links)

def _collect_traceability_coverage(root: Path) -> dict[str, set[str]]:
    cov: dict[str, set[str]] = {}
    matrix = root / "docs" / "traceability" / "TRACEABILITY-MATRIX.md"
    if not matrix.exists() and not is_link_or_junction(matrix):
        return cov
    section_feat: str | None = None
    for line in re.sub(r"<!--.*?-->", "", _strip_fenced_blocks(_safe_read_text(matrix, root, "docs/traceability/TRACEABILITY-MATRIX.md")), flags=re.DOTALL).splitlines():
        if line.lstrip().startswith("#"):
            section_feat = m.group(1).upper() if (m := _FEAT_ID_RE.search(line)) else None
        elif _split_markdown_row(line) and (feats := {m.group(1).upper() for m in _FEAT_ID_RE.finditer(line)} or ({section_feat} if section_feat else set())):
            for pm in _BARE_PATH_RE.finditer(line):
                if rel := _supported_rel(pm.group(1)):
                    cov.setdefault(rel, set()).update(feats)
    return cov

def _resolve_active_citations(state: _WorkState) -> list[SrcCitation]:
    superseded = {
        (fid, c.rel_path): cr_id
        for cr_id in sorted((k for k in state.citations_by_owner if k.startswith("CR-")), key=lambda s: int(s.partition("-")[2]) if s.partition("-")[2].isdigit() else 0)
        if state.statuses.get(cr_id, "") not in {"cancelled", "canceled", "rejected"}
        for fid in state.cr_links.get(cr_id, set()) for c in state.citations_by_owner[cr_id]
    }
    active: list[SrcCitation] = []
    for owner_id in sorted(state.citations_by_owner):
        if state.statuses.get(owner_id, "") in {"cancelled", "canceled", "rejected"}:
            continue
        merged: dict[tuple[str, str, str, str | None], SrcCitation] = {}
        for cit in state.citations_by_owner[owner_id]:
            key = (cit.feature_id, cit.src_id, cit.rel_path, cit.symbol)
            if (prev := merged.get(key)) is None or (prev.commit_sha is None and cit.commit_sha is not None):
                merged[key] = cit
        for cit in merged.values():
            if owner_id.startswith("FEAT-"):
                if (owner_id, cit.rel_path) not in superseded:
                    active.append(cit)
            elif not (linked := state.cr_links.get(owner_id, set())) or any(superseded.get((fid, cit.rel_path)) in (None, owner_id) for fid in linked):
                active.append(cit)
    return active

def _collect_governed_and_legacy(root: Path, cfg: OwnershipMapConfig | None) -> tuple[list[str], int]:
    roots = derive_candidate_roots(cfg) if cfg else _FALLBACK_ROOTS
    seen: set[str] = set()
    governed: list[str] = []
    legacy_count = 0

    def _add(fp: Path) -> None:
        nonlocal legacy_count
        if is_link_or_junction(fp):
            raise ValueError(f"Refusing symlink or junction source file: '{fp}'.")
        rel = resolve_repo_relative_path(str(fp), root)
        if rel in seen or any(part in _TEST_DIRS for part in PurePosixPath(rel).parts):
            return
        seen.add(rel)
        if cfg is not None:
            zone = resolve_path_zone(cfg, rel)
            if zone is None or zone.owner.lower() == "qa-tester":
                return
            if zone.governance == "legacy-readonly":
                legacy_count += 1
                return
        governed.append(rel)

    for rname in roots:
        if (cand := root / rname).exists() or is_link_or_junction(cand):
            resolve_repo_relative_path(rname, root)
            for sf in collect_source_files(cand, _SCAN_IGNORED):
                _add(sf)
    if cfg is not None and any(len(PurePosixPath(p).parts) == 1 for z in cfg.zones for p in z.paths):
        for entry in sorted(root.iterdir()):
            if entry.is_file() and entry.suffix.lower() in EXTENSION_PARSERS:
                _add(entry)
    return sorted(governed), legacy_count

def _extract_symbols(file_path: Path) -> tuple[set[str], set[tuple[str, str]]]:
    parser = EXTENSION_PARSERS.get(file_path.suffix.lower())
    if parser is None:
        return set(), set()
    names: set[str] = set()
    class_methods: set[tuple[str, str]] = set()
    is_py, cur_cls = file_path.suffix.lower() == ".py", None
    for raw in parser(file_path):
        s = raw.strip()
        if not s or s.startswith(("[Parse Error]", "[Read Error]")):
            continue
        if is_py:
            indent = len(raw) - len(raw.lstrip(" "))
            if m := re.match(r"^class\s+([A-Za-z_][A-Za-z0-9_]*)", s):
                names.add(m.group(1))
                cur_cls = m.group(1) if indent <= 2 else None
            elif m := re.match(r"^(?:async\s+)?def\s+([A-Za-z_][A-Za-z0-9_]*)", s):
                names.add(m.group(1))
                if indent >= 4 and cur_cls:
                    class_methods.add((cur_cls, m.group(1)))
                elif indent <= 2:
                    cur_cls = None
        elif m := (_DECL_KW_RE.match(s) or re.match(r"^(?:pub\s+const|func\s+(?:\([^)]*\)\s+)?)\s*([A-Za-z_][A-Za-z0-9_]*)", s)):
            names.add(m.group(1).split(".")[-1].split(":")[-1])
        elif m := re.match(r"^CREATE\s+(?:TABLE|VIEW|PROCEDURE|FUNCTION|INDEX|TRIGGER)\s+([A-Za-z0-9_.\"]+)", s, re.I):
            names.add(m.group(1).strip('"').split(".")[-1])
        elif toks := re.findall(r"[A-Za-z_~][A-Za-z0-9_~]*", s.split("(", 1)[0]):
            names.add(toks[-1])
    return names, class_methods

def _symbol_exists(symbol: str, ext: str, names: set[str], class_methods: set[tuple[str, str]]) -> bool:
    clean = symbol.rstrip("()")
    if "." not in clean and "::" not in clean:
        return clean in names
    parts = [p for p in re.split(r"::|\.", clean) if p]
    if not parts:
        return False
    leaf, parent = parts[-1], (parts[-2] if len(parts) >= 2 else "")
    if ext == ".py":
        return (parent, leaf) in class_methods or (leaf in names and parent not in names)
    return leaf in names or (ext in _TS_JS_EXTS and parent in names)

def _resolve_git_base(root: Path, base_ref: str | None, head_sha: str) -> str | None:
    if base_ref is not None:
        ref = base_ref.strip()
        if not ref or ref.startswith("-") or not _SAFE_GIT_REF_RE.match(ref) or not (res := _verify_commit(root, ref)):
            raise ValueError(f"Invalid or unknown --base-ref: {base_ref!r}")
        return res
    for ref in ("origin/develop", "develop", "origin/main", "main"):
        if _verify_commit(root, ref):
            mb = _run_git(root, ["merge-base", ref, "HEAD"])
            if mb.returncode == 0 and (base := mb.stdout.strip()) and base != head_sha:
                return base
    return None

def _pick_effective_cr_sha(root: Path, cr_dir: Path | None, cit_shas: list[str]) -> tuple[str | None, set[str]]:
    touched: set[str] = set()
    cands = [v for s in cit_shas if (v := _verify_commit(root, s))]
    if cr_dir is not None and (lr := _run_git(root, ["log", "--format=%H", "--name-only", "--", resolve_repo_relative_path(str(cr_dir), root)])).returncode == 0:
        latest: str | None = None
        for ln in (line.strip() for line in lr.stdout.splitlines() if line.strip()):
            if re.fullmatch(r"[0-9a-f]{40}", ln, re.I):
                latest = latest or ln
            else:
                touched.add(_norm_rel(ln))
        if latest:
            cands.append(latest)
    return _newest_commit(root, cands), touched

def _check_git_drift(
    root: Path, state: _WorkState, coverage: dict[str, set[str]], active_cits: list[SrcCitation],
    base_ref: str | None, findings: list[DriftFinding], warnings: list[str],
) -> None:
    inside = _run_git(root, ["rev-parse", "--is-inside-work-tree"])
    if inside.returncode != 0 or inside.stdout.strip().lower() != "true":
        warnings.append("Git repository check failed; skipped Git diff/status drift checks." if (root / ".git").exists() else "Repository is not a Git work tree; skipped Git diff/status drift checks.")
        return
    st = _run_git(root, ["status", "--porcelain", "-uall"])
    uncommitted = {
        resolve_repo_relative_path(c, root) for ln in (st.stdout.splitlines() if st.returncode == 0 else ()) if len(ln) >= 4
        for p in (ln[3:].strip().split(" -> ") if " -> " in ln[3:] else [ln[3:].strip()]) if (c := p.strip().strip('"'))
    }
    head_sha = _run_git(root, ["rev-parse", "--verify", "--quiet", "HEAD"]).stdout.strip()
    diff_cache: dict[str, set[str]] = {}

    def _diff_since(sha: str) -> set[str]:
        if sha not in diff_cache:
            d = _run_git(root, ["diff", "--name-only", f"{sha}..HEAD"])
            diff_cache[sha] = {_norm_rel(ln) for ln in d.stdout.splitlines() if ln.strip()} if d.returncode == 0 else set()
        return diff_cache[sha]

    base_sha = _resolve_git_base(root, base_ref, head_sha) if head_sha else None
    branch_diff = _diff_since(base_sha) if base_sha else set()
    closed_cr_info = {
        cr_id: (eff, touched | {c.rel_path for c in state.citations_by_owner.get(cr_id, [])})
        for cr_id in {cid for lst in state.closed_crs_by_feat.values() for cid in lst}
        for eff, touched in (_pick_effective_cr_sha(root, state.item_dirs.get(cr_id), [c.commit_sha for c in state.citations_by_owner.get(cr_id, []) if c.commit_sha]),)
    }
    done_cits: dict[str, list[SrcCitation]] = {}
    for cit in active_cits:
        if state.statuses.get(cit.feature_id, "") in DONE_STATES:
            done_cits.setdefault(cit.rel_path, []).append(cit)

    for rel_path in sorted(coverage):
        done_feats = {fid for fid in coverage[rel_path] if fid.startswith("FEAT-") and state.statuses.get(fid, "") in DONE_STATES}
        if not done_feats or state.has_active_bug or any(state.open_crs_by_feat.get(fid) for fid in done_feats):
            continue
        if state.active_cr_id is not None and ((not state.active_cr_links) or bool(state.active_cr_links & done_feats)):
            continue
        closed_shas = [eff for fid in done_feats for cid in state.closed_crs_by_feat.get(fid, []) for eff, touched in (closed_cr_info.get(cid, (None, set())),) if eff and rel_path in touched]
        drifted, reason = (rel_path in uncommitted), "working tree modification"
        if not drifted and head_sha:
            if closed_shas:
                if (cr_sha := _newest_commit(root, closed_shas)) and rel_path in _diff_since(cr_sha):
                    drifted, reason = True, f"modified after closed CR commit {cr_sha[:8]}"
            elif rel_path in branch_diff:
                drifted, reason = True, "modified in branch diff"
            else:
                for cit in done_cits.get(rel_path, ()):
                    if cit.commit_sha:
                        if not (rsha := _verify_commit(root, cit.commit_sha)):
                            warnings.append(f"Unknown citation SHA '{cit.commit_sha}' in {cit.feature_id} for '{rel_path}'.")
                        elif rel_path in _diff_since(rsha):
                            drifted, reason = True, f"modified since cited commit {cit.commit_sha[:8]}"
                            break
        if drifted:
            label = ",".join(sorted(done_feats))
            findings.append(DriftFinding("UNLINKED_CODE_DRIFT", "error", label, rel_path, None, f"Done feature file '{rel_path}' ({label}) has {reason} without an open linked CR/BUG/HOTFIX."))

def run_drift_check(repo_root: Path | str, *, base_ref: str | None = None, strict: bool = False) -> DriftReport:
    """Run deterministic offline Spec Drift verification across specs, ownership zones, AST map, and Git."""
    try:
        from scripts.sdd_brownfield import validate_repo_root
    except ImportError:
        from sdd_brownfield import validate_repo_root
    root = validate_repo_root(repo_root)
    warnings, findings, stack_path = [], [], root / "specs" / "STACK.md"
    if is_link_or_junction(root / "specs") or is_link_or_junction(stack_path):
        raise OwnershipError("Refusing symlink or junction on specs/STACK.md.")
    ownership_cfg = parse_ownership_map(stack_path) if stack_path.exists() else None
    state = _collect_work_state(root, warnings)
    coverage = _collect_traceability_coverage(root)
    for owner_id, cits in state.citations_by_owner.items():
        if state.statuses.get(owner_id, "") not in {"cancelled", "canceled", "rejected"}:
            targets = {owner_id} if owner_id.startswith("FEAT-") else (state.cr_links.get(owner_id, set()) or {owner_id})
            for cit in cits:
                coverage.setdefault(cit.rel_path, set()).update(targets)

    governed_list, legacy_count = _collect_governed_and_legacy(root, ownership_cfg)
    for rel_path in governed_list:
        if rel_path not in coverage:
            findings.append(DriftFinding("UNCOVERED_FILE", "error" if strict else "warning", "-", rel_path, None, f"Governed source file '{rel_path}' is not covered by any FEAT-XXX spec or TRACEABILITY-MATRIX.md."))

    active_cits = _resolve_active_citations(state)
    sym_cache: dict[str, tuple[set[str], set[tuple[str, str]]]] = {}
    for cit in active_cits:
        if state.open_crs_by_feat.get(cit.feature_id):
            continue
        sev = "error" if (state.statuses.get(cit.feature_id, "") in DONE_STATES or strict) else "warning"
        try:
            target = root / resolve_repo_relative_path(cit.rel_path, root)
            exists_ok = target.is_file() and not is_link_or_junction(target)
        except ValueError:
            exists_ok = False
        if not exists_ok:
            findings.append(DriftFinding("MISSING_SOURCE_FILE", sev, cit.feature_id, cit.rel_path, cit.symbol, f"{cit.feature_id} {cit.src_id} cites missing source file '{cit.rel_path}'."))
            continue
        if cit.symbol:
            if cit.rel_path not in sym_cache:
                sym_cache[cit.rel_path] = _extract_symbols(target)
            if not _symbol_exists(cit.symbol, target.suffix.lower(), *sym_cache[cit.rel_path]):
                findings.append(DriftFinding("MISSING_SYMBOL", sev, cit.feature_id, cit.rel_path, cit.symbol, f"{cit.feature_id} {cit.src_id} cites missing symbol '{cit.symbol}' in '{cit.rel_path}'."))

    _check_git_drift(root, state, coverage, active_cits, base_ref, findings, warnings)
    failed = any(f.severity == "error" for f in findings) or (strict and bool(findings))
    return DriftReport(str(root), "FAIL" if failed else "PASS", tuple(findings), len(governed_list), legacy_count, len(coverage), len(active_cits), tuple(warnings))

def _format_text(r: DriftReport) -> str:
    return "\n".join([
        f"SDD Spec Drift Check: {r.status}",
        f"  repo_root: {r.repo_root}",
        f"  governed_files: {r.governed_files} | legacy_readonly_files: {r.legacy_readonly_files} | covered_files: {r.covered_files} | citations_checked: {r.citations_checked}",
        *(f"  [WARN]  {w}" for w in r.warnings),
        *(f"  [{f.severity.upper()}] {f.kind} ({f.feature_id}) {f.path}{'::' + f.symbol if f.symbol else ''} - {f.detail}" for f in r.findings),
    ])

def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for `sdd drift`."""
    parser = argparse.ArgumentParser(description="Deterministic offline Spec Drift detector and Strangler Fig coverage auditor.")
    parser.add_argument("--repo-root", default=None, help="Target repository root (default: framework root)")
    parser.add_argument("--base-ref", default=None, help="Optional Git base ref/commit for branch diff drift check")
    parser.add_argument("--strict", action="store_true", help="Treat warnings (e.g. UNCOVERED_FILE) as errors")
    parser.add_argument("--format", choices=("text", "json"), default="text", help="Output format (default: text)")
    args = parser.parse_args(argv)
    try:
        report = run_drift_check(args.repo_root if args.repo_root is not None else _FRAMEWORK_ROOT, base_ref=args.base_ref, strict=args.strict)
    except (OwnershipError, ValueError, OSError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, indent=2, ensure_ascii=False) if args.format == "json" else f"[ERROR] {exc}", file=sys.stdout if args.format == "json" else sys.stderr)
        return 1
    print(json.dumps(asdict(report), indent=2, ensure_ascii=False) if args.format == "json" else _format_text(report))
    return 0 if report.status == "PASS" else 1

if __name__ == "__main__":
    raise SystemExit(main())
