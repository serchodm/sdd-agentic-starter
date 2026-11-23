#!/usr/bin/env python3
"""Deterministic offline Portfolio, Epics (EPIC-XXX), MoSCoW/RICE & Feature DAG engine."""

from __future__ import annotations

import argparse, dataclasses, json, math, pathlib, re, sys, unicodedata
from typing import Any, Sequence

_ROOT = pathlib.Path(__file__).resolve().parent.parent
for _p in (str(_ROOT), str(_ROOT / "scripts"), str(_ROOT / ".agents" / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from sdd_git_state import atomic_write_text, is_link_or_junction  # noqa: E402
from sdd_healthcheck import _clean_cell, _normalize_status, _parse_backlog_entries, _split_markdown_row  # noqa: E402
from sdd_immutable_feature_guard import resolve_repo_relative_path, strip_win32_extended_prefix  # noqa: E402
from sdd_stack_gate_guard import strip_non_normative_markdown  # noqa: E402

_EPIC_ID_RE = re.compile(r"^EPIC-\d{3,4}$")
_FEAT_ID_RE = re.compile(r"^FEAT-\d{3,4}$")
_YAML_FENCE_RE = re.compile(r"^[ \t]*(`{3,}|~{3,})[ \t]*ya?ml[ \t]+sdd:epic[ \t]*$", re.I)
_MOSCOW = {"must": "Must", "should": "Should", "could": "Could", "wont": "Wont"}
_MOSCOW_W = {"Must": 4, "Should": 3, "Could": 2, "Wont": 1}
_EPIC_ST = {"draft": "Draft", "active": "Active", "completed": "Completed", "on hold": "On Hold"}
_FEAT_ST = {
    "done": "Done", "completed": "Done", "completado": "Done", "completed / done": "Done", "done / completed": "Done",
    "in progress": "In Progress", "en progreso": "In Progress", "in review": "In Review", "en revision": "In Review",
    "en revisión": "In Review", "blocked": "Blocked", "bloqueado": "Blocked", "backlog": "Backlog",
    "candidate": "Candidate", "draft": "Candidate", "proposed": "Candidate", "propuesto": "Candidate",
    "gate 1": "Candidate", "cancelled": "Cancelled", "canceled": "Cancelled", "rejected": "Cancelled",
}
_ORPHAN_ST = frozenset({"In Progress", "In Review", "Done"})
_DEFAULT_TPL = '# Épica: `EPIC-001` — [Título de la Épica]\n\n- **ID:** `EPIC-001`\n- **Título:** [Título de la Épica]\n- **Estado:** `Draft`\n- **Prioridad MoSCoW:** `Must`\n- **RICE:** `reach=100, impact=2.0, confidence=0.8, effort=2.0`\n\n```yaml sdd:epic\nepic_id: "EPIC-001"\ntitle: "[Título de la Épica]"\nstatus: "Draft"\npriority: "Must"\nrice:\n  reach: 100\n  impact: 2.0\n  confidence: 0.8\n  effort: 2.0\nfeatures:\n  - id: "FEAT-001"\n    title: "[Slice vertical inicial]"\n    priority: "Must"\n    depends_on: []\n```\n'


class PortfolioError(ValueError):
    """Fail-closed domain, path, IO, or schema validation error."""


@dataclasses.dataclass(frozen=True)
class RiceScore:
    reach: float; impact: float; confidence: float; effort: float; score: float


@dataclasses.dataclass(frozen=True)
class PortfolioFeature:
    feature_id: str; title: str; epic_id: str | None; status: str; priority: str
    depends_on: tuple[str, ...]; rice: RiceScore | None; ready: bool; blocked_by: tuple[str, ...]


@dataclasses.dataclass(frozen=True)
class EpicSummary:
    epic_id: str; title: str; status: str; priority: str; source_file: str
    total_features: int; done_features: int; in_progress_features: int; blocked_features: int
    progress_pct: float; feature_ids: tuple[str, ...]; ready_features: tuple[str, ...]; rice: RiceScore | None


@dataclasses.dataclass(frozen=True)
class PortfolioFinding:
    code: str; severity: str; detail: str; subject: str | None = None


@dataclasses.dataclass(frozen=True)
class PortfolioReport:
    repo_root: str; has_portfolio_data: bool; status: str
    epics: tuple[EpicSummary, ...]; features: tuple[PortfolioFeature, ...]
    waves: tuple[tuple[str, ...], ...]; critical_path: tuple[str, ...]; findings: tuple[PortfolioFinding, ...]


def _validate_repo_root(repo_root: pathlib.Path | str) -> pathlib.Path:
    if not isinstance(repo_root, (pathlib.Path, str)) or not str(repo_root).strip():
        raise PortfolioError("Repository root must be a non-empty Path or string.")
    try:
        raw = pathlib.Path(strip_win32_extended_prefix(str(repo_root).strip()))
    except ValueError as exc:
        raise PortfolioError(f"Unsafe repository root path: {exc}") from exc
    if is_link_or_junction(raw) or not raw.exists() or not raw.is_dir():
        raise PortfolioError(f"Invalid, missing, or linked repository root: {raw}")
    resolved = pathlib.Path(strip_win32_extended_prefix(str(raw.resolve(strict=True))))
    if is_link_or_junction(resolved) or not resolved.is_dir():
        raise PortfolioError(f"Resolved repository root is invalid or a link: {resolved}")
    return resolved


def _validate_safe_path(repo_root: pathlib.Path, target: pathlib.Path, *, expect_dir: bool | None = None) -> pathlib.Path:
    if is_link_or_junction(target):
        raise PortfolioError(f"Symlink or junction is forbidden: {target}")
    try:
        rel = resolve_repo_relative_path(str(target), repo_root)
    except ValueError as exc:
        raise PortfolioError(f"Unsafe path outside repository root: {exc}") from exc
    res = repo_root / rel if rel != "." else repo_root
    if is_link_or_junction(res) or (expect_dir is True and res.exists() and not res.is_dir()) or (expect_dir is False and res.exists() and not res.is_file()):
        raise PortfolioError(f"Unsafe or unexpected path type at {res}")
    return res


def _scan_quotes(text: str, *, stop: str = "", split: str = "", kv: bool = False) -> tuple[str, list[str]]:
    in_s = in_d = esc = False
    parts, start = [], 0
    for idx, ch in enumerate(text):
        if esc:
            esc = False
        elif ch == "\\" and in_d:
            esc = True
        elif ch in {"'", '"'} and ((ch == "'" and not in_d) or (ch == '"' and not in_s)):
            in_s, in_d = (not in_s, in_d) if ch == "'" else (in_s, not in_d)
        elif not in_s and not in_d:
            if stop and ch == stop:
                return text[:idx].rstrip(), []
            if kv and ch == ":" and (idx + 1 == len(text) or text[idx + 1] == " "):
                if not (k := text[:idx].strip()):
                    raise PortfolioError(f"Empty YAML key: {text!r}")
                return k, [text[idx + 1 :].strip()]
            if split and ch == split:
                parts.append(text[start:idx].strip())
                start = idx + 1
    if in_s or in_d or kv:
        raise PortfolioError(f"Malformed YAML syntax: {text!r}")
    return text.rstrip(), [*parts, text[start:].strip()]


def _parse_scalar(raw: str) -> Any:
    val = raw.strip()
    if not val:
        return ""
    if val[0] in {"&", "*", "!"} or (val[0] in {'"', "'"} and (len(val) < 2 or val[-1] != val[0])) or (val[0] == "[" and not val.endswith("]")):
        raise PortfolioError(f"Invalid or unsupported YAML scalar: {raw!r}")
    if len(val) >= 2 and val[0] == val[-1] == '"':
        return val[1:-1].replace('\\"', '"').replace("\\\\", "\\").replace("\\n", "\n").replace("\\t", "\t")
    if len(val) >= 2 and val[0] == val[-1] == "'":
        return val[1:-1].replace("''", "'")
    if val.startswith("[") and val.endswith("]"):
        inner = val[1:-1].strip()
        return [_parse_scalar(x) for x in _scan_quotes(inner, split=",")[1] if x] if inner else []
    low = val.lower()
    if low in {"null", "~", "true", "false"}:
        return None if low in {"null", "~"} else (low == "true")
    return (float(val) if "." in val else int(val)) if re.fullmatch(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)", val) else val


def _extract_epic_yaml_block(md_text: str, source_name: str) -> str:
    in_c = cap = False
    fc, fl, out = "", 0, []
    for line in md_text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        if cap:
            if re.match(rf"^[ \t]*{re.escape(fc)}{{{fl},}}[ \t]*$", line):
                return "\n".join(out)
            out.append(line)
        elif in_c:
            in_c = "-->" not in line
        elif "<!--" in line and "-->" not in line:
            in_c = True
        elif m := _YAML_FENCE_RE.match(line):
            fc, fl, cap = m.group(1)[0], len(m.group(1)), True
    raise PortfolioError(f"{'Unclosed' if cap else 'Missing'} fenced 'yaml sdd:epic' block in '{source_name}'.")


def _parse_yaml_block(tokens: list[tuple[int, str]], idx: int, base: int) -> tuple[Any, int]:
    if tokens[idx][1].startswith("- "):
        items: list[Any] = []
        while idx < len(tokens) and tokens[idx][0] == base and tokens[idx][1].startswith("- "):
            rest, idx = tokens[idx][1][2:].strip(), idx + 1
            if ":" in rest and (rest.endswith(":") or ": " in rest):
                k, [v] = _scan_quotes(rest, kv=True)
                ent: dict[str, Any] = {k: _parse_scalar(v) if v else {}}
                if not v and idx < len(tokens) and tokens[idx][0] > base:
                    ent[k], idx = _parse_yaml_block(tokens, idx, tokens[idx][0])
                if idx < len(tokens) and tokens[idx][0] > base:
                    sub, idx = _parse_yaml_block(tokens, idx, tokens[idx][0])
                    if not isinstance(sub, dict):
                        raise PortfolioError(f"Expected mapping continuation near {rest!r}")
                    ent.update(sub)
                items.append(ent)
            else:
                items.append(_parse_scalar(rest))
        return items, idx
    mapping: dict[str, Any] = {}
    while idx < len(tokens) and tokens[idx][0] == base and not tokens[idx][1].startswith("- "):
        k, [v] = _scan_quotes(tokens[idx][1], kv=True)
        idx += 1
        if v:
            mapping[k] = _parse_scalar(v)
        elif idx < len(tokens) and (tokens[idx][0] > base or (tokens[idx][0] == base and tokens[idx][1].startswith("- "))):
            mapping[k], idx = _parse_yaml_block(tokens, idx, tokens[idx][0])
        else:
            mapping[k] = [] if k == "features" else {}
    return mapping, idx


def _parse_sdd_epic_yaml(yaml_text: str, source_name: str) -> dict[str, Any]:
    tokens: list[tuple[int, str]] = []
    for raw in yaml_text.splitlines():
        lead = raw[: len(raw) - len(raw.lstrip(" \t"))]
        if "\t" in lead:
            raise PortfolioError(f"Tab indentation is forbidden in '{source_name}' YAML.")
        if clean := _scan_quotes(raw, stop="#")[0].strip():
            tokens.append((len(lead), clean))
    if not tokens or tokens[0][0] != 0 or tokens[0][1].startswith("- "):
        raise PortfolioError(f"Top-level 'yaml sdd:epic' must be a non-empty mapping in '{source_name}'.")
    parsed, next_idx = _parse_yaml_block(tokens, 0, 0)
    if not isinstance(parsed, dict) or next_idx != len(tokens):
        raise PortfolioError(f"Malformed YAML structure in '{source_name}'.")
    return parsed


def _canon_st(raw: str | None, default: str = "Candidate") -> str:
    return _FEAT_ST.get(_normalize_status(str(raw)), str(raw).strip()) if raw and str(raw).strip() else default


def _norm_prio(raw: Any, subject: str, findings: list[PortfolioFinding]) -> str:
    if raw is None or not str(raw).strip():
        return "Should"
    txt = str(raw).strip()
    if (canon := _MOSCOW.get(txt.lower())) is None:
        findings.append(PortfolioFinding("INVALID_PRIORITY", "error", f"Invalid MoSCoW priority {txt!r} (Must|Should|Could|Wont).", subject))
        return txt
    return canon


def _parse_rice_map(raw: Any, subject: str, findings: list[PortfolioFinding]) -> RiceScore | None:
    if raw is None:
        return None
    if not isinstance(raw, dict):
        findings.append(PortfolioFinding("INVALID_RICE", "error", f"RICE must be a mapping for {subject}.", subject))
        return None
    vals: dict[str, float] = {}
    for f in ("reach", "impact", "confidence", "effort"):
        val = raw.get(f)
        try:
            num = float(val) if (val is not None and not isinstance(val, bool)) else float("nan")
        except (TypeError, ValueError):
            num = float("nan")
        if not math.isfinite(num):
            findings.append(PortfolioFinding("INVALID_RICE", "error", f"Missing/invalid RICE '{f}'={val!r} for {subject}.", subject))
            return None
        vals[f] = num
    if vals["reach"] < 0 or vals["impact"] < 0 or vals["confidence"] < 0 or vals["effort"] <= 0:
        findings.append(PortfolioFinding("INVALID_RICE", "error", f"Invalid RICE bounds for {subject} (effort > 0, non-negative fields).", subject))
        return None
    return RiceScore(vals["reach"], vals["impact"], vals["confidence"], vals["effort"], round((vals["reach"] * vals["impact"] * vals["confidence"]) / vals["effort"], 4))


def _parse_rice_cell(cell: str, subject: str, findings: list[PortfolioFinding]) -> RiceScore | None:
    c = _clean_cell(cell)
    if not c or c.lower() in {"-", "—", "n/a", "none"}:
        return None
    if kv := {m.group(1).lower(): m.group(2) for m in re.finditer(r"\b(reach|impact|confidence|effort)\s*[:=]\s*([-+]?\d+(?:\.\d+)?)", c, re.I)}:
        return _parse_rice_map(kv, subject, findings)
    if len(parts := [p.strip() for p in c.split("/") if p.strip()]) == 4:
        return _parse_rice_map(dict(zip(("reach", "impact", "confidence", "effort"), parts)), subject, findings)
    findings.append(PortfolioFinding("INVALID_RICE", "error", f"Malformed RICE cell {c!r} for {subject}.", subject))
    return None


def _parse_deps(raw: Any) -> tuple[str, ...]:
    if raw is None:
        return ()
    return tuple(dict.fromkeys([str(x).strip().upper() for x in raw if str(x).strip()] if isinstance(raw, list) else [m.upper() for m in re.findall(r"\bFEAT-\d{3,4}\b", str(raw), re.I)]))


def _parse_backlog_portfolio(backlog_text: str, findings: list[PortfolioFinding]) -> tuple[dict[str, dict[str, Any]], bool]:
    statuses, _ = _parse_backlog_entries(backlog_text)
    entries = {k: {"status": _canon_st(v)} for k, v in statuses.items() if _FEAT_ID_RE.match(k)}
    has_cols, cmap, in_tbl = False, {}, False
    aliases = {"id": {"id", "feature id"}, "title": {"título", "titulo", "title", "nombre", "name", "descripción", "descripcion", "description", "feature"}, "epic": {"épica", "epica", "epic"}, "priority": {"prioridad", "priority", "moscow"}, "deps": {"depende de", "depends on", "depends_on", "dependencias", "dependencies"}, "rice": {"rice"}}
    for line in strip_non_normative_markdown(backlog_text).splitlines():
        if not (cells := _split_markdown_row(line)):
            cmap, in_tbl = {}, False
        elif all(re.match(r"^:?-{2,}:?$", c.replace(" ", "")) for c in cells):
            in_tbl = True
        elif not in_tbl and (norm := [_normalize_status(c) for c in cells]) and any(h in {"id", "estado", "status", "épica", "epica", "epic"} for h in norm):
            in_tbl = True
            for i, h in enumerate(norm):
                for key, names in aliases.items():
                    if h in names:
                        cmap.setdefault(key, i)
        elif (id_i := cmap.get("id", 0)) < len(cells) and (m := re.search(r"\b(FEAT-\d{3,4})\b", _clean_cell(cells[id_i]), re.I)):
            ent = entries.setdefault(fid := m.group(1).upper(), {"status": "Candidate"})
            cell = lambda k: _clean_cell(cells[cmap[k]]) if k in cmap and cmap[k] < len(cells) else ""  # noqa: E731
            if t := cell("title"):
                ent["title"] = t
            if em := re.search(r"\b(EPIC-\d{3,4})\b", cell("epic"), re.I):
                ent["epic_id"], has_cols = em.group(1).upper(), True
            if deps := _parse_deps(cell("deps")):
                ent["depends_on"], has_cols = deps, True
            if (rp := cell("priority")) not in {"", "-", "—"}:
                ent["raw_priority"] = rp
            if (rc := cell("rice")).lower() not in {"", "-", "—", "n/a", "none"}:
                ent["rice"], has_cols = _parse_rice_cell(rc, fid, findings), True
    return entries, has_cols


def build_feature_graph(features: Sequence[PortfolioFeature]) -> tuple[tuple[tuple[str, ...], ...], tuple[str, ...], list[PortfolioFinding]]:
    """Build deterministic Kahn waves, longest pending critical path, and dependency findings."""
    by_id, findings = {f.feature_id: f for f in features}, []
    in_deg, deps_out = {fid: 0 for fid in by_id}, {fid: [] for fid in by_id}
    for fid in sorted(by_id):
        feat = by_id[fid]
        for dep_id in feat.depends_on:
            if dep_id not in by_id:
                findings.append(PortfolioFinding("UNKNOWN_DEPENDENCY", "error", f"Feature '{fid}' depends on unknown feature '{dep_id}'.", fid))
                continue
            deps_out[dep_id].append(fid)
            in_deg[fid] += 1
            dep = by_id[dep_id]
            if (wf := _MOSCOW_W.get(feat.priority)) and (wd := _MOSCOW_W.get(dep.priority)) and wf > wd and feat.priority == "Must" and dep.priority in {"Could", "Wont"}:
                findings.append(PortfolioFinding("PRIORITY_INVERSION", "warning", f"Priority inversion: '{fid}' ({feat.priority}) depends on '{dep_id}' ({dep.priority}).", fid))
    waves, queue = [], sorted(fid for fid, deg in in_deg.items() if deg == 0)
    while queue:
        waves.append(tuple(queue))
        queue = sorted(v for u in queue for v in deps_out[u] if not (in_deg.__setitem__(v, in_deg[v] - 1) or in_deg[v]))
    if cycle_nodes := sorted(fid for fid, deg in in_deg.items() if deg > 0):
        findings.append(PortfolioFinding("CYCLE_DETECTED", "error", f"Dependency cycle detected among features: {', '.join(cycle_nodes)}.", cycle_nodes[0]))
    pending: dict[str, tuple[str, ...]] = {}
    for wave in waves:
        for fid in wave:
            if by_id[fid].status != "Done":
                preds = [d for d in by_id[fid].depends_on if d in pending]
                pending[fid] = (fid,) if not preds else pending[min(preds, key=lambda p: (-len(pending[p]), pending[p]))] + (fid,)
    return tuple(waves), min(pending.values(), key=lambda p: (-len(p), p)) if pending else (), findings


def _make_row(fid: str, title: str, epic_id: str | None, status: str, prio: Any, deps: tuple[str, ...], rice: RiceScore | None, findings: list[PortfolioFinding]) -> dict[str, Any]:
    return {"feature_id": fid, "title": title, "epic_id": epic_id, "status": status, "priority": _norm_prio(prio, fid, findings), "depends_on": deps, "rice": rice}


def analyze_portfolio(repo_root: pathlib.Path | str) -> PortfolioReport:
    """Analyze epics and feature dependencies under repo_root in strict offline fail-closed mode."""
    root = _validate_repo_root(repo_root)
    specs_dir = _validate_safe_path(root, root / "specs", expect_dir=True)
    backlog_path = _validate_safe_path(root, specs_dir / "BACKLOG.md", expect_dir=False)
    epics_dir = _validate_safe_path(root, specs_dir / "epics", expect_dir=True)
    epic_files = sorted(epics_dir.glob("EPIC-*.md")) if epics_dir.is_dir() else []
    for ef in epic_files:
        _validate_safe_path(root, ef, expect_dir=False)
    findings: list[PortfolioFinding] = []
    bl_text = backlog_path.read_text(encoding="utf-8") if backlog_path.is_file() else ""
    bl_entries, has_bl = _parse_backlog_portfolio(bl_text, findings) if bl_text else ({}, False)
    if not epic_files and not has_bl:
        return PortfolioReport(str(root), False, "SKIPPED_NO_APPLICABLE", (), (), (), (), ())

    epics_meta, raw_feats, owner = {}, {}, {}
    for ef in epic_files:
        rel = resolve_repo_relative_path(str(ef), root)
        parsed = _parse_sdd_epic_yaml(_extract_epic_yaml_block(ef.read_text(encoding="utf-8"), rel), rel)
        epic_id = str(parsed.get("epic_id") or "").strip().upper()
        if not _EPIC_ID_RE.match(epic_id):
            raise PortfolioError(f"Invalid or missing epic_id in '{rel}': {epic_id!r}")
        if epic_id in epics_meta:
            findings.append(PortfolioFinding("DUPLICATE_EPIC", "error", f"Duplicate epic '{epic_id}' in '{rel}'.", epic_id))
            continue
        raw_est = str(parsed.get("status") or "Draft").strip()
        epics_meta[epic_id] = {"epic_id": epic_id, "title": str(parsed.get("title") or epic_id).strip(), "source_file": rel, "status": _EPIC_ST.get(raw_est.lower(), raw_est), "priority": _norm_prio(parsed.get("priority"), epic_id, findings), "rice": _parse_rice_map(parsed.get("rice"), epic_id, findings), "feature_ids": []}
        if not isinstance(feat_list := parsed.get("features") or [], list):
            raise PortfolioError(f"'features' must be a list in '{rel}'.")
        for fi in feat_list:
            if not isinstance(fi, dict) or not _FEAT_ID_RE.match(fid := str(fi.get("id") or "").strip().upper()):
                raise PortfolioError(f"Invalid feature entry/id in '{rel}': {fi!r}")
            if fid in owner:
                findings.append(PortfolioFinding("DUPLICATE_FEATURE_EPIC", "error", f"Feature '{fid}' declared in multiple epics ({owner[fid]}, {epic_id}).", fid))
                continue
            owner[fid] = epic_id
            epics_meta[epic_id]["feature_ids"].append(fid)
            bl, decl_st = bl_entries.get(fid), _canon_st(fi.get("status"))
            if bl is None and decl_st in _ORPHAN_ST:
                findings.append(PortfolioFinding("ORPHAN_FEATURE_REF", "warning", f"Feature '{fid}' is '{decl_st}' in '{rel}' but missing from specs/BACKLOG.md.", fid))
            prio = fi.get("priority") if fi.get("priority") is not None else (bl.get("raw_priority") if bl else None)
            deps = tuple(dict.fromkeys([*_parse_deps(fi.get("depends_on")), *(bl.get("depends_on", ()) if bl else ())]))
            rice = _parse_rice_map(fi.get("rice"), fid, findings) if "rice" in fi else (bl.get("rice") if bl else None)
            raw_feats[fid] = _make_row(fid, str(fi.get("title") or (bl.get("title") if bl else "") or fid).strip(), epic_id, bl["status"] if bl else decl_st, prio, deps, rice, findings)

    for fid, bl in sorted(bl_entries.items()):
        if fid in raw_feats and (be := bl.get("epic_id")) and be != raw_feats[fid]["epic_id"]:
            findings.append(PortfolioFinding("DUPLICATE_FEATURE_EPIC", "error", f"Feature '{fid}' assigned to '{raw_feats[fid]['epic_id']}' in epic file and '{be}' in BACKLOG.md.", fid))
        elif fid not in raw_feats and (bl.get("epic_id") or bl.get("depends_on") or bl.get("rice") is not None):
            if be := bl.get("epic_id"):
                epics_meta.setdefault(be, {"epic_id": be, "title": be, "status": "Active", "priority": "Should", "source_file": "specs/BACKLOG.md", "rice": None, "feature_ids": []})["feature_ids"].append(fid)
            raw_feats[fid] = _make_row(fid, bl.get("title") or fid, be, bl["status"], bl.get("raw_priority"), bl.get("depends_on", ()), bl.get("rice"), findings)
    for dep_id in sorted({d for rf in raw_feats.values() for d in rf["depends_on"]} - set(raw_feats)):
        if bl := bl_entries.get(dep_id):
            raw_feats[dep_id] = _make_row(dep_id, bl.get("title") or dep_id, bl.get("epic_id"), bl["status"], bl.get("raw_priority"), bl.get("depends_on", ()), bl.get("rice"), findings)
    done_ids = {fid for fid, rf in raw_feats.items() if rf["status"] == "Done"}
    features = tuple(PortfolioFeature(rf["feature_id"], rf["title"], rf["epic_id"], rf["status"], rf["priority"], rf["depends_on"], rf["rice"], rf["status"] not in {"Done", "Blocked", "Cancelled"} and all(d in done_ids for d in rf["depends_on"]), tuple(d for d in rf["depends_on"] if d not in done_ids)) for _, rf in sorted(raw_feats.items()))
    waves, critical_path, graph_findings = build_feature_graph(features)
    findings.extend(graph_findings)
    feat_map = {f.feature_id: f for f in features}
    epics = tuple(EpicSummary(m["epic_id"], m["title"], m["status"], m["priority"], m["source_file"], len(ef := [feat_map[i] for i in m["feature_ids"] if i in feat_map]), done := sum(1 for f in ef if f.status == "Done"), sum(1 for f in ef if f.status in {"In Progress", "In Review"}), sum(1 for f in ef if f.status == "Blocked" or (f.status != "Done" and bool(f.blocked_by))), round((done / len(ef)) * 100.0, 1) if ef else 0.0, tuple(m["feature_ids"]), tuple(sorted(f.feature_id for f in ef if f.ready)), m["rice"]) for _, m in sorted(epics_meta.items()))
    return PortfolioReport(str(root), True, "FAIL" if any(f.severity == "error" for f in findings) else "PASS", epics, features, waves, critical_path, tuple(findings))


def init_epic_doc(repo_root: pathlib.Path | str, epic_id: str, title: str, *, force: bool = False) -> pathlib.Path:
    """Create specs/epics/<EPIC-ID>-<slug>.md atomically from official template."""
    root, norm_id, clean_title = _validate_repo_root(repo_root), epic_id.strip().upper(), title.strip()
    if not _EPIC_ID_RE.match(norm_id) or not clean_title:
        raise PortfolioError(f"Invalid epic_id ({epic_id!r}) or empty title.")
    slug = re.sub(r"[^a-z0-9]+", "-", "".join(c for c in unicodedata.normalize("NFKD", clean_title) if not unicodedata.combining(c)).lower()).strip("-")
    if not slug or ".." in slug:
        raise PortfolioError(f"Cannot derive a safe kebab-case slug from title: {clean_title!r}")
    specs_dir = _validate_safe_path(root, root / "specs", expect_dir=True)
    epics_dir = _validate_safe_path(root, specs_dir / "epics", expect_dir=True)
    target = _validate_safe_path(root, epics_dir / f"{norm_id}-{slug}.md", expect_dir=False)
    if target.exists() and not force:
        raise PortfolioError(f"Epic document already exists (pass --force to overwrite): {target}")
    tpl_path = _validate_safe_path(root, specs_dir / "templates" / "09-epic-roadmap.template.md", expect_dir=False)
    template = tpl_path.read_text(encoding="utf-8") if tpl_path.is_file() else _DEFAULT_TPL
    rendered = template.replace('title: "[Título de la Épica]"', f'title: "{json.dumps(clean_title, ensure_ascii=False)[1:-1]}"')
    atomic_write_text(target, rendered.replace("EPIC-001", norm_id).replace("[Título de la Épica]", clean_title))
    return target


def _report_to_dict(report: PortfolioReport) -> dict[str, Any]:
    payload = dataclasses.asdict(report)
    for feat in payload["features"]:
        feat["rice_score"] = feat["rice"]["score"] if feat["rice"] else None
    return payload


def run_portfolio_ci_check(repo_root: pathlib.Path) -> tuple[str, str, dict[str, Any]]:
    """CI entry point returning (SKIPPED_NO_APPLICABLE|PASS|FAIL, summary, details)."""
    try:
        report = analyze_portfolio(repo_root)
    except PortfolioError as exc:
        return "FAIL", f"Portfolio validation error: {exc}", {"error": str(exc)}
    if not report.has_portfolio_data:
        return "SKIPPED_NO_APPLICABLE", "No epics or feature dependencies declared.", {"has_portfolio_data": False}
    if report.status == "PASS":
        return "PASS", f"Portfolio OK ({len(report.epics)} epic(s), {len(report.features)} feature(s)).", _report_to_dict(report)
    return "FAIL", "; ".join(f"{f.code}: {f.detail}" for f in report.findings if f.severity == "error") or "Portfolio validation failed.", _report_to_dict(report)


def _format_report_text(report: PortfolioReport, mode: str) -> str:
    lines = [f"SDD Portfolio ({mode}) — Status: {report.status}", f"Repo: {report.repo_root}"]
    if not report.has_portfolio_data:
        return "\n".join([*lines, "No portfolio epics or feature dependencies found (SKIPPED_NO_APPLICABLE)."])
    if mode in {"status", "validate"} and report.epics:
        lines.extend(["Epics:", *(f"  - {e.epic_id} [{e.status}/{e.priority}] {e.title}: {e.done_features}/{e.total_features} ({e.progress_pct}%) | Ready: {', '.join(e.ready_features) or 'None'}" for e in report.epics)])
    if mode in {"graph", "validate"}:
        lines.extend(["Execution Waves:", *(f"  Wave {i}: {', '.join(w)}" for i, w in enumerate(report.waves, 1)), f"Critical Path: {' -> '.join(report.critical_path) if report.critical_path else 'None'}"])
    if report.findings:
        lines.extend(["Findings:", *(f"  [{f.severity.upper()}] {f.code}: {f.detail}" for f in report.findings)])
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(prog="sdd portfolio", description="SDD Portfolio, Epics & Feature DAG CLI")
    sub = parser.add_subparsers(dest="command", required=True)
    p_init = sub.add_parser("init", help="Create a new specs/epics/EPIC-XXX-<slug>.md from template")
    for p in (p_init, *(sub.add_parser(c, help=f"Run portfolio {c} analysis") for c in ("status", "graph", "validate"))):
        p.add_argument("--repo-root", default=".", help="Repository root directory")
        p.add_argument("--format", choices=("text", "json"), default="text")
    p_init.add_argument("--id", required=True, dest="epic_id", help="Epic ID (e.g. EPIC-001)")
    p_init.add_argument("--title", required=True, help="Epic title")
    p_init.add_argument("--force", action="store_true", help="Overwrite existing epic file")
    sub.choices["status"].add_argument("--epic", default=None, help="Filter by EPIC-XXX")
    args = parser.parse_args(argv)
    try:
        if args.command == "init":
            created = init_epic_doc(args.repo_root, args.epic_id, args.title, force=args.force)
            print(json.dumps({"status": "CREATED", "path": str(created)}, ensure_ascii=False, indent=2) if args.format == "json" else f"Created epic document: {created}")
            return 0
        report = analyze_portfolio(args.repo_root)
        if args.command == "status" and getattr(args, "epic", None):
            te = args.epic.strip().upper()
            report = dataclasses.replace(report, epics=tuple(e for e in report.epics if e.epic_id == te), features=tuple(f for f in report.features if f.epic_id == te))
        print(json.dumps(_report_to_dict(report), ensure_ascii=False, indent=2) if args.format == "json" else _format_report_text(report, args.command))
        return 1 if report.status == "FAIL" else 0
    except PortfolioError as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, ensure_ascii=False, indent=2) if args.format == "json" else f"[ERROR] {exc}", file=sys.stdout if args.format == "json" else sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
