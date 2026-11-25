# Referencia `search-first`: Orden de Consulta, Matriz *Reuse-vs-Build* e Higiene de Paquetes

Cargar en **Gate 0 / Pre-Gate 2** (`@architect`, `@orchestrator`) antes de redactar `02-tech-spec.md` y en **Gate 4** antes de crear módulos, contratos o dependencias nuevas (`RN-SDD-SELECTIVE-CONTEXT`).

## 1. Orden Determinista de Consulta Pre-Diseño

Antes de lanzar búsquedas recursivas o diseñar código nuevo, consultar en esta secuencia exacta mediante lecturas acotadas:

1. **`docs/knowledge/SYSTEM_TOPOLOGY.md`**
   - Localizar *Bounded Contexts*, módulos propietarios, capas válidas y reglas auditadas por `verify_architecture_boundaries.py`.
2. **`docs/knowledge/API_CATALOG.md`**
   - Revisar endpoints REST/gRPC, subcomandos CLI, webhooks, eventos y DTOs publicados para impedir rutas u operaciones duplicadas.
3. **`docs/knowledge/DATA_MODELS.md`**
   - Inspeccionar entidades, esquemas de tablas, índices, invariantes de dominio y campos marcados como sensibles/PII.
4. **`docs/knowledge/ADRS.md` y `specs/STACK.md`**
   - Verificar decisiones arquitectónicas vigentes, versión de runtime, librerías congeladas en `Gate S0` y políticas de dependencias (p. ej., *stdlib-only* con `dependencies = []`).
5. **Código Fuente Focalizado**
   - Con las rutas acotadas en los 4 catálogos, inspeccionar contratos compartidos (`packages/`, `src/**/domain/`, utilidades comunes) o ejecutar `uv run python scripts/sdd_cli.py repo-map` sin volcados masivos ciegos.

```text
[Nueva Necesidad Técnica]
   ├── 1. Consultar docs/knowledge/{SYSTEM_TOPOLOGY,API_CATALOG,DATA_MODELS,ADRS}.md + specs/STACK.md
   ├── 2. ¿Existe contrato/servicio interno (>= 90%)? ─────────► NIVEL 1: Reutilizar (importar)
   ├── 3. ¿Mismo Bounded Context ampliable (60%–89%)? ─────────► NIVEL 2: Extender (retrocompatible)
   ├── 4. ¿Problema transversal cubierto por stdlib / STACK.md? ► NIVEL 3: Adoptar librería aprobada
   └── 5. ¿Regla de negocio core o restricción zero-deps? ─────► NIVEL 4: Construir + documentar 0DD
```

## 2. Matriz Cuantitativa: *Reutilizar -> Extender -> Adoptar -> Construir*

Evaluar secuencialmente del Nivel 1 al 4; descender de nivel exige justificación explícita en `02-tech-spec.md`:

| Nivel | Encaje Actual | Criterio Cuantitativo y Arquitectónico | Decisión SDD Obligatoria |
| :--- | :---: | :--- | :--- |
| **1. Reutilizar** | `>= 90%` | Contrato, servicio, componente o helper interno cubre el caso respetando fronteras de capa. | Importar directamente sin wrappers redundantes ni copias locales. Coste adicional: `0`. |
| **2. Extender** | `60%–89%` | Abstracción del **mismo** *Bounded Context* adaptable con parámetros opcionales o nuevo adaptador. | Ampliar de forma **100% retrocompatible** (defaults seguros). Si muta una `FEAT-XXX` `Done`, abrir `CR-XXX` (`RN-SDD-IMMUTABLE-DONE`). |
| **3. Adoptar librería aprobada** | `< 60%` *(transversal)* | Capacidad técnica no diferenciadora (criptografía, protocolo, parsing complejo, validación, resiliencia). | Usar **stdlib** primero; si no cubre el caso, usar paquete aprobado en `specs/STACK.md` o solicitar alta en `Gate 2` (ADR + sign-off humano). |
| **4. Construir** | `< 60%` *(core / zero-deps)* | Lógica de negocio diferenciadora del producto o proyecto bajo restricción *stdlib-only*. | Especificar contrato tipado en `02-tech-spec.md`, implementar en el módulo canónico de `SYSTEM_TOPOLOGY.md` y documentar en `Gate 5` (`0DD`). |

### Regla Anti-*Wrong Abstraction*
- Si el candidato reside en otro *Bounded Context* o requeriría flags booleanos acoplados (`< 60%` de cohesión semántica), **prohibido** forzar el Nivel 2 (`Extender`).
- Extraer un contrato explícito en `packages/` o pasar a los Niveles 3–4 cumpliendo `verify_architecture_boundaries.py`.

## 3. Auditoría *Fail-Closed* de Paquetes y Cero Alucinación

Queda prohibido añadir paquetes ad-hoc en `Gate 4` o referenciar librerías/APIs no verificadas en disco:

1. **Compatibilidad con `specs/STACK.md`:**
   - Confirmar que la librería consta en `specs/STACK.md` y en el manifiesto real (`pyproject.toml`, `package.json`, `go.mod`, `Cargo.toml`, `pom.xml` / `build.gradle.kts`).
   - Respetar estrictamente `dependencies = []` en proyectos o herramientas *stdlib-only*.
2. **Cero Alucinación de Paquetes (*Anti-Slopsquatting*):**
   - Prohibido inventar nombres de paquetes, submódulos o firmas de métodos por memoria.
   - Validar nombre exacto, versión bloqueada en lockfile (`uv.lock`, `package-lock.json`, `pnpm-lock.yaml`, `Cargo.lock`) y símbolos exportados reales.
3. **Licencia Permisiva y Cumplimiento Legal:**
   - Permitir solo licencias permisivas compatibles (`MIT`, `Apache-2.0`, `BSD-2-Clause`, `BSD-3-Clause`, `ISC`) registradas cuando aplique en `THIRD_PARTY_NOTICES.md`.
   - Bloquear en modo *fail-closed* licencias copyleft restrictivas (`GPL`, `AGPL`, `SSPL`) o paquetes sin `LICENSE` explícita salvo autorización escrita del PO.
4. **Mantenimiento y Superficie de Dependencias:**
   - Exigir soporte activo, `0` CVEs críticos abiertos (`sdd-security-audit`), tipado estático y grafo transitivo mínimo.
   - Rechazar micro-dependencias triviales (`< 30` líneas resolubles con stdlib) que incrementan el riesgo *supply-chain*.

## 4. Plantilla de Evidencia en `02-tech-spec.md` y Checklist

```markdown
- **Reutilización (`search-first`):** Reutiliza `<módulo/DTO>` (`API_CATALOG.md`); extiende `<servicio>` sin breaking changes; `0` dependencias nuevas fuera de `specs/STACK.md`.
```

- [ ] Revisados `SYSTEM_TOPOLOGY.md`, `API_CATALOG.md`, `DATA_MODELS.md`, `ADRS.md` y `specs/STACK.md` en orden.
- [ ] Listados los módulos/DTOs reutilizados o extendidos (Niveles 1–2) sin duplicar contratos.
- [ ] Verificada cada dependencia en `specs/STACK.md` + lockfile, con licencia permisiva y `0` paquetes/APIs alucinados.
- [ ] Toda dependencia nueva propuesta justifica por qué la stdlib no basta y exige sign-off humano en `Gate 2`.
