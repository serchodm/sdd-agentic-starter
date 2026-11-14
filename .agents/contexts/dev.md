---
name: dev
description: Contexto de Implementación Activa (Gate 4, affaan-m/ECC) orientado a código tipado, TDD y verificación DoD.
---

# Contexto: `dev.md` (Gate 4)

- **Foco:** Código limpio y tipado 1:1 con `02-tech-spec.md` y `03-tasks.md`, respaldado por pruebas deterministas.
- **Reglas de Ejecución:**
  1. Respetar exactamente DTOs, firmas e interfaces selladas en `02-tech-spec.md`.
  2. Ciclo corto código $\rightarrow$ comando DoD de `specs/STACK.md` (§2.5).
  3. Cero fallos silenciosos; usar tipos explícitos y logging estructurado.
  4. Lectura acotada (`view_file` por rangos) $\rightarrow$ edición mínima $\rightarrow$ verificación.
