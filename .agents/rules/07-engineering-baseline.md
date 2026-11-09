# Regla 07: Estándar Universal de Ingeniería de Software (Baseline de Calidad)

> **ESTÁNDAR NORMATIVO OBLIGATORIO (CORE GOVERNANCE):**
> Esta regla define los principios universales de calidad, tipado, asincronía, modularidad y disciplina técnica que rigen todo el código desarrollado en el proyecto, inspirada en las reglas comunes de `affaan-m/ECC` (Everything Claude Code) y `morluto/rea`.

---

## 1. Principios de Diseño y Estilo de Código (`coding-style`)

1. **Inmutabilidad por Defecto**:
   - Prefiere estructuras de datos inmutables (`dataclass(frozen=True)`, `readonly` types, `record`, structs inmutables).
   - Minimiza el estado global compartido. Si se requiere mutabilidad, encapsúlala en clases con métodos semánticos explícitos.
2. **Tipado Estricto y Explícito**:
   - Todo parámetro de función, retorno y atributo de clase debe contar con anotaciones de tipo estáticas completas.
   - Prohibido el uso de `Any`, `dynamic`, `object` no acotado o `# type: ignore` / `@ts-ignore` sin una justificación técnica documentada.
3. **Manejo de Errores Tipado (Result Pattern & Fail-Closed)**:
   - Prohibido silenciar errores o capturar excepciones sin logging estructurado (`except: pass`, `catch () {}`).
   - Usa el patrón `Result<T, E>` para fallos de dominio esperados y lanza excepciones semánticas solo en situaciones irrecuperables.
4. **Límite de Fichero y Modularidad (Techo de 800 líneas)**:
   - Ningún fichero de código de producción o test debe superar las **800 líneas** (alerta de modularización preventiva en **500 líneas**).
   - Si un fichero crece, divídelo en submódulos de alta cohesión.

---

## 2. Estándar de Pruebas Automatizadas (`testing`)

1. **Pirámide de Pruebas Determinista**:
   - **Unitarias en Memoria (< 1s)**: Sin dependencias de red, base de datos externa ni sleeps arbitrarios. Uso intensivo de fakes y mocks controlados.
   - **Integración**: Con servicios auxiliares reales levantados en contenedores (`Testcontainers` o `docker-compose`).
   - **End-to-End (E2E)**: Flujos críticos de usuario guiados por herramientas como Playwright o CLI runners.
2. **Cero Falsos Verdes (Anti-Tautología)**:
   - Toda prueba debe contar con aserciones explícitas y evaluar casos límite, valores nulos y escenarios de fallo (`unhappy paths`).
   - Los Criterios de Aceptación de Gate 1 (Given-When-Then) deben contar con correspondencia 1:1 en las suites de prueba.

---

## 3. Asincronía y Concurrencia Limpia (`performance`)

1. **I/O 100% Asíncrono**:
   - Todo acceso a base de datos, sistema de archivos o APIs externas debe usar primitivas asíncronas (`async`/`await`).
   - Propaga tokens o contextos de cancelación (`CancellationToken`, `AbortController`, `context.Context`) en operaciones de I/O de larga duración.
2. **Prevención de Condiciones de Carrera**:
   - Protege estructuras de datos compartidas mediante mecanismos de sincronización explícitos (semáforos, locks, colas de mensajes).

---

## 4. Seguridad y Confianza Cero (`security`)

1. **Principio de Mínimo Privilegio**:
   - Las conexiones y procesos deben ejecutarse con los menores privilegios requeridos.
2. **Validación en Fronteras Productoras**:
   - Todo input externo (HTTP, WebSocket, CLI, archivos de configuración) debe ser validado contra esquemas estrictos antes de entrar a la capa de aplicación o dominio.
3. **Cero Secretos**:
   - Prohibido commitear credenciales, API keys o tokens reales en el repositorio. Usar `.env.example` tipado y gestores de secretos.

---

## 5. Control de Versiones y Convenciones Git (`git-workflow`)

1. **Conventional Commits**:
   - Todos los commits siguen el formato: `<tipo>(<alcance>): <descripción>` (`feat`, `fix`, `docs`, `refactor`, `test`, `chore`).
2. **Sincronización y Protección de Ramas (`RN-SDD-BRANCH-SYNC`)**:
   - **`main` blindada**: Prohibido comitear o pushear directamente a `main`.
   - Cada commit de desarrollo se efectúa en su rama de trabajo (`feat/*`, `change/*`, `fix/*`).
   - Las actualizaciones de gobernanza e integración se consolidan en `develop`.
   - `main` solo se actualiza mediante Pull Request de Release (`release/*`) o Hotfix (`hotfix/*`) con aprobación humana explícita.
   - Sincronización obligatoria tras aprobación: `git add`, `git commit` y `git push origin <rama-activa>`.
