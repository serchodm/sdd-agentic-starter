# Regla 00: Bloqueo de Stack Tecnológico, Ownership Map y Bootstrap (Gate S0 / Legacy Gate 00)

> **NORMA DE SEGURIDAD ABSOLUTA:** El código de producción y tests permanece en estado **ESTRICTAMENTE BLOQUEADO** hasta que el stack técnico, la arquitectura, el Ownership Map y el escuadrón agéntico hayan sido formalmente acordados y firmados en `specs/STACK.md` (`[x] Gate S0 Approved`, aceptándose `[x] Gate 00 Approved` como alias legacy).

---

## 1. Motivo y Justificación
Desarrollar sin definir el stack provoca código incompatible, agentes desorientados, dependencias parásitas y retrabajo masivo. El Gate S0 (Stack Lock) garantiza que antes de la primera línea de especificación o código, se conocen con total certeza las herramientas de trabajo, el destino de hosting (Cloud, Docker, Vercel/PaaS), el ciclo CI/CD, los comandos deterministas DoD y los dueños de cada zona de código.

---

## 2. Protocolo de Disparo del Asistente de Bootstrap (`sdd-bootstrap`)

1. **Detección Automática (Fail-Closed):**
   - Siempre que `specs/STACK.md` contenga `[ ] Gate S0 Approved (Human Sign-off)` (o su alias legacy `[ ] Gate 00 Approved`), el `@orchestrator` tiene prohibido aceptar tareas de programación o redactar features en `specs/BACKLOG.md`.
   - Ante cualquier petición de inicio de proyecto o saludo inicial, el `@orchestrator` activará la skill `.agents/skills/sdd-bootstrap/SKILL.md`.

2. **Ejecución del Asistente:**
   - Se ejecuta el cuestionario interactivo de 10 dimensiones con **poda dinámica en árbol**:
     - Las respuestas tempranas (ej: *Solo Backend*, *Solo Frontend*, *Stateless*) podan automáticamente las ramas irrelevantes.
     - Se configuran las directrices para Cloud, Contenedores Docker o plataformas PaaS/Serverless (Vercel, Netlify, Railway).
   - Se congela la Sección 2.5 de **Comandos Deterministas de Verificación DoD** (lint, test unitario <1s, integración, build) para eliminar el overhead de descubrimiento.
   - Se genera el **Ownership Map (§3.2)** asignando un único agente constructor por zona de código con sus imports prohibidos y comandos DoD.
   - Se ejecuta `python scripts/sdd_agent_generator.py --materialize` para compilar los agentes constructores y activar los stack packs requeridos desde `.sdd/catalog/`.

---

## 3. Criterios Estrictos de Aprobación de Gate S0
`specs/STACK.md` debe estar formalmente redactado y contar con:
- Topología, hosting y unidad de empaquetado definidas.
- Tecnologías core de Backend, Frontend y Persistencia (o marcadas como N/A explícitamente).
- Comandos deterministas DoD verificados en la Sección 2.5.
- Ownership Map (§3.2) sin zonas huérfanas ni solapes.
- Golden Samples canónicos de código limpio (Do) vs antipatrones prohibidos (Don't).
- Casilla `[x] Gate S0 Approved (Human Sign-off)` (o alias legacy `[x] Gate 00 Approved`) marcada exclusivamente tras la confirmación expresa del usuario en el chat.

---

## 4. Guardia Mecánica
La herramienta `.agents/scripts/sdd_code_gate_guard.py` comprobará el estado de `specs/STACK.md`. Cualquier intento de edición sobre código de producción o tests será rechazado de inmediato si Gate S0 no está superado.
