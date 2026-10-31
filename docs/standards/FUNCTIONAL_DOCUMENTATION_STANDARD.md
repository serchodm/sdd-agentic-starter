# Estándar de documentación funcional de aplicaciones

**Tipo de documento:** Estándar normativo para el agente `documentator`  
**Estado:** Propuesto para adopción  
**Versión:** 1.0  
**Idioma de documentación:** Español, salvo que el proyecto establezca explícitamente otro idioma  
**Formato fuente:** Markdown versionado en Git

---

## 1. Propósito

Este documento define el método, la estructura, las plantillas y las reglas que el agente `documentator` debe seguir para crear y mantener la documentación funcional de una aplicación informática.

El objetivo es disponer de una **fuente de verdad funcional, modular, visual, trazable y verificable**, útil tanto para negocio como para diseño, desarrollo, QA y agentes de IA.

La documentación debe permitir que una persona o agente que no haya participado en las conversaciones iniciales comprenda:

- Qué problema resuelve el producto y cuáles son sus objetivos.
- Qué está dentro y fuera del alcance.
- Qué módulos y funcionalidades componen la aplicación.
- Qué usuarios existen y qué permisos tienen.
- Cómo se realizan los procesos y cuáles son sus variantes.
- Qué pantallas existen, cómo se organizan y cómo se navega entre ellas.
- Qué campos, controles, acciones, validaciones, estados y mensajes contiene cada pantalla.
- Qué reglas de negocio gobiernan el comportamiento.
- Qué conceptos de dominio y sistemas externos intervienen.
- Qué requisitos de calidad deben cumplirse.
- Cómo se verificará que cada requisito se ha implementado correctamente.

Este estándar es normativo para el agente `documentator`. Si una instrucción específica del proyecto contradice este estándar, el agente debe identificar el conflicto y solicitar una decisión o registrar la excepción aprobada; no debe elegir silenciosamente una interpretación.

## 2. Principios obligatorios

### 2.1. Una única fuente de verdad

Cada dato o decisión debe tener un lugar canónico de mantenimiento. Otros documentos pueden enlazarlo o resumirlo, pero no deben mantener copias manuales que puedan divergir.

Ejemplo: el catálogo general de requisitos puede generarse a partir de las fichas de requisitos; no deben existir dos descripciones independientes del mismo requisito.

### 2.2. Documentación modular

La documentación se organiza en archivos Markdown pequeños y con una responsabilidad clara. Un índice maestro proporciona una visión global y permite navegar entre ellos.

No crear todos los archivos de antemano por obligación. Crear los artefactos cuando exista contenido real que documentar, manteniendo la estructura prevista.

### 2.3. Distinguir hechos, decisiones, supuestos y preguntas

El agente nunca debe inventar requisitos, reglas, comportamientos, permisos, valores, mensajes o decisiones de arquitectura para completar una plantilla.

Debe identificar cada punto como uno de los siguientes cuando corresponda:

- **Confirmado:** respaldado por una fuente aprobada o una decisión explícita.
- **Propuesto:** recomendación del agente pendiente de aprobación.
- **Supuesto:** hipótesis temporal necesaria para continuar.
- **Pendiente:** pregunta que necesita una decisión.
- **Descartado:** opción rechazada expresamente, conservada cuando sea útil para el historial.

Las propuestas y los supuestos nunca deben redactarse como requisitos aprobados.

### 2.4. De lo general a lo concreto

Definir primero visión y alcance, después mapa funcional y procesos, y luego requisitos, reglas, pantallas y criterios de aceptación. El orden puede ser iterativo: un hallazgo en una pantalla puede obligar a revisar un flujo o una regla.

### 2.5. Separación funcional/técnica

La especificación funcional describe **qué debe hacer el producto y cómo debe comportarse**.

Puede incluir arquitectura conceptual de alto nivel, límites del sistema, sistemas externos y flujos de información. No debe imponer detalles de implementación salvo que sean una restricción aprobada del proyecto.

No incluir como contenido funcional detallado, salvo que el alcance lo exija expresamente:

- Diseño interno de clases o paquetes.
- Endpoints, contratos JSON o códigos HTTP completos.
- Esquemas físicos de base de datos y tipos SQL.
- Configuración de infraestructura o despliegue.
- Implementaciones concretas de autenticación.
- Detalles internos de código.

Esos detalles pertenecen a la documentación técnica, enlazada cuando corresponda.

### 2.6. Requisitos verificables

Cada requisito aprobado debe tener una forma observable de comprobar su cumplimiento. Evitar expresiones vagas como «fácil de usar», «rápido», «intuitivo» o «gestionar usuarios» sin concretar el comportamiento esperado.

### 2.7. Diseño visual progresivo

Primero crear wireframes de baja fidelidad, preferentemente con Excalidraw, para validar estructura y comportamiento. Solo después de la aprobación funcional se desarrolla el diseño de alta fidelidad.

### 2.8. Completo no significa innecesariamente exhaustivo

Documentar todos los aspectos relevantes de una funcionalidad antes de implementarla, incluidos los casos alternativos y errores pertinentes. No obligar a cerrar con el mismo nivel de detalle las funcionalidades futuras que aún no se van a construir.

### 2.9. Trazabilidad

Los objetivos, módulos, funcionalidades, requisitos, reglas, pantallas, flujos, criterios de aceptación y evidencias deben poder relacionarse mediante identificadores y enlaces.

### 2.10. Cambios controlados

Los cambios sobre artefactos aprobados deben explicar su motivo y evaluar el impacto en los elementos relacionados. No modificar silenciosamente decisiones aprobadas.

---

## 3. Estructura del repositorio

Utilizar la siguiente estructura como destino recomendado. Adaptar los módulos y archivos al tamaño real del producto sin crear archivos vacíos o duplicados.

