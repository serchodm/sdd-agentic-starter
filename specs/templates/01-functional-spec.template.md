# Especificación Funcional: [Título de la Feature]

- **ID de la Feature**: [Ej. FEAT-006-declarative-agents]
- **Estado**: [Draft | In Review | Approved | Done]
- **Analista Funcional (Ingeniería de Requisitos)**: `@functional-analyst`
- **Arquitecto Cognitivo / IA**: `@ai-architect`
- **Tech Lead**: `@orchestrator`
- **Fecha de Creación**: YYYY-MM-DD
- **Última Actualización**: YYYY-MM-DD

---

## 1. Resumen, Contexto y Claridad Epistémica (`morluto/rea`)
- **Problema y Valor de Negocio**: [Descripción concisa de la funcionalidad y el valor medible que aporta.]
- **Hechos Observados (Observations)**: [Contratos existentes, tablas actuales o paquetes verificados en el workspace.]
- **Restricciones Derivadas (Derivations)**: [Límites deterministas impuestos por arquitectura o hardware.]

---

## 1.1. Fuentes Registradas y Trazabilidad (`SRC-###`)
> El chat con el usuario / PO es fuente válida y suficiente. Registrar todas las fuentes de origen:

| ID Fuente | Tipología / Origen | Fecha | Notificado por | Descripción / Contenido Facilitado |
|---|---|---|---|---|
| `SRC-001` | Chat / Directriz PO | YYYY-MM-DD | Usuario (PO) | [Requerimiento o necesidad comunicada en conversación] |

---

## 1.2. Registro de Ambigüedades y Cuestiones Pendientes (`AMB-###`)
> Aplicar Stop-the-Line ante cualquier vacío funcional o contradicción antes de autorizar Gate 1:

| ID | Descripción de la Ambigüedad / Conflicto | Requisitos Afectados | Pregunta Directa para el PO | Impacto Funcional | Estado |
|---|---|---|---|---|---|
| `AMB-001` | [Descripción objetiva de la duda o caso de borde] | `RF-001` | [Pregunta clara de negocio sin jerga técnica] | [Pantalla / flujo bloqueado] | `Open` / `Resolved` |

---

## 2. Historias de Usuario y Casos de Uso

### Historia 1: [Título de la Historia]
> **Como** [tipo de usuario o rol],
> **Quiero** [acción o capacidad deseada],
> **Para que** [beneficio o valor obtenido].

### Historia 2: [Título de la Historia]
> **Como** [tipo de usuario o rol],
> **Quiero** [acción o capacidad deseada],
> **Para que** [beneficio o valor obtenido].

---

## 3. Alcance (Scope)

### ✅ Dentro del Alcance (In-Scope)
- [Funcionalidad o capacidad 1]
- [Funcionalidad o capacidad 2]
- [Validación o comportamiento 3]

### 🚫 Fuera del Alcance (Out-of-Scope)
- [Lo que expresamente NO se implementará en esta versión/iteración]
- [Funcionalidades postergadas para futuras fases]

---

