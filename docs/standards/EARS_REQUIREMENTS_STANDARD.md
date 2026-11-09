# Reglas Técnicas: Estándar EARS (Easy Approach to Requirements Syntax)
**Estándar Normativo:** SDD / AIDD (Project Core Governance)  
**Ámbito de Aplicación:** `@functional-analyst` (Redactor Funcional Principal en Gate 1), `@ai-architect` (Arquitecto Cognitivo en Gate 1), `@orchestrator` (Gate 2 Auditor), `@documentator` (Living Docs)  

---

## 1. Declaración de Misión y Norma Rectora

Toda especificación funcional (`01-spec.md` / Gate 1), regla de negocio (`RN-###`) y requisito funcional atómico (`RF-###`) en Project debe redactarse obligatoriamente bajo la sintaxis **EARS** (*Easy Approach to Requirements Syntax*).

Queda **terminantemente prohibido** redactar requisitos funcionales en prosa libre no estructurada o limitarse a Historias de Usuario abstractas. Las Historias de Usuario definen el *valor de negocio*, pero los requisitos EARS definen el *comportamiento determinista del sistema*.

---

## 2. Los 5 Patrones Canónicos EARS + Patrón Combinado

| Código | Tipo de Patrón | Palabras Clave Obligatorias | Propósito y Aplicación |
| :--- | :--- | :--- | :--- |
| **`EARS-UBI`** | **Ubiquitous (Omnipresente)** | `El sistema <Project> deberá <respuesta>` | Invariantes globales, seguridad, cifrado, integridad que aplican en todo momento sin depender de un evento o estado. |
| **`EARS-EVT`** | **Event-Driven (Disparado por Evento)** | `CUANDO <evento disparador>, el sistema <Project> deberá <respuesta>` | Comportamientos disparados por un estímulo instantáneo (clic, atajo de teclado, llegada de webhook, petición HTTP). |
| **`EARS-STA`** | **State-Driven (Basado en Estado)** | `MIENTRAS <el sistema esté en estado X>, el sistema <Project> deberá <respuesta>` | Comportamientos activos únicamente mientras el sistema permanezca en un estado específico de su máquina de estados (FSM). |
| **`EARS-UNW`** | **Unwanted Behavior (Error / Borde)** | `SI <condición anómala o error>, ENTONCES el sistema <Project> deberá <respuesta>` | Manejo de excepciones, fallos de red, timeouts, violaciones de permisos y políticas *fail-closed*. |
| **`EARS-OPT`** | **Optional Feature (Opcional / Config)** | `DONDE <funcionalidad/flag esté habilitada>, el sistema <Project> deberá <respuesta>` | Comportamientos que solo aplican si un módulo, servicio de terceros o flag de configuración está activo. |
| **`EARS-CMP`** | **Complex / Combined (Combinado)** | `MIENTRAS <estado>, CUANDO/SI <evento/error>, el sistema <Project> deberá <respuesta>` | Casos donde confluyen un estado activo persistente con un evento instantáneo o una condición de fallo. |

---

## 3. Catálogo Contrastivo de Ejemplos: Cumple vs. No Cumple

Para facilitar el entrenamiento y la inferencia precisa de los agentes LLM, se establecen los siguientes pares de calibración:

### Caso 1: Supresión de Eco Acústico en Reproducción de Voz
* ❌ **NO CUMPLE (Antipatrón - Vago e Incompleto)**:  
  *"El sistema no debe hacer eco cuando la IA hable."*  
  *(Motivo del fallo: No define cuándo empieza, cuándo termina, ni qué componente exacto debe actuar).*
* ✅ **CUMPLE (`EARS-STA` - State-Driven)**:  
  *"MIENTRAS el servicio de audio esté reproduciendo habla (`speaking`), el sistema Project deberá pausar la captura del micrófono de entrada."*

### Caso 2: Manejo de Truncamiento y Presupuesto de Tokens
* ❌ **NO CUMPLE (Antipatrón - Desiderata sin Contrato)**:  
  *"El asistente debe ser conciso y no debe cortarse la respuesta a mitad de frase."*  
  *(Motivo del fallo: Es un deseo abstracto; no establece la condición de fallo ni el comportamiento alternativo).*
