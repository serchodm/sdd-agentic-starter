# Estándar de Protección de Ramas Git (GitHub & GitLab)

> **Gobernanza Git SDD (`RN-SDD-BRANCH-SYNC`):** Este estándar define las reglas de protección que deben configurarse en GitHub o GitLab para blindar la estabilidad del repositorio e impedir regresiones o commits accidentales en `main` y `develop`.

---

## 1. Configuración de Protección para `main` (Producción & Releases)

En **GitHub**: `Settings` $\rightarrow$ `Rules` $\rightarrow$ `Rulesets` (o `Branches` $\rightarrow$ `Branch protection rules`):

- **Target branch:** `main`
- **Enforcement status:** `Active`
- **Reglas obligatorias:**
  1. **Restrict deletions**: Activado (Nadie puede eliminar `main`).
  2. **Block force pushes**: Activado (Prohibido `git push --force`).
  3. **Require a pull request before merging**:
     - **Required approvals**: `1` (Aprobación humana explícita).
     - **Dismiss stale pull request approvals when new commits are pushed**: Activado.
     - **Require review from Code Owners**: Opcional.
  4. **Require status checks to pass before merging**:
     - **Require branches to be up to date before merging**: Activado.
     - **Status checks requeridos**:
       - `SDD Governance & Architecture Audit` (del workflow `ci.yml`)
       - `Validate Conventional Commits Title` (del workflow `pr-check.yml`)
  5. **Require linear history**: Activado (Fuerza Squash & Merge o Rebase limpio).
  6. **Do not allow bypassing the above settings**: Activado (Aplica incluso a administradores).

---

## 2. Configuración de Protección para `develop` (Integración Continua)

- **Target branch:** `develop`
- **Enforcement status:** `Active`
- **Reglas obligatorias:**
  1. **Restrict deletions**: Activado.
  2. **Block force pushes**: Activado.
  3. **Require a pull request before merging**:
     - Permite **Auto-Merge Agéntico** si los checks automáticos están verdes y se ha superado la doble revisión (Santa Loop / GAN $\ge 8.5/10$).
  4. **Require status checks to pass before merging**:
     - `SDD Governance & Architecture Audit` (del workflow `ci.yml`).
     - `Validate Conventional Commits Title` (del workflow `pr-check.yml`).
  5. **Require linear history**: Activado (Squash & Merge obligatorio para ramas `feat/*`, `change/*`, `fix/*`).

---

## 3. Comandos CLI con GitHub CLI (`gh`)

Para configurar estas reglas de forma desatendida mediante GitHub CLI:

```bash
# Verificar autenticación
gh auth status

# Crear Pull Request de trabajo hacia develop
gh pr create --base develop --head feat/FEAT-001 --title "feat(auth): add login flow (FEAT-001)" --body "Resuelve FEAT-001 según especificación."

# Habilitar auto-merge una vez los checks pasen
gh pr merge --auto --squash
```
