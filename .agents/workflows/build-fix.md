---
description: Repara quirúrgicamente errores de compilación, tipos o tests con el diff mínimo respetando 02-tech-spec.md.
---

# Workflow `/build-fix` (`@build-error-resolver` / Builder)

1. **Aislar Error:** Reproducir con los comandos DoD de `specs/STACK.md` (§2.5: lint, typecheck, test o build).
2. **Diagnosticar:** Clasificar import roto, desajuste de contrato espejo (`snake_case`/`camelCase`), nulabilidad o firma de mock.
3. **Diff Mínimo:** Corregir solo las líneas afectadas según `02-tech-spec.md` (prohibido `any` o `# type: ignore` / `@ts-ignore`).
4. **Re-Verificar:** Re-ejecutar hasta obtener `exit code 0`.
