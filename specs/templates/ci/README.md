# Plantillas CI-Agnósticas (`specs/templates/ci/`)

Guía de activación para ejecutar la verificación SDD unificada (`scripts/sdd_cli.py ci-verify`) de forma determinista y sin secretos en cualquier proveedor CI o entorno local.

## Comando Canónico

```sh
uv run python scripts/sdd_cli.py ci-verify --mode auto --run-stack-if-approved --format text
```

- **En el repositorio starter (`Gate S0` sin aprobar):** detecta `--mode framework`, valida las invariantes de gobernanza SDD y ejecuta la suite de regresión (`tests/`).
- **En proyectos derivados (`Gate S0` aprobado en `specs/STACK.md`):** detecta `--mode project`, valida gobernanza/0DD/DAGs y ejecuta automáticamente los comandos seguros (`shell=False`) definidos en `specs/STACK.md §2.5` (`lint`, `unit_test`, `build`, `infra`).

### Opciones útiles

- `--format json`: salida estructurada para integración con pipelines o reportes.
- `--include-integration`: incluye los slots `integration_test` / `full_suite` de `STACK.md §2.5` cuando `Gate S0` está aprobado.
- `--run-stack`: exige *fail-closed* que `Gate S0` esté aprobado antes de ejecutar comandos de stack.

---

## Activación por Proveedor

| Proveedor / Entorno | Plantilla | Activación |
| :--- | :--- | :--- |
| **GitHub Actions** | `.github/workflows/ci.yml` | Activo por defecto en `push` y `pull_request` sobre `develop` y `main`. |
| **GitLab CI** | [`gitlab-ci.yml`](gitlab-ci.yml) | Copiar a la raíz del repositorio como `.gitlab-ci.yml`. |
| **Bitbucket Pipelines** | [`bitbucket-pipelines.yml`](bitbucket-pipelines.yml) | Copiar a la raíz del repositorio como `bitbucket-pipelines.yml`. |
| **Jenkins / Forgejo / Gitea / Woodpecker / Local** | [`ci-verify.sh`](ci-verify.sh) | Ejecutar `sh specs/templates/ci/ci-verify.sh` (o dar permisos `chmod +x specs/templates/ci/ci-verify.sh`) desde la raíz del repo. |

## Requisitos de Entorno

- Clonado con historial completo (`fetch-depth: 0` / `GIT_DEPTH: "0"` / `depth: full`) para auditorías Git.
- Python `3.12+` (gestionado vía `uv` o `python3` estándar; `scripts/sdd_ci.py` solo usa librería estándar).
- Cero secretos requeridos en CI para la verificación de gobernanza y tests unitarios offline.
