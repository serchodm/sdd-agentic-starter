---
name: postgres-patterns
description: Guía de referencia rápida y patrones de producción PostgreSQL 16 + pgvector (índices HNSW/GIN/B-Tree, upserts idempotentes, transacciones cortas y aislamiento multi-tenant).
---

# Skill: `postgres-patterns` (Patrones de Producción PostgreSQL 16 + `pgvector` de `affaan-m/ECC`)

Patrones de ingeniería de base de datos de `affaan-m/ECC` adaptados para la capa de datos y memoria semántica (`Mnemo`) de Project

## 1. Selección de Índices según Carga de Trabajo
- **`B-Tree` (por defecto)**: Claves primarias UUID, claves foráneas (`session_id`, `user_id`, `agent_id`) y ordenación temporal (`created_at DESC`).
- **`HNSW` (`pgvector`)**: Búsqueda de similitud coseno en embeddings (`USING hnsw (embedding vector_cosine_ops)`), ofreciendo baja latencia y alta precisión sin requerir entrenamiento previo como `IVFFlat`.
- **`GIN`**: Columnas `JSONB` de metadatos (`metadata JSONB`) o búsqueda de texto completo.

## 2. Idempotencia Obligatoria en Scripts DDL y Semillas (`DDBB/scripts/`)
- Toda definición de esquema debe poder ejecutarse múltiples veces sin fallar:
  ```sql
  CREATE EXTENSION IF NOT EXISTS vector;
  CREATE TABLE IF NOT EXISTS ...;
  CREATE INDEX IF NOT EXISTS ...;
  ```
- Toda semilla de datos debe usar `INSERT INTO ... ON CONFLICT (...) DO UPDATE/NOTHING`.

## 3. Prevención de Problemas de Concurrencia y Rendimiento
- **Transacciones Ultracortas**: Nunca ejecutes llamadas a Gemini/ACP, síntesis TTS ni I/O de red dentro de un bloque transaccional de base de datos.
- **Paginación por Cursor o Límite Estricto**: Toda consulta de historial o memorias debe incluir un `LIMIT` explícito.
- **Filtrado de Scope y Tenant**: Incluir siempre predicados explícitos por `agent_id` / `scope` en consultas de `Mnemo` y por `user_id` en recursos de usuario.
