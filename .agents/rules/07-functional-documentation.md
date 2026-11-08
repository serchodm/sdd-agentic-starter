# Reglas Técnicas: Estándar de Documentación Funcional de Project

## 1. Norma Rectora
Toda la documentación funcional del proyecto se rige de forma obligatoria por el estándar normativo:
[`docs/standards/FUNCTIONAL_DOCUMENTATION_STANDARD.md`](file:///c:/Projects/sdd-agentic-starter/docs/standards/FUNCTIONAL_DOCUMENTATION_STANDARD.md)

---

## 2. Taxonomía Obligatoria de Identificadores
Queda estrictamente prohibido crear artefactos funcionales sin identificador o con nomenclaturas improvisadas. Se adoptan los prefijos globales normativos:

| Prefijo | Tipo de Artefacto | Ejemplo | Responsable Principal |
|---|---|---|---|
| `OBJ-###` | Objetivos Estratégicos | `OBJ-001` | `@functional-analyst` / `@ai-architect` |
| `MOD-###` | Módulos de Producto | `MOD-001` | `@functional-analyst` / `@ai-architect` / `@documentator` |
| `FN-###` | Funcionalidades | `FN-001` | `@functional-analyst` / `@ai-architect` |
| `SRC-###` | Fuentes de Información | `SRC-001` | `@functional-analyst` |
| `AMB-###` | Ambigüedades Funcionales | `AMB-001` | `@functional-analyst` |
| `RF-###` | Requisitos Funcionales Atómicos | `RF-001` | `@functional-analyst` / `@documentator` |
| `RN-###` | Reglas de Negocio | `RN-001` | `@functional-analyst` |
| `SCR-###` | Pantallas y Modales de UI | `SCR-001` | `@front-ui` / `@documentator` |
| `CT-###` | Controles / Campos Relevantes | `CT-001` | `@front-ui` |
| `AC-###` | Acciones de Interfaz | `AC-001` | `@front-ui` |
| `UC-###` | Casos de Uso | `UC-001` | `@functional-analyst` |
| `FL-###` | Flujos de Usuario | `FL-001` | `@functional-analyst` / `@front-ui` |
| `DOM-###` | Conceptos de Dominio Conceptual | `DOM-001` | `@functional-analyst` / `@back-domain` |
| `INT-###` | Integraciones de Sistemas | `INT-001` | `@ai-architect` / `@back-infra` |
| `RNF-###` | Requisitos No Funcionales | `RNF-001` | `@ai-architect` / `@orchestrator` |
| `DEC-###` | Registro de Decisiones | `DEC-001` | Tríada (`@functional-analyst`, `@orchestrator`, `@documentator`) |
| `RF-###-CA-##` | Criterios de Aceptación BDD | `RF-001-CA-01` | `@functional-analyst` / `@back-test` / `@front-test` |

---

## 3. Principio de Veracidad y Cero Invenciones (Hechos vs Supuestos)
- Ningún agente inventará requerimientos, permisos, mensajes de error, umbrales de rendimiento ni reglas de negocio no confirmadas.
- Todo dato debe clasificarse expresamente como:
  - **`CONFIRMED`**: Aprobado por el usuario o especificación ratificada.
  - **`PROPOSED`**: Sugerencia del agente pendiente de aprobación formal.
  - **`ASSUMPTION`**: Hipótesis temporal de trabajo con responsable y riesgo documentado.
  - **`OPEN`**: Pregunta abierta o bloqueo pendiente de resolución en `OPEN-QUESTIONS.md`.

---

## 4. Separación Tajante entre Documentación Funcional y Técnica
- **Funcional (`docs/{lang}/` & `01-spec.md`)**: Describe **qué** hace el sistema, cómo se comporta, qué ve el usuario, qué reglas aplican y cómo se valida.
- **Técnica (`backend/`, `frontend/`, `02-tech-spec.md`)**: Describe **cómo** se implementa internamente (clases, DTOs Pydantic, interfaces TypeScript, esquemas SQL físicos, configuraciones Docker).

---

## 5. Estructura Bilingüe Modular y Consolidación Viva
- La documentación funcional de Project se consolida en carpetas de idioma paralelas:
  - `docs/es/`: Árbol funcional completo en Español (ES-ES).
  - `docs/en/`: Árbol funcional completo en Inglés británico (EN-GB).
- Los 7 bloques modulares son:
  - `00-governance/`: Índice, estado, glosario, preguntas abiertas, registro de decisiones y changelog.
  - `01-product/`: Visión, objetivos, alcance, actores, roles y matriz de permisos.
  - `02-functional/`: Mapa funcional, catálogo de requisitos, reglas de negocio y módulos (`MOD-XXX`).
  - `03-ux-ui/`: Navegación, catálogo de pantallas (`SCR-XXX`), componentes y wireframes.
  - `04-domain-and-context/`: Modelo conceptual, diccionario de datos, contexto e integraciones.
  - `05-quality-and-acceptance/`: Requisitos no funcionales, criterios y Definition of Done funcional.
  - `06-traceability/`: Matriz de trazabilidad global y cobertura.

---

## 6. Gobernanza 0DD (Zero Document Debt) y Gate 5
- **Regla Rectora (`RN-SDD-0DD`)**: Ninguna Feature (`FEAT-XXX`), Change Request (`CR-XXX`) ni Bug (`BUG-XXX`) puede marcarse como `Done` / `Completado` sin que `@documentator` haya redactado y consolidado la documentación en `docs/es/` y `docs/en/` y actualizado `TRACEABILITY-MATRIX.md`.
- **Encolado de Tareas**: Todo plan de tareas (`03-tasks.md`) debe incluir como requisito de Gate 5 la tarea explícita asignada a `@documentator`:
  `- [ ] Tarea X.X: Consolidar documentación funcional bilingüe en docs/es/ y docs/en/ y actualizar TRACEABILITY-MATRIX.md (@documentator).`
