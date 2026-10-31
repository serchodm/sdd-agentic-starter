# Regla 00: Bloqueo de Stack Tecnológico (Gate 00 Bootstrap)

> **NORMA DE SEGURIDAD ABSOLUTA:** El repositorio permanece en estado BLOQUEADO hasta que el stack técnico haya sido acordado y formalmente firmado en `specs/STACK.md`.

## 1. Motivo y Justificación
Desarrollar sin definir el stack provoca código incompatible, agentes desorientados, deuda técnica y retrabajo masivo. El Gate 00 garantiza que antes de la primera línea de especificación o código, se conocen con total certeza las herramientas de trabajo.

## 2. Criterios de Aprobación de Gate 00
`specs/STACK.md` debe estar relleno y contar con la firma humana:
- Lenguaje y versión del Backend (o N/A si es solo front/estático).
- Framework y biblioteca de Frontend (o HTML5 vanilla, etc.).
- Motor de base de datos o almacenamiento de persistencia (o N/A).
- Herramientas de pruebas y comandos de ejecución (`test_runner_command`).
- Casilla `[x] Gate 00 Approved (Human Sign-off)` marcada tras confirmación del usuario.

## 3. Guardia Mecánica
La herramienta `sdd_code_gate_guard.py` comprobará el estado de `specs/STACK.md`. Cualquier intento de edición sobre `src/` será rechazado de inmediato si Gate 00 no está superado.
