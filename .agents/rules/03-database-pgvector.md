# Reglas Técnicas: Base de Datos PostgreSQL 16 & pgvector

## 1. Organización de Scripts
```text
DDBB/scripts/
├── definition/       # Scripts DDL estructurados y versionados (tablas, extensiones, índices)
│   ├── V001__init_extensions.sql
│   ├── V002__create_users_sessions.sql
│   └── ...
└── data/             # Scripts de semillas (seeds), catálogos base y configuraciones
    ├── S001__default_roles.sql
    └── ...
```

## 2. Convenciones de Nombrado y Estructura
- **Formato de Archivos:** `V{numero_secuencial}__{descripcion_en_snake_case}.sql` para definición; `S{numero_secuencial}__{descripcion}.sql` para datos.
- **Tablas y Columnas:** Todo identificador en base de datos debe ser en `snake_case` en minúsculas (ej. `user_id`, `created_at`, `execution_status`).
- **Nombres de Índices:** Convención explícita: `idx_{tabla}_{columna}_{tipo}` (ej. `idx_embeddings_vector_hnsw`, `idx_events_run_id`).

## 3. Idempotencia Absoluta
- Todo script DDL debe poder ejecutarse múltiples veces sin producir errores ni estados inconsistentes:
  ```sql
  CREATE EXTENSION IF NOT EXISTS vector;
  CREATE TABLE IF NOT EXISTS users ( ... );
  CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
  ```
- Prohibidas las operaciones destructivas directas (`DROP TABLE`, `DROP COLUMN`) en entornos con datos sin un plan de migración previo.

## 4. Almacenamiento Vectorial y Búsqueda Híbrida
- **Índices Vectoriales HNSW:** Columnas de embeddings configuradas con índices HNSW usando métrica de distancia coseno:
  ```sql
  CREATE INDEX IF NOT EXISTS idx_memories_embedding_hnsw 
  ON memories USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 64);
  ```
- **Búsqueda Léxica (Full-Text Search):** Columnas de búsqueda de texto de tipo `tsvector` indexadas con `GIN` para búsqueda híbrida combinada con RRF.

## 5. Tablas de Series Temporales y Eventos
- Tablas con alto volumen de inserción (`run_events`, `audit_events`) deben incluir índices compuestos sobre `(run_id, created_at)` para permitir ordenamiento y filtrado de latencia cero en la consola `/debug`.

## 6. Validación Obligatoria
- Los scripts deben ser sintácticamente válidos para PostgreSQL 16.
- Ejecución limpia sin advertencias ni bloqueos de transacciones.
