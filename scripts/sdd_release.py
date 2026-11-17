#!/usr/bin/env python3
"""SDD Gate 6 Release Readiness & Deterministic CHANGELOG Engine (FWK-014)."""

from __future__ import annotations

import argparse, datetime, json, re, sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any

_FRAMEWORK_ROOT = Path(__file__).resolve().parent.parent
for _p in (str(_FRAMEWORK_ROOT), str(_FRAMEWORK_ROOT / "scripts"), str(_FRAMEWORK_ROOT / ".agents" / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from sdd_healthcheck import _parse_backlog_entries  # noqa: E402
from sdd_stack_gate_guard import strip_non_normative_markdown  # noqa: E402

try:
    from scripts.sdd_ci import detect_ci_mode, run_ci_verify
    from scripts.sdd_gate_seal import compute_gate_doc_sha256, extract_inline_gate_seal
    from scripts.sdd_git_state import GitRunner, atomic_write_text, is_link_or_junction
except ImportError:
    from sdd_ci import detect_ci_mode, run_ci_verify
    from sdd_gate_seal import compute_gate_doc_sha256, extract_inline_gate_seal
    from sdd_git_state import GitRunner, atomic_write_text, is_link_or_junction

VALID_CATEGORIES = frozenset({"features", "changes", "fixes", "framework", "other"})
VALID_CHECK_STATUSES = frozenset({"PASS", "FAIL", "SKIPPED_STAGE"})
_BLOCKING_STATUSES = frozenset({"in progress", "in review", "en progreso", "en revision", "en revisión", "blocked", "bloqueado"})
_SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z]+(?:\.[0-9A-Za-z]+)*)?$")
_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_GATE6_MARKER_RE = re.compile(r"\[[xX]\]\s*(?:\*\*)?Gate\s+6\s+Approved(?:\*\*)?", re.IGNORECASE)
_PLACEHOLDER_RE = re.compile(r"<(?!https?://)[^<>\n]{1,80}>")
_SDD_ID_RE = re.compile(r"\b((?:FEAT|CR|BUG|HOTFIX|FWK)-\d{3,4})\b", re.IGNORECASE)
_NOISE_SUBJECT_RE = re.compile(r"^(?:merge\b|(?:chore|ci|style)(?:\([^)]*\))?!?:)", re.IGNORECASE)
_CONV_COMMIT_RE = re.compile(r"^(feat|fix|perf|refactor)(?:\(([^)]+)\))?(!)?:\s*(.+)$", re.IGNORECASE)
_SPEC_BUCKETS = ("specs/features", "specs/changes", "specs/bugs", ".sdd/framework/work-items")
_CATEGORY_HEADINGS = (("features", "### Features"), ("changes", "### Changes"), ("fixes", "### Fixes & Hotfixes"), ("framework", "### Framework"), ("other", "### Other Changes"))
_FALLBACK_TEMPLATE = (
    "# Release Readiness: REL-vX.Y.Z (vX.Y.Z)\n\n- **ID:** `REL-vX.Y.Z`\n- **Versión / Tag:** `vX.Y.Z`\n- **Tag previo:** `<prev_tag>`\n- **Fecha objetivo:** `YYYY-MM-DD`\n- **Estado:** `Draft`\n\n"
    "## 1. Alcance y Work Items Incluidos\n{{RELEASE_ITEMS}}\n\n## 2. Checklist de Verificación Automática\n- [ ] `sdd ci-verify` en verde (`PASS`).\n- [ ] Sin work items abiertos.\n- [ ] `CHANGELOG.md` actualizado para `vX.Y.Z`.\n\n"
    "## 3. Riesgos y Migraciones\n- `<N/A o detallar migraciones>`\n\n## 4. Plan de Despliegue y Rollback\n- **Despliegue:** `<Pasos>`\n- **Rollback:** `<Procedimiento de rollback>`\n\n"
    "## 5. Aprobación Gate 6\n- [ ] **Gate 6 Approved (Human Sign-off):** Release Readiness, verificación CI, `CHANGELOG.md` y plan de rollback aprobados.\n"
)


@dataclass(frozen=True)
class ReleaseItem:
    """Traceable work item or substantive commit included in a release."""
    item_id: str; category: str; title: str; status: str; rfc: str = ""

    def __post_init__(self) -> None:
        if self.category not in VALID_CATEGORIES:
            raise ValueError(f"Invalid release item category {self.category!r}.")