## 4. Requisitos del Sistema bajo Protocolo EARS (Easy Approach to Requirements Syntax)
> ⚠️ **Obligatorio para `@functional-analyst` y `@ai-architect`**: Todo requisito y regla de negocio debe formularse siguiendo uno de los patrones canónicos EARS ([`.agents/rules/03-ears-requirements.md`](file:///c:/Projects/sdd-agentic-starter/.agents/rules/03-ears-requirements.md)). `@orchestrator` auditará esta tabla como Definition of Ready antes de autorizar Gate 2.

| ID Requisito | Fuente | Patrón EARS | Cláusula EARS (Sintaxis Formal Canónica) | Componente Afectado |
|---|---|---|---|---|
| `RF-001` | `SRC-001` | `Ubiquitous` | `El sistema [Sistema] deberá [comportamiento global permanente]` | [Core / Seguridad] |
| `RF-002` | `SRC-001` | `Event-driven` | `CUANDO [evento disparador / orden], el sistema [Sistema] deberá [respuesta]` | [API / UI] |
| `RF-003` | `SRC-001` | `State-driven` | `MIENTRAS [el sistema esté en estado X], el sistema [Sistema] deberá [respuesta]` | [FSM / Audio / UI] |
| `RF-004` | `SRC-001` | `Unwanted` | `SI [condición anómala, timeout o error], ENTONCES el sistema [Sistema] deberá [respuesta fail-closed]` | [Error Handling] |
| `RF-005` | `SRC-001` | `Optional` | `DONDE [funcionalidad o API key esté configurada], el sistema [Sistema] deberá [respuesta]` | [Config / Plugins] |
| `RF-006` | `SRC-001` | `Complex` | `MIENTRAS [estado], CUANDO/SI [evento o silencio], el sistema [Sistema] deberá [respuesta]` | [Multi-Estado] |

---

## 4.1. Reglas de Negocio Vinculantes (`RN-###`)
1. **RN-01 [Nombre de la Regla]**: [Descripción detallada de la restricción, cálculo o validación obligatoria derivada de los requisitos EARS].
2. **RN-02 [Nombre de la Regla]**: [Descripción detallada].

---

## 4.2. Example Mapping (Datos Concretos de Entrada / Salida)
> Desglosar al menos un ejemplo de éxito y un ejemplo de fallo con datos reales para cada regla clave:

| Regla Asociada | Caso de Ejemplo | Datos de Entrada (Input Real) | Estado / Precondición | Salida Esperada (Output Verificable) |
|---|---|---|---|---|
| `RN-01` | Éxito Nominal | `[ej. payload exacto, texto o path]` | `[ej. usuario autenticado]` | `[ej. HTTP 200, evento emitido, registro en BD]` |
| `RN-01` | Fallo / Borde | `[ej. valor nulo, timeout o sin permisos]` | `[ej. token expirado]` | `[ej. HTTP 403, fail-closed, log estructurado]` |

---

## 4.3. Requisitos No Funcionales y SLAs Cuantitativos (Planguage)
> Prohibido el uso de adjetivos subjetivos ("rápido", "ligero", "escalable"). Todo SLA debe ser numérico:

- **Tag**: `PERF-[NOMBRE]-01`
  - **Ambition**: [Objetivo cualitativo de alto nivel]
  - **Scale**: [Unidad de medida exacta, ej. ms, MB, porcentaje]
  - **Meter**: [Método de prueba automatizado, ej. test Playwright / benchmark pytest]
  - **Baseline**: [Valor actual previo]
  - **Target**: [Valor objetivo que define el éxito, ej. < 250ms]
  - **Constraint**: [Límite inaceptable de fallo, ej. > 500ms]

---

## 5. Criterios de Aceptación (BDD / Given-When-Then)

### Escenario 1: [Flujo Exitoso Principal]
- **Dado que** [estado inicial del sistema]
- **Cuando** [se emite una orden o se ejecuta una acción]
- **Entonces** [el sistema responde con el resultado esperado]
- **Y** [se persiste el estado o evento correspondiente]

### Escenario 2: [Manejo de Error o Límite (Fail-Closed)]
- **Dado que** [estado inicial]
- **Cuando** [falla un servicio externo o se viola una restricción]
- **Entonces** [el sistema rechaza la operación de forma segura e informa el motivo estructurado]

---

## 6. Pre-Mortem Inverso (Anticipación de Puntos Ciegos y Fallos)
> *"Supongamos que estamos a 3 semanas del despliegue en producción y la feature ha fallado catastróficamente. ¿Qué causó el desastre?"*

1. **Escenario de Fallo Catastrófico 1**: [Descripción del desastre operacional o bug crítico]
   - **Causa Oculta**: [Factor no previsto: concurrencia, permisos de disco, corte de red, cuota de API]
   - **Mitigación Preventiva en Gate 1**: [Regla de negocio o validación incorporada para impedir que ocurra]
2. **Escenario de Fallo Catastrófico 2**: [Descripción del desastre]
   - **Causa Oculta**: [Factor no previsto]
   - **Mitigación Preventiva en Gate 1**: [Mitigación incorporada]

---

## 7. Incógnitas y Decisiones Pendientes (`NOT_ENOUGH_INFO` — Tarjetas Rojas / Stop-the-Line)
- [ ] [Pregunta o alternativa de diseño pendiente de confirmar por el usuario; debe quedar resuelta antes de cerrar Gate 1]

---

## 8. Aprobación Formal Gate 1 (`RN-SDD-HUMAN-GATE-OWNERSHIP`)
> ⚠️ **Exclusivo para el Stakeholder Humano** (Los agentes de IA tienen prohibido marcar esta casilla por su cuenta):
- [ ] **Gate 1 Approved (Human Sign-off):** El alcance funcional, requisitos EARS, ejemplos concretos, métricas Planguage y criterios BDD han sido revisados y validados.
