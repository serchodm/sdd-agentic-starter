# Reglas Técnicas: Backend Python & Clean Architecture

## 1. Organización en Capas (Clean Architecture)
```text
backend/src/
├── domain/            # Entidades puras, Value Objects, contratos abstractos (Sin dependencias externas)
├── application/       # Casos de uso (Use Cases), orquestación de comandos/queries, validadores
├── infrastructure/    # Persistencia SQLModel, clientes MCP, audio local, runners CLI
└── api/               # FastAPI routers, WebSockets, SSE streaming, DTOs Pydantic espejo, OIDC auth
```

## 2. Invariantes de Dominio
- **Aislamiento Total:** Las entidades en `backend/src/domain/` no importan frameworks web (FastAPI) ni librerías de persistencia (SQLModel, SQLAlchemy).
- **Tipado Estricto:** Uso riguroso de `typing`, `pydantic` (`frozen=True`) o `dataclasses` (frozen).
- **Control de Errores Semántico:** Excepciones de dominio semánticas para flujos de error de negocio; evitar excepciones genéricas o no controladas.

## 3. Contratos Espejo & camelCase
- Todos los DTOs en `backend/src/api/dtos/` deben heredar de la clase base con alias generator en `camelCase`:
  ```python
  from pydantic import BaseModel, ConfigDict
  from pydantic.alias_generators import to_camel

  class BaseDto(BaseModel):
      model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
  ```
- Cada campo debe coincidir 1:1 con la interfaz TypeScript en `frontend/src/types/`.

## 4. Asincronía y Rendimiento
- Uso obligatorio de `async`/`await` en todas las operaciones de I/O (base de datos, llamadas HTTP, WebSockets, streaming de audio, subprocesos).
- Subprocesos de CLIs ejecutados exclusivamente con `asyncio.create_subprocess_exec` con control de timeout y señales de cancelación.

## 5. Pruebas y Validación
- Pruebas unitarias en `backend/tests/unit/` sin dependencias de base de datos real ni llamadas a LLMs con coste (uso de mocks y fakes).
- Pruebas de integración en `backend/tests/integration/` con base de datos de test aislada.
- Comando de verificación obligatoria: `pytest backend/tests/`.

## 6. Directivas ECC para FastAPI Asíncrono, Inyección de Dependencias y Esquemas (`affaan-m/ECC`)
- **Separación Estricta de Esquemas (`fastapi-patterns`)**: Separar siempre los DTOs de petición/respuesta HTTP (`backend/src/api/dtos/`) de los modelos de persistencia SQLModel y de las entidades/dataclasses de dominio.
- **Pureza en Rutas `async def`**: Prohibido ejecutar llamadas bloqueantes de disco o red síncrona en endpoints `async def`. Para escrituras atómicas de archivos de configuración o anatomía (`.md` / `.yaml`), utilizar reemplazo atómico seguro (`tempfile` + `os.replace`) e invalidar cachés en memoria mediante firma `mtime`.
- **Inyección de Dependencias con `Depends`**: Centralizar la resolución de servicios de aplicación, repositorios y autenticación en proveedores inyectables para permitir sustitución limpia en tests unitarios (`dependency_overrides`).
- **Cero Fallos Silenciosos (`silent-failure-hunter`)**: Prohibido usar `except Exception: pass`. Todo bloque de captura debe registrar contexto estructurado (`logger.warning` / `logger.error`) o propagar una excepción semántica.
