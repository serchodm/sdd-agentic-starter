# Épica: `EPIC-001` — [Título de la Épica]

- **ID:** `EPIC-001`
- **Título:** [Título de la Épica]
- **Estado:** `Draft` <!-- Draft | Active | Completed | On Hold -->
- **Prioridad MoSCoW:** `Must` <!-- Must | Should | Could | Wont -->
- **RICE:** `reach=100, impact=2.0, confidence=0.8, effort=2.0`

## 1. Definición Estructurada (`sdd:epic`)

```yaml sdd:epic
epic_id: "EPIC-001"
title: "[Título de la Épica]"
status: "Draft"
priority: "Must"
rice:
  reach: 100
  impact: 2.0
  confidence: 0.8
  effort: 2.0
features:
  - id: "FEAT-001"
    title: "[Slice vertical inicial]"
    priority: "Must"
    depends_on: []
```

## 2. Visión y Valor de Negocio

- **Objetivo:** [Describe el resultado de negocio medible que habilita esta Épica.]
- **Criterios de Éxito:**
  - [ ] Criterio 1: [Métrica o hito verificable]

## 3. Alcance y Roadmap de Features

| Feature | Título | Prioridad | Depende de | Estado |
| :--- | :--- | :--- | :--- | :--- |
| `FEAT-001` | [Slice vertical inicial] | `Must` | — | `Candidate` |
