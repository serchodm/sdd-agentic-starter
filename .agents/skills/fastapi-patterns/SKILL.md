---
name: fastapi-patterns
description: Patrones de arquitectura y producción para FastAPI asíncrono, Pydantic v2 camelCase, inyección de dependencias Depends, ciclo lifespan y streaming SSE/WebSocket en Project
---

# Skill: `fastapi-patterns` (Patrones de Producción FastAPI Asíncrono de `affaan-m/ECC`)

Recopilación de patrones obligatorios de `affaan-m/ECC` adaptados al stack de Project (Python 3.12 + FastAPI + Pydantic v2 + SQLModel + SSE/WebSockets).

## 1. Regla de Oro de Rutas Asíncronas (`async def` vs `def`)
- Usa `async def` para todos los endpoints de Project y asegúrate de que **toda operación de I/O interna sea no bloqueante** (`await`).
- Si es imprescindible ejecutar una operación intensiva en CPU o librería síncrona heredada, envuélvela con `await asyncio.to_thread(...)` para no congelar el bucle de eventos de streaming SSE.

## 2. Separación de Esquemas Pydantic v2 y Contratos Espejo
- **Nunca reutilices modelos de tabla SQLModel directamente como respuesta HTTP.**
- Define esquemas explícitos por operación heredando de `BaseDto`:
  ```python
  from pydantic import BaseModel, ConfigDict
  from pydantic.alias_generators import to_camel

  class BaseDto(BaseModel):
      model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
  ```

## 3. Gestión de Recursos con `lifespan` e Inyección `Depends`
- Inicializa clientes compartidos de larga vida (pools de base de datos, hidradores de anatomía, clientes HTTP asíncronos `httpx.AsyncClient`) en el `lifespan` de la aplicación o mediante proveedores inyectados con `Depends(...)`.
- Facilita el testing unitario sobreescribiendo dependencias mediante `app.dependency_overrides[get_service] = lambda: fake_service`.

## 4. Resiliencia en Streaming SSE (`EventSourceResponse` / `StreamingResponse`)
- Emite eventos con estructura tipada `EventEnvelopeDto` (`type`, `sessionId`, `timestamp`, `payload`).
- Garantiza que cualquier error durante el stream emita un evento de estado recuperable (`session.state_changed` $\rightarrow$ `error` / `idle`) en lugar de cortar abruptamente la conexión sin feedback al HUD.
