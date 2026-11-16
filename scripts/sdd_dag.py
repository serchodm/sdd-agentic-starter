#!/usr/bin/env python3
"""Deterministic SDD DAG parser, validator, and inbox state transition engine."""

from __future__ import annotations

import argparse, datetime as dt, json, os, re, sys, tempfile
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from scripts.sdd_ownership import _normalize_glob, _segs_intersect
except ImportError:
    from sdd_ownership import _normalize_glob, _segs_intersect

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

ROOT_DIR = Path(__file__).resolve().parent.parent
VALID_INBOX_STATES: frozenset[str] = frozenset({"pending", "in_progress", "done", "blocked"})
ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    "pending": frozenset({"in_progress", "blocked"}), "in_progress": frozenset({"done", "blocked"}),
    "blocked": frozenset({"in_progress", "pending"}), "done": frozenset(),
}

_FENCE_RE = re.compile(r"^[ \t]*(`{3,}|~{3,})(.*)$")
_HEADING_RE = re.compile(r"^(#{2,6})[ \t]+(?:\[([ xX~>!])\][ \t]+)?(.+)$")
_BULLET_RE = re.compile(r"^[ \t]*(?:[-*+]|\d+\.)[ \t]+(?:\[([ xX~>!])\][ \t]+)?(.+)$")
_TASK_ID_RE = re.compile(r"^(?P<id>TASK[-_]\d+(?:\.\d+)*|T_[A-Za-z0-9]+(?:\.\d+)*|T-\d+(?:\.\d+)*|T\d+(?:\.\d+)*)(?=$|[\s:*_`\]):—–-])", re.I)
_TASK_WORD_RE = re.compile(r"^(?:Tarea|Task)[ \t]+(?P<id>[A-Za-z]+(?:\.\d+)+|[A-Za-z]+\d+|\d+(?:\.\d+)*)(?=$|[\s:*_`\]):—–-])", re.I)
_BLOCK_NAME_RE = re.compile(r"(?:Bloque|Block)[_\s-]+([A-Za-z0-9._-]+)", re.I)
_MODE_TAG_RE = re.compile(r"\[(PARALLEL|SEQUENTIAL)(?:[ \t]*[:\-–—][ \t]*([^\]]+))?\]", re.I)
_INLINE_DEP_TAG_RE = re.compile(r"\[(?:Depends\s+on|Depende\s+de|After|Requires|Requiere)[ \t]*:[ \t]*([^\]]+)\]", re.I)
_INLINE_DEP_LINE_RE = re.compile(r"(?:^|[\s|;(—–-])(?:Depends\s+on|Depende\s+de|After|Requires|Requiere)[ \t]*:[ \t]*([^|()\n]+)", re.I)
_OWNER_RE = re.compile(r"(?:^|[\s\[(`/,;:])@([A-Za-z][A-Za-z0-9_-]*)(?=$|[\s\]`),;:.*])")
_SUB_DEP_RE = re.compile(r"^[ \t]*(?:[-*+][ \t]+)?(?:[*_`]+)?(?:Depends\s+on|Depende\s+de|After|Requires|Requiere|Blocked\s+by)(?:[*_`]+)?[ \t]*:[ \t]*(?:[*_`]+)?[ \t]*(.+)$", re.I)
_SUB_OWNER_RE = re.compile(r"^[ \t]*(?:[-*+][ \t]+)?(?:[*_`]+)?(?:Owner|Agente|Agent|Assigned\s+to)(?:[*_`]+)?[ \t]*:[ \t]*(.+)$", re.I)
_SUB_DOD_RE = re.compile(r"^[ \t]*(?:[-*+][ \t]+)?(?:[*_`]+)?(?:Comando\s+de\s+verificaci[oó]n\s+DoD|DoD)(?:[*_`]+)?[ \t]*:[ \t]*(.+)$", re.I)
_SUB_STATUS_RE = re.compile(r"^[ \t]*(?:[-*+][ \t]+)?(?:[*_`]+)?(?:Status|Estado)(?:[*_`]+)?[ \t]*:[ \t]*(.+)$", re.I)
_SUB_PATHS_RE = re.compile(r"^[ \t]*(?:[-*+][ \t]+)?(?:[*_`]+)?(?:Archivos(?:\s+exactos)?|Ficheros(?:\s+exactos)?|Rutas\s+objetivo|Target\s+(?:paths?|files?)|Files|Write[-_\s]?set)(?:[*_`]+)?[ \t]*:[ \t]*(.+)$", re.I)
_TICKET_FIELD_RE = re.compile(r"^([ \t]*-[ \t]+\*\*(?P<key>Estado|Status|Updated|Note)\*\*[ \t]*:[ \t]*)(?P<val>.*)$", re.I)
_TICKET_META_RE = re.compile(r"^[ \t]*-[ \t]+\*\*([^*]+)\*\*[ \t]*:[ \t]*(.*)$")
_NONE_TOKENS = frozenset({"", "-", "none", "n/a", "na", "ninguna", "ninguno", "null"})
_CHECKBOX_STATUS = {"x": "done", "X": "done", "~": "in_progress", ">": "in_progress", "!": "blocked", " ": "pending"}
_STATUS_ALIASES = {"done": "done", "completed": "done", "completado": "done", "pending": "pending", "pendiente": "pending", "in_progress": "in_progress", "en_progreso": "in_progress", "blocked": "blocked", "bloqueado": "blocked"}