* ✅ **CUMPLE (`EARS-UNW` - Unwanted Behavior)**:  
  *"SI el consumo de tokens de razonamiento (*thinking*) supera el 50% de la cuota asignada, ENTONCES el sistema Project deberá reservar el presupuesto restante para garantizar la emisión completa de la respuesta visible al usuario sin truncamiento."*

### Caso 3: Persistencia de Mensajes en el HUD
* ❌ **NO CUMPLE (Antipatrón - Texto Libre Ambiguo)**:  
  *"Las conversaciones del chat se tienen que guardar para que si recargo no se borren."*  
  *(Motivo del fallo: Lenguaje informal, omite la clave de almacenamiento y el evento disparador).*
* ✅ **CUMPLE (`EARS-EVT` - Event-Driven)**:  
  *"CUANDO se reciba o envíe un mensaje en el widget conversacional del HUD, el sistema Project deberá serializar y persistir el historial completo en `localStorage` bajo la clave `paco_hud_chat_messages_v1`."*

### Caso 4: Gobernanza de Código en Módulo de Desarrollo (Gate 2)
* ❌ **NO CUMPLE (Antipatrón - Prohibición Coloquial)**:  
  *"Los agentes no pueden tocar el código sin permiso del usuario."*  
  *(Motivo del fallo: No especifica qué rutas, qué mecanismo de fallo aplica ni qué excepción se lanza).*
* ✅ **CUMPLE (`EARS-UBI` + `EARS-UNW`)**:  
  *"El sistema Project deberá rechazar en modo *fail-closed* cualquier intento de modificación de archivos en `backend/`, `frontend/` o `DDBB/` SI la operación no cuenta con una aprobación humana explícita de Gate 2 registrada en sesión."*

### Caso 5: Temporizador de Silencio en Sesión de Voz
* ❌ **NO CUMPLE (Antipatrón - Temporizador Indefinido)**:  
  *"Si el usuario no dice nada después de que hable la IA, el micro se apaga al rato."*  
  *(Motivo del fallo: "¿Al rato?" es una ambigüedad intolerable; no especifica los segundos ni el estado).*
* ✅ **CUMPLE (`EARS-CMP` - Complex / Combined)**:  
  *"MIENTRAS la sesión de voz continua esté activa, SI transcurren 7 segundos en estado `listening` sin detección acústica de habla, ENTONCES el sistema Project deberá detener el micrófono y transicionar al estado visual `idle`."*

### Caso 6: Selección de Proveedor de Audio Opcional
* ❌ **NO CUMPLE (Antipatrón - Mezcla de Modos)**:  
  *"Usamos ElevenLabs si hay API key, pero si falla usamos el sintetizador local."*  
  *(Motivo del fallo: No desglosa la condición de presencia frente a la condición de error).*
* ✅ **CUMPLE (`EARS-OPT` + `EARS-UNW`)**:  
  *"DONDE la variable `ELEVENLABS_API_KEY` esté configurada en el entorno, el sistema Project deberá enrutar la síntesis vocal a través de ElevenLabs; SI la llamada remota falla o agota el timeout de 5 segundos, ENTONCES el sistema deberá conmutar automáticamente al sintetizador local sin interrumpir la experiencia."*

---

---

## 4. Metodologías Complementarias de Toma y Aterrizaje de Requisitos

Junto con EARS (que estandariza la *sintaxis*), se adoptan formalmente cuatro metodologías complementarias de ingeniería de requisitos para la interacción entre `@ai-architect` y el Stakeholder Humano:

```mermaid
flowchart LR
    A["1. Event Storming (DDD)"] -->|Eventos en pasado y comandos| B["2. Example Mapping (BDD)"]
    B -->|Reglas + Datos concretos + Dudas| C["3. Sintaxis EARS"]
    C -->|Comportamiento determinista del sistema| D["4. Planguage (Gilb)"]
    D -->|Métricas cuantitativas y SLAs sin adjetivos| E["5. Pre-Mortem (Klein)"]
    E -->|Anticipación de puntos ciegos y fallos| F["Gate 1 Aprobado"]
```

---

