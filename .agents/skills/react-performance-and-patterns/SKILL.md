---
name: react-performance-and-patterns
description: Reglas de rendimiento, arquitectura Container/Presentational, árbol de decisión de estado (Zustand vs Local) y fluidez 60 FPS en React 19 + Three.js de affaan-m/ECC.
---

# Skill: `react-performance-and-patterns` (Arquitectura y Rendimiento React 19 de `affaan-m/ECC`)

Destilación de los patrones de composición y las reglas de rendimiento de React 19 de `affaan-m/ECC` aplicados al HUD holográfico y la Sala de Consejo 3D de Project

## 1. División `Container` vs `Presentational`
- **Componentes Presentacionales (Puros)**: Reciben datos y callbacks por `props`, carecen de acoplamiento directo a conexiones SSE o lógica de negocio compleja, y se centran en el renderizado accesible y estilizado con Tailwind v4 (ej. burbujas individuales, badges de réplica `↪ Réplica a ...` y badges `🧠 Aprendizaje autónomo`).
- **Contenedores y Orquestadores de Vista**: Conectan selectores de Zustand (`useWidgetStore`, `useSessionStore`), gestionan la cola de reproducción de audio y delegan la representación visual.

## 2. Árbol de Decisión de Ubicación de Estado
1. **¿Se puede calcular al vuelo a partir de props o estado existente?** $\rightarrow$ **Constante derivada durante el render** (PROHIBIDO usar `useState` + `useEffect`).
2. **¿Solo importa a un único widget local (ej. input de texto borrador, hover)?** $\rightarrow$ `useState` / `useRef` local.
3. **¿Se comparte entre múltiples widgets del HUD o proviene del bus SSE del backend?** $\rightarrow$ **Store Zustand** con selectores atómicos (`useWidgetStore(s => s.conversational.messages)`).

## 3. Reglas de Oro de Rendimiento 60 FPS (React 19 + WebGL)
- **Estabilidad de Referencias en Listas de Streaming**: Usar `message.id` único y estable como `key` en el historial de conversación; nunca usar el índice del array si la lista muta o se filtra.
- **Aislamiento del Canvas Three.js (`@react-three/fiber`)**: Los estados de alta frecuencia (como amplitud de audio FFT o rotación de avatares en `useFrame`) se leen por referencia (`ref.current` o `useStore.getState()`) sin disparar re-renders del árbol React en cada fotograma.