class DagError(Exception):
    """Base fail-closed error for DAG parsing, validation, and inbox transitions."""

class DagCycleError(DagError):
    """Raised when one or more dependency cycles exist in the task graph."""
    def __init__(self, message: str, cycle: tuple[str, ...] = ()) -> None:
        super().__init__(message); self.cycle = cycle

class DagWriteSetCollisionError(DagError):
    """Raised when two or more tasks in the same parallel wave have overlapping target paths/globs."""

@dataclass(frozen=True)
class DagTask:
    """Single task node extracted from a 03-tasks.md specification."""
    task_id: str; title: str; owner: str | None = None; owners: tuple[str, ...] = ()
    block: str | None = None; mode: str = "PARALLEL"; depends_on: tuple[str, ...] = ()
    status: str = "pending"; dod_command: str | None = None; line_no: int = 0; target_paths: tuple[str, ...] = ()

@dataclass(frozen=True)
class DagPlan:
    """Validated topological execution plan and adjacency representation."""
    tasks: dict[str, DagTask]; order: tuple[str, ...]; waves: list[list[DagTask]]
    adjacency: dict[str, tuple[str, ...]]; dependencies: dict[str, tuple[str, ...]]

@dataclass(frozen=True)
class InboxTicket:
    """Result of a validated, atomic inbox ticket state transition."""
    task_id: str; agent: str; state: str; previous_state: str
    ticket_path: Path; depends_on: tuple[str, ...] = ()

def _clean(text: str) -> str:
    return text.strip().strip("`*_[](){}\"'").strip()
def _norm_status(raw: str) -> str | None:
    return _STATUS_ALIASES.get(_clean(raw).lower().replace("-", "_").replace(" ", "_"))
def _norm_path_token(raw: str) -> str:
    p = raw.strip().strip("`'\"*_").replace("\\", "/")
    while p.startswith("./"):
        p = p[2:]
    return p.rstrip("/")

def _parse_target_paths(raw: str) -> list[str]:
    cleaned = re.sub(r"\([^)]*\)", "", raw).strip()
    chunks = re.findall(r"`([^`]+)`", cleaned) if "`" in cleaned else [cleaned]
    paths: list[str] = []
    for chunk in chunks:
        for part in re.split(r"[,;](?![^{]*\})", chunk):
            if (tok := _norm_path_token(part)) and tok.lower() not in _NONE_TOKENS and tok not in paths:
                paths.append(tok)
    return paths