```text
docs/
├── README.md
├── 00-governance/
│   ├── DOCUMENTATION-INDEX.md
│   ├── DOCUMENT-STATUS.md
│   ├── CHANGELOG.md
│   ├── GLOSSARY.md
│   ├── OPEN-QUESTIONS.md
│   ├── DECISION-LOG.md
│   └── conventions/
│       ├── DOCUMENTATION-STANDARDS.md
│       ├── IDENTIFICATION-RULES.md
│       └── WRITING-GUIDELINES.md
├── 01-product/
│   ├── PRODUCT-VISION.md
│   ├── OBJECTIVES-AND-SUCCESS-METRICS.md
│   ├── SCOPE.md
│   ├── ASSUMPTIONS-AND-CONSTRAINTS.md
│   ├── STAKEHOLDERS.md
│   ├── USER-ROLES.md
│   ├── PERMISSION-MATRIX.md
│   └── RELEASE-SCOPE.md
├── 02-functional/
│   ├── FUNCTIONAL-MAP.md
│   ├── FUNCTIONAL-CATALOG.md
│   ├── REQUIREMENTS-CATALOG.md
│   ├── BUSINESS-RULES.md
│   ├── USE-CASES.md
│   ├── USER-FLOWS.md
│   ├── STATES-AND-TRANSITIONS.md
│   └── modules/
│       ├── MOD-001/
│       │   ├── README.md
│       │   ├── functional-spec.md
│       │   ├── requirements.md
│       │   └── rules.md
│       └── MOD-002/
├── 03-ux-ui/
│   ├── UX-PRINCIPLES.md
│   ├── NAVIGATION-MAP.md
│   ├── SCREEN-CATALOG.md
│   ├── COMPONENT-CATALOG.md
│   ├── INTERACTION-STANDARDS.md
│   ├── ACCESSIBILITY-AND-RESPONSIVE.md
│   └── screens/
│       ├── SCR-001/
│       │   ├── screen-spec.md
│       │   ├── wireframe.excalidraw
│       │   ├── wireframe.png
│       │   ├── hi-fi/
│       │   └── assets/
│       └── SCR-002/
├── 04-domain-and-context/
│   ├── DOMAIN-GLOSSARY.md
│   ├── CONCEPTUAL-DATA-MODEL.md
│   ├── DATA-DICTIONARY.md
│   ├── SYSTEM-CONTEXT.md
│   ├── HIGH-LEVEL-ARCHITECTURE.md
│   ├── EXTERNAL-SYSTEMS.md
│   ├── INTEGRATION-CATALOG.md
│   └── diagrams/
├── 05-quality-and-acceptance/
│   ├── NON-FUNCTIONAL-REQUIREMENTS.md
│   ├── ACCEPTANCE-STRATEGY.md
│   ├── ACCEPTANCE-CRITERIA.md
│   ├── VALIDATION-SCENARIOS.md
│   └── DEFINITION-OF-DONE.md
├── 06-traceability/
│   ├── TRACEABILITY-MATRIX.md
│   ├── REQUIREMENT-COVERAGE.md
│   ├── CHANGE-IMPACT.md
│   └── BASELINES.md
└── templates/
    ├── TEMPLATE-MODULE.md
    ├── TEMPLATE-FUNCTIONAL-REQUIREMENT.md
    ├── TEMPLATE-SCREEN.md
    ├── TEMPLATE-BUSINESS-RULE.md
    ├── TEMPLATE-USE-CASE.md
    ├── TEMPLATE-USER-FLOW.md
    ├── TEMPLATE-INTEGRATION.md
    └── TEMPLATE-ACCEPTANCE-CRITERIA.md
```

### 3.1. Responsabilidad de cada bloque

- `00-governance`: convenciones, índice, estado, preguntas, decisiones e historial.
- `01-product`: visión, objetivos, alcance, actores, roles y versiones.
- `02-functional`: módulos, funcionalidades, requisitos, reglas, casos de uso, flujos y estados.
- `03-ux-ui`: navegación, inventario de pantallas, componentes, mockups e interacción.
- `04-domain-and-context`: conceptos de negocio, modelo conceptual, sistemas externos y arquitectura conceptual.
- `05-quality-and-acceptance`: requisitos no funcionales, criterios y estrategia de validación.
- `06-traceability`: relaciones entre artefactos, cobertura, impacto y baselines.
- `templates`: plantillas reutilizables.

Los catálogos generales deben actuar como índices o vistas agregadas cuando los detalles se mantengan en fichas por módulo o artefacto. Evitar duplicar manualmente el contenido.

---

## 4. Convenciones de escritura y formato

### 4.1. Idioma y estilo

- Escribir en español claro, directo y profesional, salvo que el proyecto defina otro idioma.
- Utilizar términos de negocio coherentes y añadirlos al glosario.
- Definir cada sigla en su primera aparición.
- Evitar frases ambiguas, adornos y repeticiones.
- Preferir tablas para inventarios y propiedades; listas numeradas para secuencias; diagramas para relaciones y flujos.
- Explicar abreviaturas y símbolos de los diagramas.
- No usar imágenes como sustituto de la especificación textual.

### 4.2. Reglas para requisitos

Preferir expresiones como:

- «El sistema deberá permitir…»
- «Cuando se cumpla [condición], el sistema deberá…»
- «Si [situación], entonces…»

Un requisito debe tener una intención principal. Dividir requisitos que mezclen varios comportamientos independientes.

No usar «debería» para un requisito obligatorio. Reservar las recomendaciones y opciones para propuestas no aprobadas.

### 4.3. Metadatos mínimos

Los artefactos importantes deben indicar, cuando aplique:

- Identificador.
- Nombre.
- Estado.
- Responsable o validador.
- Fecha o versión de revisión si el proceso del proyecto la requiere.
- Referencias relacionadas.
- Historial o enlace al historial de Git.

No duplicar en todos los archivos información que Git o el índice ya proporcionen de forma fiable, salvo que resulte necesaria para publicar el documento de forma independiente.

---

## 5. Convención de identificadores

Usar identificadores únicos, estables y permanentes. No codificar en el identificador la carpeta, el nombre del módulo o la prioridad, ya que pueden cambiar.

| Artefacto | Prefijo | Ejemplo |
|---|---|---|
| Objetivo | `OBJ` | `OBJ-001` |
| Módulo | `MOD` | `MOD-001` |
| Funcionalidad | `FN` | `FN-001` |
| Requisito funcional | `RF` | `RF-001` |
| Regla de negocio | `RN` | `RN-001` |
| Pantalla | `SCR` | `SCR-001` |
| Control de pantalla | `CT` | `CT-001` |
| Acción de interfaz | `AC` | `AC-001` |
| Caso de uso | `UC` | `UC-001` |
| Flujo de usuario | `FL` | `FL-001` |
| Concepto de dominio | `DOM` | `DOM-001` |
| Integración | `INT` | `INT-001` |
| Requisito no funcional | `RNF` | `RNF-001` |
| Decisión | `DEC` | `DEC-001` |
| Criterio de aceptación | Subordinado al requisito | `RF-014-CA-01` |

Reglas:

1. No reutilizar un ID retirado para un artefacto nuevo.
2. Si un artefacto se mueve o cambia de nombre, conservar su ID.
3. Usar IDs globales para entidades que puedan ser referenciadas por varios documentos.
4. Los criterios de aceptación pueden usar IDs subordinados al requisito propietario.
5. Asignar IDs individuales a controles o acciones solo cuando deban referenciarse de manera independiente; no crear IDs innecesarios para cada elemento decorativo.
6. Mantener un registro o mecanismo de validación que impida duplicados.

---

## 6. Estados documentales

Usar un conjunto controlado de estados. Aplicar solo los que tengan sentido para el tipo de artefacto.

- `Draft`: en elaboración.
- `In Review`: pendiente de revisión.
- `Approved`: aprobado para el alcance indicado.
- `Implemented`: implementado; no significa que esté validado.
- `Verified`: verificado frente a sus criterios de aceptación.
- `Deprecated`: retirado o sustituido.

No confundir el estado del documento con el estado de la funcionalidad en el producto. Un requisito puede estar aprobado y todavía no implementado.

Para preguntas y propuestas, usar etiquetas explícitas como `OPEN`, `PROPOSED`, `ASSUMPTION` o `REJECTED`, según las convenciones del repositorio.