@dataclass(frozen=True)
class ReleaseCheck:
    """Single fail-closed release preflight check result."""
    name: str; status: str; detail: str; data: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.status not in VALID_CHECK_STATUSES:
            raise ValueError(f"Invalid release check status {self.status!r} for '{self.name}'.")


@dataclass(frozen=True)
class ReleaseReadinessReport:
    """Aggregated Gate 6 release readiness report."""
    version: str; tag: str; release_id: str; stage: str; overall_status: str
    checks: tuple[ReleaseCheck, ...]; repo_root: str

    def __post_init__(self) -> None:
        if self.stage not in {"start", "finish"} or self.overall_status not in {"PASS", "FAIL"}:
            raise ValueError(f"Invalid stage={self.stage!r} or overall_status={self.overall_status!r}.")


def normalize_release_version(raw: str) -> tuple[str, str, str]:
    """Validate strict SemVer (optional leading `v`) and return `(semver, tag, release_id)`."""
    cleaned = raw.strip()[1:] if isinstance(raw, str) and raw.strip().startswith("v") else (raw.strip() if isinstance(raw, str) else "")
    if not _SEMVER_RE.match(cleaned):
        raise ValueError(f"Invalid SemVer release version {raw!r}; expected X.Y.Z or vX.Y.Z.")
    return cleaned, f"v{cleaned}", f"REL-v{cleaned}"


def _assert_safe_repo_path(repo_root: Path, *parts: str) -> Path:
    root_res = repo_root.resolve()
    if is_link_or_junction(repo_root):
        raise ValueError(f"Repository root cannot be a symlink or junction: {repo_root}")
    curr = repo_root
    for part in parts:
        curr = curr / part
        if is_link_or_junction(curr):
            raise ValueError(f"Path component cannot be a symlink or junction: {curr}")
    if not curr.resolve(strict=False).is_relative_to(root_res):
        raise ValueError(f"Resolved path escapes repository root: {curr}")
    return curr


def resolve_release_spec_path(repo_root: Path, version: str) -> Path:
    """Resolve `specs/releases/REL-vX.Y.Z.md` safely without symlinks or traversal."""
    _, _, release_id = normalize_release_version(version)
    specs_dir, releases_dir = _assert_safe_repo_path(repo_root, "specs"), _assert_safe_repo_path(repo_root, "specs", "releases")
    target = _assert_safe_repo_path(repo_root, "specs", "releases", f"{release_id}.md")
    if (specs_dir.exists() and not specs_dir.is_dir()) or (releases_dir.exists() and not releases_dir.is_dir()) or (target.exists() and not target.is_file()):
        raise ValueError(f"Invalid directory/file type along release path: {target}")
    return target


def _make_disk_reader(base_dir: Path) -> Callable[[str], str | None]:
    def _read(rel_path: str) -> str | None:
        clean = rel_path.replace("\\", "/").lstrip("/")
        if not clean or ":" in clean or ".." in (parts := PurePosixPath(clean).parts):
            return None
        try:
            target = _assert_safe_repo_path(base_dir, *parts)
            return target.read_text(encoding="utf-8") if target.is_file() else None
        except (ValueError, OSError, UnicodeDecodeError):
            return None
    return _read


def _resolve_release_source_reader(repo_root: Path, tag: str, release_branch: str | None) -> tuple[Path, Callable[[str], str | None]]:
    """Resolve effective release workspace and safe relative-file reader across worktrees/branches."""
    eff_branch = (release_branch or f"release/{tag}").strip()
    if (repo_root / ".git").exists() and eff_branch:
        for wt in GitRunner.get_worktrees(cwd=repo_root):
            if wt.get("branch") == eff_branch and (wt_raw := wt.get("path", "")) and not is_link_or_junction(wt_path := Path(wt_raw)) and wt_path.is_dir():
                return wt_path, _make_disk_reader(wt_path)
        if GitRunner.get_current_branch(cwd=repo_root) != eff_branch and GitRunner.branch_exists(eff_branch, cwd=repo_root):
            def _git_show_reader(rel_path: str) -> str | None:
                clean = rel_path.replace("\\", "/").lstrip("/")
                if not clean or ":" in clean or ".." in PurePosixPath(clean).parts:
                    return None
                res = GitRunner.run(["show", f"{eff_branch}:{clean}"], cwd=repo_root, check=False)
                return res.stdout if res.returncode == 0 else None
            return repo_root, _git_show_reader
    return repo_root, _make_disk_reader(repo_root)


