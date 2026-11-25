#!/usr/bin/env python3
"""
SDD Catalog Importer & Packager
Fetches upstream components from affaan-m/ecc (MIT License), adapts frontmatter
for SDD agentic governance, and registers them cleanly inside `.sdd/catalog/`.
"""

import argparse
from collections.abc import Callable
import http.client
import json
import os
import pathlib
import re
import sys
from typing import TypedDict
import urllib.error
import urllib.request

RAW_BASE = "https://raw.githubusercontent.com/affaan-m/ecc/main"
REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
CATALOG_DIR = REPO_ROOT / ".sdd" / "catalog"
SPECIALISTS_DIR = CATALOG_DIR / "specialists"
SPECIALISTS_OPTIN_DIR = CATALOG_DIR / "specialists-optin"
PACKS_DIR = CATALOG_DIR / "packs"
DEFAULT_SPECIALISTS: tuple[str, ...] = ("security-reviewer",)
SDD_CUSTOMIZED_SPECIALISTS: frozenset[str] = frozenset({"spec-miner"})

TextFetcher = Callable[[str], str | None]


class PackDefinition(TypedDict):
    """Schema for built-in stack pack declarations in STACK_PACKS."""

    id: str
    family: str
    requires: list[str]
    description: str
    rules: list[str]
    specialists: list[str]
    skills: list[str]
    workflows: list[str]


# Universal specialists that belong to baseline catalog
UNIVERSAL_SPECIALISTS: list[str] = [
    "code-explorer", "spec-miner", "code-architect", "type-design-analyzer", "security-reviewer",
    "silent-failure-hunter", "build-error-resolver", "tdd-guide", "performance-optimizer", "e2e-runner",
    "code-simplifier", "refactor-cleaner", "gan-planner", "gan-generator", "gan-evaluator",
    "conversation-analyzer", "docs-lookup", "pr-test-analyzer", "comment-analyzer", "opensource-sanitizer",
]