def _strip_comments_and_fences(text: str) -> list[str]:
    no_comments = re.sub(r"<!--.*?-->", lambda m: "\n" * m.group(0).count("\n"), text.lstrip("\ufeff").replace("\r\n", "\n").replace("\r", "\n"), flags=re.S)
    out, fchar, flen = [], "", 0
    for line in no_comments.split("\n"):
        if fchar:
            if (s := line.lstrip()).startswith(fchar * flen) and s.strip(fchar).strip() == "":
                fchar, flen = "", 0
            out.append("")
        elif m := _FENCE_RE.match(line):
            fchar, flen = m.group(1)[0], len(m.group(1)); out.append("")
        else:
            out.append(line)
    return out

def _norm_task_id(raw: str) -> str:
    c = _clean(raw)
    if m := _TASK_ID_RE.match(c):
        return m.group("id").upper()
    if m := _TASK_WORD_RE.match(c):
        return val if "." in (val := m.group("id").upper()) or val[0].isalpha() else f"TASK-{val}"
    return c.upper()
def _norm_block(raw: str) -> str:
    c = _clean(raw)
    return f"BLOCK_{m.group(1).upper()}" if (m := _BLOCK_NAME_RE.search(c)) else re.sub(r"[\s-]+", "_", c).upper()

def _split_dep_refs(raw: str) -> list[str]:
    if raw.strip().lower() in _NONE_TOKENS:
        return []
    refs: list[str] = []
    for part in re.split(r"[,;&]|\s+(?:and|y)\s+", raw.strip(), flags=re.I):
        c = _clean(re.sub(r"^(?:AFTER|REQUIRES?|REQUIERE|DEPENDS\s+ON|DEPENDE\s+DE)[_\s:-]+", "", _clean(part), flags=re.I))
        if c.lower() not in _NONE_TOKENS:
            refs.append(_norm_task_id(c) if (_TASK_ID_RE.match(c) or _TASK_WORD_RE.match(c)) else (_norm_block(c) if _BLOCK_NAME_RE.search(c) else re.sub(r"\s+", "_", c).upper()))
    return refs

def _split_header_and_desc(body: str) -> tuple[str, str]:
    depth = 0
    for idx, ch in enumerate(body):
        depth += (ch in "[(") - (ch in "])" and depth > 0)
        if ch == ":" and depth == 0:
            return body[:idx], body[idx + 1 :].strip()
    return body, ""

def _extract_task_header(body: str) -> tuple[str, str] | None:
    ps = re.sub(r"^[*_`\[\s]+", "", body.lstrip())
    for rx, is_word in ((_TASK_ID_RE, False), (_TASK_WORD_RE, True)):
        if m := rx.match(ps):
            return (_norm_task_id(m.group(0)) if is_word else m.group("id").upper()), re.sub(r"^[*_`\]\s]+", " ", ps[m.end() :]).strip()
    return None

def _parse_block_heading(body: str, prev_block: str | None) -> tuple[str | None, str, list[str]] | None:
    mode_m, block_m = _MODE_TAG_RE.search(body), _BLOCK_NAME_RE.search(body)
    if not mode_m and not block_m:
        return None
    block_id, mode, deps = (f"BLOCK_{block_m.group(1).upper()}" if block_m else None), (mode_m.group(1).upper() if mode_m else "PARALLEL"), []
    if mode_m and mode_m.group(2):
        tail = mode_m.group(2).strip()
        if req_m := re.search(r"(?:Requiere|Requires|After|Depende\s+de|Depends\s+on)[:\s_-]+(.+)$", tail, re.I):
            deps.extend(_split_dep_refs(req_m.group(1)))
        elif not block_id:
            block_id = _norm_block(tail)
    if mode == "SEQUENTIAL" and not deps and prev_block and prev_block != block_id:
        deps.append(prev_block)
    return block_id, mode, deps

def _consume_subline(line: str, t: dict[str, Any]) -> None:
    if dm := _SUB_DEP_RE.match(line):
        t["deps"].extend(_split_dep_refs(dm.group(1)))
    elif om := _SUB_OWNER_RE.match(line):
        if owners := tuple(dict.fromkeys(m.group(1).lower() for m in _OWNER_RE.finditer(om.group(1)))):
            t["owners"], t["owner"] = owners, owners[0]
        elif (raw := _clean(om.group(1)).lstrip("@").lower()) and raw not in _NONE_TOKENS:
            t["owners"], t["owner"] = (raw,), raw
    elif dod_m := _SUB_DOD_RE.match(line):
        t["dod"] = dod_m.group(1).strip().strip("`")
    elif (sm := _SUB_STATUS_RE.match(line)) and (st := _norm_status(sm.group(1))):
        t["status"] = st
    elif pm := _SUB_PATHS_RE.match(line):
        t["paths"].extend(_parse_target_paths(pm.group(1)))

