---
name: dev
description: Modo de contexto de Implementación Activa (Gate 4) de affaan-m/ECC orientado a construcción limpia, TDD y verificación determinista DoD.
---

# Contexto Operativo: `dev.md` (Modo Implementación — Gate 4)

- **Modo**: Desarrollo e Implementación Activa (`Gate 4`).
- **Foco Principal**: Construir código limpio, tipado y alineado 1:1 con `02-tech-spec.md` y `03-tasks.md`, respaldado por pruebas unitarias deterministas.

## Comportamiento en Modo `dev`
1. **Respeto Estricto a Contratos Sellados**: Implementar exactamente las firmas, DTOs (`camelCase`) e interfaces especificadas en `02-tech-spec.md`.
2. **Ciclo Corto Código $\rightarrow$ Verificación**: Tras cada archivo creado o editado, ejecutar el comando determinista de compilación o test (`py_compile`, `pytest`, `tsc --noEmit`, `vitest`).
3. **Cero Fallos Silenciosos**: Manejar errores explícitamente con logs estructurados y tipos seguros.
4. **Prioridad de Herramientas**: `read_file` (acotado al ámbito) $\rightarrow$ `write_file` / `edit_file` $\rightarrow$ `run_command` (verificación DoD).