def parse_gate6_approval(text: str) -> tuple[bool, list[str]]:
    """Verify Gate 6 sign-off, rollback substance, placeholder absence, and inline SHA-256 seal."""
    if not text or not text.strip():
        return False, ["Gate 6 release dossier is empty."]
    errors, cleaned = [], strip_non_normative_markdown(text)
    marker_lines = [ln for ln in cleaned.splitlines() if _GATE6_MARKER_RE.search(ln)]
    if not marker_lines:
        errors.append("Missing '[x] Gate 6 Approved' sign-off outside HTML comments and fenced code blocks.")
    elif any(_PLACEHOLDER_RE.search(ln) for ln in marker_lines):
        errors.append("Gate 6 sign-off line contains unfilled '<...>' placeholder(s).")
    body_only = re.sub(rf"^.*{_GATE6_MARKER_RE.pattern}.*$", "", cleaned, flags=re.MULTILINE)
    if len(cleaned.strip()) < 20 or len(re.sub(r"[\s#*\-_`>:|.\[\]()]+", "", body_only)) < 8:
        errors.append("Gate 6 release dossier lacks substantive content.")
    lines = cleaned.splitlines()
    rb_section = next(("\n".join(lines[idx + 1 : next((j for j in range(idx + 1, len(lines)) if (hm := re.match(r"^(#{1,6})\s+", lines[j])) and len(hm.group(1)) <= len(m.group(1))), len(lines))]) for idx, ln in enumerate(lines) if (m := re.match(r"^(#{1,6})\s+.*rollback.*$", ln, re.I))), None)
    if rb_section is None:
        errors.append("Missing Rollback section in Gate 6 release dossier.")
    elif len(re.sub(r"[\s#*\-_`>:|.\[\]()]+", "", rb_section)) < 8:
        errors.append("Rollback section in Gate 6 release dossier is empty.")
    elif _PLACEHOLDER_RE.search(rb_section):
        errors.append("Rollback section contains unfilled '<...>' placeholder(s).")
    if (inline_seal := extract_inline_gate_seal(text, gate_num=6)) == "INVALID":
        errors.append("Malformed inline sdd:gate-seal comment for Gate 6.")
    elif inline_seal is not None and (actual := compute_gate_doc_sha256(text)).lower() != inline_seal.lower():
        errors.append(f"Gate 6 SHA-256 seal mismatch (expected {inline_seal.lower()}, got {actual.lower()}).")
    return not errors, errors


def check_open_work_items(repo_root: Path, *, allow_release_id: str) -> list[str]:
    """Fail-closed check for active/open work items in `.agents/active_work_item.json` and backlogs."""
    errors, norm_allow = [], allow_release_id.strip().upper()
    allowed_ids = {norm_allow, *(("REL-" + norm_allow[5:],) if norm_allow.startswith("REL-V") else (("REL-V" + norm_allow[4:],) if norm_allow.startswith("REL-") else ()))}
    agents_dir, state_file = repo_root / ".agents", repo_root / ".agents" / "active_work_item.json"
    if is_link_or_junction(agents_dir) or is_link_or_junction(state_file):
        errors.append("State path .agents/active_work_item.json cannot be a symlink or junction.")
    elif state_file.exists():
        try:
            state = json.loads(state_file.read_text(encoding="utf-8"))
            if not isinstance(state, dict):
                errors.append(".agents/active_work_item.json must be a JSON object.")
            elif (aid := str(state.get("active_work_item_id") or "").strip()) and aid.upper() != "IDLE" and aid.upper() not in allowed_ids:
                errors.append(f"Active work item '{aid}' is still open in .agents/active_work_item.json.")
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            errors.append(f"Invalid .agents/active_work_item.json: {exc}")

    targets: list[tuple[str, Path]] = [("specs/BACKLOG.md", repo_root / "specs" / "BACKLOG.md")]
    try:
        if detect_ci_mode(repo_root) == "framework" and (fwk_bl := repo_root / ".sdd" / "framework" / "BACKLOG.md").exists():
            targets.append((".sdd/framework/BACKLOG.md", fwk_bl))
    except Exception as exc:
        errors.append(f"Cannot determine CI mode from specs/STACK.md: {exc}")
    for label, path in targets:
        if is_link_or_junction(path):
            errors.append(f"Backlog file cannot be a symlink or junction: {label}")
        elif path.is_file():
            try:
                statuses, _ = _parse_backlog_entries(path.read_text(encoding="utf-8"))
                errors.extend(f"Open work item '{iid}' has blocking status '{st}' in {label}." for iid, st in sorted(statuses.items()) if iid not in allowed_ids and st in _BLOCKING_STATUSES)
            except (OSError, UnicodeDecodeError) as exc:
                errors.append(f"Cannot read {label}: {exc}")
    return errors


