# Referencia `santa-method`: Prompts, Verdict Gate y Fix Cycle

## 1. Inputs (*The List*) por Gate

`@orchestrator` entrega el **mismo paquete compacto** a Revisor B y Revisor C:
- **`PRE_GATE_2`:** `01-spec.md`, `02-tech-spec.md`, secciones aplicables de `specs/STACK.md` y `docs/knowledge/`.
- **`GATE_4`:** *The List* (EARS/BDD de `01-spec.md`, contratos de `02-tech-spec.md`, tareas de `03-tasks.md`), ficheros tocados y confirmación de Capa 1 Determinista en verde.
- **`GATE_5`:** Ficheros actualizados en `docs/es/`, `docs/en/`, `docs/knowledge/`, `TRACEABILITY-MATRIX.md`, `specs/BACKLOG.md` y resumen de cambios reales.

## 2. Prompt Adversario (Revisor B y Revisor C en Paralelo)

Lanzar **dos subagentes frescos en paralelo** (solo lectura, sin contexto compartido):

```markdown
Eres un revisor independiente SDD (Santa Reviewer). NO has visto otra revisión ni creaste este entregable.

## Contexto
- Gate: {PRE_GATE_2 | GATE_4 | GATE_5} | Work Item: {WORK_ITEM_ID} | Alcance: {FULL | CHUNK_NAME}

## The List (Fuente de Verdad)
{TASK_SPEC_AND_THE_LIST}

## Entregable Bajo Revisión
{OUTPUT_OR_FILE_PATHS}

## Rúbrica Binaria Obligatoria
{RUBRIC_FROM_SDD_RUBRICS_MD}

## Instrucciones
1. Verifica CADA criterio contra los ficheros reales en disco.
2. Emite `PASS` (sin bloqueantes) o `FAIL` (defecto verificable con `archivo:línea` o sección).
3. Actitud adversaria: busca fallos reales, contradicciones, fallos silenciosos y alucinaciones; NO apruebes por cortesía.
4. Preferencias de estilo van en `suggestions`, nunca en `FAIL`.
5. En `PRE_GATE_2`, si un defecto nace en `01-spec.md` ya aprobado, añádelo a `upstream_spec_conflicts`.

## Salida Obligatoria (JSON estricto)
{
  "verdict": "PASS" | "FAIL",
  "gate": "PRE_GATE_2" | "GATE_4" | "GATE_5",
  "scope": "...",
  "checks": [
    {"criterion": "<id>", "result": "PASS" | "FAIL", "evidence": "<archivo:línea>", "detail": "<hallazgo>"}
  ],
  "critical_issues": ["[<id>] <archivo:línea> — <defecto bloqueante>"],
  "suggestions": ["<mejora no bloqueante>"],
  "upstream_spec_conflicts": ["<solo PRE_GATE_2 si el defecto está en 01-spec.md>"]
}
```

**Coherencia:** Cualquier `result == "FAIL"`, `critical_issues` o `upstream_spec_conflicts` no vacío obliga a `"verdict": "FAIL"`.

## 3. Verdict Gate (`NICE` vs. `NAUGHTY`)

- **`NICE`:** Solo si `review_b.verdict == "PASS"` **AND** `review_c.verdict == "PASS"` con 0 `critical_issues` y 0 `upstream_spec_conflicts` en ambos.
- **`NAUGHTY`:** Cualquier otro caso. Deduplicar `all_critical_issues = dedupe(B + C)` y `all_suggestions = dedupe(B + C)` (informativo). Si hay `upstream_spec_conflicts` en `PRE_GATE_2`, escalar al humano sin editar `01-spec.md`.

## 4. Fix Prompt Estricto (Fase 4)

```markdown
## Fix Cycle — Santa Method (Ronda {ITERATION}/3)
### Defectos Bloqueantes (`critical_issues`)
{DEDUPED_CRITICAL_ISSUES}
### Reglas
1. Corrige ÚNICAMENTE los `critical_issues` listados.
2. PROHIBIDO refactorizar, renombrar fuera de alcance o añadir cambios no solicitados.
3. En Gate 4, re-ejecuta los comandos DoD (`specs/STACK.md §2.5`) afectados y confirma verde.
4. Devuelve ficheros modificados y qué issue resuelve cada cambio.
```

Tras el fix, relanzar **2 revisores nuevos** (sin historial previo). Al agotar 3 rondas, persistir en `.agents/ACTIVE_STATE.md` y escalar al usuario.

## 5. Patrones y Métricas Opcionales

- **Patrón A (Recomendado):** Subagentes paralelos (`invoke_subagent` / `runSubAgent`).
- **Patrón B (Fallback sin subagentes):** Revisor 1 en contexto limpio $\rightarrow$ guardar JSON $\rightarrow$ limpiar contexto $\rightarrow$ Revisor 2 en contexto limpio.
- **Métricas (opcionales):** *First-pass rate* ($>70\%$), *Mean iterations* ($<1.5$), *Issue taxonomy* ($\rightarrow$ `sdd_instincts.py record`), *Reviewer agreement* (baja coincidencia $\rightarrow$ endurecer rúbrica).
