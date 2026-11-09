# Regla 03: Estándar EARS para Requisitos Funcionales y Criterios BDD (Gate 1)

> **ESTÁNDAR NORMATIVO:** Todo requisito funcional (`RF-###`) en especificaciones de Gate 1 (`01-spec.md`) debe redactarse mediante la sintaxis formal **EARS** (*Easy Approach to Requirements Syntax*). Queda prohibida la prosa ambigua.
> *(Para la norma exhaustiva con matriz de anti-patrones, consulta [`docs/standards/EARS_REQUIREMENTS_STANDARD.md`](file:///c:/Projects/sdd-agentic-starter/docs/standards/EARS_REQUIREMENTS_STANDARD.md)).*

---

## 1. Los 5 Patrones EARS Canónicos

1. **Ubiquitous (Omnipresente - Invariantes del Sistema):**
   - Sintaxis: `El sistema <NOMBRE> deberá <acción/respuesta>`
   - Ejemplo: *El sistema deberá cifrar todas las credenciales en reposo mediante AES-256.*

2. **Event-Driven (Disparado por Evento):**
   - Sintaxis: `CUANDO <evento disparador>, el sistema <NOMBRE> deberá <respuesta>`
   - Ejemplo: *CUANDO el usuario envíe el formulario con campos vacíos, el sistema deberá mostrar un mensaje de error inline en cada campo requerido.*

3. **State-Driven (Basado en Estado):**
   - Sintaxis: `MIENTRAS <el sistema esté en estado X>, el sistema <NOMBRE> deberá <respuesta>`
   - Ejemplo: *MIENTRAS la conexión con el servidor esté interrumpida, el sistema deberá deshabilitar el botón de sincronización y mostrar un banner de aviso.*

4. **Unwanted Behavior (Casos de Error o Condición Anómala):**
   - Sintaxis: `SI <condición anómala o fallo>, ENTONCES el sistema <NOMBRE> deberá <respuesta>`
   - Ejemplo: *SI el servicio de autenticación devuelve HTTP 401, ENTONCES el sistema deberá redirigir al usuario a la pantalla de login borrando el token caducado.*

5. **Optional Feature (Comportamiento Condicionado a Configuración):**
   - Sintaxis: `DONDE <funcionalidad/flag esté habilitada>, el sistema <NOMBRE> deberá <respuesta>`
   - Ejemplo: *DONDE el modo oscuro esté habilitado por el usuario, el sistema deberá aplicar la paleta de colores de alto contraste.*

---

## 2. Criterios de Aceptación BDD (Given-When-Then)
Cada requisito funcional redactado en EARS debe acompañarse obligatoriamente de al menos un escenario BDD verificable:
```gherkin
Escenario: [Nombre del escenario]
  DADO [precondición o estado inicial del sistema]
  CUANDO [acción disparada por el usuario o evento del sistema]
  ENTONCES [resultado observable esperado y verificable]
```
Todo criterio Given-When-Then se trasladará como prueba automatizada obligatoria en Gate 4 antes de considerar la funcionalidad finalizada.
