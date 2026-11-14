# Regla 07: Estándar Universal de Ingeniería (Quality Baseline)

> Baseline normativo inspirado en `affaan-m/ECC` y `morluto/rea`.

## 1. Diseño y Estilo (`coding-style`)
- **Inmutabilidad:** Preferir `dataclass(frozen=True)`, `readonly`, `record`, structs inmutables; minimizar estado global.
- **Tipado Estricto:** Anotar parámetros, retornos y atributos; prohibido `Any`, `dynamic`, `object` abierto o `# type: ignore`/`@ts-ignore` sin justificación.
- **Fail-Closed & Result:** Prohibido silenciar excepciones (`except: pass`, `catch () {}`). Usar `Result<T, E>` para fallos de dominio y logging estructurado.
- **Modularidad:** Máximo **800 líneas** por fichero (alerta preventiva en **500 líneas**).

## 2. Pruebas (`testing`)
- **Pirámide:** Unitarias en memoria (< 1s, sin red/BD), Integración (`Testcontainers` / `docker-compose`), E2E (Playwright / CLI).
- **Cero Falsos Verdes:** Aserciones explícitas, casos límite/fallo y cobertura 1:1 de escenarios Given-When-Then de Gate 1.

## 3. Asincronía (`performance`) y Seguridad (`security`)
- **I/O Asíncrono:** `async`/`await` con propagación de cancelación (`CancellationToken`, `AbortController`, `context.Context`) y locks explícitos ante estado compartido.
- **Seguridad:** Mínimo privilegio, validación estricta en fronteras productoras y cero secretos (usar `.env.example`).

## 4. Git y Ramas (`git-workflow`, `RN-SDD-BRANCH-SYNC`)
- **Conventional Commits:** `<tipo>(<alcance>): <descripción>` (`feat`, `fix`, `docs`, `refactor`, `test`, `chore`).
- **`main` blindada:** Prohibido commit/push directo a `main`. Trabajar en `feat/*`, `change/*`, `fix/*`; gobernanza en `develop`; `main` solo vía PR `release/*` o `hotfix/*` con aprobación humana, haciendo siempre `git add`, `git commit` y `git push origin <rama-activa>`.
