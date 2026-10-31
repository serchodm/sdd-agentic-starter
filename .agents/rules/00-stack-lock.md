# Regla 00: Bloqueo de Stack Tecnológico y Asistente Bootstrap (Gate 00)

> **NORMA DE SEGURIDAD ABSOLUTA:** El repositorio permanece en estado **BLOQUEADO** hasta que el stack técnico, la arquitectura y el escuadrón agéntico hayan sido formalmente acordados y firmados en `specs/STACK.md`.

---

## 1. Motivo y Justificación
Desarrollar sin definir el stack provoca código incompatible, agentes desorientados, dependencias parásitas y retrabajo masivo. El Gate 00 garantiza que antes de la primera línea de especificación o código, se conocen con total certeza las herramientas de trabajo, el destino de hosting (Cloud, Docker, Vercel/PaaS), el ciclo CI/CD y los roles activos.

---

## 2. Protocolo de Disparo del Asistente de Bootstrap (`sdd-bootstrap`)

1. **Detección Automática (Fail-Closed):**
   - Siempre que `specs/STACK.md` contenga `[ ] Gate 00 Approved (Human Sign-off)`, el `@orchestrator` tiene prohibido aceptar tareas de programación o redactar features en `specs/BACKLOG.md`.
   - Ante cualquier petición de inicio de proyecto o saludo inicial, el `@orchestrator` activará la skill `.agents/skills/sdd-bootstrap/SKILL.md`.

2. **Ejecución del Asistente:**
   - Se ejecuta el cuestionario interactivo de 10 dimensiones con **poda dinámica en árbol**:
     - Las respuestas tempranas (ej: *Solo Backend*, *Solo Frontend*, *Stateless*) podan automáticamente las ramas irrelevantes.
     - Se configuran las directrices para Cloud, Contenedores Docker o plataformas PaaS/Serverless (Vercel, Netlify, Railway).
   - Se genera `specs/STACK.md` con los Golden Samples (Do's & Don'ts) y la matriz del **Escuadrón Agéntico**.

---

## 3. Criterios Estrictos de Aprobación de Gate 00
`specs/STACK.md` debe estar formalmente redactado y contar con:
- Topología, hosting y unidad de empaquetado definidas.
- Tecnologías core de Backend, Frontend y Persistencia (o marcadas como N/A explícitamente).
- Matriz del Escuadrón Agéntico con roles `ACTIVO` o `INACTIVO (N/A)`, directorios permitidos y comandos CLI asignados.
- Golden Samples canónicos de código limpio (Do) vs antipatrones prohibidos (Don't).
- Casilla `[x] Gate 00 Approved (Human Sign-off)` marcada exclusivamente tras la confirmación expresa del usuario en el chat.

---

## 4. Guardia Mecánica
La herramienta `.agents/scripts/sdd_code_gate_guard.py` comprobará el estado de `specs/STACK.md`. Cualquier intento de edición sobre `src/` será rechazado de inmediato si Gate 00 no está superado.