def _build_raw_task(tid: str, rest: str, chk: str | None, line_no: int, cur_block: str | None, blk_mode: str, blk_deps: list[str]) -> dict[str, Any]:
    head_part, desc_part = _split_header_and_desc(rest)
    owners = tuple(dict.fromkeys(m.group(1).lower() for m in _OWNER_RE.finditer(head_part))) or tuple(dict.fromkeys(m.group(1).lower() for m in _OWNER_RE.finditer(rest)))
    t_block, t_mode, t_deps = cur_block, blk_mode, list(blk_deps)
    for tm in _MODE_TAG_RE.finditer(rest):
        t_mode = tm.group(1).upper()
        for piece in re.split(r"[,;]", (tm.group(2) or "").strip()):
            if p := piece.strip():
                if re.match(r"^(?:AFTER|REQUIRES?|REQUIERE)[_\s:-]+", p, re.I) or t_mode != "PARALLEL":
                    t_deps.extend(_split_dep_refs(p))
                else:
                    t_block = _norm_block(p)
    for dm in _INLINE_DEP_TAG_RE.finditer(rest):
        t_deps.extend(_split_dep_refs(dm.group(1)))
    if im := _INLINE_DEP_LINE_RE.search(_INLINE_DEP_TAG_RE.sub("", _MODE_TAG_RE.sub("", rest))):
        t_deps.extend(_split_dep_refs(im.group(1)))
    title = _INLINE_DEP_TAG_RE.sub("", _MODE_TAG_RE.sub("", desc_part or head_part)).strip(" :-–—")
    return {"task_id": tid, "title": title or tid, "owner": owners[0] if owners else None, "owners": owners, "block": t_block, "mode": t_mode, "deps": t_deps, "status": _CHECKBOX_STATUS.get(chk or " ", "pending"), "dod": None, "line_no": line_no, "paths": []}

def parse_tasks_text(text: str, source: str = "<string>") -> list[DagTask]:
    """Parse structured DAG tasks and block dependencies from Markdown content."""
    lines = _strip_comments_and_fences(text)
    raw_tasks, block_members, cur_block, last_block, blk_mode, blk_deps, cur_task = [], {}, None, None, "PARALLEL", [], None
    def _flush() -> None:
        nonlocal cur_task
        if cur_task is not None:
            raw_tasks.append(cur_task)
            if cur_task["block"]:
                block_members.setdefault(cur_task["block"], []).append(cur_task["task_id"])
            cur_task = None
    for line_no, line in enumerate(lines, start=1):
        if not (stripped := line.strip()) or stripped == "---":
            if stripped == "---":
                _flush()
            continue
        if hm := _HEADING_RE.match(stripped):
            _flush(); chk, body = hm.group(2), hm.group(3)
            if (parsed := _extract_task_header(body)) is None:
                cur_block, blk_mode, blk_deps = blk if (blk := _parse_block_heading(body, last_block)) is not None else (None, "PARALLEL", [])
                last_block = cur_block or last_block; continue
        elif (bm := _BULLET_RE.match(line)) and (parsed := _extract_task_header(bm.group(2))) is not None:
            _flush(); chk = bm.group(1)
        else:
            if cur_task is not None:
                _consume_subline(line, cur_task)
            continue
        cur_task = _build_raw_task(parsed[0], parsed[1], chk, line_no, cur_block, blk_mode, blk_deps)
    _flush()
    if not raw_tasks:
        if any(_MODE_TAG_RE.search(ln) for ln in lines):
            raise DagError(f"DAG markers found in '{source}', but no structured task IDs could be parsed.")
        return []
    return [DagTask(task_id=i["task_id"], title=i["title"], owner=i["owner"], owners=i["owners"], block=i["block"], mode=i["mode"], depends_on=tuple(dict.fromkeys(t for r in i["deps"] for t in block_members.get(r, [r]))), status=i["status"], dod_command=i["dod"], line_no=i["line_no"], target_paths=tuple(dict.fromkeys(i["paths"]))) for i in raw_tasks]