def find_previous_tag(repo_root: Path, current_tag: str) -> str | None:
    """Return latest reachable SemVer tag excluding `current_tag`, or latest SemVer tag in history."""
    if not (repo_root / ".git").exists() or (res := GitRunner.run(["tag", "-l", "--sort=-v:refname"], cwd=repo_root, check=False)).returncode != 0:
        return None
    candidates = []
    for raw in res.stdout.splitlines():
        if (tag := raw.strip()) and tag != current_tag:
            try:
                normalize_release_version(tag)
                candidates.append(tag)
            except ValueError:
                pass
    if candidates and GitRunner.ref_exists("HEAD", cwd=repo_root):
        for tag in candidates:
            if GitRunner.run(["merge-base", "--is-ancestor", tag, "HEAD"], cwd=repo_root, check=False).returncode == 0:
                return tag
    return candidates[0] if candidates else None


def _load_backlog_metadata(repo_root: Path) -> dict[str, dict[str, str]]:
    meta: dict[str, dict[str, str]] = {}
    for rel in ("specs/BACKLOG.md", ".sdd/framework/BACKLOG.md"):
        if is_link_or_junction(path := repo_root / rel) or not path.is_file():
            continue
        try:
            raw = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for iid, st in _parse_backlog_entries(raw)[0].items():
            meta.setdefault(iid, {})["status"] = st
        id_col, title_col, rfc_col = 0, None, None
        for line in strip_non_normative_markdown(raw).splitlines():
            if not ((s := line.strip()).startswith("|") and "|" in s[1:]):
                id_col, title_col, rfc_col = 0, None, None
                continue
            cells = [re.sub(r"[`*]+", "", c).strip() for c in s.strip("|").split("|")]
            if all(re.match(r"^:?-{2,}:?$", c.replace(" ", "")) for c in cells if c):
                continue
            lows = [c.lower() for c in cells]
            if any(h in {"título", "titulo", "title", "estado", "status", "estado final"} for h in lows):
                id_col = next((i for i, h in enumerate(lows) if h in {"id", "id cr", "id bug"}), 0)
                title_col = next((i for i, h in enumerate(lows) if any(k in h for k in ("título", "titulo", "title"))), None)
                rfc_col = next((i for i, h in enumerate(lows) if "rfc" in h), None)
            elif id_col < len(cells) and (m := _SDD_ID_RE.search(cells[id_col])):
                entry = meta.setdefault(m.group(1).upper(), {})
                if title_col is not None and title_col < len(cells) and cells[title_col] not in {"", "-"}:
                    entry.setdefault("title", cells[title_col])
                if rfc_col is not None and rfc_col < len(cells) and cells[rfc_col] not in {"", "-", "—"}:
                    entry.setdefault("rfc", cells[rfc_col])
    return meta


def _find_spec_heading_title(repo_root: Path, item_id: str) -> str | None:
    id_re = re.compile(rf"^{re.escape(item_id)}(?:-|$)", re.IGNORECASE)
    for bucket in _SPEC_BUCKETS:
        if is_link_or_junction(bpath := repo_root / bucket) or not bpath.is_dir():
            continue
        for entry in sorted(bpath.iterdir()):
            if not is_link_or_junction(entry) and entry.is_dir() and id_re.match(entry.name):
                for doc in (entry / n for n in ("01-spec.md", "01-bug-report.md")):
                    if not is_link_or_junction(doc) and doc.is_file():
                        for ln in doc.read_text(encoding="utf-8", errors="ignore").lstrip("\ufeff").splitlines():
                            if ln.startswith("# "):
                                return re.sub(r"`+", "", re.sub(rf"^{re.escape(item_id)}\s*[:\-–]\s*", "", ln[2:].strip(), flags=re.I)).strip()
    return None


