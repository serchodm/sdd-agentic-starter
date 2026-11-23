---
description: Ejecuta doble verificación adversaria independiente (Santa Method: Checking It Twice) en Pre-Gate 2, Gate 4 o Gate 5 hasta veredicto NICE unánime.
---

# Workflow `/santa-loop` (*Santa Method*)

Sigue estrictamente `.agents/skills/santa-method/SKILL.md` junto con sus referencias (`references/reviewer-prompt.md` y `references/sdd-rubrics.md`):

1. **Capa 1 Determinista (si es Gate 4):** Confirmar en verde los comandos DoD de `specs/STACK.md §2.5`, `verify_architecture_boundaries.py` y `sdd_healthcheck.py` antes de invocar Santa.
2. **Construir *The List*:** Seleccionar la frontera activa (`PRE_GATE_2`, `GATE_4` o `GATE_5`), su rúbrica binaria en `references/sdd-rubrics.md` y particionar en lotes coherentes (*Chunked Santa* / *Batch Sampling*) si supera el umbral de longitud.
3. **Doble Revisión Aislada en Paralelo:** Lanzar **Revisor B** y **Revisor C** como subagentes frescos en modo solo-lectura con **idéntica rúbrica binaria**, mismos inputs y salida JSON estructurada (`references/reviewer-prompt.md`), sin contexto compartido.
4. **Verdict Gate & Fix Cycle:**
   - **`NICE + NICE`** (0 `critical_issues` y 0 `upstream_spec_conflicts`) $\rightarrow$ certificar la frontera de Gate.
   - Cualquier **`NAUGHTY`** $\rightarrow$ si hay `upstream_spec_conflicts` en `PRE_GATE_2`, escalar al humano (no auto-editar `01-spec.md`); si no, fusionar y deduplicar `critical_issues`, aplicar Fix Cycle estricto (*solo issues marcados*), re-verificar Capa 1 si tocó código y relanzar **2 revisores frescos** (máx. 3 rondas antes de escalar al usuario y persistir estado en `.agents/ACTIVE_STATE.md`).