### Metodología A: Example Mapping (de Matt Wynne / BDD)
* **Definición**: Técnica estructurada que descompone una Historia de Usuario en cuatro componentes visuales de "Los Tres Amigos":
  1. **Story (Amarillo)**: La intención o capacidad perseguida.
  2. **Rules (Azul)**: Las reglas de negocio que gobiernan la historia (formuladas con EARS).
  3. **Examples (Verde)**: Ejemplos con **datos de entrada y salida reales y concretos** que ilustran las reglas.
  4. **Questions (Rojo)**: Incógnitas o dudas que el equipo o la IA no tienen claras todavía.
* **Propósito en IA**: Erradicar la tendencia de los LLM a redactar generalizaciones vacías y obligar a levantar tarjetas rojas (*preguntas al usuario*) en lugar de alucinar o inventar supuestos.

---

### Metodología B: Planguage (de Tom Gilb / Requisitos Cuantitativos)
* **Definición**: Lenguaje formal para especificar requisitos no funcionales, de rendimiento y de calidad, erradicando por completo adjetivos subjetivos (*"rápido"*, *"fácil"*, *"robusto"*, *"escalable"*).
* **Parámetros Canónicos**:
  - `Tag`: Identificador único del requisito de calidad (ej. `PERF-AUDIO-LATENCY-01`).
  - `Ambition`: Objetivo cualitativo de alto nivel.
  - `Scale`: Unidad de medida exacta y reproducible.
  - `Meter`: Procedimiento de medición automatizado (ej. test Playwright o pytest benchmark).
  - `Baseline`: Medida actual en el sistema antes del cambio.
  - `Target`: Meta numérica obligatoria que define el éxito.
  - `Constraint`: Umbral numérico inaceptable que provoca el fallo del sistema.

---

### Metodología C: Event Storming (de Alberto Brandolini / Domain-Driven Design)
* **Definición**: Modelado de dominio centrado en **Eventos de Dominio en pasado gramatical** (`VerboEnPasado`), comandos disparadores y modelos de lectura.
* **Propósito en IA**: Diseñar de forma natural arquitecturas orientadas a eventos como el Event Bus SSE de Project, asegurando que cada cambio de estado quede tipado, desacoplado y con secuencia temporal clara.

---

### Metodología D: Pre-Mortem Inverso (de Gary Klein / Ingeniería Estoica)
* **Definición**: Ejercicio contrafactual en Gate 1 que asume de antemano que la feature ha fallado estrepitosamente en producción a las pocas semanas de desplegarse, rastreando retrospectivamente las causas para blindar el diseño.
* **Propósito en IA**: Destruir el sesgo de optimismo y la complacencia de los agentes, identificando puntos ciegos operacionales (reinicio de contenedores, pérdida de red, concurrencia, permisos de disco).

---

## 5. Catálogo Contrastivo de Metodologías Complementarias: Cumple vs. No Cumple

### 5.1. Example Mapping (BDD)
* ❌ **NO CUMPLE (Antipatrón - Abstracción Genérica sin Datos)**:  
  *"El sistema debe verificar permisos antes de modificar un archivo y responder según lo que diga el usuario."*  
  *(Fallo: No hay datos reales de entrada, no define cómo se formatea la respuesta ni qué pasa si el usuario rechaza).*
* ✅ **CUMPLE (Example Mapping Canónico con Tabla de Datos Reales)**:  
  * **Regla (`EARS-UBI`)**: El sistema Project deberá requerir autorización interactiva antes de alterar cualquier archivo en producción.
  * **Ejemplo 1 (Éxito / Autorizado)**:
    - *Entrada*: `path="backend/src/main.py"`, `op="file_write"`
    - *Evento*: Emite `AcpPermissionRequest(id="req-01", type="file_write", target_path="backend/src/main.py")`
    - *Acción Usuario*: `POST /permission/respond` con `{ "requestId": "req-01", "decision": "allow" }`
    - *Salida Esperada*: Retorna HTTP 200 `{ "status": "success", "decision": "allowed" }`, escribe en disco y continúa el turno.
  * **Ejemplo 2 (Rechazo / Denegado)**:
    - *Acción Usuario*: `{ "requestId": "req-01", "decision": "deny" }`
    - *Salida Esperada*: Retorna HTTP 200 `{ "decision": "denied" }`, el archivo permanece inalterado y el orbe pasa a estado visual `awaiting_approval`.
  * **Pregunta Abierta (Tarjeta Roja)**:
    - *¿Qué ocurre si el usuario cierra la pestaña del navegador con una petición de permiso en vuelo?* ➔ *(Se registra en `OPEN-QUESTIONS.md` antes de Gate 1; no se asume).*