---

## 7. Plantilla: índice maestro

**Archivo:** `00-governance/DOCUMENTATION-INDEX.md`

Debe proporcionar una puerta de entrada clara al conjunto documental. No repetir el contenido de los documentos enlazados.

```markdown
# Índice de documentación funcional

## Información del producto
- Producto:
- Descripción breve:
- Versión/baseline funcional vigente:
- Estado global:
- Responsable funcional:

## Cómo utilizar esta documentación
Explicar el orden de lectura y las convenciones.

## 1. Producto
- [Visión](../01-product/PRODUCT-VISION.md)
- [Objetivos](../01-product/OBJECTIVES-AND-SUCCESS-METRICS.md)
- [Alcance](../01-product/SCOPE.md)
- [Roles](../01-product/USER-ROLES.md)

## 2. Funcionalidad
- [Mapa funcional](../02-functional/FUNCTIONAL-MAP.md)
- [Catálogo de requisitos](../02-functional/REQUIREMENTS-CATALOG.md)
- [Reglas de negocio](../02-functional/BUSINESS-RULES.md)
- [Casos de uso](../02-functional/USE-CASES.md)

## 3. UX/UI
- [Mapa de navegación](../03-ux-ui/NAVIGATION-MAP.md)
- [Catálogo de pantallas](../03-ux-ui/SCREEN-CATALOG.md)

## 4. Dominio y contexto
- [Modelo conceptual](../04-domain-and-context/CONCEPTUAL-DATA-MODEL.md)
- [Contexto del sistema](../04-domain-and-context/SYSTEM-CONTEXT.md)
- [Arquitectura de alto nivel](../04-domain-and-context/HIGH-LEVEL-ARCHITECTURE.md)

## 5. Calidad y aceptación
- [Requisitos no funcionales](../05-quality-and-acceptance/NON-FUNCTIONAL-REQUIREMENTS.md)
- [Estrategia de aceptación](../05-quality-and-acceptance/ACCEPTANCE-STRATEGY.md)

## 6. Trazabilidad
- [Matriz de trazabilidad](../06-traceability/TRACEABILITY-MATRIX.md)
- [Cobertura](../06-traceability/REQUIREMENT-COVERAGE.md)

## Estado y riesgos
- Artefactos aprobados:
- Decisiones abiertas:
- Riesgos funcionales:
- Próximos pasos:
```

El agente debe mantener enlaces relativos válidos y retirar del índice las referencias a archivos que no existan. No debe marcar una sección como completa solo porque exista el archivo.

---

## 8. Plantilla: visión del producto

**Archivo:** `01-product/PRODUCT-VISION.md`

```markdown
# Visión del producto

## 1. Resumen
Descripción breve del producto y su propósito.

## 2. Problema u oportunidad
¿Qué necesidad, dificultad o oportunidad motiva el producto?

## 3. Usuarios y contexto
¿Quién lo utilizará y en qué contexto?

## 4. Propuesta de valor
¿Qué mejora ofrece y por qué importa?

## 5. Objetivos
- OBJ-001 — ...
- OBJ-002 — ...

## 6. Indicadores de éxito
| ID | Indicador | Método de medición | Objetivo | Fuente |
|---|---|---|---|---|
| ... | ... | ... | ... | ... |

No inventar objetivos numéricos. Registrar como pendiente cualquier objetivo que deba decidirse.

## 7. Principios del producto
- ...

## 8. Límites de la visión
Qué aspectos no pretende resolver el producto.

## 9. Relaciones
Alcance, actores, módulos y decisiones relevantes.

## 10. Preguntas abiertas
- ...
```

---

## 9. Plantilla: alcance, supuestos y restricciones

**Archivo:** `01-product/SCOPE.md`

```markdown
# Alcance del producto

## 1. Resumen
## 2. Incluido en el alcance
| ID | Elemento | Justificación | Versión objetivo |
|---|---|---|---|
| ... | ... | ... | ... |

## 3. Excluido explícitamente
| Elemento | Motivo | Posible revisión futura |
|---|---|---|
| ... | ... | ... |

## 4. Entregas
- MVP:
- V1:
- Evoluciones posteriores:

## 5. Dependencias
## 6. Restricciones
## 7. Supuestos
| ID | Supuesto | Impacto si es falso | Responsable de confirmar |
|---|---|---|---|
| ... | ... | ... | ... |

## 8. Preguntas abiertas
## 9. Historial de decisiones de alcance
```

No incluir como alcance aprobado una idea que solo se haya sugerido. Etiquetar las propuestas hasta que se confirmen.

---

## 10. Plantilla: actores, roles y matriz de permisos

**Archivos:** `01-product/USER-ROLES.md` y `01-product/PERMISSION-MATRIX.md`

```markdown
# Roles y permisos

## 1. Actores y roles
| ID | Rol | Objetivo | Descripción | Ámbito |
|---|---|---|---|---|
| ... | ... | ... | ... | ... |

## 2. Matriz de permisos
| Rol | Módulo/recurso | Consultar | Crear | Modificar | Eliminar | Ejecutar | Administrar |
|---|---|---|---|---|---|---|---|
| ... | ... | ... | ... | ... | ... | ... | ... |

## 3. Restricciones de ámbito
Describir si los permisos dependen de propiedad, organización, estado u otra condición.

## 4. Comportamiento sin permiso
Definir qué muestra la interfaz y qué operaciones se rechazan.

## 5. Segregación de funciones
Documentar restricciones de combinación de permisos cuando apliquen.

## 6. Requisitos y reglas relacionados
## 7. Preguntas abiertas
```

La interfaz no es el único control de autorización. La especificación debe indicar que las operaciones no autorizadas deben rechazarse también en el límite funcional correspondiente, aunque se intente acceder por una vía distinta de la interfaz.

---

## 11. Plantilla: módulo funcional

**Archivo por módulo:** `02-functional/modules/MOD-XXX/README.md` o `functional-spec.md`

```markdown
# MOD-001 — Nombre del módulo

## 1. Propósito
¿Qué necesidad del usuario o negocio resuelve?

## 2. Alcance
### Incluye
- ...

### No incluye
- ...

## 3. Actores y permisos
| Actor | Consultar | Crear | Modificar | Eliminar/Ejecutar |
|---|---|---|---|---|
| ... | ... | ... | ... | ... |

## 4. Funcionalidades
| ID | Nombre | Descripción | Prioridad | Estado |
|---|---|---|---|---|
| FN-001 | ... | ... | Must/Should/Could | Draft |

## 5. Requisitos relacionados
- RF-001

## 6. Reglas de negocio
- RN-001

## 7. Pantallas
- SCR-001

## 8. Casos de uso y flujos
- UC-001
- FL-001

## 9. Datos y dependencias
- Conceptos:
- Integraciones:
- Módulos relacionados:

## 10. Criterios de aceptación globales
- ...

## 11. Decisiones abiertas
- ...

## 12. Historial de cambios
```

