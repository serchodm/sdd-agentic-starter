#!/usr/bin/env python3
"""
SDD Catalog Importer & Packager
Fetches upstream components from affaan-m/ecc (MIT License), adapts frontmatter
for SDD agentic governance, and registers them cleanly inside `.sdd/catalog/`.
"""

import json
import os
import pathlib
import re
import sys
import urllib.error
import urllib.request

RAW_BASE = "https://raw.githubusercontent.com/affaan-m/ecc/main"
REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
CATALOG_DIR = REPO_ROOT / ".sdd" / "catalog"
SPECIALISTS_DIR = CATALOG_DIR / "specialists"
PACKS_DIR = CATALOG_DIR / "packs"

# Universal specialists that belong to baseline catalog
UNIVERSAL_SPECIALISTS = [
    "code-explorer",
    "spec-miner",
    "code-architect",
    "type-design-analyzer",
    "security-reviewer",
    "silent-failure-hunter",
    "build-error-resolver",
    "tdd-guide",
    "performance-optimizer",
    "e2e-runner",
    "code-simplifier",
    "refactor-cleaner",
    "gan-planner",
    "gan-generator",
    "gan-evaluator",
    "conversation-analyzer",
    "docs-lookup",
    "pr-test-analyzer",
    "comment-analyzer",
    "opensource-sanitizer",
]

# Stack packs definition
STACK_PACKS = {
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
    url = f"{RAW_BASE}/{rel_url.lstrip('/')}"
    req = urllib.request.Request(url, headers={"User-Agent": "sdd-agentic-starter-catalog-importer/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read().decode("utf-8")
    except Exception as exc:
        return None


def adapt_agent_frontmatter(agent_name: str, content: str, read_only: bool = True) -> str:
    """Ensures consistent SDD Subagent frontmatter while preserving original Prompt Defense & Body."""
    desc = f"Especialista ECC en auditoria y resolucion tecnica: {agent_name}."
    
    # Extract description from existing frontmatter if present
    match_desc = re.search(r"description:\s*(.+)", content)
    if match_desc:
        desc = match_desc.group(1).strip()

    body = content
    # Strip any top YAML frontmatter from raw content
    if body.startswith("---"):
        parts = body.split("---", 2)
        if len(parts) >= 3:
            body = parts[2].lstrip()

    tools_block = "  bash: true\n  write: false\n  edit: false" if read_only else "  bash: true\n  write: true\n  edit: true"

    adapted = f"""---
name: {agent_name}
description: {desc}
mode: subagent
tools:
{tools_block}
---

<!-- Sourced from upstream affaan-m/ecc (MIT License, Copyright 2026 Affaan Mustafa) -->

{body}
"""
    return adapted


def import_specialists():
    SPECIALISTS_DIR.mkdir(parents=True, exist_ok=True)
    print("\n[+] Importando Especialistas Universales ECC a .sdd/catalog/specialists/...")
    for name in UNIVERSAL_SPECIALISTS:
        rel_path = f"agents/{name}.md"
        content = fetch_text(rel_path)
        if not content:
            print(f"  -> [WARN] No se pudo descargar {name} desde {rel_path}")
            continue

        read_only = name not in {"build-error-resolver", "code-simplifier", "refactor-cleaner"}
        adapted = adapt_agent_frontmatter(name, content, read_only=read_only)
        target = SPECIALISTS_DIR / f"{name}.md"
        target.write_text(adapted, encoding="utf-8")
        print(f"  -> [OK] Guardado especialista: {name}.md")


def import_packs():
    PACKS_DIR.mkdir(parents=True, exist_ok=True)
    print("\n[+] Importando y Estructurando Stack Packs en .sdd/catalog/packs/...")

    for pack_dir_name, meta in STACK_PACKS.items():
        pack_dir = PACKS_DIR / pack_dir_name
        pack_dir.mkdir(parents=True, exist_ok=True)

        manifest = {
            "id": meta["id"],
            "family": meta["family"],
            "requires": meta["requires"],
            "description": meta["description"],
            "upstream": {
                "repo": "affaan-m/ecc",
                "license": "MIT",
                "copyright": "Copyright (c) 2026 Affaan Mustafa",
            },
            "rules": meta["rules"],
            "specialists": meta["specialists"],
            "skills": meta["skills"],
            "workflows": meta["workflows"],
        }
        (pack_dir / "pack.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

        # Download pack rules
        if meta["rules"]:
            rules_dir = pack_dir / "rules"
            rules_dir.mkdir(parents=True, exist_ok=True)
            for r in meta["rules"]:
                txt = fetch_text(r)
                if txt:
                    r_target = rules_dir / pathlib.Path(r).name
                    r_target.write_text(txt, encoding="utf-8")

        # Download pack specialists
        if meta["specialists"]:
            agents_dir = pack_dir / "agents"
            agents_dir.mkdir(parents=True, exist_ok=True)
            for a in meta["specialists"]:
                txt = fetch_text(a)
                if txt:
                    agent_name = pathlib.Path(a).stem
                    read_only = "resolver" not in agent_name
                    adapted = adapt_agent_frontmatter(agent_name, txt, read_only=read_only)
                    a_target = agents_dir / pathlib.Path(a).name
                    a_target.write_text(adapted, encoding="utf-8")

        # Download pack skills (SKILL.md)
        if meta["skills"]:
            skills_dir = pack_dir / "skills"
            skills_dir.mkdir(parents=True, exist_ok=True)
            for s in meta["skills"]:
                skill_slug = pathlib.Path(s).name
                txt = fetch_text(f"{s}/SKILL.md")
                if txt:
                    s_target_dir = skills_dir / skill_slug
                    s_target_dir.mkdir(parents=True, exist_ok=True)
                    (s_target_dir / "SKILL.md").write_text(txt, encoding="utf-8")

        print(f"  -> [OK] Pack configurado: {pack_dir_name} ({meta['id']})")


def main():
    CATALOG_DIR.mkdir(parents=True, exist_ok=True)
    import_specialists()
    import_packs()
    print("\n[SUCCESS] Catalogo .sdd/catalog/ inicializado con exito bajo Licencia MIT de ECC.")


if __name__ == "__main__":
    main()
