# Sistema de Buzón Asíncrono de Agentes (.agent-inbox)

Este directorio implementa el patrón de buzones asíncronos para el desacoplamiento de tareas en el desarrollo multi-agente SDD.

## Estructura de Buzones
- `orchestrator/`: Tareas de coordinación, revisión de puertas y desbloqueo.
- `architect/`: Tareas de diseño de contratos, interfaces, esquemas de datos y ADRs.
- `back-engineer/`: Tareas de desarrollo de backend, APIs, persistencia y lógica de negocio.
- `front-engineer/`: Tareas de interfaz de usuario, componentes, maquetación y accesibilidad.
- `qa-tester/`: Tareas de pruebas unitarias, de integración, BDD y auditorías de cobertura.
- `documentator/`: Tareas de documentación viva (0DD), catálogo de APIs y matriz de trazabilidad.

## Formato de Ticket de Tarea (TICKET-XXX-slug.md)
Cada tarea delegada mediante la skill `opsx-delegate` debe cumplir con la siguiente estructura:

```markdown
# TICKET-XXX: [Título de la Tarea Atómica]

- **Work Item**: FEAT-XXX / CR-XXX / BUG-XXX
- **Agente Asignado**: @agente-destinatario
- **Estado**: PENDING | IN_PROGRESS | DONE
- **Prioridad**: BLOCKER | HIGH | MEDIUM | LOW
- **Dependencias**: [TICKET-YYY] (o None)

---

### 1. Definición de Listo (Definition of Ready - DoR)
- [x] Especificación técnica (Gate 2) formalmente aprobada.
- [x] Contratos de entrada y salida rigurosamente tipados.
- [x] Dependencias previas resueltas y verificadas.

### 2. Alcance Exacto y Ficheros Afectados
- `src/...`: [Descripción de la modificación]

### 3. Criterio de Aceptación y Definición de Hecho (DoD)
- [ ] Implementación conforme al contrato sin invención de alcance.
- [ ] Comando de verificación exitoso: `[comando de test del stack]`
- [ ] Cero fallos silenciosos y tipado estricto.
```