def collect_release_items(repo_root: Path, *, since_tag: str | None = None, current_tag: str | None = None) -> tuple[str | None, list[ReleaseItem]]:
    """Collect deterministic SDD items (or Conventional Commits fallback) from `<since_tag>..HEAD`."""
    eff_since = since_tag.strip() if isinstance(since_tag, str) and since_tag.strip() else find_previous_tag(repo_root, current_tag or "")
    if not (repo_root / ".git").exists() or not GitRunner.ref_exists("HEAD", cwd=repo_root):
        return eff_since, []
    if eff_since and not GitRunner.ref_exists(eff_since, cwd=repo_root):
        raise ValueError(f"Git tag or ref not found for --since-tag: {eff_since}")
    rev_range = f"{eff_since}..HEAD" if eff_since else "HEAD"
    if (res := GitRunner.run(["log", "--no-merges", "--format=%H%x1f%s", rev_range], cwd=repo_root, check=False)).returncode != 0:
        raise RuntimeError(f"Failed to read git log for {rev_range}: {res.stderr.strip()}")
    meta, sdd_items, conv_items = _load_backlog_metadata(repo_root), {}, []
    prefix_cat = {"FEAT": "features", "CR": "changes", "BUG": "fixes", "HOTFIX": "fixes", "FWK": "framework"}
    for line in res.stdout.splitlines():
        if "\x1f" not in line:
            continue
        sha, subject = line.split("\x1f", 1)
        if not (subj := subject.strip()) or _NOISE_SUBJECT_RE.match(subj):
            continue
        if ids := [m.group(1).upper() for m in _SDD_ID_RE.finditer(subj)]:
            for iid in ids:
                if iid not in sdd_items:
                    info = meta.get(iid, {})
                    title = info.get("title") or _find_spec_heading_title(repo_root, iid) or subj
                    sdd_items[iid] = ReleaseItem(iid, prefix_cat.get(iid.split("-", 1)[0], "other"), title, info.get("status", "unknown"), info.get("rfc", ""))
        elif cc := _CONV_COMMIT_RE.match(subj):
            cc_type, cc_scope, _, cc_desc = cc.groups()
            conv_items.append(ReleaseItem(sha[:7], {"feat": "features", "fix": "fixes"}.get(cc_type.lower(), "other"), f"{cc_scope}: {cc_desc.strip()}" if cc_scope else cc_desc.strip(), "committed"))
    cat_order = {cat: idx for idx, (cat, _) in enumerate(_CATEGORY_HEADINGS)}
    ordered = sorted(sdd_items.values(), key=lambda it: (cat_order[it.category], it.item_id)) if sdd_items else sorted(conv_items, key=lambda it: (cat_order[it.category], it.title.lower(), it.item_id))
    return eff_since, ordered


def render_changelog_section(version: str, items: Sequence[ReleaseItem], *, release_date: str) -> str:
    """Render deterministic Markdown section `## [vX.Y.Z] - YYYY-MM-DD` grouped by category."""
    _, tag, _ = normalize_release_version(version)
    lines: list[str] = [f"## [{tag}] - {release_date}"]
    grouped: dict[str, list[ReleaseItem]] = {cat: [] for cat, _ in _CATEGORY_HEADINGS}
    for it in items:
        grouped[it.category].append(it)
    for cat, heading in _CATEGORY_HEADINGS:
        if grouped[cat]:
            lines.extend(["", heading, *(f"- **{it.item_id}**: {it.title}" + (f" ({it.rfc})" if it.rfc else "") if _SDD_ID_RE.match(it.item_id) else f"- {it.title} (`{it.item_id}`)" for it in grouped[cat])])
    return "\n".join(lines if len(lines) > 1 else [*lines, "", "- Maintenance release without tracked SDD feature changes."])


def _validate_date(release_date: str | None) -> str:
    eff = release_date or datetime.date.today().isoformat()
    if not _ISO_DATE_RE.match(eff):
        raise ValueError(f"Invalid --date {eff!r}; expected YYYY-MM-DD.")
    return eff