No convertir cada módulo en una copia del catálogo global. La ficha debe explicar su responsabilidad y enlazar a los artefactos canónicos.

---

## 12. Plantilla: funcionalidad

**Ubicación:** dentro de la ficha del módulo o en un archivo propio si su complejidad lo justifica.

```markdown
# FN-001 — Nombre de la funcionalidad

## Objetivo
## Actor principal
## Valor para el usuario
## Alcance
## Precondiciones
## Flujo principal
## Alternativas y excepciones
## Resultado esperado
## Reglas de negocio
## Requisitos funcionales asociados
## Pantallas relacionadas
## Datos y sistemas implicados
## Criterios de aceptación
## Prioridad y versión objetivo
## Preguntas abiertas
```

Una funcionalidad agrupa comportamientos relacionados. No sustituye a los requisitos atómicos que especifican esos comportamientos.

---

## 13. Plantilla: requisito funcional

**Archivo:** ficha dentro del módulo o catálogo de requisitos, según la estrategia elegida. Debe existir una sola fuente canónica para cada requisito.

```markdown
# RF-001 — Nombre del requisito

## Metadatos
- Estado: Draft
- Prioridad: Must / Should / Could
- Módulo: MOD-001
- Funcionalidad: FN-001
- Responsable de validación:
- Versión objetivo:

## Descripción
El sistema deberá...

## Justificación
¿Por qué se necesita?

## Actor y permisos
¿Quién puede utilizarlo y con qué autorización?

## Disparador
¿Qué inicia el comportamiento?

## Precondiciones
¿Qué debe cumplirse antes?

## Comportamiento esperado
1. ...
2. ...
3. ...

## Datos de entrada
- ...

## Resultado observable
¿Qué ve el usuario o qué cambia funcionalmente?

## Reglas de negocio
- RN-001

## Alternativas y excepciones
- ...

## Criterios de aceptación
- RF-001-CA-01

## Referencias
- Pantallas:
- Flujos:
- Casos de uso:
- Integraciones:
- Conceptos de dominio:

## Preguntas abiertas
- ...

## Historial de cambios
- ...
```

Reglas:

1. Un requisito debe expresar un comportamiento principal identificable.
2. Separar comportamientos independientes en requisitos distintos.
3. No usar términos vagos sin una definición verificable.
4. Registrar explícitamente precondiciones, resultado y excepciones relevantes.
5. No dar por aprobada una decisión pendiente.
6. Vincular cada requisito aprobado con criterios de aceptación adecuados.
7. Evitar duplicar en el requisito todos los detalles de una pantalla; enlazar a la ficha de pantalla.

---

## 14. Plantilla: regla de negocio

**Archivo:** `rules.md` del módulo o catálogo canónico de reglas.

```markdown
# RN-001 — Nombre de la regla

## Propósito
¿Qué condición de negocio regula?

## Regla
Cuando [condición], el sistema deberá [comportamiento].

## Condiciones de aplicación
- ...

## Entradas y datos afectados
- ...

## Excepciones
- ...

## Prioridad y precedencia
¿Qué ocurre si entra en conflicto con otra regla?

## Ejemplos
| Condición/entrada | Resultado esperado | Explicación |
|---|---|---|
| ... | ... | ... |

## Requisitos afectados
- RF-001

## Pantallas y flujos afectados
- SCR-001
- FL-001

## Criterios de verificación
- ...

## Responsable y estado de aprobación
- ...

## Preguntas abiertas
- ...
```

Las reglas compartidas por varios módulos deben tener una ubicación canónica única. Las fichas de otros módulos las referenciarán.

---

## 15. Plantilla: caso de uso

**Archivo:** catálogo de casos de uso o ficha independiente si es complejo.

```markdown
# UC-001 — Nombre del caso de uso

## Objetivo
## Actor principal
## Actores secundarios
## Disparador
## Precondiciones
## Flujo principal
1. El actor...
2. El sistema...
3. ...

## Flujos alternativos
- A1 — ...

## Excepciones
- E1 — ...

## Postcondiciones
## Requisitos relacionados
## Reglas de negocio relacionadas
## Pantallas relacionadas
## Criterios de aceptación
## Diagrama asociado
## Preguntas abiertas
```

Utilizar casos de uso cuando ayuden a explicar objetivos y secuencias relevantes. No crear fichas independientes para interacciones triviales que se entiendan mejor dentro de un requisito.

---

## 16. Plantilla: flujo de usuario

**Archivo:** `02-functional/USER-FLOWS.md` o ficha separada para flujos complejos.

```markdown
# FL-001 — Nombre del flujo

## Objetivo del usuario
## Actor
## Punto de entrada
## Precondiciones
## Camino principal
1. ...
2. ...

## Decisiones y bifurcaciones
- ...

## Caminos alternativos
- ...

## Errores y recuperación
- ...

## Punto de salida y resultado
## Pantallas implicadas
## Requisitos y reglas relacionados
## Diagrama Mermaid o Excalidraw
## Criterios de aceptación
```

Los diagramas deben mostrar decisiones y resultados de manera comprensible. El texto debe explicar las condiciones que no puedan inferirse con claridad del dibujo.

---

## 17. Plantilla: pantalla

**Archivo:** `03-ux-ui/screens/SCR-XXX/screen-spec.md`

```markdown
# SCR-001 — Nombre de la pantalla

## 1. Identificación
- Módulo:
- Ruta o punto de acceso:
- Tipo: página / modal / panel / asistente
- Estado documental:
- Versión objetivo:

## 2. Propósito
¿Qué tarea permite realizar?

## 3. Actores y permisos
- Roles autorizados:
- Restricciones:
- Comportamiento sin permisos:

## 4. Navegación
- Orígenes:
- Destinos:
- Acciones de salida:
- Comportamiento al cancelar o volver:

## 5. Artefactos visuales
- Wireframe editable:
- Exportación del wireframe:
- Diseño de alta fidelidad:
- Versión/estado del diseño:
- Leyenda y anotaciones:

## 6. Estructura visual
| Zona | Contenido | Comportamiento |
|---|---|---|
| Cabecera | ... | ... |
| Navegación | ... | ... |
| Área principal | ... | ... |
| Acciones | ... | ... |

## 7. Campos y controles
| ID | Etiqueta/control | Tipo | Obligatorio | Editable | Regla |
|---|---|---|---|---|---|
| CT-001 | ... | ... | Sí/No | Sí/No | RN-001 |

## 8. Acciones
| ID | Acción | Permiso | Condición | Resultado |
|---|---|---|---|---|
| AC-001 | ... | ... | ... | ... |

## 9. Validaciones
| Campo/acción | Condición | Momento | Mensaje | Recuperación |
|---|---|---|---|---|
| ... | ... | ... | ... | ... |

## 10. Estados de pantalla
- Inicial:
- Cargando:
- Normal:
- Vacío:
- Sin resultados:
- Error:
- Solo lectura:
- Sin permisos:
- Confirmación:
- Otros estados relevantes:

## 11. Comportamiento de controles
Describir filtros, ordenación, paginación, autocompletado, dependencias,
selección, confirmaciones y persistencia de estado cuando aplique.

## 12. Reglas y requisitos relacionados
- RF-001
- RN-001

## 13. Flujos y casos de uso relacionados
- FL-001
- UC-001

## 14. Criterios de aceptación
- RF-001-CA-01

## 15. Accesibilidad y responsive
- Uso con teclado y gestión del foco:
- Etiquetas y mensajes:
- Contraste y estados:
- Adaptación a tamaños de pantalla:
- Otros requisitos aplicables:

## 16. Preguntas abiertas
- ...

## 17. Historial de cambios
- ...
```

