#!/usr/bin/env python3
"""
Guardia de Gate S0 (Stack Lock, legacy Gate 00): Bloqueo de Stack Tecnológico
Comprueba que specs/STACK.md exista, sea un fichero regular seguro y contenga
el sign-off humano formal fuera de comentarios HTML o bloques de código.
"""

from __future__ import annotations

import os
import pathlib
import re
import stat
import sys

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

ACCEPTED_STACK_MARKERS: tuple[str, ...] = (
    "[x] Gate S0 Approved",
    "[X] Gate S0 Approved",
    "[x] Gate 00 Approved",
    "[X] Gate 00 Approved",
)

_OPEN_FENCE_RE = re.compile(r"^[ \t]*(`{3,}|~{3,})(.*)$")
_HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
_UNCLOSED_COMMENT_RE = re.compile(r"<!--.*$", re.DOTALL)


def is_link_or_junction(path: pathlib.Path) -> bool:
    """Return True if path is a symlink or Windows NTFS junction/reparse link."""
    if path.is_symlink():
        return True
    is_junc = getattr(os.path, "isjunction", None)
    if callable(is_junc) and is_junc(path):
        return True
    try:
        st = os.lstat(path)
    except FileNotFoundError:
        return False
    except NotADirectoryError:
        return False
    tag = getattr(st, "st_reparse_tag", 0)
    mount_tag = getattr(stat, "IO_REPARSE_TAG_MOUNT_POINT", 0xA0000003)
    sym_tag = getattr(stat, "IO_REPARSE_TAG_SYMLINK", 0xA000000C)
    return tag in (mount_tag, sym_tag)


def strip_non_normative_markdown(content: str) -> str:
    """Strip fenced code blocks and HTML comments from markdown text."""
    normalized = content.replace("\r\n", "\n").replace("\r", "\n")
    kept_lines: list[str] = []
    fence_char: str | None = None
    fence_len = 0

    for line in normalized.split("\n"):
        if fence_char is not None:
            close_pat = rf"^[ \t]*{re.escape(fence_char)}{{{fence_len},}}[ \t]*$"
            if re.match(close_pat, line):
                fence_char = None
                fence_len = 0
            continue

        match = _OPEN_FENCE_RE.match(line)
        if match:
            marker, info = match.group(1), match.group(2)
            if not (marker[0] == "`" and "`" in info):
                fence_char = marker[0]
                fence_len = len(marker)
                continue
        kept_lines.append(line)

    without_fences = "\n".join(kept_lines)
    without_comments = _HTML_COMMENT_RE.sub("", without_fences)
    return _UNCLOSED_COMMENT_RE.sub("", without_comments)


def check_stack_gate(repo_root: pathlib.Path) -> tuple[bool, str]:
    """Validate specs/STACK.md exists, is safe, and contains an active Gate S0 sign-off."""
    try:
        specs_dir = repo_root / "specs"
        if specs_dir.exists() and is_link_or_junction(specs_dir):
            return False, "Gate S0 LOCKED: El directorio specs/ no puede ser un symlink o junction."

        stack_file = specs_dir / "STACK.md"
        if is_link_or_junction(stack_file):
            return False, "Gate S0 LOCKED: specs/STACK.md no puede ser un symlink o junction."
        if not stack_file.exists():
            return False, "Gate S0 LOCKED: Falta el fichero specs/STACK.md."
        if not stack_file.is_file():
            return False, "Gate S0 LOCKED: specs/STACK.md no es un fichero regular."

        content = stack_file.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return False, f"Gate S0 LOCKED: No se pudo leer specs/STACK.md de forma segura ({exc})."

    normative = strip_non_normative_markdown(content)
    if not any(marker in normative for marker in ACCEPTED_STACK_MARKERS):
        return False, (
            "Gate S0 LOCKED: specs/STACK.md no cuenta con la firma de aprobacion humana "
            "([x] Gate S0 Approved o [x] Gate 00 Approved legacy).\n"
            "Define el stack tecnico con el @orchestrator y solicita la aprobacion del usuario antes de crear codigo."
        )
    return True, "Gate S0 OK"


def main() -> int:
    try:
        root = pathlib.Path(__file__).resolve().parent.parent.parent
        ok, msg = check_stack_gate(root)
    except Exception as exc:
        print(f"[BLOQUEO GATE S0] Error inesperado verificando Gate S0: {exc}", file=sys.stderr)
        return 1

    if not ok:
        print(f"[BLOQUEO GATE S0] {msg}", file=sys.stderr)
        return 1
    print(f"[OK] {msg}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
