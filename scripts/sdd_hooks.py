#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SDD Git Hooks Validator (sdd_hooks.py)
======================================
Validador determinista multiplataforma para hooks nativos de Git (.githooks).
Asegura la gobernanza de ramas (RN-SDD-BRANCH-SYNC), inmutabilidad de features
Done (RN-SDD-IMMUTABLE-DONE), límites de fichero y ausencia de secretos.
"""

import io
import os
import pathlib
import posixpath
import re
import subprocess
import sys

def _configure_stdio_utf8() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                if (getattr(stream, "encoding", "") or "").lower() != "utf-8":
                    reconfigure(encoding="utf-8", errors="replace")
            except (AttributeError, OSError, ValueError, io.UnsupportedOperation):
                pass


_configure_stdio_utf8()

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent

# Patrones de secretos conocidos
SECRET_PATTERNS = [
    (re.compile(r"ghp_[A-Za-z0-9_]{36}"), "GitHub Personal Access Token (Classic)"),
    (re.compile(r"github_pat_[A-Za-z0-9_]{82}"), "GitHub Fine-Grained Token"),
    (re.compile(r"AKIA[0-9A-Z]{16}"), "AWS Access Key ID"),
    (re.compile(r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----"), "Private Key PEM block"),
]

# Marcadores de conflicto Git
CONFLICT_PATTERNS = [
    re.compile(r"^<<<<<<< ", re.MULTILINE),
    re.compile(r"^=======$", re.MULTILINE),
    re.compile(r"^>>>>>>> ", re.MULTILINE),
]

SKIP_CONTENT_SUFFIXES = {".png", ".jpg", ".jpeg", ".ico", ".pdf", ".lock", ".jsonl", ".pyc"}
SHA_RE = re.compile(r"^[0-9a-fA-F]{40,64}$")
DONE_STATUS_RE = re.compile(r"^`?(?:Done|Completado|Completed)(?:\s*/\s*(?:Done|Completado|Completed))?`?$", re.IGNORECASE)
FEAT_ID_CELL_RE = re.compile(r"^`?(FEAT-\d{3,4})`?$", re.IGNORECASE)
DONE_SECTION_RE = re.compile(
    r"####\s+`?(FEAT-\d{3,4})`?[^\n]*\n(?:-[^\n]*\n){0,3}?-\s+\*\*Estado:\*\*\s+`?(?:Completed|Completado|Done)",
    re.IGNORECASE,
)
DONE_FEATURE_PATH_RE = re.compile(r"^specs/features/(FEAT-\d{3,4})(?![0-9])(?:[^/]*)(?:/|$)", re.IGNORECASE)


def _is_junction(path: pathlib.Path) -> bool:
    isjunction = getattr(os.path, "isjunction", None)
    return bool(isjunction(path)) if callable(isjunction) else False


def _run_git(args: list[str], cwd: pathlib.Path | None = None) -> subprocess.CompletedProcess[str]:
    target_cwd = cwd or ROOT_DIR
    return subprocess.run(
        ["git", "-c", "core.quotePath=false", *args],
        cwd=str(target_cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def parse_done_features_from_text(content: str) -> set[str]:
    """Extrae los IDs FEAT-XXX marcados como Done/Completado/Completed en BACKLOG.md."""
    done_features: set[str] = set()
    for raw_line in content.splitlines():
        stripped = raw_line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) < 2:
            continue
        feat_match = FEAT_ID_CELL_RE.match(cells[0])
        if feat_match and DONE_STATUS_RE.match(cells[-1]):
            done_features.add(feat_match.group(1).upper())

    for match in DONE_SECTION_RE.finditer(content):
        done_features.add(match.group(1).upper())

    return done_features


def _get_done_features_at_rev(repo_root: pathlib.Path, rev: str) -> set[str]:
    exists_res = _run_git(["cat-file", "-e", f"{rev}:specs/BACKLOG.md"], cwd=repo_root)
    if exists_res.returncode != 0:
        return set()
    show_res = _run_git(["show", f"{rev}:specs/BACKLOG.md"], cwd=repo_root)
    if show_res.returncode != 0:
        raise RuntimeError(f"No se pudo leer {rev}:specs/BACKLOG.md: {show_res.stderr.strip()}")
    return parse_done_features_from_text(show_res.stdout)


def get_done_features(repo_root: pathlib.Path | None = None) -> set[str]:
    """Obtiene el conjunto de features Done desde specs/BACKLOG.md y HEAD:specs/BACKLOG.md."""
    root = repo_root or ROOT_DIR
    repo_resolved = root.resolve(strict=False)
    done_features: set[str] = set()

    backlog_path = root / "specs" / "BACKLOG.md"
    if backlog_path.exists() or backlog_path.is_symlink() or _is_junction(backlog_path):
        resolved_backlog = backlog_path.resolve(strict=False)
        if not resolved_backlog.is_relative_to(repo_resolved):
            raise RuntimeError(f"specs/BACKLOG.md apunta fuera del repositorio: {resolved_backlog}")
        content = backlog_path.read_text(encoding="utf-8", errors="strict")
        done_features |= parse_done_features_from_text(content)

    if (root / ".git").exists():
        head_res = _run_git(["rev-parse", "--verify", "--quiet", "HEAD"], cwd=root)
        if head_res.returncode == 0:
            done_features |= _get_done_features_at_rev(root, "HEAD")

    return done_features


def _find_immutable_done_violation(rel_posix: str, done_features: set[str]) -> str | None:
    if not done_features:
        return None
    normalized = posixpath.normpath(rel_posix.replace("\\", "/")).lstrip("./")
    match = DONE_FEATURE_PATH_RE.match(normalized)
    if not match:
        return None
    feat_id = match.group(1).upper()
    if feat_id in done_features:
        return feat_id
    return None


def get_staged_files() -> list[pathlib.Path]:
    """Retorna los archivos preparados en staging (ACMR). Falla cerrado si git diff falla."""
    res = _run_git(["diff", "--cached", "--name-only", "--diff-filter=ACMR"], cwd=ROOT_DIR)
    if res.returncode != 0:
        err = res.stderr.strip() or res.stdout.strip() or f"exit code {res.returncode}"
        raise RuntimeError(f"git diff --cached falló ({res.returncode}): {err}")
    lines = [line.strip() for line in res.stdout.splitlines() if line.strip()]
    return [ROOT_DIR / line for line in lines]


def get_staged_all_paths() -> list[pathlib.Path]:
    """Retorna todas las rutas cambiadas en staging (incluyendo borrados y renombrados)."""
    res = _run_git(["diff", "--cached", "--name-only", "--no-renames"], cwd=ROOT_DIR)
    if res.returncode != 0:
        err = res.stderr.strip() or res.stdout.strip() or f"exit code {res.returncode}"
        raise RuntimeError(f"git diff --cached --no-renames falló ({res.returncode}): {err}")
    lines = [line.strip() for line in res.stdout.splitlines() if line.strip()]
    return [ROOT_DIR / line for line in lines]


def validate_pre_commit() -> int:
    """Ejecuta las validaciones previas al commit con política fail-closed."""
    print("--- [HOOK SDD] Ejecutando pre-commit hook ---")
    try:
        staged_files = get_staged_files()
        all_staged_paths = get_staged_all_paths() if (ROOT_DIR / ".git").exists() else list(staged_files)

        if not staged_files and not all_staged_paths:
            print("[HOOK SDD] No hay ficheros en staging.")
            return 0

        repo_resolved = ROOT_DIR.resolve(strict=False)
        done_features = get_done_features(ROOT_DIR)
        errors = 0

        # Validar RN-SDD-IMMUTABLE-DONE y contención en todas las rutas en staging (incl. D/R)
        seen_paths: set[pathlib.Path] = set()
        for path_obj in [*all_staged_paths, *staged_files]:
            if path_obj in seen_paths:
                continue
            seen_paths.add(path_obj)
            try:
                rel_path = path_obj.relative_to(ROOT_DIR)
            except ValueError as exc:
                print(f"[ERROR SDD] Ruta en staging fuera de la raíz del repositorio ({path_obj}): {exc}")
                errors += 1
                continue

            violated_feat = _find_immutable_done_violation(rel_path.as_posix(), done_features)
            if violated_feat:
                print(
                    f"[ERROR SDD] Violación RN-SDD-IMMUTABLE-DONE: '{rel_path.as_posix()}' pertenece a "
                    f"'{violated_feat}' marcado como Done en specs/BACKLOG.md. Usa un CR en specs/changes/."
                )
                errors += 1

            if path_obj.exists() or path_obj.is_symlink() or _is_junction(path_obj):
                resolved = path_obj.resolve(strict=False)
                if not resolved.is_relative_to(repo_resolved):
                    print(f"[ERROR SDD] Ruta en staging apunta fuera del repositorio: {rel_path}")
                    errors += 1
                else:
                    resolved_rel = resolved.relative_to(repo_resolved).as_posix()
                    violated_resolved = _find_immutable_done_violation(resolved_rel, done_features)
                    if violated_resolved and violated_resolved != violated_feat:
                        print(
                            f"[ERROR SDD] Violación RN-SDD-IMMUTABLE-DONE (destino resuelto): "
                            f"'{resolved_rel}' pertenece a '{violated_resolved}' marcado como Done."
                        )
                        errors += 1

        for file_path in staged_files:
            try:
                rel_path = file_path.relative_to(ROOT_DIR)
            except ValueError:
                continue

            # Omitir archivos binarios, imágenes, lockfiles pesados y logs (tras validar inmutabilidad)
            if rel_path.suffix.lower() in SKIP_CONTENT_SUFFIXES:
                continue

            if file_path.is_dir() or not file_path.exists():
                print(f"[ERROR SDD] Fichero en staging no existe o es directorio inaccesible: {rel_path}")
                errors += 1
                continue

            try:
                content = file_path.read_text(encoding="utf-8", errors="strict")
            except Exception as exc:
                print(f"[ERROR SDD] No se pudo leer el fichero en staging {rel_path}: {exc}")
                errors += 1
                continue

            # 1. Verificar marcadores de conflicto Git
            for pat in CONFLICT_PATTERNS:
                if pat.search(content):
                    print(f"[ERROR SDD] Marcador de conflicto Git detectado en: {rel_path}")
                    errors += 1
                    break

            # 2. Verificar secretos expuestos
            for pat, desc in SECRET_PATTERNS:
                if pat.search(content):
                    print(f"[ERROR SDD] Posible secreto expuesto ({desc}) en: {rel_path}")
                    errors += 1

            # 3. Verificar límite de 800 líneas en código fuente y especificaciones
            lines_count = len(content.splitlines())
            rel_posix = rel_path.as_posix()
            is_source_or_rule = (
                rel_posix.startswith("src/")
                or rel_posix.startswith(".agents/rules/")
                or rel_posix.startswith(".agents/agents/")
                or (rel_posix.startswith("specs/") and rel_posix != "specs/STACK.md")
            )
            if is_source_or_rule and lines_count > 800:
                print(f"[ERROR SDD] {rel_path} supera el límite de 800 líneas ({lines_count} líneas). Divide la responsabilidad.")
                errors += 1

        # 4. Ejecutar Healthcheck de gobernanza SDD
        healthcheck_script = ROOT_DIR / ".agents" / "scripts" / "sdd_healthcheck.py"
        if healthcheck_script.exists():
            hc_res = subprocess.run([sys.executable, str(healthcheck_script)], cwd=str(ROOT_DIR))
            if hc_res.returncode != 0:
                print("[ERROR SDD] Healthcheck falló. Resuelve las advertencias o errores antes de comitear.")
                errors += 1

        if errors > 0:
            print(f"\n[RECHAZADO] Pre-commit cancelado por {errors} error(es) de gobernanza SDD.")
            return 1

        print("[APROBADO] Pre-commit validado con éxito.")
        return 0
    except Exception as exc:
        print(f"[ERROR SDD] Fallo inesperado en pre-commit (fail-closed): {exc}")
        return 1


def _git_object_exists(repo_root: pathlib.Path, rev: str) -> bool:
    res = _run_git(["cat-file", "-e", rev], cwd=repo_root)
    return res.returncode == 0


def _collect_pushed_commits(repo_root: pathlib.Path, local_sha: str, remote_sha: str) -> tuple[list[str], bool]:
    if int(remote_sha, 16) != 0 and _git_object_exists(repo_root, remote_sha):
        res = _run_git(["rev-list", f"{remote_sha}..{local_sha}"], cwd=repo_root)
        if res.returncode != 0:
            raise RuntimeError(f"git rev-list falló ({res.returncode}): {res.stderr.strip()}")
        return [c.strip() for c in res.stdout.splitlines() if c.strip()], True

    remotes_res = _run_git(["for-each-ref", "--count=1", "refs/remotes/"], cwd=repo_root)
    if remotes_res.returncode != 0:
        raise RuntimeError(f"git for-each-ref falló ({remotes_res.returncode}): {remotes_res.stderr.strip()}")

    has_remotes = bool(remotes_res.stdout.strip())
    rev_args = ["rev-list", local_sha, "--not", "--remotes"] if has_remotes else ["rev-list", local_sha]
    res = _run_git(rev_args, cwd=repo_root)
    if res.returncode != 0:
        raise RuntimeError(f"git rev-list falló ({res.returncode}): {res.stderr.strip()}")
    return [c.strip() for c in res.stdout.splitlines() if c.strip()], has_remotes


def _validate_pushed_commit_immutability(
    repo_root: pathlib.Path,
    commit_sha: str,
    done_at_remote: set[str],
    done_now: set[str],
    has_remote_context: bool,
) -> list[str]:
    violations: list[str] = []
    diff_res = _run_git(["diff-tree", "--no-commit-id", "--name-only", "-r", "--root", commit_sha], cwd=repo_root)
    if diff_res.returncode != 0:
        raise RuntimeError(f"git diff-tree falló para {commit_sha}: {diff_res.stderr.strip()}")

    changed_files = [line.strip() for line in diff_res.stdout.splitlines() if line.strip()]
    if not changed_files:
        return violations

    parents_res = _run_git(["rev-list", "--parents", "-n", "1", commit_sha], cwd=repo_root)
    if parents_res.returncode != 0:
        raise RuntimeError(f"git rev-list --parents falló para {commit_sha}: {parents_res.stderr.strip()}")

    parent_tokens = parents_res.stdout.strip().split()
    done_at_parent: set[str] = set()
    for parent_sha in parent_tokens[1:]:
        done_at_parent |= _get_done_features_at_rev(repo_root, parent_sha)

    effective_done = set(done_at_parent) | set(done_at_remote)
    if has_remote_context and "specs/BACKLOG.md" not in changed_files:
        effective_done |= done_now

    for rel_path in changed_files:
        violated = _find_immutable_done_violation(rel_path, effective_done)
        if violated:
            violations.append(
                f"[ERROR SDD] Violación RN-SDD-IMMUTABLE-DONE en commit {commit_sha[:8]}: "
                f"'{rel_path}' modifica '{violated}' marcado como Done."
            )
    return violations


def validate_pre_push(args: list[str]) -> int:
    """Ejecuta las validaciones previas al push (protección estricta de main e inmutabilidad Done)."""
    print("--- [HOOK SDD] Ejecutando pre-push hook ---")
    try:
        if sys.stdin is None:
            print("[ERROR SDD] stdin no disponible en pre-push (fail-closed).")
            return 1

        stdin_content = sys.stdin.read()
        if not stdin_content.strip():
            # Git invoca `pre-push <remote> <url>` con stdin vacío cuando no hay refs que pushear (up-to-date)
            if len(args) >= 2:
                print("[INFO SDD] Sin refs pendientes por pushear (up-to-date).")
                return 0
            print("[ERROR SDD] stdin vacío en pre-push sin contexto de remoto (fail-closed).")
            return 1

        lines = [line.strip() for line in stdin_content.splitlines() if line.strip()]
        blocked = False
        has_git_repo = (ROOT_DIR / ".git").exists()
        done_now = get_done_features(ROOT_DIR) if has_git_repo else set()

        for line in lines:
            parts = line.split()
            if len(parts) != 4:
                print(f"[ERROR SDD] Línea de ref inválida en pre-push: {line}")
                blocked = True
                continue

            local_ref, local_sha, remote_ref, remote_sha = parts
            if not remote_ref.startswith("refs/"):
                print(f"[ERROR SDD] remote_ref inválido en pre-push: {remote_ref}")
                blocked = True
                continue

            # Bloqueo estricto e incondicional sobre main / master (sin bypass)
            if remote_ref in ("refs/heads/main", "refs/heads/master"):
                print("\n🛑 [BLOQUEO DE GOBERNANZA SDD - RN-SDD-BRANCH-SYNC]")
                print(f"   Intento de push directo a '{remote_ref}' denegado.")
                print("   La rama principal de producción está protegida contra pushes directos.")
                print("   Para integrar cambios en producción:")
                print("     1. Crea una rama 'release/<version>' o 'hotfix/<bug>'")
                print("     2. Abre una Pull Request hacia 'main'")
                print("     3. Requiere sign-off humano explícito y CI verde.\n")
                blocked = True
                continue

            is_delete = local_ref == "(delete)" or (SHA_RE.fullmatch(local_sha) is not None and int(local_sha, 16) == 0)
            if is_delete:
                continue

            if not SHA_RE.fullmatch(local_sha) or not SHA_RE.fullmatch(remote_sha):
                print(f"[ERROR SDD] SHA inválido en línea pre-push: {line}")
                blocked = True
                continue

            if has_git_repo:
                done_at_remote = (
                    _get_done_features_at_rev(ROOT_DIR, remote_sha)
                    if int(remote_sha, 16) != 0 and _git_object_exists(ROOT_DIR, remote_sha)
                    else set()
                )
                commits, has_remote_context = _collect_pushed_commits(ROOT_DIR, local_sha, remote_sha)
                for commit_sha in commits:
                    violations = _validate_pushed_commit_immutability(
                        ROOT_DIR, commit_sha, done_at_remote, done_now, has_remote_context
                    )
                    for msg in violations:
                        print(msg)
                        blocked = True

        if blocked:
            return 1

        print("[APROBADO] Pre-push validado con éxito.")
        return 0
    except Exception as exc:
        print(f"[ERROR SDD] Fallo inesperado en pre-push (fail-closed): {exc}")
        return 1


def main() -> int:
    if len(sys.argv) < 2:
        print("Uso: python sdd_hooks.py [pre-commit | pre-push]")
        return 1

    command = sys.argv[1].lower()
    if command == "pre-commit":
        return validate_pre_commit()
    if command == "pre-push":
        return validate_pre_push(sys.argv[2:])

    print(f"[ERROR] Hook desconocido: {command}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