### 17.1. Reglas para documentar pantallas

- Cada pantalla relevante debe tener una ficha y un identificador `SCR`.
- Los modales, paneles y asistentes pueden tener ID propio cuando posean comportamiento significativo.
- Los mockups deben llevar anotaciones o una leyenda que relacione los controles con la ficha.
- No documentar únicamente el estado ideal con datos.
- Especificar estados vacíos, errores, carga, permisos y confirmaciones cuando sean relevantes.
- Describir el resultado de cada acción, no solo su etiqueta.
- Los mensajes de error deben explicar el problema y, cuando sea posible, cómo resolverlo.
- Especificar las reglas de filtros, ordenación y paginación cuando existan.
- No inferir que un control se comporta de una manera estándar si la decisión afecta al producto.
- Si un campo depende de otro, documentar la dependencia, las condiciones y qué sucede al cambiar el campo padre.
- Distinguir entre ocultar, deshabilitar y rechazar una acción por falta de permisos.

### 17.2. Plantilla ampliada de campo/control

Utilizarla para campos complejos o relevantes; no es obligatorio repetir todas las propiedades en cada control sencillo.

```markdown
### CT-001 — Nombre del campo

- Etiqueta visible:
- Tipo de dato:
- Tipo de control:
- Descripción:
- Obligatorio:
- Valor inicial:
- Longitud mínima/máxima:
- Formato:
- Valores permitidos:
- Origen de opciones:
- Editable en qué estados:
- Roles autorizados:
- Dependencias:
- Regla de validación:
- Momento de validación:
- Mensaje de error:
- Comportamiento al corregir:
- Requisito/regla relacionados:
```

Los valores concretos deben proceder de decisiones confirmadas o quedar marcados como pendientes. No inventar longitudes, límites o mensajes definitivos.

---

## 18. Proceso obligatorio de wireframe a alta fidelidad

### Fase A — Wireframe funcional

Crear un wireframe de baja fidelidad con Excalidraw u otra herramienta aprobada. Debe mostrar la distribución, las zonas, los controles, las acciones y las anotaciones necesarias para comprender el comportamiento.

Archivos recomendados:

- `wireframe.excalidraw`: fuente editable.
- `wireframe.png` o `.svg`: exportación de lectura.
- `screen-spec.md`: especificación funcional de la pantalla.

### Fase B — Revisión funcional

Comprobar que:

- La pantalla satisface un objetivo identificable.
- Los controles y las acciones están definidos.
- La navegación está resuelta.
- Los permisos y las reglas relevantes están identificados.
- Los estados y errores importantes están contemplados.
- Las preguntas pendientes están registradas.
- Los requisitos relacionados existen y son coherentes.

### Fase C — Aprobación del wireframe

Registrar el estado de aprobación. Aprobar el wireframe significa validar la estructura y el comportamiento funcional, no cerrar la estética.

### Fase D — Alta fidelidad

Aplicar el sistema visual aprobado: tipografía, colores, espaciado, iconografía, componentes y comportamiento responsive cuando aplique.

Guardar el diseño en un formato editable adecuado y enlazarlo desde `screen-spec.md`. No asumir que el PNG exportado es la fuente original.

### Fase E — Revisión final

Comprobar que el diseño de alta fidelidad respeta la especificación funcional aprobada. Si introduce o modifica comportamiento, actualizar los requisitos, reglas, criterios y wireframe afectados y volver a revisar lo necesario.

No pasar directamente a alta fidelidad una pantalla cuyo comportamiento fundamental esté pendiente de aprobación, salvo excepción explícita registrada.

---

## 19. Plantilla: catálogo de pantallas

**Archivo:** `03-ux-ui/SCREEN-CATALOG.md`

```markdown
# Catálogo de pantallas

| ID | Nombre | Módulo | Propósito | Estado funcional | Wireframe | Alta fidelidad |
|---|---|---|---|---|---|---|
| SCR-001 | ... | MOD-001 | ... | Draft | Enlace | Enlace |

## Reglas de navegación
Describir convenciones globales y enlazar el mapa de navegación.

## Pantallas retiradas o sustituidas
Registrar referencias cuando sea necesario conservar trazabilidad.
```

El catálogo debe servir como índice y no duplicar la ficha detallada de cada pantalla.

---

## 20. Plantilla: mapa funcional y catálogo de requisitos

**Archivo:** `02-functional/FUNCTIONAL-MAP.md`

```markdown
# Mapa funcional

## Vista general
Diagrama de módulos y relaciones.

## Módulos
| ID | Módulo | Propósito | Prioridad | Estado |
|---|---|---|---|---|
| MOD-001 | ... | ... | ... | ... |

## Funcionalidades
| ID | Módulo | Nombre | Descripción | Versión |
|---|---|---|---|---|
| FN-001 | MOD-001 | ... | ... | ... |

## Dependencias entre módulos
- ...

## Preguntas abiertas
- ...
```

**Archivo:** `02-functional/REQUIREMENTS-CATALOG.md`

```markdown
# Catálogo de requisitos funcionales

| ID | Nombre | Módulo | Funcionalidad | Prioridad | Estado | Criterios |
|---|---|---|---|---|---|---|
| RF-001 | ... | MOD-001 | FN-001 | Must | Draft | RF-001-CA-01 |

Este catálogo debe ser un índice de las fichas canónicas de requisitos.
No mantener descripciones completas duplicadas aquí.
```

---

## 21. Plantilla: modelo conceptual de datos y diccionario

**Archivos:** `04-domain-and-context/CONCEPTUAL-DATA-MODEL.md` y `DATA-DICTIONARY.md`

El modelo conceptual explica conceptos de negocio y sus relaciones; no es el esquema físico de la base de datos.

```markdown
# Modelo conceptual de datos

## Objetivo y alcance
## Diagrama conceptual
## Entidades/conceptos
| ID | Concepto | Descripción | Identificador de negocio |
|---|---|---|---|
| DOM-001 | ... | ... | ... |

## Relaciones
| Origen | Relación | Destino | Cardinalidad | Restricciones |
|---|---|---|---|---|
| ... | ... | ... | ... | ... |

## Ciclos de vida y estados
## Reglas de integridad funcional
## Sistemas propietarios y origen de datos
## Requisitos relacionados
## Preguntas abiertas
```

Plantilla para el diccionario:

