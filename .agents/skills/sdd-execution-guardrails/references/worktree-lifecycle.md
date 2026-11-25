# Referencia `sdd-execution-guardrails`: Ciclo de Vida de Git Worktrees y Ejecución Multiplataforma

Cargar en **Gate 4** (y releases/hotfixes en **Gate 6**) al ejecutar tareas paralelas `[PARALLEL]`, despachar subagentes concurrentes o invocar herramientas Python del framework en **Windows, Linux o macOS**.

## 1. Ejecución Determinista de Python (`inst-win-py-alias`)

Prohibido invocar `python` desnudo en Windows (abre el alias `WindowsApps\python.exe` de Microsoft Store) o usar `shell=True`. Aplicar esta jerarquía estricta:

| Prioridad | Windows (PowerShell / CMD) | Linux / macOS (POSIX) | Caso de Uso |
| :---: | :--- | :--- | :--- |
| **1** | `uv run python <script.py>` | `uv run python <script.py>` | Opción preferida cuando `uv` gestiona el proyecto. |
| **2** | `.venv\Scripts\python.exe <script.py>` | `.venv/bin/python <script.py>` | Entorno virtual local ya creado en repo/worktree. |
| **3** | `py -3 <script.py>` | `python3 <script.py>` | Intérprete del sistema verificado sin alias roto. |
| **CLI** | `.\sdd.ps1 <cmd>` o `uv run python scripts/sdd_cli.py <cmd>` | `./sdd <cmd>` o `uv run python scripts/sdd_cli.py <cmd>` | Dispatcher SDD (`git`, `healthcheck`, `verify-gates`). |

## 2. Creación Contenida bajo `.worktrees/` (`sdd git worktree-create`)

Montar un worktree dedicado por cada flujo concurrente usando el orquestador determinista:

```text
uv run python scripts/sdd_cli.py git worktree-create --spec <WORK_ITEM_ID> [--name <slug>] [--base <rama>]
```

Garantías *fail-closed* de `WorktreeManager` (`scripts/sdd_git_worktree.py`):
- **Contención física estricta:** Valida nombres de ref Git, sanitiza `<slug>`, rechaza symlinks o *junctions* NTFS y verifica `target_path.resolve().is_relative_to(<repo>/.worktrees)`.
- **Resolución de rama normativa:** Deriva automáticamente `feat/`, `change/`, `fix/`, `hotfix/` o `release/` según `specs/STACK.md` sin operar jamás directo sobre `main`.

## 3. Aislamiento de Puertos (`ports_registry.json`) y `.env.test` Seguro

1. **Reserva Atómica sin Colisiones (`ports_registry.json`):**
   - Bajo bloqueo `.agents/worktree_states/.ports.lock`, `allocate_worktree_ports()` asigna `BACKEND_PORT` (`8000–8899`) y `FRONTEND_PORT` (`3000–3899`).
   - Comprueba disponibilidad real de bind TCP en `127.0.0.1`, `0.0.0.0` y `::1` antes de registrar la reserva.
   - Persiste el par asignado en `.agents/worktree_states/ports_registry.json` y el estado del worktree en `.agents/worktree_states/<slug>.json`.
2. **Copia Segura desde `.env.example` (Cero Secretos Reales):**
   - Genera `<worktree>/.env.test` con variables aisladas:
     ```ini
     PORT=<backend_port>
     TEST_PORT=<backend_port>
     BACKEND_PORT=<backend_port>
     FRONTEND_PORT=<frontend_port>
     DATABASE_URL=sqlite:///./test_<slug>.sqlite
     WORKTREE_NAME=<slug>
     ```
   - Anexa **únicamente** las plantillas inocuas de `.env.example` (comprobando antes que no sea symlink/junction).
   - **Bloqueo de seguridad (`.agents/rules/05-security-and-secrets.md`):** Prohibido copiar `.env`, `.env.local`, claves privadas o tokens reales al worktree.

## 4. Verificación Baseline Pre-Edición y Rama Activa

Antes de tocar código o tests dentro de `.worktrees/<slug>/`, ejecutar en orden:

1. **Rama e higiene Git (`RN-SDD-BRANCH-SYNC`):**
   - Verificar `git branch --show-current` (abortar si devuelve `main` o `HEAD` desconectado no previsto) y `git status --short` limpio.
2. **Integridad de Puertas SDD:**
   - Ejecutar `uv run python scripts/sdd_cli.py verify-gates` y `uv run python scripts/sdd_cli.py healthcheck` para validar sellos SHA-256 de Gates `1..3`.
3. **Baseline de Tests (`specs/STACK.md §2.5`):**
   - Correr el comando rápido de lint/unit test del área afectada **antes** de editar; si falla en limpio, reportar el bloqueo preexistente en lugar de enmascararlo.

## 5. Integración y Poda Limpia Post-Merge (`worktree-remove` / `worktree-prune`)

Tras validar el DoD, comitear localmente e integrar la rama en su base (vía merge local autorizado o PR, nunca push directo a `main`):

1. **Salir del `CWD` del worktree:** Volver siempre a la raíz del repositorio principal antes de desmontar (en Windows un proceso ubicado dentro de `.worktrees/<slug>` bloquea el borrado con `WinError 32`).
2. **Desmontar y liberar recursos:**
   ```text
   uv run python scripts/sdd_cli.py git worktree-remove --spec <WORK_ITEM_ID>
   ```
   *(O `--path .worktrees/<slug>`).* Desmonta el árbol Git, ejecuta `git worktree prune`, libera los puertos en `ports_registry.json` y borra `.agents/worktree_states/<slug>.json`.
3. **Poda de metadatos huérfanos:** Si algún worktree quedó interrumpido, ejecutar `uv run python scripts/sdd_cli.py git worktree-prune` y verificar limpieza con `uv run python scripts/sdd_cli.py git status`.

## 6. Checklist de Control Operativo

- [ ] Comandos Python lanzados vía `uv run python`, `.venv`, `python3` o `py -3` (sin `shell=True`).
- [ ] Worktree contenido en `.worktrees/` con puertos propios en `ports_registry.json`.
- [ ] `.env.test` generado solo desde `.env.example` con `0` credenciales reales.
- [ ] Baseline pre-edición verde y rama activa validada (`!= main`).
- [ ] Worktree desmontado y podado (`worktree-remove` / `worktree-prune`) tras integrar.
