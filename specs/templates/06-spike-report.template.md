# SPIKE-XXX: <Título breve de la investigación o PoC>

> **Uso obligatorio:** Copiar esta plantilla en `specs/spikes/SPIKE-XXX-<slug>/SPIKE_REPORT.md` siguiendo `specs/SDD_FRAMEWORK.md §8.1`. Debe permanecer no vacía y libre de contenido malicioso para superar `.agents/scripts/sdd_healthcheck.py`.

- **ID:** `SPIKE-XXX`
- **Dominio / Área:** `<dominio-o-modulo>`
- **Estado del Documento:** `Draft` | `In Progress` | `Completed`
- **Timebox:** `<ej. 4h / 1 día>` (Fecha límite: `YYYY-MM-DD`)
- **Rama / Script aislado de PoC:** `<spike/SPIKE-XXX-slug o ruta temporal desechable>`
- **Work Item relacionado:** `FEAT-XXX` | `CR-XXX` | `N/A`

---

## 1. Hipótesis y Preguntas Técnicas a Resolver
- **Problema / Incertidumbre:** `<qué riesgo técnico, librería, algoritmo o integración se evalúa>`
- **Hipótesis principal:** `<afirmación falsable; ej. "La librería X soporta carga Y con latencia p95 < 50ms">`
- **Preguntas clave:**
  1. `<Pregunta técnica 1>`
  2. `<Pregunta técnica 2>`
- **Criterio de éxito / salida:** `<umbral medible que valida o refuta la hipótesis>`

---

## 2. Experimentos Aislados y Código Desechable
- **Regla de aislamiento (`SDD_FRAMEWORK.md §8.1`):** El código escrito durante este Spike es estrictamente experimental y desechable; **bajo ningún concepto se fusiona directamente en producción (`src/` o `main`)**.
- **Entorno de prueba:** `<versión de runtime, dependencias probadas, dataset sintético sin datos reales ni secretos>`
- **Experimentos ejecutados:**
  1. `<Experimento A: descripción breve y parámetros>`
  2. `<Experimento B: descripción breve y parámetros>`

---

## 3. Hallazgos y Métricas Comparativas

| Alternativa / Caso | Latencia / Rendimiento | Complejidad / Mantenibilidad | Compatibilidad Stack (`STACK.md`) | Resultado |
| :--- | :--- | :--- | :--- | :--- |
| `<Opción A>` | `<métrica observada>` | `<Baja / Media / Alta>` | `<Compatible / Restricciones>` | `<Apta / Descartada>` |
| `<Opción B>` | `<métrica observada>` | `<Baja / Media / Alta>` | `<Compatible / Restricciones>` | `<Apta / Descartada>` |

- **Observaciones clave:** `<hechos verificados durante la PoC, cuellos de botella o límites descubiertos>`

---

## 4. Riesgos de Seguridad, Rendimiento y Arquitectura
- **Superficie de seguridad y secretos:** `<confirmación de cero secretos expuestos, manejo de credenciales, validación fail-closed>`
- **Deuda técnica / Dependencias:** `<licencias, tamaño de bundle, límites de hardware/red o acoplamientos detectados>`
- **Riesgos residuales:** `<aspectos que requieren mitigación en el diseño formal>`

---

## 5. Decisión y Recomendación para Gate 2 (`02-tech-spec.md`)
- **Veredicto:** `Go (Adoptar Opción X)` | `No-Go (Descartar)` | `Pivot (Requiere nueva hipótesis)`
- **Resumen de decisión (base para ADR):** `<justificación objetiva respaldada por las métricas de la sección 3>`
- **Insumos concretos para `02-tech-spec.md`:**
  - `<Contrato, patrón o restricción a incorporar en Gate 2>`
  - `<Plan de limpieza: rama/scripts desechables eliminados o archivados>`