# Stack packs definition
STACK_PACKS: dict[str, PackDefinition] = {
    "lang-python": {
        "id": "lang:python",
        "family": "language",
        "requires": [],
        "description": "Python 3.12+ engineering guidance, type safety, asyncio, and pytest patterns.",
        "rules": [f"rules/python/{r}.md" for r in ["coding-style", "hooks", "patterns", "security", "testing"]],
        "specialists": ["agents/python-reviewer.md"],
        "skills": ["skills/python-patterns", "skills/python-testing"],
        "workflows": ["commands/python-review.md"],
    },
    "framework-fastapi": {
        "id": "framework:fastapi",
        "family": "framework",
        "requires": ["lang:python"],
        "description": "FastAPI async REST, WebSockets, SSE, Pydantic v2 DTOs, and dependency injection.",
        "rules": ["rules/python/fastapi.md"],
        "specialists": ["agents/fastapi-reviewer.md"],
        "skills": ["skills/fastapi-patterns"],
        "workflows": ["commands/fastapi-review.md"],
    },
    "framework-django": {
        "id": "framework:django",
        "family": "framework",
        "requires": ["lang:python"],
        "description": "Django ORM, Celery, TDD, security, and verification workflows.",
        "rules": [],
        "specialists": ["agents/django-reviewer.md", "agents/django-build-resolver.md"],
        "skills": ["skills/django-patterns", "skills/django-security", "skills/django-tdd", "skills/django-verification", "skills/django-celery"],
        "workflows": [],
    },
    "lang-typescript": {
        "id": "lang:typescript",
        "family": "language",
        "requires": [],
        "description": "TypeScript strict type design, Node/Bun runtime, and modern tooling.",
        "rules": [f"rules/typescript/{r}.md" for r in ["coding-style", "hooks", "patterns", "security", "testing"]],
        "specialists": ["agents/typescript-reviewer.md"],
        "skills": ["skills/typescript-patterns", "skills/vite-patterns", "skills/bun-runtime"],
        "workflows": [],
    },
    "framework-react": {
        "id": "framework:react",
        "family": "framework",
        "requires": ["lang:typescript"],
        "description": "React 19, hooks, component architecture, Vitest, and performance patterns.",
        "rules": [f"rules/react/{r}.md" for r in ["coding-style", "hooks", "patterns", "security", "testing"]],
        "specialists": ["agents/react-reviewer.md", "agents/react-build-resolver.md"],
        "skills": ["skills/react-patterns", "skills/react-performance", "skills/react-testing", "skills/frontend-patterns"],
        "workflows": ["commands/react-build.md", "commands/react-review.md", "commands/react-test.md"],
    },
    "framework-vue": {
        "id": "framework:vue",
        "family": "framework",
        "requires": ["lang:typescript"],
        "description": "Vue 3 Composition API, Pinia, Vue Router, and Nuxt 4 SSR patterns.",
        "rules": [f"rules/vue/{r}.md" for r in ["coding-style", "hooks", "patterns", "security", "testing"]],
        "specialists": ["agents/vue-reviewer.md"],
        "skills": ["skills/vue-patterns", "skills/nuxt4-patterns", "skills/ui-to-vue"],
        "workflows": ["commands/vue-review.md"],
    },
    "lang-csharp": {
        "id": "lang:csharp",
        "family": "language",
        "requires": [],
        "description": "C# .NET 9, nullable reference types, EF Core, async ValueTask, and xUnit patterns.",
        "rules": [f"rules/csharp/{r}.md" for r in ["coding-style", "hooks", "patterns", "security", "testing"]],
        "specialists": ["agents/csharp-reviewer.md"],
        "skills": ["skills/dotnet-patterns", "skills/csharp-testing"],
        "workflows": [],
    },
    "lang-go": {
        "id": "lang:go",
        "family": "language",
        "requires": [],
        "description": "Idiomatic Go, table-driven tests, goroutine concurrency, and build resolvers.",
        "rules": [f"rules/golang/{r}.md" for r in ["coding-style", "hooks", "patterns", "security", "testing"]],
        "specialists": ["agents/go-reviewer.md", "agents/go-build-resolver.md"],
        "skills": ["skills/golang-patterns", "skills/golang-testing"],
        "workflows": ["commands/go-build.md", "commands/go-review.md", "commands/go-test.md"],
    },
    "lang-rust": {
        "id": "lang:rust",
        "family": "language",
        "requires": [],
        "description": "Rust safety, memory model, cargo workflows, and build resolvers.",
        "rules": [],
        "specialists": ["agents/rust-reviewer.md", "agents/rust-build-resolver.md"],
        "skills": ["skills/rust-patterns", "skills/rust-testing"],
        "workflows": ["commands/rust-build.md", "commands/rust-review.md", "commands/rust-test.md"],
    },
    "lang-java": {
        "id": "lang:java",
        "family": "language",
        "requires": [],
        "description": "Java 21+, Spring Boot, Gradle/Maven, JPA, and verification workflows.",
        "rules": [f"rules/java/{r}.md" for r in ["coding-style", "hooks", "patterns", "security", "testing"]],
        "specialists": ["agents/java-reviewer.md", "agents/java-build-resolver.md"],
        "skills": ["skills/java-coding-standards", "skills/springboot-patterns", "skills/springboot-security", "skills/springboot-tdd", "skills/springboot-verification", "skills/jpa-patterns"],
        "workflows": ["commands/gradle-build.md"],
    },
    "lang-kotlin": {
        "id": "lang:kotlin",
        "family": "language",
        "requires": [],
        "description": "Kotlin, coroutines, flows, Ktor, Exposed, and Compose Multiplatform patterns.",
        "rules": [f"rules/kotlin/{r}.md" for r in ["coding-style", "hooks", "patterns", "security", "testing"]],
        "specialists": ["agents/kotlin-reviewer.md", "agents/kotlin-build-resolver.md"],
        "skills": ["skills/kotlin-patterns", "skills/kotlin-testing", "skills/kotlin-coroutines-flows", "skills/kotlin-ktor-patterns"],
        "workflows": ["commands/kotlin-build.md", "commands/kotlin-review.md", "commands/kotlin-test.md"],
    },
    "lang-swift": {
        "id": "lang:swift",
        "family": "language",
        "requires": [],
        "description": "Swift 6+, SwiftUI, Actor concurrency, protocols, and iOS engineering.",
        "rules": [],
        "specialists": ["agents/swift-reviewer.md", "agents/swift-build-resolver.md"],
        "skills": ["skills/swiftui-patterns", "skills/swift-concurrency-6-2", "skills/swift-actor-persistence", "skills/swift-protocol-di-testing"],
        "workflows": [],
    },
    "lang-dart": {
        "id": "lang:dart",
        "family": "language",
        "requires": [],
        "description": "Dart & Flutter state management, widget testing, and build resolvers.",
        "rules": [],
        "specialists": ["agents/flutter-reviewer.md", "agents/dart-build-resolver.md"],
        "skills": ["skills/dart-flutter-patterns", "skills/flutter-dart-code-review"],
        "workflows": ["commands/flutter-build.md", "commands/flutter-review.md", "commands/flutter-test.md"],
    },
    "lang-cpp": {
        "id": "lang:cpp",
        "family": "language",
        "requires": [],
        "description": "C++ 20 standards, memory safety, RAII, and testing patterns.",
        "rules": [],
        "specialists": ["agents/cpp-reviewer.md", "agents/cpp-build-resolver.md"],
        "skills": ["skills/cpp-coding-standards", "skills/cpp-testing"],
        "workflows": ["commands/cpp-build.md", "commands/cpp-review.md", "commands/cpp-test.md"],
    },
    "capability-database": {
        "id": "capability:database",
        "family": "capability",
        "requires": [],
        "description": "Relational and vector database modeling, migrations, and performance.",
        "rules": [],
        "specialists": ["agents/database-reviewer.md"],
        "skills": ["skills/database-migrations", "skills/postgres-patterns", "skills/mysql-patterns", "skills/redis-patterns", "skills/clickhouse-io", "skills/prisma-patterns"],
        "workflows": [],
    },
    "capability-devops": {
        "id": "capability:devops",
        "family": "capability",
        "requires": [],
        "description": "Containerization, Kubernetes, deployment patterns, and healthchecks.",
        "rules": [],
        "specialists": [],
        "skills": ["skills/docker-patterns", "skills/kubernetes-patterns", "skills/deployment-patterns", "skills/canary-watch"],
        "workflows": [],
    },
    "capability-web-frontend": {
        "id": "capability:web-frontend",
        "family": "capability",
        "requires": [],
        "description": "Web frontend quality: accessibility (WCAG 2.1 AA), design systems, SEO, and browser QA.",
        "rules": [f"rules/web/{r}.md" for r in ["coding-style", "design-quality", "hooks", "patterns", "performance", "security", "testing"]],
        "specialists": ["agents/a11y-architect.md", "agents/seo-specialist.md"],
        "skills": ["skills/accessibility", "skills/frontend-a11y", "skills/design-system", "skills/browser-qa", "skills/make-interfaces-feel-better", "skills/motion-foundations", "skills/i18n-sync"],
        "workflows": [],
    },
    "capability-ai-llm": {
        "id": "capability:ai-llm",
        "family": "capability",
        "requires": [],
        "description": "AI/LLM pipelines, RAG evaluation, prompt caching, MCP server patterns, and ML lifecycle.",
        "rules": [],
        "specialists": ["agents/rag-pipeline-reviewer.md", "agents/mle-reviewer.md", "agents/pytorch-build-resolver.md"],
        "skills": ["skills/cost-aware-llm-pipeline", "skills/prompt-optimizer", "skills/prompt-caching-strategy", "skills/eval-harness", "skills/ai-regression-testing", "skills/iterative-retrieval", "skills/mcp-server-patterns", "skills/pytorch-patterns", "skills/mle-workflow"],
        "workflows": [],
    },
}


