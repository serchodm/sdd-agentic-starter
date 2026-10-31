# Regla 02: Estándar EARS para Requisitos Funcionales

Todo requisito funcional (`RF-###`) en especificaciones de Gate 1 debe redactarse mediante la sintaxis **EARS** (*Easy Approach to Requirements Syntax*). Queda prohibida la prosa ambigua.

## Los 5 Patrones EARS Canónicos

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