def parse_tasks_markdown(path: Path) -> list[DagTask]:
    """Read and parse a 03-tasks.md Markdown file into DagTask entries."""
    try:
        return parse_tasks_text(path.read_text(encoding="utf-8"), source=str(path))
    except (OSError, UnicodeDecodeError) as exc:
        raise DagError(f"Cannot read tasks file '{path}': {exc}") from exc

def _glob_segs(p: str) -> tuple[tuple[str, ...], ...]:
    try:
        variants = list(_normalize_glob(p))
    except Exception:
        variants = [tuple(s for s in p.split("/") if s)]
    if not any(c in p for c in "*?[{") and "." not in p.rsplit("/", 1)[-1]:
        variants.append((*variants[0], "**"))
    return tuple(variants)

def _paths_overlap(path_a: str, path_b: str) -> bool:
    """Return True if two repo-relative file/directory/glob targets can touch the same file."""
    a, b = _norm_path_token(path_a).lower(), _norm_path_token(path_b).lower()
    if not a or not b:
        return False
    if a == b or a.startswith(f"{b}/") or b.startswith(f"{a}/"):
        return True
    if not any(c in a for c in "*?[{") and not any(c in b for c in "*?[{"):
        return False
    return any(_segs_intersect(sa, sb) for sa in _glob_segs(a) for sb in _glob_segs(b))

def find_wave_write_set_collisions(wave: Sequence[DagTask]) -> list[tuple[str, str, str, str]]:
    """Return all (task_a, task_b, path_a, path_b) write-set collisions within a parallel wave."""
    return [(t1.task_id, t2.task_id, pa, pb) for i, t1 in enumerate(wave) for t2 in wave[i + 1 :] for pa in t1.target_paths for pb in t2.target_paths if _paths_overlap(pa, pb)]

def _find_cycle_path(remaining: set[str], dependencies: dict[str, tuple[str, ...]]) -> tuple[str, ...]:
    state, stack = {}, []
    def _dfs(node: str) -> list[str] | None:
        state[node] = 1; stack.append(node)
        for dep in dependencies.get(node, ()):
            if dep in remaining:
                if state.get(dep) == 1:
                    return list(reversed([*stack[stack.index(dep) :], dep]))
                if state.get(dep, 0) == 0 and (found := _dfs(dep)):
                    return found
        stack.pop(); state[node] = 2; return None
    for start in sorted(remaining):
        if state.get(start, 0) == 0 and (cycle := _dfs(start)):
            return tuple(cycle)
    return tuple(sorted(remaining))