def update_changelog(repo_root: Path, version: str, *, since_tag: str | None = None, release_date: str | None = None, dry_run: bool = False) -> tuple[Path, str, bool]:
    """Idempotently insert or replace the `## [vX.Y.Z]` block in `CHANGELOG.md`."""
    semver, tag, _ = normalize_release_version(version)
    eff_date, cl_path = _validate_date(release_date), _assert_safe_repo_path(repo_root, "CHANGELOG.md")
    if cl_path.exists() and not cl_path.is_file():
        raise ValueError(f"CHANGELOG.md must be a regular file: {cl_path}")
    old_text = cl_path.read_text(encoding="utf-8") if cl_path.exists() else "# Changelog\n\nAll notable changes to this project will be documented in this file.\n"
    section = render_changelog_section(semver, collect_release_items(repo_root, since_tag=since_tag, current_tag=tag)[1], release_date=eff_date)
    norm_old = old_text.replace("\r\n", "\n").replace("\r", "\n")
    target_re, any_ver_re = re.compile(rf"^##\s+\[v?{re.escape(semver)}\](?:\s|$).*$", re.MULTILINE), re.compile(r"^##\s+\[", re.MULTILINE)
    if m := target_re.search(norm_old):
        nxt = any_ver_re.search(norm_old, m.end())
        new_text = "\n\n".join(p for p in (norm_old[: m.start()].rstrip(), section, norm_old[nxt.start() :].strip() if nxt else "") if p) + "\n"
    elif first := any_ver_re.search(norm_old):
        new_text = "\n\n".join(p for p in (norm_old[: first.start()].rstrip(), section, norm_old[first.start() :].strip()) if p) + "\n"
    else:
        new_text = (norm_old.rstrip() + "\n\n" + section + "\n") if norm_old.strip() else (section + "\n")
    changed = (not cl_path.exists()) or (new_text != norm_old)
    if changed and not dry_run:
        atomic_write_text(cl_path, new_text)
    return cl_path, new_text, changed


def verify_changelog_version(changelog_text: str, version: str) -> tuple[bool, str]:
    """Verify `CHANGELOG.md` contains a non-empty section for `vX.Y.Z`."""
    semver, tag, _ = normalize_release_version(version)
    norm = changelog_text.replace("\r\n", "\n").replace("\r", "\n")
    if not (m := re.search(rf"^##\s+\[v?{re.escape(semver)}\](?:\s|$).*$", norm, re.MULTILINE)):
        return False, f"CHANGELOG.md is missing section '## [{tag}]'."
    nxt = re.search(r"^##\s+\[", norm[m.end() :], re.MULTILINE)
    return (True, f"CHANGELOG.md contains section for {tag}.") if (norm[m.end() : m.end() + nxt.start()] if nxt else norm[m.end() :]).strip() else (False, f"CHANGELOG.md section '## [{tag}]' is empty.")


def prepare_release(repo_root: Path, version: str, *, since_tag: str | None = None, release_date: str | None = None, force: bool = False, update_changelog_file: bool = True) -> dict[str, Any]:
    """Generate `specs/releases/REL-vX.Y.Z.md` (unchecked Gate 6) and update `CHANGELOG.md`."""
    semver, tag, release_id = normalize_release_version(version)
    eff_date, spec_path = _validate_date(release_date), resolve_release_spec_path(repo_root, semver)
    if spec_path.exists() and not force:
        raise FileExistsError(f"Release dossier already exists: {spec_path} (pass --force to overwrite).")
    prev_tag, items = collect_release_items(repo_root, since_tag=since_tag, current_tag=tag)
    tmpl_path = repo_root / "specs" / "templates" / "08-release-readiness.template.md"
    template = tmpl_path.read_text(encoding="utf-8") if (not is_link_or_junction(tmpl_path) and tmpl_path.is_file() and tmpl_path.resolve().is_relative_to(repo_root.resolve())) else _FALLBACK_TEMPLATE
    items_md = "\n".join(f"- `{it.item_id}` ({it.category}, `{it.status}`): {it.title}" for it in items) or "- *(Sin work items SDD detectados en el rango)*"
    rendered = re.sub(r"\[[xX]\](\s*(?:\*\*)?Gate\s+6\s+Approved(?:\*\*)?)", r"[ ]\1", template.replace("REL-vX.Y.Z", release_id).replace("vX.Y.Z", tag).replace("X.Y.Z", semver).replace("YYYY-MM-DD", eff_date).replace("<prev_tag>", prev_tag or "N/A").replace("vA.B.C", prev_tag or "inicial").replace("{{RELEASE_ITEMS}}", items_md), flags=re.I)
    atomic_write_text(spec_path, rendered.rstrip() + "\n")
    cl_path, _, cl_changed = update_changelog(repo_root, semver, since_tag=since_tag, release_date=eff_date, dry_run=False) if update_changelog_file else (None, "", False)
    return {"version": semver, "tag": tag, "release_id": release_id, "spec_path": str(spec_path), "previous_tag": prev_tag, "items_count": len(items), "changelog_path": str(cl_path) if cl_path else None, "changelog_updated": cl_changed}