### 5.2. Planguage (Métricas Cuantitativas de Gilb)
* ❌ **NO CUMPLE (Antipatrón - Desiderata Subjetiva sin Métrica)**:  
  *"La latencia de síntesis vocal debe ser ultra-rápida, fluida e imperceptible para el usuario."*  
  *(Fallo: Palabras vacías imposibles de validar con una aserción booleana en un test automatizado).*
* ✅ **CUMPLE (Planguage Canónico con Parámetros Medibles)**:  
  - **Tag**: `PERF-AUDIO-LATENCY-01`
  - **Ambition**: Conversación de voz fluida sin silencios perceptibles tras hablar Project.
  - **Scale**: Milisegundos transcurridos desde el fin del habla del usuario (`webkitSpeechRecognition.onresult`) hasta la emisión del primer paquete de audio decodificado en `AudioContext`.
  - **Meter**: Test E2E de Playwright midiendo marcas `performance.now()`.
  - **Baseline**: 1450 ms (usando síntesis remota sin optimizar en `v0.1.0`).
  - **Target**: < 250 ms (empleando `eleven_flash_v2_5` o `MockTTSProvider` local).
  - **Constraint**: Nunca superior a 500 ms (si supera 500 ms, el orbe debe modular en estado `thinking` visible).

### 5.3. Event Storming (DDD Reactivo)
* ❌ **NO CUMPLE (Antipatrón - Mezcla Imperativa Difusa)**:  
  *"El backend procesa la pregunta, consulta las herramientas y le manda los trozos al frontend para que los pinte."*  
  *(Fallo: No hay eventos explícitos en pasado, no define si es batch o stream, ni el contrato de transición).*
* ✅ **CUMPLE (Event Storming Canónico - Flujo Monótono de Eventos en Pasado)**:  
  1. `Comando`: `EnviarEntradaUsuario(content, session_id)`
  2. `Evento 1`: `TurnoAgénticoIniciado` ➔ EventBus emite `state_changed` (`visualState="thinking"`).
  3. `Evento 2`: `HerramientaEjecutada` ➔ EventBus emite `tool_call_completed` (`tool="get_backlog_status"`).
  4. `Evento 3`: `DeltaMensajeEmitido` ➔ EventBus emite `message_delta` (`delta="...", done=false`).
  5. `Evento 4`: `TurnoAgénticoCompletado` ➔ EventBus emite `message_delta` (`done=true`) con telemetría de tokens.
  6. `Evento 5`: `AudioReproducido` ➔ Orbe transiciona a `speaking` y modula niveles RMS a 60 FPS.
  7. `Evento 6`: `AudioFinalizado` ➔ Orbe transiciona a `idle` y reactiva escucha (`listening`).

### 5.4. Pre-Mortem Inverso (Ingeniería de Resiliencia)
* ❌ **NO CUMPLE (Antipatrón - Confianza Ciega en el Happy Path)**:  
  *"El montaje de repositorios funciona porque docker-compose.yml ya tiene el volumen configurado y en mi máquina local no falla."*  
  *(Fallo: Ignora diferencias de SO, caídas de contenedor, permisos en Linux/TrueNAS ZFS y saturación de I/O).*
* ✅ **CUMPLE (Pre-Mortem Inverso Canónico - Post-Mortem Anticipado)**:  
  * **Escenario de Catástrofe**: *"Estamos a 15 días tras el despliegue en TrueNAS SCALE. El usuario intenta inspeccionar el proyecto Nexus desde el HUD y la aplicación colapsa con error HTTP 500 o timeout infinito. ¿Qué falló?"*.
  * **Causa Oculta 1**: El daemon de Docker en TrueNAS reinició y los permisos de `/repo` se montaron con UID 1000, dejando al usuario del contenedor sin permisos de lectura.
    - ➔ **Mitigación en Gate 1 (`RN-PERM-01`)**: El contenedor corre con UID no root compatible y el `entrypoint.sh` audita permisos de lectura antes de arrancar Uvicorn.
  * **Causa Oculta 2**: La exploración recursiva de archivos en proyectos grandes con 50.000 ficheros en `node_modules` bloquea el event-loop de FastAPI.
    - ➔ **Mitigación en Gate 1 (`RN-WORKSPACE-02`)**: Exclusión obligatoria e instantánea en disco de `node_modules`, `.git`, `__pycache__` antes de cualquier iteración de árbol.