def build_and_validate_dag(tasks: Sequence[DagTask], *, auto_split_waves: bool = False) -> DagPlan:
    """Validate task uniqueness, dependency existence, write-set safety, and acyclicity via Kahn's waves."""
    by_id: dict[str, DagTask] = {}
    for task in tasks:
        if task.task_id in by_id:
            raise DagError(f"Duplicate task ID '{task.task_id}' (line {task.line_no}).")
        by_id[task.task_id] = task
    dependencies, adj_sets, in_degree = {}, {tid: [] for tid in by_id}, {}
    for tid, task in by_id.items():
        for dep in task.depends_on:
            if dep not in by_id:
                raise DagError(f"Task '{tid}' references unknown dependency '{dep}'.")
        dependencies[tid] = tuple(dict.fromkeys(task.depends_on)); in_degree[tid] = len(dependencies[tid])
        for dep in dependencies[tid]:
            adj_sets[dep].append(tid)
    sort_key = lambda k: (by_id[k].line_no, k)
    adjacency = {tid: tuple(sorted(children, key=sort_key)) for tid, children in adj_sets.items()}
    waves, order, current_wave = [], [], sorted((tid for tid, deg in in_degree.items() if deg == 0), key=sort_key)
    while current_wave:
        wave_tasks = [by_id[tid] for tid in current_wave]
        if auto_split_waves:
            sub_waves: list[list[DagTask]] = []
            for task in wave_tasks:
                for sub in sub_waves:
                    if not find_wave_write_set_collisions([*sub, task]):
                        sub.append(task); break
                else:
                    sub_waves.append([task])
            waves.extend(sub_waves); order.extend(t.task_id for sub in sub_waves for t in sub)
        else:
            if cols := find_wave_write_set_collisions(wave_tasks):
                t1, t2, pa, pb = cols[0]
                raise DagWriteSetCollisionError(f"Parallel write-set collision in Wave {len(waves) + 1}: tasks '{t1}' ({pa!r}) and '{t2}' ({pb!r}) overlap.")
            waves.append(wave_tasks); order.extend(current_wave)
        next_wave = [v for u in current_wave for v in adjacency[u] if (in_degree.__setitem__(v, in_degree[v] - 1) or in_degree[v] == 0)]
        current_wave = sorted(next_wave, key=sort_key)
    if len(order) != len(by_id):
        cycle = _find_cycle_path({tid for tid, deg in in_degree.items() if deg > 0}, dependencies)
        raise DagCycleError(f"Dependency cycle detected: {' -> '.join(cycle)}", cycle=cycle)
    return DagPlan(tasks=by_id, order=tuple(order), waves=waves, adjacency=adjacency, dependencies=dependencies)

def _atomic_write_text(target: Path, content: str) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=str(target.parent))
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content); handle.flush(); os.fsync(handle.fileno())
        os.replace(tmp_path, target)
    except Exception:
        tmp_path.unlink(missing_ok=True); raise

def _norm_agent(agent: str) -> str:
    cleaned = agent.strip().lstrip("@").lower()
    if not cleaned or not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", cleaned):
        raise DagError(f"Invalid agent identifier: {agent!r}.")
    return cleaned
def _validate_ticket_path(ticket_path: Path, inbox_root: Path | None = None) -> None:
    if ticket_path.is_symlink() or ticket_path.parent.is_symlink():
        raise DagError(f"Symlink ticket paths are forbidden: '{ticket_path}'.")
    if inbox_root is not None:
        base, resolved = inbox_root.resolve(), ticket_path.resolve()
        if not resolved.is_relative_to(base) or resolved == base:
            raise DagError(f"Ticket path '{ticket_path}' escapes inbox root '{inbox_root}'.")
def _validate_target_state(new_state: str) -> str:
    if not (target := _norm_status(new_state)) or target not in VALID_INBOX_STATES:
        raise DagError(f"Invalid target inbox state: {new_state!r}.")
    return target

def _load_task_for_transition(tasks_path: Path, task_id: str, target_state: str) -> tuple[DagPlan, DagTask]:
    plan = build_and_validate_dag(parse_tasks_markdown(tasks_path))
    if (norm_id := _norm_task_id(task_id)) not in plan.tasks:
        raise DagError(f"Task '{norm_id}' not found in '{tasks_path}'.")
    task = plan.tasks[norm_id]
    if target_state in {"in_progress", "done"}:
        if unmet := [f"{d} ({plan.tasks[d].status})" for d in task.depends_on if plan.tasks[d].status != "done"]:
            raise DagError(f"Cannot transition '{task.task_id}' to '{target_state}': upstream dependencies in '{tasks_path.name}' are not done: {', '.join(unmet)}.")
    return plan, task

def _mark_task_done_in_markdown(tasks_path: Path, task: DagTask) -> None:
    lines = tasks_path.read_text(encoding="utf-8").lstrip("\ufeff").splitlines(keepends=True)
    if not (1 <= task.line_no <= len(lines)):
        raise DagError(f"Task '{task.task_id}' line {task.line_no} out of range in '{tasks_path}'.")
    line = lines[task.line_no - 1]
    updated = re.sub(r"\[[ ~>!xX]\]", "[x]", line, count=1) if re.search(r"\[[ xX~>!]\]", line) else re.sub(r"^([ \t]*(?:[-*+]|\d+\.|#{2,6})[ \t]+)", r"\1[x] ", line, count=1)
    if updated != line:
        lines[task.line_no - 1] = updated; _atomic_write_text(tasks_path, "".join(lines))