def run_release_preflight(repo_root: Path, version: str, *, stage: str = "finish", run_ci: bool = True, run_stack: bool = False, skip_tests: bool = False, release_branch: str | None = None) -> ReleaseReadinessReport:
    """Execute fail-closed release preflight (`start` or `finish`) and return `ReleaseReadinessReport`."""
    if stage not in {"start", "finish"}:
        raise ValueError(f"Invalid release stage {stage!r}; expected 'start' or 'finish'.")
    root = repo_root.resolve()
    try:
        semver, tag, release_id = normalize_release_version(version)
    except ValueError as exc:
        return ReleaseReadinessReport(str(version), f"v{version}", f"REL-v{version}", stage, "FAIL", (ReleaseCheck("semver", "FAIL", str(exc)),), str(root))
    eff_root, read_rel = _resolve_release_source_reader(root, tag, release_branch)
    tag_exists = (root / ".git").exists() and GitRunner.run(["rev-parse", "--verify", "--quiet", f"refs/tags/{tag}"], cwd=root, check=False).returncode == 0
    open_errors = check_open_work_items(root, allow_release_id=release_id)
    if eff_root != root:
        open_errors.extend(e for e in check_open_work_items(eff_root, allow_release_id=release_id) if e not in open_errors)
    checks: list[ReleaseCheck] = [
        ReleaseCheck("semver", "PASS", f"Valid SemVer {tag}."),
        ReleaseCheck("tag_absent", "FAIL" if tag_exists else "PASS", f"Tag '{tag}' already exists." if tag_exists else f"Tag '{tag}' is available."),
        ReleaseCheck("worktree_clean", "SKIPPED_STAGE", "Clean tree check deferred to stage 'finish'.") if stage == "start" else (
            ReleaseCheck("worktree_clean", "FAIL", f"Working tree '{eff_root}' has uncommitted changes.") if ((eff_root / ".git").exists() and not GitRunner.is_clean(cwd=eff_root)) else ReleaseCheck("worktree_clean", "PASS", "Release working tree is clean.")
        ),
        ReleaseCheck("open_work_items", "FAIL" if open_errors else "PASS", "; ".join(open_errors) if open_errors else "No blocking open work items."),
    ]
    if stage == "start":
        checks.extend([ReleaseCheck("gate6_approval", "SKIPPED_STAGE", "Gate 6 dossier check deferred to stage 'finish'."), ReleaseCheck("changelog", "SKIPPED_STAGE", "CHANGELOG.md check deferred to stage 'finish'.")])
    else:
        try:
            resolve_release_spec_path(root, semver)
            doc_text = read_rel(f"specs/releases/{release_id}.md")
            ok_g6, gate_errs = parse_gate6_approval(doc_text) if doc_text is not None else (False, [f"Missing or unreadable specs/releases/{release_id}.md."])
        except ValueError as exc:
            ok_g6, gate_errs = False, [str(exc)]
        checks.append(ReleaseCheck("gate6_approval", "PASS" if ok_g6 else "FAIL", f"Gate 6 approved in {release_id}.md." if ok_g6 else "; ".join(gate_errs)))
        cl_text = read_rel("CHANGELOG.md")
        ok_cl, msg_cl = verify_changelog_version(cl_text, semver) if cl_text is not None else (False, "Missing or unreadable CHANGELOG.md.")
        checks.append(ReleaseCheck("changelog", "PASS" if ok_cl else "FAIL", msg_cl))
    if not run_ci:
        checks.append(ReleaseCheck("ci_verify", "SKIPPED_STAGE", "CI verification skipped by caller."))
    else:
        ci_report = run_ci_verify(eff_root if eff_root.is_dir() else root, mode="auto", run_stack_if_approved=run_stack, skip_tests=skip_tests)
        failed = [c.name for c in ci_report.checks if c.status == "FAIL"]
        checks.append(ReleaseCheck("ci_verify", "PASS" if ci_report.overall_status == "PASS" else "FAIL", f"CI verify ({ci_report.mode} mode) passed." if not failed else f"CI verify failed: {', '.join(failed)}.", {"mode": ci_report.mode, "failed_checks": failed}))
    return ReleaseReadinessReport(semver, tag, release_id, stage, "FAIL" if any(c.status == "FAIL" for c in checks) else "PASS", tuple(checks), str(root))


