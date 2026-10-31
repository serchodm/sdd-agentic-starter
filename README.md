# SDD Agentic Starter Template

Plantilla universal de desarrollo de software guiado por especificaciones (**Spec-Driven Development - SDD**) y orquestación multi-agente.

---

## 🚀 Cómo Iniciar un Nuevo Proyecto a partir de este Template

### 1. Clonar o Usar este Template
Crea un nuevo repositorio en GitHub haciendo clic en **"Use this template"** o mediante la CLI de GitHub:
```bash
gh repo create mi-nuevo-proyecto --template <tu-usuario>/sdd-agentic-starter --private
cd mi-nuevo-proyecto
```

### 2. El Repositorio Inicia BLOQUEADO (`Gate 00: Stack Lock`)
Para garantizar orden y compatibilidad, **el código de producción está bloqueado** por la regla `RN-SDD-GATE00-STACK-LOCK`. No se puede escribir código en `src/` hasta definir las tecnologías.

### 3. Habla con el `@orchestrator` en tu asistente IA (Antigravity / Cursor / Claude Code)
Envía este mensaje al agente:
> *"Hola @orchestrator. Vamos a iniciar el proyecto. Quiero definir el stack tecnológico: Backend en [.NET C# / Python / Go / Java], Frontend en [HTML5+CSS / React / Vue] y base de datos [PostgreSQL / MongoDB / N/A]. Procedamos con el Gate 00."*

El orquestador:
1. Rellenará `specs/STACK.md` con las herramientas, convenciones y comandos de test.
2. Te pedirá confirmar la casilla `[x] Gate 00 Approved (Human Sign-off)`.
3. Una vez aprobada, el repositorio se desbloqueará y comenzará el ciclo normal de desarrollo (Gate 0 -> Gate 5).

---

## 🏛️ Ciclo de Vida SDD (Gate 0 a Gate 5)

```text
[ Gate 00: STACK.md ] ──► [ Gate 0: Backlog Intake ]
                                   │
                                   ▼
[ Gate 1: 01-spec.md (EARS) ] ──► [ Gate 2: 02-tech-spec.md (Contratos) ]
                                   │
                                   ▼
[ Gate 3: 03-tasks.md (DAG) ] ──► [ Implementación Subagentes (.agent-inbox/) ]
                                   │
                                   ▼
[ Gate 4: Verificación QA ] ───► [ Gate 5: Living Docs 0DD (docs/) ] ──► DONE
```

---

## 🛡️ Verificación de Salud del Framework
Para auditar en cualquier momento la integridad de las reglas y directorios del repositorio:
```bash
python .agents/scripts/sdd_healthcheck.py
```