def fetch_text(rel_url: str) -> str | None:
    """Download a UTF-8 text asset relative to RAW_BASE, logging transport failures."""
    url = f"{RAW_BASE}/{rel_url.lstrip('/')}"
    req = urllib.request.Request(url, headers={"User-Agent": "sdd-agentic-starter-catalog-importer/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read().decode("utf-8")
    except (urllib.error.URLError, http.client.HTTPException, TimeoutError, OSError, UnicodeDecodeError, ValueError) as exc:
        print(f"  -> [WARN] Error descargando '{url}': {exc}", file=sys.stderr)
        return None


def _safe_target(parent_dir: pathlib.Path, filename: str) -> pathlib.Path:
    """Resolve filename and enforce strict containment inside parent_dir."""
    if not filename or filename in {".", ".."}:
        raise ValueError(f"Nombre de fichero invalido en catalogo: {filename!r}")
    base = parent_dir.resolve()
    target = (base / filename).resolve()
    if not target.is_relative_to(base):
        raise ValueError(f"Ruta fuera de '{base}': {target}")
    return target


def _fetch_or_warn(fetcher: TextFetcher, label: str, rel_path: str, warnings: list[str]) -> str | None:
    """Fetch rel_path via fetcher and record an explicit [WARN] if it returns None."""
    txt = fetcher(rel_path)
    if txt is None:
        warn = f"[WARN] {label}: no se pudo descargar '{rel_path}'"
        print(f"  -> {warn}")
        warnings.append(warn)
    return txt


def _import_flat_assets(
    fetcher: TextFetcher, pack_dir: pathlib.Path, pack_dir_name: str,
    subdir_name: str, entries: list[str], warnings: list[str],
) -> None:
    """Download flat pack assets (rules/workflows), creating subdir_name only when non-empty."""
    if not entries:
        return
    target_dir = pack_dir / subdir_name
    target_dir.mkdir(parents=True, exist_ok=True)
    for entry in entries:
        txt = _fetch_or_warn(fetcher, f"({pack_dir_name}) {subdir_name}", entry, warnings)
        if txt is not None:
            _safe_target(target_dir, pathlib.Path(entry).name).write_text(txt, encoding="utf-8")


def adapt_agent_frontmatter(agent_name: str, content: str, read_only: bool = True) -> str:
    """Ensures consistent SDD Subagent frontmatter while preserving original Prompt Defense & Body."""
    match_desc = re.search(r"description:\s*(.+)", content)
    desc = match_desc.group(1).strip() if match_desc else f"Especialista ECC en auditoria y resolucion tecnica: {agent_name}."
    body = content.split("---", 2)[2].lstrip() if content.startswith("---") and len(content.split("---", 2)) >= 3 else content
    tools_block = "  bash: true\n  write: false\n  edit: false" if read_only else "  bash: true\n  write: true\n  edit: true"
    return (
        f"---\nname: {agent_name}\ndescription: {desc}\nmode: subagent\ntools:\n{tools_block}\n---\n\n"
        f"<!-- Sourced from upstream affaan-m/ecc (MIT License, Copyright 2026 Affaan Mustafa) -->\n\n{body}\n"
    )


def import_specialists(
    fetcher: TextFetcher = fetch_text,
    specialists_dir: pathlib.Path = SPECIALISTS_DIR,
    optin_dir: pathlib.Path | None = None,
    overwrite_sdd_custom: bool = False,
) -> list[str]:
    """Import universal ECC specialists into default and opt-in catalog directories."""
    warnings: list[str] = []
    specialists_dir.mkdir(parents=True, exist_ok=True)
    resolved_optin = optin_dir if optin_dir is not None else (SPECIALISTS_OPTIN_DIR if specialists_dir == SPECIALISTS_DIR else specialists_dir)
    resolved_optin.mkdir(parents=True, exist_ok=True)
    print(f"\n[+] Importando Especialistas Universales ECC a {specialists_dir} (opt-in: {resolved_optin})...")
    for name in UNIVERSAL_SPECIALISTS:
        dest_dir = specialists_dir if name in DEFAULT_SPECIALISTS else resolved_optin
        target = _safe_target(dest_dir, f"{name}.md")
        if name in SDD_CUSTOMIZED_SPECIALISTS and target.exists() and not overwrite_sdd_custom:
            print(f"  -> [SKIP-SDD] Preservando especialista adaptado a SDD: {dest_dir.name}/{name}.md")
            continue
        content = _fetch_or_warn(fetcher, f"specialist '{name}'", f"agents/{name}.md", warnings)
        if content is None:
            continue
        read_only = name not in {"build-error-resolver", "code-simplifier", "refactor-cleaner"}
        target.write_text(adapt_agent_frontmatter(name, content, read_only=read_only), encoding="utf-8")
        print(f"  -> [OK] Guardado especialista: {dest_dir.name}/{name}.md")
    return warnings


def _is_link(path: pathlib.Path) -> bool:
    """Return True if path is a symlink or Windows directory junction."""
    is_junc = getattr(os.path, "isjunction", None)
    return path.is_symlink() or (callable(is_junc) and bool(is_junc(path)))


def _require_str_list(value: object, field: str, prev_path: pathlib.Path) -> list[str]:
    """Fail-closed validation for a list of non-empty, non-whitespace strings."""
    if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
        raise ValueError(f"Campo '{field}' invalido en {prev_path}: se esperaba list[str] no vacios.")
    return list(value)


def _merge_prev_pack_manifest(
    pack_dir: pathlib.Path, meta: PackDefinition
) -> tuple[list[str], list[str] | None]:
    """Fail-closed merge of extra SDD skills and upstream.references from an existing pack.json."""
    skills = list(meta["skills"])
    prev_path = pack_dir / "pack.json"
    if not prev_path.exists():
        return skills, None
    try:
        prev = json.loads(prev_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"pack.json previo invalido en {prev_path}: {exc}") from exc
    if not isinstance(prev, dict):
        raise ValueError(f"La raiz de {prev_path} debe ser un objeto JSON.")
    prev_skills = _require_str_list(prev.get("skills"), "skills", prev_path)
    prev_refs: list[str] | None = None
    if "upstream" in prev:
        prev_up = prev["upstream"]
        if not isinstance(prev_up, dict):
            raise ValueError(f"Campo 'upstream' invalido en {prev_path}: se esperaba dict.")
        if "references" in prev_up:
            prev_refs = _require_str_list(prev_up["references"], "upstream.references", prev_path)

    pack_root = pack_dir.resolve()
    if _is_link(pack_dir):
        raise ValueError(f"Symlink/junction no permitido en pack_dir: {pack_dir}")
    meta_skills = set(meta["skills"])
    for s in prev_skills:
        if s in meta_skills:
            continue
        rel = pathlib.Path(s)
        posix_parts = pathlib.PurePosixPath(s.replace("\\", "/")).parts
        if rel.is_absolute() or bool(rel.drive) or s.startswith(("/", "\\")) or ".." in posix_parts:
            raise ValueError(f"Ruta de skill fuera de {pack_dir}: {s!r}")
        cur = pack_dir
        for part in rel.parts:
            cur = cur / part
            if _is_link(cur):
                raise ValueError(f"Symlink/junction no permitido en ruta de skill: {cur}")
        if _is_link(cur / "SKILL.md"):
            raise ValueError(f"Symlink/junction no permitido en {cur / 'SKILL.md'}")
        cand = cur.resolve()
        if cand == pack_root or not cand.is_relative_to(pack_root):
            raise ValueError(f"Ruta de skill escapa {pack_root}: {s!r}")
        if (cand / "SKILL.md").is_file() and s not in skills:
            skills.append(s)
    return skills, prev_refs


def import_packs(
    fetcher: TextFetcher = fetch_text,
    packs_dir: pathlib.Path = PACKS_DIR,
) -> list[str]:
    """Import STACK_PACKS into packs_dir while strictly preserving external pack directories."""
    warnings: list[str] = []
    packs_dir.mkdir(parents=True, exist_ok=True)
    print(f"\n[+] Importando y Estructurando Stack Packs en {packs_dir}...")

    for pack_dir_name, meta in STACK_PACKS.items():
        pack_dir = _safe_target(packs_dir, pack_dir_name)
        pack_dir.mkdir(parents=True, exist_ok=True)
        skills, prev_refs = _merge_prev_pack_manifest(pack_dir, meta)
        upstream: dict[str, object] = {
            "repo": "affaan-m/ecc",
            "license": "MIT",
            "copyright": "Copyright (c) 2026 Affaan Mustafa",
        }
        if prev_refs is not None:
            upstream["references"] = prev_refs
        manifest = {
            "id": meta["id"],
            "family": meta["family"],
            "requires": list(meta["requires"]),
            "description": meta["description"],
            "upstream": upstream,
            "rules": list(meta["rules"]),
            "specialists": list(meta["specialists"]),
            "skills": skills,
            "workflows": list(meta["workflows"]),
        }
        (pack_dir / "pack.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

        _import_flat_assets(fetcher, pack_dir, pack_dir_name, "rules", meta["rules"], warnings)

        if meta["specialists"]:
            agents_dir = pack_dir / "agents"
            agents_dir.mkdir(parents=True, exist_ok=True)
            for a in meta["specialists"]:
                txt = _fetch_or_warn(fetcher, f"({pack_dir_name}) specialist", a, warnings)
                if txt is not None:
                    agent_name = pathlib.Path(a).stem
                    read_only = "resolver" not in agent_name
                    adapted = adapt_agent_frontmatter(agent_name, txt, read_only=read_only)
                    a_target = _safe_target(agents_dir, pathlib.Path(a).name)
                    a_target.write_text(adapted, encoding="utf-8")

        if meta["skills"]:
            skills_dir = pack_dir / "skills"
            skills_dir.mkdir(parents=True, exist_ok=True)
            for s in meta["skills"]:
                skill_slug = pathlib.Path(s).name
                skill_rel = f"{s}/SKILL.md"
                txt = _fetch_or_warn(fetcher, f"({pack_dir_name}) skill", skill_rel, warnings)
                if txt is not None:
                    s_target_dir = _safe_target(skills_dir, skill_slug)
                    s_target_dir.mkdir(parents=True, exist_ok=True)
                    (s_target_dir / "SKILL.md").write_text(txt, encoding="utf-8")

        _import_flat_assets(fetcher, pack_dir, pack_dir_name, "workflows", meta["workflows"], warnings)
        print(f"  -> [OK] Pack configurado: {pack_dir_name} ({meta['id']})")

    return warnings


def main(argv: list[str] | None = None) -> None:
    """Run the CLI catalog import for universal specialists and STACK_PACKS."""
    parser = argparse.ArgumentParser(description="SDD Catalog Importer & Packager")
    parser.add_argument("--overwrite-sdd-custom", action="store_true", help="Sobreescribir especialistas adaptados a SDD (p. ej. spec-miner.md).")
    args = parser.parse_args(argv)
    CATALOG_DIR.mkdir(parents=True, exist_ok=True)
    warnings = import_specialists(overwrite_sdd_custom=args.overwrite_sdd_custom) + import_packs()
    if warnings:
        print(f"\n[WARN] Catalogo .sdd/catalog/ actualizado con {len(warnings)} advertencia(s).", file=sys.stderr)
    else:
        print("\n[SUCCESS] Catalogo .sdd/catalog/ inicializado con exito bajo Licencia MIT de ECC.")


if __name__ == "__main__":
    main()