def build_parser() -> argparse.ArgumentParser:
    """Build CLI argument parser for `scripts/sdd_release.py`."""
    p = argparse.ArgumentParser(description="SDD Gate 6 Release Readiness and Deterministic CHANGELOG Engine.")
    sub = p.add_subparsers(dest="subcommand", required=True)
    for name, help_txt, extras in (
        ("prepare", "Create specs/releases/REL-vX.Y.Z.md (unchecked Gate 6) and update CHANGELOG.md.", (("--since-tag", {"default": None}), ("--date", {"dest": "release_date", "default": None}), ("--force", {"action": "store_true"}))),
        ("changelog", "Generate or update CHANGELOG.md deterministically.", (("--since-tag", {"default": None}), ("--date", {"dest": "release_date", "default": None}), ("--stdout", {"action": "store_true"}))),
        ("verify", "Run fail-closed Gate 6 release readiness verification.", (("--stage", {"choices": ("start", "finish"), "default": "finish"}), ("--release-branch", {"default": None}), ("--run-stack-if-approved", {"action": "store_true"}), ("--skip-tests", {"action": "store_true"}))),
    ):
        sp = sub.add_parser(name, help=help_txt)
        for flag, kw in (("--version", {"required": True}), ("--format", {"dest": "output_format", "choices": ("text", "json"), "default": "text"}), ("--repo-root", {"type": Path, "default": _FRAMEWORK_ROOT}), *extras):
            sp.add_argument(flag, **kw)
    return p


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint returning `0` on success/PASS and `1` on failure/FAIL."""
    for s in (sys.stdout, sys.stderr):
        if hasattr(s, "reconfigure"):
            try: s.reconfigure(encoding="utf-8", errors="replace")
            except (AttributeError, OSError, ValueError): pass
    args = build_parser().parse_args(argv)
    try:
        root = args.repo_root.resolve()
        if args.subcommand == "prepare":
            res = prepare_release(root, args.version, since_tag=args.since_tag, release_date=args.release_date, force=args.force)
            print(json.dumps(res, indent=2, ensure_ascii=False) if args.output_format == "json" else f"[OK] Prepared {res['release_id']} at {res['spec_path']}")
            return 0
        if args.subcommand == "changelog":
            cl_path, text, changed = update_changelog(root, args.version, since_tag=args.since_tag, release_date=args.release_date, dry_run=args.stdout)
            print(text, end="") if args.stdout else print(json.dumps({"changelog_path": str(cl_path), "changed": changed}, indent=2, ensure_ascii=False) if args.output_format == "json" else f"[OK] {'Updated' if changed else 'Unchanged'} {cl_path}")
            return 0
        rep = run_release_preflight(root, args.version, stage=args.stage, run_stack=args.run_stack_if_approved, skip_tests=args.skip_tests, release_branch=args.release_branch)
        payload = {"version": rep.version, "tag": rep.tag, "release_id": rep.release_id, "stage": rep.stage, "overall_status": rep.overall_status, "repo_root": rep.repo_root, "checks": [{"name": c.name, "status": c.status, "detail": c.detail, "data": c.data} for c in rep.checks]}
        print(json.dumps(payload, indent=2, ensure_ascii=False) if args.output_format == "json" else "\n".join([f"=== SDD Gate 6 Release Verify ({rep.release_id} / stage={rep.stage}) [{rep.overall_status}] ===", *(f"  [{c.status}] {c.name}: {c.detail}" for c in rep.checks)]))
        return 0 if rep.overall_status == "PASS" else 1
    except (ValueError, OSError, RuntimeError) as exc:
        print(json.dumps({"overall_status": "FAIL", "error": str(exc)}, indent=2, ensure_ascii=False) if getattr(args, "output_format", "text") == "json" else f"[FAIL] {exc}", file=sys.stdout if getattr(args, "output_format", "text") == "json" else sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
