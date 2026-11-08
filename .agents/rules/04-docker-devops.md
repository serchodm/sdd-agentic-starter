# Reglas Técnicas: Docker Compose, DevOps & TrueNAS SCALE

## 1. Organización de Infraestructura de Contenedores
```text
/
├── docker-compose.yml          # Definición base y desarrollo local reproducible
├── docker-compose.prod.yml     # Orquestación optimizada para producción
├── Dockerfile.backend          # Imagen multi-stage de FastAPI / Python 3.12+
├── Dockerfile.frontend         # Imagen multi-stage de React 19 / Nginx
└── deploy/
    ├── truenas/                # Plantillas y guías de configuración para TrueNAS SCALE
    ├── cloudflare/             # Configuración del túnel seguro Cloudflare
    └── .env.example            # Catálogo documentado de variables de entorno (sin valores reales)
```

## 2. Principios de Construcción de Imágenes
- **Multi-Stage Builds Obligatorios:** Las imágenes finales no deben contener compiladores, SDKs innecesarios ni herramientas de desarrollo.
- **Seguridad y Usuarios No-Root:** Los procesos dentro del contenedor deben ejecutarse con usuarios dedicados sin privilegios de root (`USER appuser`).
- **Reproducibilidad:** Fijar versiones base de imágenes (ej. `python:3.12-slim-bookworm`, `node:22-alpine`, `pgvector/pgvector:pg16`).

## 3. Persistencia y Almacenamiento
- **Volúmenes Mapeados:** Todos los datos con estado deben residir en volúmenes explícitos compatibles con datasets de almacenamiento persistente:
  - Base de datos relacional y vectores: `postgres_data:/var/lib/postgresql/data`
  - Workspaces y artefactos: `app_storage:/app/storage`
  - Modelos locales de audio: `audio_models:/app/models`
- **Cero Pérdida de Datos:** Los contenedores deben poder eliminarse y recrearse (`docker compose down && docker compose up -d`) conservando el estado al 100%.

## 4. Healthchecks de Sistema
- Todo servicio en `docker-compose.yml` debe definir su bloque `healthcheck`:
  - Backend: `curl -f http://localhost:8000/health || exit 1`
  - PostgreSQL: `pg_isready -U postgres`
  - Parámetros estándar: `interval: 10s`, `timeout: 5s`, `retries: 5`, `start_period: 15s`.
- Los servicios dependientes deben usar `depends_on` con condición `service_healthy`.

## 5. Validación Obligatoria
- `docker compose config` (Validación de sintaxis y sustitución de variables sin errores).