def _render_ticket(task: DagTask, agent: str, state: str, tasks_path: Path, note: str | None = None) -> str:
    now = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    lines = [
        f"# {task.task_id}: {task.title}", "", f"- **Task ID**: {task.task_id}", f"- **Tasks File**: {tasks_path.as_posix()}",
        f"- **Agente Asignado**: @{agent}", f"- **Estado**: {state}", f"- **Dependencias**: {', '.join(task.depends_on) or 'None'}", f"- **Updated**: {now}",
    ]
    return "\n".join([*lines, f"- **Note**: {note}"] if note else lines) + "\n"

def _rewrite_ticket(content: str, new_state: str, note: str | None = None) -> str:
    now, out, seen = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), [], set()
    for line in content.replace("\r\n", "\n").split("\n"):
        if m := _TICKET_FIELD_RE.match(line):
            key = m.group("key").lower()
            if key in {"estado", "status"} and "state" not in seen:
                out.append(f"{m.group(1)}{new_state}"); seen.add("state"); continue
            if key == "updated":
                out.append(f"{m.group(1)}{now}"); seen.add("updated"); continue
            if key == "note" and note is not None:
                out.append(f"{m.group(1)}{note}"); seen.add("note"); continue
        out.append(line)
    if "updated" not in seen:
        out.append(f"- **Updated**: {now}")
    if note is not None and "note" not in seen:
        out.append(f"- **Note**: {note}")
    return "\n".join(out).rstrip("\n") + "\n"

def update_inbox_ticket(
    ticket_path: Path, new_state: str, *, tasks_path: Path | None = None, task_id: str | None = None,
    note: str | None = None, inbox_root: Path | None = None, sync_tasks_md: bool = True,
) -> InboxTicket:
    """Validate and atomically transition an existing inbox ticket file."""
    target_state = _validate_target_state(new_state)
    _validate_ticket_path(ticket_path, inbox_root)
    if not ticket_path.is_file():
        raise DagError(f"Inbox ticket not found: '{ticket_path}'.")
    try:
        content = ticket_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise DagError(f"Cannot read inbox ticket '{ticket_path}': {exc}") from exc
    meta = {m.group(1).strip().lower(): m.group(2).strip() for line in content.splitlines() if (m := _TICKET_META_RE.match(line))}
    raw_state = meta.get("estado") or meta.get("status")
    current_state = _norm_status(raw_state) if raw_state else None
    if not current_state or current_state not in VALID_INBOX_STATES:
        raise DagError(f"Inbox ticket '{ticket_path.name}' has missing or invalid Estado/Status: {raw_state!r}.")
    if target_state not in ALLOWED_TRANSITIONS[current_state]:
        raise DagError(f"Invalid state transition '{current_state}' -> '{target_state}' for '{ticket_path.name}'.")
    resolved_task_id = _norm_task_id(task_id or meta.get("task id") or meta.get("task") or ticket_path.stem)
    resolved_tasks = tasks_path or (Path(meta["tasks file"]) if "tasks file" in meta else None)
    agent = _norm_agent(meta.get("agente asignado") or meta.get("agent") or ticket_path.parent.name)
    deps, task_obj = (), None
    if resolved_tasks is not None:
        if not resolved_tasks.is_absolute() and not resolved_tasks.exists():
            resolved_tasks = next((cand for anc in ticket_path.resolve().parents if (cand := anc / resolved_tasks).is_file()), resolved_tasks)
        _, task_obj = _load_task_for_transition(resolved_tasks, resolved_task_id, target_state)
        deps = task_obj.depends_on
    elif target_state in {"in_progress", "done"}:
        raise DagError(f"Cannot transition '{resolved_task_id}' to '{target_state}' without a 03-tasks.md file.")
    _atomic_write_text(ticket_path, _rewrite_ticket(content, target_state, note=note))
    if target_state == "done" and sync_tasks_md and resolved_tasks is not None and task_obj is not None:
        _mark_task_done_in_markdown(resolved_tasks, task_obj)
    return InboxTicket(resolved_task_id, agent, target_state, current_state, ticket_path, deps)