---

## 6. Matriz de Roles y Reglas de Actuación de los Agentes

### `@functional-analyst` (Redactor Funcional Principal en Gate 1)
1. Actúa como interlocutor y copiloto del Product Owner (PO) en la extracción y refinamiento de requerimientos.
2. Registra formalmente todas las fuentes de información (`SRC-###`), reconociendo el chat como evidencia válida.
3. Identifica proactivamente ambigüedades, contradicciones o vacíos y los registra en la tabla `AMB-###` para su resolución con el PO antes de cerrar la spec.
4. Redacta obligatoriamente todos los requisitos funcionales (`RF-###`) bajo los 5 patrones canónicos EARS y sus criterios de aceptación BDD Given-When-Then.
5. Mantiene una frontera hermética 100% funcional (prohibido especificar tecnologías, endpoints, esquemas SQL o implementaciones).

### `@ai-architect` (Arquitecto Cognitivo y Co-firmante en Gate 1)
1. Recibe el borrador funcional de `@functional-analyst` y evalúa la viabilidad cognitiva de los requisitos (modelos LLM, prompt caching, RAG híbrido, herramientas MCP).
2. Al co-firmar [`01-spec.md`](file:///c:/Projects/sdd-agentic-starter/specs/templates/01-functional-spec.template.md):
   - **Sección 4**: Obligatoriamente en formato de tabla EARS (`RF-###`).
   - **Sección 4.2**: Tabla de Example Mapping con datos reales de entrada y salida (éxito y fallo).
   - **Sección 4.3**: Requisitos no funcionales en formato Planguage con metas numéricas exactas (`Target`, `Constraint`).
   - **Sección 6**: Ejercicio de Pre-Mortem identificando al menos 2 modos de fallo catastrófico y sus mitigaciones.
3. Prohibido usar adjetivos subjetivos ("rápido", "intuitivo", "eficiente", "adecuado") sin métrica Planguage o condición EARS.

### `@orchestrator` (Auditor de Entrada en Gate 2 — Definition of Ready)
1. Antes de iniciar [`02-tech-spec.md`](file:///c:/Projects/sdd-agentic-starter/specs/templates/02-technical-spec.template.md), `@orchestrator` audita la lista de requisitos de `01-spec.md`.
2. **Criterio Stop-the-Line**: Si detecta un solo requisito que sea texto libre o carezca de cláusulas EARS, métricas Planguage o ejemplos concretos, **rechaza el paso a Gate 2** y devuelve el ticket a `@functional-analyst` y `@ai-architect`.
3. `@orchestrator` traduce directamente:
   - `WHILE` ➔ Máquinas de estado en Zustand / Enum FSM Python.
   - `WHEN` ➔ Event handlers, listeners SSE, endpoints REST.
   - `IF / THEN` ➔ `try/except`, validaciones Pydantic, HTTP Status Codes (400, 403, 404, 500).
   - `WHERE` ➔ Feature flags en `settings.py` / condicionales de entorno.
   - `Meter (Planguage)` ➔ Aserciones numéricas en tests automáticos de pytest o vitest.

### `@documentator` (Custodio de la Documentación Viva)
1. Toda regla de negocio consolidada en [`docs/es/02-functional/BUSINESS-RULES.md`](file:///c:/Projects/sdd-agentic-starter/docs/es/02-functional/BUSINESS-RULES.md) debe mantener la formulación canónica EARS.
2. Todos los SLAs de rendimiento se documentan en tablas Planguage en [`docs/es/05-quality-and-acceptance/`](file:///c:/Projects/sdd-agentic-starter/docs/es/05-quality-and-acceptance/).
