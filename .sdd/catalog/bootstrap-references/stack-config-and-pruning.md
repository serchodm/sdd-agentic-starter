# `sdd-bootstrap` Reference: Dynamic Tree Pruning & `sdd:stack-config` Contract

## 1. Dynamic Tree Pruning Rules
| Condición Detectada | Preguntas Podadas (Omitidas) | Impacto en Escuadrón Agéntico |
| :--- | :--- | :--- |
| **`Solo Backend / API Only`** | Framework visual, Estilos CSS, Estado cliente, Tests UI, Vercel Previews, todas las preguntas `uiux` (`ui-ux-pro-max`, `hifi_format`, `brand_constraints`) | `@front-engineer` -> **INACTIVO / INACTIVE (N/A)**; no se activan `capability-ui-design` ni `@ui-ux-designer` |
| **`Solo Frontend / Client Only`** | Framework backend, DTOs backend, ORM, Migraciones BD, Testcontainers backend | `@back-engineer` -> **INACTIVO / INACTIVE (N/A)**; mantiene preguntas `uiux` activas |
| **`CLI / Herramienta Local`** | Frontend, Hosting serverless/cloud, Contenedores, Vercel, todas las preguntas `uiux` | `@front-engineer` -> **INACTIVO / INACTIVE (N/A)**; no se activan `capability-ui-design` ni `@ui-ux-designer` |
| **`Persistencia: N/A (Stateless)`** | Motor BD, ORM/Micro-ORM, Migraciones de esquema, Testcontainers de BD | - |
| **`Hosting: Vercel / Netlify / Cloudflare`** | Kubernetes, Docker Swarm, Registries de contenedores | CI/CD orientado a GitOps y Previews por PR |
| **`Hosting: Air-Gapped / Aislado`** | CDNs remotas, Gestores de secretos en nube pública | Assets 100% locales, `.env` o Vault on-prem |

## 2. Emisión del Bloque `sdd:stack-config` en `specs/STACK.md` (§3.3)
- Usar `specs/templates/00-stack.template.md` en el idioma elegido (`ES-ES` o `EN-GB`).
- Mantener `stack_approved: false` (y legacy `gate00_approved: false`) hasta aprobación humana expresa.
- Cuando el proyecto tiene UI (`Fullstack` o `Frontend Only`):
  - Si `uiux.enabled: true`, añadir `capability-web-frontend` y `capability-ui-design` en `packs`:
    ````markdown
    ```yaml sdd:stack-config
    stack_approved: false
    gate00_approved: false
    preset: <compact|granular|spa-only>
    packs:
      - <lang-pack>
      - <framework-pack>
      - capability-web-frontend
      - capability-ui-design
    uiux:
      enabled: true
      provider: ui-ux-pro-max
      version: "2.15.0"
      hifi_format: <html|figma|html+figma>
      # brand_constraints: docs/design-system/BRAND.md  # Optional relative path
    ```
    ````
  - Si `uiux.enabled: false`: incluir `capability-web-frontend` sin `capability-ui-design` y fijar `uiux: { enabled: false }` (mantiene `@a11y-architect` sin `@ui-ux-designer`).
- Cuando sea `Backend Only / API Only` o `CLI`: omitir `capability-ui-design` y fijar `uiux.enabled: false` (u omitir `uiux`).

## 3. Tablas de Escuadrón, Ownership Map (§3.2), Gate S0 y Materialización
1. Completar **Agent Squad Table** (`ACTIVE` vs `INACTIVE (N/A)`), **Ownership Map (§3.2)** y **Golden Samples (Do/Don't)**.
2. Pedir confirmación humana (`RN-SDD-HUMAN-GATE-OWNERSHIP`) antes de marcar `[x] Gate S0 Approved (Human Sign-off)` (alias legacy `Gate 00`) y `stack_approved: true` / `gate00_approved: true`.
3. Tras la aprobación, ejecutar:
   `uv run python scripts/sdd_agent_generator.py --materialize`
4. **Si y solo si `uiux.enabled: true`** tras aprobar Gate S0: registrar una fila en `specs/BACKLOG.md` titulada **`Design System Foundation`** con el siguiente `FEAT-XXX` secuencial, `Gate 0 (Intake)` = `[x]`, Gates 1–5 = `[ ]`, y `Estado Final` = `Backlog`. No crear carpetas ni código durante Gate S0 (`RN-SDD-SESSION-LIFECYCLE`).