```markdown
# DOM-001 — Nombre del concepto

## Definición
## Propósito de negocio
## Atributos relevantes
| Atributo | Significado | Tipo conceptual | Obligatorio | Restricciones |
|---|---|---|---|---|
| ... | ... | ... | ... | ... |

## Relaciones
## Estados y transiciones
## Origen y destino de la información
## Reglas relacionadas
## Requisitos relacionados
## Notas y preguntas abiertas
```

No añadir tipos SQL, índices o detalles de persistencia física salvo que se trate expresamente de documentación técnica.

---

## 22. Plantilla: contexto y arquitectura conceptual de alto nivel

**Archivos:** `04-domain-and-context/SYSTEM-CONTEXT.md` y `HIGH-LEVEL-ARCHITECTURE.md`

```markdown
# Contexto del sistema

## Propósito
## Frontera del sistema
## Actores externos
## Sistemas externos
## Diagrama de contexto
## Interacciones principales
| Origen | Destino | Propósito | Información intercambiada |
|---|---|---|---|
| ... | ... | ... | ... |

## Responsabilidades dentro/fuera del sistema
## Restricciones y dependencias
## Requisitos relacionados
## Preguntas abiertas
```

```markdown
# Arquitectura conceptual de alto nivel

## Objetivo del diagrama
## Principios y restricciones confirmados
## Diagrama lógico
## Bloques funcionales
| Bloque | Responsabilidad | Entradas/salidas | Relaciones |
|---|---|---|---|
| ... | ... | ... | ... |

## Flujos de información
## Límites y responsabilidades
## Sistemas externos
## Riesgos y dependencias
## Decisiones que quedan para la arquitectura técnica
## Requisitos relacionados
## Preguntas abiertas
```

El diagrama debe representar responsabilidades y relaciones, no imponer servicios separados, tecnologías o infraestructura sin una decisión aprobada. Cuando una decisión técnica sea obligatoria por una restricción del proyecto, registrar su origen.

---

## 23. Plantilla: sistemas e integraciones

**Archivo:** `04-domain-and-context/INTEGRATION-CATALOG.md` y una ficha por integración compleja.

```markdown
# INT-001 — Nombre de la integración

## Objetivo funcional
## Sistema propietario
## Sistema consumidor
## Propósito del intercambio
## Datos intercambiados
## Disparador y frecuencia
## Resultado esperado
## Errores funcionales
## Indisponibilidad y recuperación esperada
## Reintentos o intervención del usuario
## Permisos y restricciones
## Impacto visible para el usuario
## Diagrama conceptual o secuencia
## Requisitos y reglas relacionados
## Preguntas abiertas
```

No inventar disponibilidad, frecuencia, mecanismos de reintento ni garantías de los sistemas externos. Si se desconocen, registrarlos como preguntas abiertas.

---

## 24. Plantilla: requisito no funcional

**Archivo:** `05-quality-and-acceptance/NON-FUNCTIONAL-REQUIREMENTS.md`

```markdown
# RNF-001 — Nombre del requisito no funcional

## Categoría
Rendimiento / disponibilidad / seguridad / privacidad / accesibilidad /
usabilidad / compatibilidad / observabilidad / capacidad / recuperación.

## Necesidad y justificación
## Requisito verificable
El sistema deberá...

## Condiciones y contexto de medición
## Métrica y umbral
## Método de verificación
## Prioridad
## Componentes o funcionalidades afectados
## Restricciones y supuestos
## Responsable de aprobación
## Preguntas abiertas
```

No convertir adjetivos vagos en umbrales inventados. Si el valor de rendimiento o disponibilidad no está definido, registrar que necesita una decisión de producto, negocio o arquitectura.

---

## 25. Plantilla: criterios de aceptación

**Archivo:** criterios dentro de la ficha del requisito o en un archivo canónico cuando se gestione una suite compartida.

Usar formato Dado/Cuando/Entonces para escenarios observables.

```markdown
# RF-001-CA-01 — Nombre del escenario

- Requisito: RF-001
- Tipo: principal / alternativo / validación / autorización / recuperación
- Prioridad: ...

### Dado
Contexto inicial y precondiciones relevantes.

### Cuando
Acción o evento que activa el comportamiento.

### Entonces
Resultado observable que debe producirse.

### Y
Resultados adicionales necesarios, si los hay.

### Datos de ejemplo
Solo cuando sean útiles para hacer el escenario verificable.

### Evidencia de verificación
Enlace a prueba o evidencia, una vez disponible.
```

No es obligatorio que todos los requisitos tengan los mismos cinco tipos de escenario. Incluir todos los escenarios relevantes y evitar duplicaciones. Los criterios deben ser concretos, inequívocos y comprobables.

---

## 26. Plantilla: estrategia y escenarios de aceptación

**Archivo:** `05-quality-and-acceptance/ACCEPTANCE-STRATEGY.md`

```markdown
# Estrategia de aceptación

## Alcance de la validación
## Responsables
## Tipos de validación
## Criterios de entrada
## Criterios de salida
## Entornos o condiciones necesarios
## Gestión de defectos y desviaciones
## Evidencias requeridas
## Relación con los requisitos
```

**Archivo:** `05-quality-and-acceptance/VALIDATION-SCENARIOS.md`

```markdown
# Escenarios de validación

| ID | Escenario | Requisitos | Precondiciones | Resultado esperado | Evidencia |
|---|---|---|---|---|---|
| ... | ... | ... | ... | ... | ... |
```

La especificación funcional define el resultado esperado; la evidencia de que se ha cumplido se incorpora cuando exista. No afirmar que un requisito está verificado sin pruebas o evidencia suficiente.

---

## 27. Plantilla: matriz de trazabilidad

**Archivo:** `06-traceability/TRACEABILITY-MATRIX.md`

```markdown
# Matriz de trazabilidad

| Objetivo | Módulo | Funcionalidad | Requisito | Regla | Pantalla/flujo | Criterios | Evidencia |
|---|---|---|---|---|---|---|---|
| OBJ-001 | MOD-001 | FN-001 | RF-001 | RN-001 | SCR-001 / FL-001 | RF-001-CA-01 | Pendiente |

## Reglas
- No incluir referencias inexistentes.
- Permitir relaciones de uno a muchos y de muchos a muchos.
- Marcar expresamente las relaciones aún no resueltas.
- Distinguir criterio definido de evidencia ejecutada.
- Generar esta matriz automáticamente cuando sea razonable.
```

La matriz es una vista de las relaciones, no una fuente de verdad alternativa. Siempre que sea posible, derivarla de las referencias declaradas en las fichas.

---

## 28. Plantilla: registro de decisiones

**Archivo:** `00-governance/DECISION-LOG.md`

```markdown
# DEC-001 — Título de la decisión

- Estado: Proposed / Accepted / Rejected / Superseded
- Fecha:
- Responsable:
- Artefactos afectados:

## Contexto
¿Qué pregunta o problema requiere una decisión?

## Opciones consideradas
1. ...
2. ...

## Decisión
¿Qué se ha decidido? No rellenar como aceptado hasta que exista aprobación.

## Justificación
## Consecuencias
## Impacto en requisitos, pantallas, reglas y arquitectura conceptual
## Referencias
```