def advance_inbox_task(
    tasks_path: Path, task_id: str, new_state: str, *, agent: str | None = None, inbox_root: Path | None = None,
    ticket_path: Path | None = None, note: str | None = None, sync_tasks_md: bool = True,
) -> InboxTicket:
    """Enforce DAG dependencies and advance a task's inbox ticket state atomically."""
    target_state = _validate_target_state(new_state)
    _, task = _load_task_for_transition(tasks_path, task_id, target_state)
    chosen_agent = _norm_agent(agent or task.owner or "")
    if not re.fullmatch(r"[A-Za-z0-9._-]+", task.task_id):
        raise DagError(f"Unsafe task ID for ticket filename: {task.task_id!r}.")
    root = inbox_root or next((p / ".agent-inbox" for p in tasks_path.resolve().parents if (p / ".agent-inbox").is_dir() or (p / ".git").exists()), ROOT_DIR / ".agent-inbox")
    target_ticket = ticket_path or (root / chosen_agent / f"{task.task_id}.md")
    _validate_ticket_path(target_ticket, root)
    if not target_ticket.exists():
        if target_state == "done":
            raise DagError(f"Invalid state transition 'pending' -> 'done' for '{task.task_id}': must pass through 'in_progress'.")
        _atomic_write_text(target_ticket, _render_ticket(task, chosen_agent, target_state, tasks_path, note=note))
        return InboxTicket(task.task_id, chosen_agent, target_state, "pending", target_ticket, task.depends_on)
    return update_inbox_ticket(target_ticket, target_state, tasks_path=tasks_path, task_id=task.task_id, note=note, inbox_root=root, sync_tasks_md=sync_tasks_md)

def format_dag_plan(plan: DagPlan, as_json: bool = False) -> str:
    """Format a validated DagPlan as text waves or deterministic JSON."""
    if as_json:
        return json.dumps({
            "task_count": len(plan.tasks), "wave_count": len(plan.waves), "order": list(plan.order),
            "waves": [[t.task_id for t in wave] for wave in plan.waves],
            "dependencies": {k: list(v) for k, v in plan.dependencies.items()},
            "adjacency": {k: list(v) for k, v in plan.adjacency.items()},
        }, indent=2)
    lines = [f"DAG OK: {len(plan.tasks)} task(s) across {len(plan.waves)} wave(s)."]
    for idx, wave in enumerate(plan.waves, start=1):
        lines.append(f"  Wave {idx}: " + ", ".join(f"{t.task_id}{f' (@{t.owner})' if t.owner else ''}" for t in wave))
    return "\n".join(lines)

def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate and plan SDD 03-tasks.md DAGs.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--verify", type=Path, help="Verify acyclicity and dependencies of a 03-tasks.md file.")
    group.add_argument("--plan", type=Path, help="Print deterministic execution waves for a 03-tasks.md file.")
    parser.add_argument("--auto-split", action="store_true", help="Split parallel waves with colliding target_paths into sequential sub-waves.")
    parser.add_argument("--format", choices=("text", "json"), default="text", help="Output format.")
    args = parser.parse_args(argv)
    target = args.verify or args.plan
    try:
        if not target.is_file():
            raise DagError(f"Tasks file does not exist: '{target}'.")
        if not (tasks := parse_tasks_markdown(target)):
            raise DagError(f"No structured DAG tasks found in '{target}'.")
        plan = build_and_validate_dag(tasks, auto_split_waves=args.auto_split)
    except DagError as exc:
        print(f"[DAG ERROR] {exc}", file=sys.stderr)
        return 1
    print(format_dag_plan(plan, as_json=(args.format == "json")))
    return 0

if __name__ == "__main__":
    sys.exit(main())
