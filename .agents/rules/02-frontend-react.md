# Reglas Técnicas: Frontend React 19, TypeScript & Three.js

## 1. Organización del Código
```text
frontend/src/
├── components/
│   ├── orb/          # Canvas WebGL Three.js / R3F, geometrías del Orbe y partículas
│   └── ui/           # Diálogo minimalista de texto, botones, sheets y modales discretos
├── views/            # Vistas principales: Core (/), Debug (/debug), Settings (/settings)
├── types/            # Interfaces TypeScript espejo de los DTOs de Python (camelCase)
├── stores/           # Stores Zustand para estado del Orbe, sesiones y ejecuciones
├── api/              # Clientes HTTP (fetch/axios) y receptores WebSocket / SSE
├── services/audio/   # Web Audio API, micrófono, analizador FFT y control acústico
└── styles/           # Tailwind CSS y directivas de diseño dark futurista
```

## 2. Invariantes de TypeScript & Calidad
- **TypeScript Estricto:** Configuración con `strict: true`. Prohibido el uso del tipo `any` y conversiones de tipo forzadas no verificadas (`as any`).
- **Contratos Espejo Biunívocos:** Toda interfaz en `frontend/src/types/` debe replicar de manera idéntica los campos en `camelCase` generados por los DTOs de Python.
- **Los 4 Estados de UI Obligatorios:** Todo componente o vista que consuma datos asíncronos debe implementar:
  1. *Loading State* (esqueleto sutil o indicador no invasivo).
  2. *Empty State* (mensaje claro sin estridencias cuando no hay datos).
  3. *Error State* (mensaje de error comprensible con opción de reintento).
  4. *Success State* (renderizado de los datos reales).

## 3. Rendimiento en Canvas 3D (React Three Fiber / Three.js)
- **Cero Asignaciones en el Render Loop:** Prohibido crear objetos (`new THREE.Vector3()`, arrays o funciones anónimas) dentro del hook `useFrame`. Todo vector o variable de cálculo debe declararse fuera y reutilizarse (`ref.current`).
- **Disposal y Liberación de Memoria:** Limpieza explícita de geometrías, materiales y texturas al desmontar componentes WebGL para evitar fugas de memoria en la GPU.
- **Fluidez Garantizada:** El renderizado debe sostener 60 FPS estables en navegadores de escritorio y móviles.

## 4. Filosofía Minimalista de la UI
- La pantalla principal `/` no debe mostrar barras de navegación fijas ni dashboards recargados en reposo.
- Las transiciones visuales responden exclusivamente a eventos confirmados por el backend (Event Bus).
- Diálogo de texto flotante accesible al hacer clic/tap en el orbe para interacción manual silenciosa.

## 5. Comando de Validación Obligatoria
- `cd frontend && npx tsc --noEmit`
- `cd frontend && npm run build`
- `cd frontend && npm run test`

## 6. Directivas ECC para React 19: División Container/Presentational y Árbol de Estado (`affaan-m/ECC`)
- **Separación `Container` vs `Presentational` (`react-performance-and-patterns`)**:
  - Los componentes presentacionales reciben datos y callbacks por `props` y se centran en el renderizado semántico, accesible (WCAG 2.1 AA, `aria-live`) y estilizado.
  - Los contenedores conectan selectores atómicos de Zustand (`useWidgetStore`, `useSessionStore`) y coordinan efectos de audio o streaming SSE.
- **Árbol de Decisión de Ubicación de Estado**:
  1. **Valor derivable de `props` o estado actual** $\rightarrow$ Calcular en línea durante el render (prohibido sincronizar con `useEffect` + `setState`).
  2. **Estado efímero de un único control UI** $\rightarrow$ `useState` / `useRef` local.
  3. **Estado compartido entre widgets del HUD o alimentado por eventos SSE** $\rightarrow$ Store Zustand con selectores granulares.
- **Estabilidad en Streaming Multi-Agente**: Cada turno de un agente en la Sala de Consejo debe poseer un `id` estable y único como `key`, renderizando de forma diferenciada sus badges de réplica (`↪ Réplica a ...`) y de aprendizaje autónomo (`🧠 Aprendizaje autónomo`).
