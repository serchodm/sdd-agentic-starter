# Regla 03: Estándar EARS y Criterios BDD (Gate 1)

> **NORMA:** Todo requisito funcional (`RF-###`) en `01-spec.md` debe usar sintaxis formal **EARS** (prohibida prosa ambigua). Ver norma completa en [`docs/standards/EARS_REQUIREMENTS_STANDARD.md`](file:///c:/Projects/sdd-agentic-starter/docs/standards/EARS_REQUIREMENTS_STANDARD.md).

## 1. Los 5 Patrones EARS Canónicos
1. **Ubiquitous (Invariante):** `El sistema <NOMBRE> deberá <acción/respuesta>` — *Ej.: cifrar credenciales en reposo con AES-256.*
2. **Event-Driven (Evento):** `CUANDO <evento>, el sistema <NOMBRE> deberá <respuesta>` — *Ej.: CUANDO falten campos requeridos, mostrar error inline.*
3. **State-Driven (Estado):** `MIENTRAS <estado X>, el sistema <NOMBRE> deberá <respuesta>` — *Ej.: MIENTRAS no haya red, deshabilitar sincronización.*
4. **Unwanted Behavior (Error/Anomalía):** `SI <condición anómala>, ENTONCES el sistema <NOMBRE> deberá <respuesta>` — *Ej.: SI HTTP 401, limpiar token y redirigir a login.*
5. **Optional Feature (Configuración):** `DONDE <flag habilitada>, el sistema <NOMBRE> deberá <respuesta>` — *Ej.: DONDE modo oscuro esté activo, usar paleta alto contraste.*

## 2. Criterios de Aceptación BDD (Given-When-Then)
Cada `RF-###` exige al menos un escenario verificable que se automatizará en Gate 4:
```gherkin
Escenario: [Nombre]
  DADO [precondición]
  CUANDO [acción/evento]
  ENTONCES [resultado observable]
```
