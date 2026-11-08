---
description: Repara quirúrgicamente errores de compilación, tipos o tests (py_compile, pytest, tsc --noEmit, vite build) con el diff mínimo.
---

# Workflow `/build-fix` — Resolución Quirúrgica de Errores de Compilación (`@build-error-resolver`)

Ejecuta este workflow cuando cualquier comando de verificación DoD falle en backend o frontend.

## Pasos de Ejecución

1. **Reproducir y Aislar la Traza de Error**:
   - Backend: `uv run --project backend python -m py_compile <archivos>` y `uv run --project backend pytest <ruta_test> -q`.
   - Frontend: `cd frontend && npx tsc --noEmit` y `cd frontend && npm run build`.
2. **Diagnosticar Causa Raíz sin Rediseñar**:
   - Clasificar cada fallo: importación rota, discrepancia de nombre en contrato espejo (`snake_case` vs `camelCase`), tipo nulo no controlado o firma desactualizada en mock.
3. **Aplicar el Diff Mínimo (`@build-error-resolver`)**:
   - Editar exclusivamente las líneas afectadas respetando `02-tech-spec.md`. Prohibido usar `any` o desactivar reglas del compilador.
4. **Re-Verificar en Verde**:
   - Volver a ejecutar los comandos del Paso 1 hasta obtener salida 100% limpia (`exit code 0`).