Utilizar este registro para decisiones con impacto. No registrar cada corrección editorial como una decisión de producto.

---

## 29. Plantilla: preguntas abiertas

**Archivo:** `00-governance/OPEN-QUESTIONS.md`

```markdown
# Preguntas abiertas

| ID | Pregunta | Contexto | Impacto | Responsable de resolver | Estado | Artefactos afectados |
|---|---|---|---|---|---|---|
| Q-001 | ... | ... | Alto/Medio/Bajo | ... | Open | RF-001 |

## Criterios
- Describir una pregunta concreta.
- Explicar qué decisión está bloqueada o qué riesgo genera.
- Asignar responsable cuando se conozca.
- Actualizar el estado cuando se resuelva.
- Enlazar la decisión resultante en DECISION-LOG.md.
```

Si se utiliza el prefijo `Q`, añadirlo a la convención de IDs del repositorio y validar su unicidad.

---

## 30. Plantilla: Definition of Done funcional

**Archivo:** `05-quality-and-acceptance/DEFINITION-OF-DONE.md`

Una funcionalidad solo puede declararse funcionalmente completa cuando se cumplan los puntos aplicables:

- [ ] El requisito está aprobado para el alcance de la entrega.
- [ ] Los actores y permisos están definidos.
- [ ] Las reglas de negocio relevantes están documentadas.
- [ ] Los flujos alternativos y errores importantes están considerados.
- [ ] Las pantallas y controles afectados tienen especificación.
- [ ] Los wireframes están aprobados si la funcionalidad tiene interfaz.
- [ ] Los criterios de aceptación están definidos.
- [ ] Las relaciones de trazabilidad están actualizadas.
- [ ] Las preguntas bloqueantes están resueltas o existe una excepción aprobada.
- [ ] La implementación ha sido comprobada contra los criterios.
- [ ] La evidencia de validación está enlazada.
- [ ] Las desviaciones y cambios están documentados.

Distinguir entre **Definition of Ready** (la funcionalidad está suficientemente definida para implementarse) y **Definition of Done** (la funcionalidad está implementada y verificada). No utilizar ambos conceptos como sinónimos.

---

## 31. Plantilla: historial de cambios

Cada artefacto puede mantener un historial breve si aporta valor. El historial global debe residir en Git y/o en `CHANGELOG.md`.

```markdown
## Historial de cambios

| Versión/commit | Fecha | Cambio | Motivo | Artefactos relacionados |
|---|---|---|---|---|
| ... | ... | ... | ... | ... |
```

No inventar fechas, aprobadores o números de versión. Si Git ya registra de forma fiable un cambio editorial, evitar duplicar todo el historial de commits en el archivo.

---

## 32. Diagramas y recursos visuales

### 32.1. Tipos de diagrama y finalidad

| Diagrama | Pregunta que resuelve | Formato preferido |
|---|---|---|
| Contexto del sistema | ¿Quién utiliza el sistema y con qué sistemas se relaciona? | Mermaid o Excalidraw |
| Mapa funcional | ¿Cómo se divide el producto? | Mermaid |
| Mapa de navegación | ¿Cómo se accede a las pantallas? | Mermaid o Excalidraw |
| Flujo de usuario/proceso | ¿Qué pasos y decisiones existen? | Mermaid o Excalidraw |
| Arquitectura conceptual | ¿Qué responsabilidades y relaciones existen? | Mermaid o Excalidraw |
| Secuencia | ¿Cómo colaboran actores y sistemas en una operación? | Mermaid |
| Estados | ¿Qué estados y transiciones son posibles? | Mermaid |
| Modelo conceptual de datos | ¿Qué conceptos y relaciones existen? | Mermaid o herramienta aprobada |
| Wireframe | ¿Cómo se distribuye y comporta una pantalla? | Excalidraw |

### 32.2. Reglas visuales

- Cada diagrama debe tener un título, propósito, identificador si se referencia de forma independiente y una explicación breve.
- Mantener el archivo fuente editable en Git.
- Las exportaciones PNG/SVG son representaciones; no deben convertirse en una segunda fuente de edición.
- Los diagramas deben tener leyenda cuando utilicen símbolos o convenciones no obvias.
- Usar flechas y relaciones etiquetadas con un significado claro.
- Evitar diagramas saturados; dividirlos cuando mezclen demasiados niveles.
- No añadir diagramas solo por decoración.
- Cualquier afirmación derivada del diagrama debe ser coherente con la especificación textual.
- Si el diagrama y el texto entran en conflicto, registrar y resolver la discrepancia; no elegir arbitrariamente uno.

---

## 33. Proceso de elaboración

El agente `documentator` debe seguir estas fases, de forma iterativa:

### Fase 1 — Descubrimiento del producto

Crear o actualizar:

- Visión del producto.
- Objetivos y métricas.
- Alcance y exclusiones.
- Actores, roles y restricciones.
- Glosario inicial.
- Registro de preguntas y decisiones.

No diseñar todas las pantallas antes de comprender el problema y el alcance.

### Fase 2 — Descomposición funcional

Crear o actualizar:

- Mapa funcional.
- Módulos y responsabilidades.
- Catálogo de funcionalidades.
- Prioridad y versión objetivo.
- Dependencias entre módulos.

### Fase 3 — Procesos y reglas

Definir:

- Casos de uso relevantes.
- Flujos principales y alternativos.
- Reglas de negocio.
- Estados y transiciones.
- Excepciones y recuperación.

Resolver primero las decisiones que afectan a múltiples pantallas.

### Fase 4 — Wireframes y navegación

Crear:

- Mapa de navegación.
- Catálogo de pantallas.
- Wireframes anotados.
- Fichas iniciales de pantalla.
- Relaciones con requisitos y flujos.

### Fase 5 — Especificación detallada

Completar:

- Requisitos atómicos.
- Campos y controles.
- Acciones y permisos.
- Validaciones y mensajes.
- Estados vacíos, carga, error y solo lectura cuando apliquen.
- Criterios de aceptación.
- Relaciones de trazabilidad.

### Fase 6 — Contexto, arquitectura conceptual y calidad

Definir:

- Modelo conceptual de datos.
- Sistemas externos e integraciones.
- Contexto del sistema.
- Arquitectura lógica de alto nivel.
- Requisitos no funcionales verificables.

### Fase 7 — Diseño de alta fidelidad

Solo después de aprobar el comportamiento funcional de las pantallas:

- Crear el diseño visual detallado.
- Vincular los artefactos visuales.
- Revisar accesibilidad y responsive cuando apliquen.
- Actualizar la especificación si cambia algún comportamiento.

### Fase 8 — Revisión y baseline

Antes de aprobar una versión:

- Comprobar enlaces e IDs.
- Revisar cobertura de requisitos.
- Verificar que cada requisito aprobado tiene criterios de aceptación.
- Resolver o declarar explícitamente las preguntas bloqueantes.
- Confirmar consistencia entre texto, flujos, reglas y mockups.
- Registrar versión/baseline y aprobaciones.

