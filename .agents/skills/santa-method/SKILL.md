---
name: santa-method
description: Protocolo de doble verificación adversaria independiente (Checking It Twice) en Pre-Gate 2, Gate 4 y Gate 5: exige veredicto NICE unánime de dos revisores aislados con idéntica rúbrica binaria y agentes frescos por ronda.
---

# Skill: `santa-method` (*Checking It Twice*)

Verificación adversaria multiagente que rompe sesgos y puntos ciegos mediante dos revisores aislados sin contexto compartido evaluando la **misma rúbrica binaria completa**.

> **Referencias (carga al ejecutar):** [references/reviewer-prompt.md](references/reviewer-prompt.md) (prompts JSON, Verdict Gate, Fix Cycle) y [references/sdd-rubrics.md](references/sdd-rubrics.md) (rúbricas `PRE_GATE_2`, `GATE_4`, `GATE_5`).

## 1. Triggers Objetivos y Exclusiones

**Capa 1 antes que Capa 2 (obligatorio):** Santa verifica calidad **semántica**, nunca sustituye checks deterministas. En Gate 4 ejecutar primero `specs/STACK.md §2.5` (DoD), `verify_architecture_boundaries.py` y `sdd_healthcheck.py`; si fallan, reparar antes de invocar Santa.

Activar con `/santa-loop` o si se cumple **cualquier** trigger:

| Frontera | Trigger por Riesgo / Dominio | Trigger por Volumen / Contaminación de Contexto |
| :--- | :--- | :--- |
| **Pre-Gate 2** (`01-spec` + `02-tech-spec`, antes del sign-off humano) | Auth/seguridad, pagos/compliance, PII, migraciones destructivas, APIs públicas o `CR-XXX` que reemplaza lógica. | `01-spec.md` $\ge 8$ EARS (o $\ge 5$ BDD), **o** `02-tech-spec.md` $\ge 4$ entidades/contratos/endpoints o $> 250$ líneas. |
| **Gate 4** (post-Capa 1 verde, antes de Gate 5) | Mismos riesgos + cambios en boundaries críticos o lógica core sin E2E completo. | `03-tasks.md` $\ge 2$ bloques DAG, $\ge 6$ tareas, $\ge 8$ ficheros tocados, o Work Item con compactación / `/continue`. |
| **Gate 5** (`@documentator`, antes de `git push`) | Cambios en `API_CATALOG.md`, `DATA_MODELS.md` o `ADRS.md` con contratos públicos. | $\ge 4$ docs actualizados/creados en `docs/es/`, `docs/en/` y `docs/knowledge/`. |

**NO activar en:** `Gate S0`, `Gate 0`, `Gate 3`, borradores exploratorios o cambios locales triviales (1–3 ficheros, 1 bloque, sin contrato/seguridad ni compactación).

## 2. Flujo de 4 Fases

```text
[1. Make a List]      Construir The List (EARS, contratos, entregables/docs) + salida generada
        │
[2. Check It Twice]   Revisor B ∥ Revisor C (subagentes paralelos, misma rúbrica, 0 contexto compartido)
        │
[3. Verdict Gate]     B == PASS && C == PASS ──► NICE (certificar frontera)
        │             Cualquier FAIL         ──► NAUGHTY (deduplicar critical_issues)
[4. Fix Until Nice]   Fix estricto (SOLO critical_issues) ──► Capa 1 (si código)
                      ──► Relanzar 2 revisores FRESCOS (máx. 3 rondas ──► Escalar al usuario)
```

## 3. Las 5 Invariantes Innegociables

1. **Aislamiento total:** Revisor B y Revisor C corren en paralelo en solo lectura; ninguno ve el dictamen del otro.
2. **Misma rúbrica binaria (nunca criterios disjuntos):** Ambos evalúan **todos** los criterios `PASS`/`FAIL`. Se admiten roles complementarios (`@architect` + `@qa-tester`/`@silent-failure-hunter`), pero sin excluir criterios: si solo 1 detecta un fallo, neutralizó el punto ciego del otro.
3. **Agentes frescos por ronda:** Cero memoria de rondas previas para evitar *anchoring bias* y cazar regresiones del fix.
4. **Fix estricto + Inmutabilidad de `01-spec.md`:** Corregir **solo** `critical_issues` (`suggestions` no bloquean); prohibido refactorizar fuera de alcance. En `PRE_GATE_2`, si un defecto nace en `01-spec.md` aprobado (`upstream_spec_conflicts`), **no** auto-editar `01-spec.md`: escalar al usuario (`RN-SDD-HUMAN-GATE-OWNERSHIP`, `RN-SDD-FAIL-CLOSED`).
5. **Tope de 3 rondas:** Si no converge en 3 rondas o salta Semáforo Rojo (`RN-SDD-CONTEXT-SEMAPHORE`), persistir `all_issues` en `.agents/ACTIVE_STATE.md` y escalar al usuario.

## 4. Escalado para Specs/Diffs Largos

- **Chunked Santa:** Si un diff supera $> 12$ ficheros / $> 600$ líneas (o `02-tech-spec.md` $> 600$ líneas), particionar por capa coherente (*Contratos + Backend*, *Contratos + Frontend*) manteniendo **2 revisores frescos por partición**.
- **Batch Sampling (Gate 5):** Para lotes $> 15$ docs, muestrear 15–20% (mín. 5); si aparece un fallo sistemático, corregir todo el lote y re-muestrear hasta muestra limpia.

## 5. Modos de Fallo y Mitigaciones

| Modo de Fallo | Mitigación |
| :--- | :--- |
| Bucle infinito | Tope estricto `MAX_ITERATIONS = 3` + escalado humano. |
| Rubber stamping | Prompt adversario + `evidence` obligatoria por criterio en JSON. |
| Subjective drift | Rúbrica binaria objetiva; estilo va a `suggestions` (no bloqueante). |
| Fix regression | Fix estricto + re-ejecutar Capa 1 + revisores frescos. |
| Blind spot compartido | Independencia real; en entregas críticas añadir 3er revisor o spot-check humano. |
| Explosión de coste | Triggers objetivos + Capa 1 primero + Chunked Santa / Batch Sampling. |

## 6. Integración con el Ecosistema SDD

- **`gan-style-harness` (`/gan-build`):** Construcción iterativa intra-bloque en Gate 4 (1 evaluador, $\ge 8.5/10$). `santa-method` certifica fronteras de Gate (`Pre-Gate 2`, `Gate 4`, `Gate 5`); pasar GAN no exime de Santa si saltan sus triggers.
- **`strategic-compact`:** Ejecutar Santa **antes** de compactar; nunca compactar a mitad de ronda.
- **`continuous-learning-v2`:** Tras rondas `NAUGHTY`, registrar la taxonomía de fallos recurrentes con `uv run python scripts/sdd_instincts.py record`.