El proceso es iterativo. Si al diseñar una pantalla aparece una regla nueva, actualizar la regla y los requisitos relacionados. No continuar propagando una contradicción por el resto de los documentos.

---

## 34. Flujo de cambios y control de versiones

Cada cambio funcional debe seguir un proceso proporcional a su impacto:

1. Registrar la necesidad y su motivo.
2. Identificar los artefactos afectados.
3. Modificar los artefactos canónicos.
4. Ejecutar las validaciones automáticas disponibles.
5. Revisar el impacto en reglas, pantallas, flujos, criterios y requisitos dependientes.
6. Obtener la revisión/aprobación requerida.
7. Integrar los cambios en Git.
8. Actualizar el estado y la baseline cuando corresponda.

Cambios editoriales sin impacto semántico pueden utilizar una revisión ligera. Los cambios en comportamiento, permisos, reglas, alcance o aceptación requieren revisión funcional.

No borrar un requisito aprobado sin conservar trazabilidad suficiente. Marcarlo como retirado o sustituido y documentar la alternativa cuando corresponda.

---

## 35. Validaciones automáticas recomendadas

Implementar gradualmente un validador documental que compruebe:

1. Unicidad de IDs.
2. Existencia de referencias y enlaces relativos.
3. Existencia de los archivos referenciados.
4. Requisitos aprobados con criterios de aceptación.
5. Pantallas aprobadas con especificación y requisitos relacionados.
6. Funcionalidades con módulo asignado.
7. Integridad de los enlaces de trazabilidad.
8. Artefactos obsoletos todavía referenciados.
9. Diferencias no reflejadas entre un mockup aprobado y su ficha, cuando puedan detectarse mediante revisión o herramientas adecuadas.
10. Consistencia de estados y metadatos obligatorios.

No afirmar que una validación se ha ejecutado si no existe una herramienta o evidencia que lo confirme. Si no se dispone de un validador, realizar una revisión manual y declarar su alcance.

---

## 36. Responsabilidades del agente `documentator`

El agente debe:

- Leer este estándar y las instrucciones específicas del proyecto antes de crear documentación.
- Inspeccionar la documentación existente antes de crear archivos nuevos.
- Reutilizar decisiones aprobadas y convenciones ya establecidas.
- Mantener una sola fuente canónica por artefacto.
- Crear y actualizar el índice maestro.
- Usar las plantillas correspondientes.
- Mantener los IDs y enlaces estables.
- Separar información confirmada, propuestas, supuestos y preguntas abiertas.
- No inventar decisiones ni presentar inferencias como hechos.
- Documentar casos alternativos, errores, permisos y estados relevantes.
- Mantener coherentes mockups, requisitos, reglas y criterios.
- Actualizar la trazabilidad al modificar un artefacto.
- Informar de los cambios realizados, los artefactos afectados, las preguntas pendientes y las validaciones ejecutadas.
- Preferir cambios pequeños y revisables en lugar de reescribir indiscriminadamente toda la documentación.
- No crear documentación duplicada que contradiga la fuente existente.
- No declarar un requisito aprobado, implementado o verificado sin evidencia apropiada.

Cuando falte información, el agente debe registrar la pregunta y explicar el impacto. Puede proponer opciones, pero debe etiquetarlas como propuestas y no convertirlas en decisiones aprobadas.

### 36.1. Orden de precedencia

En caso de conflicto, seguir este orden:

1. Instrucciones explícitas del usuario o responsable autorizado para el proyecto.
2. Decisiones de producto/funcionales aprobadas y vigentes.
3. Requisitos y artefactos aprobados de la baseline actual.
4. Este estándar documental.
5. Propuestas o convenciones sugeridas por el agente.

Si el conflicto entre dos fuentes aprobadas no puede resolverse por fecha, autoridad o alcance, registrarlo como pregunta/decisión pendiente y pedir resolución.

---

## 37. Definición de una especificación funcional completa

Una funcionalidad está **lista para implementación** cuando, en función de su naturaleza:

- [ ] Tiene propósito, alcance y prioridad claros.
- [ ] Tiene actor y permisos identificados.
- [ ] Sus requisitos están definidos de forma verificable.
- [ ] Las reglas de negocio están descritas y referenciadas.
- [ ] Las precondiciones, resultados y excepciones relevantes están definidos.
- [ ] Los flujos y estados necesarios están documentados.
- [ ] Las pantallas y sus controles están especificados si hay interfaz.
- [ ] Los wireframes están aprobados si son necesarios.
- [ ] Las integraciones y los conceptos de datos relevantes están identificados.
- [ ] Los criterios de aceptación cubren los escenarios pertinentes.
- [ ] Las referencias de trazabilidad son válidas.
- [ ] Las preguntas bloqueantes están resueltas o existe una excepción aprobada.

Una funcionalidad está **verificada** cuando además existe evidencia suficiente de que la implementación satisface sus criterios de aceptación.

La documentación no debe declarar que un requisito está verificado solo porque esté bien escrito, el código compile o se haya completado una revisión visual.

---

## 38. Primera adopción del estándar

No intentar rellenar toda la estructura a la vez. Aplicar el método de manera incremental:

1. Crear el índice maestro, las convenciones de IDs, el registro de decisiones y preguntas, y las plantillas de módulo, requisito y pantalla.
2. Elegir una funcionalidad representativa de complejidad media.
3. Documentarla de extremo a extremo: objetivo, módulo, requisitos, reglas, flujo, wireframe, ficha de pantalla y criterios de aceptación.
4. Revisar con negocio y desarrollo si la definición elimina las ambigüedades necesarias para implementar.
5. Ajustar las plantillas y registrar los cambios del estándar.
6. Añadir automatización de enlaces, IDs y cobertura cuando el volumen lo justifique.
7. Escalar el método al resto del producto.

La primera funcionalidad es una prueba del método, no una excusa para omitir las convenciones globales.

---

## 39. Checklist final para cada intervención del `documentator`

Antes de dar por terminada una tarea documental, comprobar:

- [ ] He leído las instrucciones del proyecto y la documentación existente.
- [ ] He localizado la fuente canónica de cada artefacto afectado.
- [ ] No he inventado reglas, valores, permisos ni decisiones.
- [ ] He marcado claramente las propuestas, supuestos y preguntas abiertas.
- [ ] He utilizado IDs estables y únicos.
- [ ] He actualizado el índice y los enlaces que correspondían.
- [ ] He mantenido la coherencia entre requisitos, reglas, flujos, pantallas y mockups.
- [ ] He añadido criterios de aceptación verificables cuando corresponde.
- [ ] He evaluado el impacto en la trazabilidad.
- [ ] He realizado las validaciones disponibles y he informado de las que no se pudieron ejecutar.
- [ ] He informado de los archivos modificados, las decisiones pendientes y los riesgos detectados.
- [ ] No he declarado aprobación o verificación sin evidencia.

**Resultado esperado:** documentación funcional modular, legible para negocio, precisa para desarrollo, visualmente conectada a las pantallas, trazable hasta criterios de aceptación y mantenible a lo largo de la evolución del producto.
