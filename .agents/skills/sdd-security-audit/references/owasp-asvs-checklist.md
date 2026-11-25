# Referencia `sdd-security-audit`: Checklist OWASP Top 10 / ASVS v4+ en Gate 4

Checklist determinista bajo demanda para `Gate 4` (`pipeline-run` Capa 1, `@qa-tester` y `@security-reviewer`).
Extiende `.agents/rules/05-security-and-secrets.md` y `.agents/agents/security-reviewer.md` sin duplicar sus tablas.

## 1. Autorización, BOLA/IDOR y Sesiones (`OWASP A01, A07` · `ASVS V2, V3, V4`)

- [ ] **Deny-by-Default (`V4.1`):**
  - Exigir identidad y permiso explícito en cada ruta HTTP, handler RPC, resolver GraphQL, Server Action o consumidor.
  - Permitir rutas públicas solo si están declaradas explícitamente en `02-tech-spec.md`.

- [ ] **Anti-BOLA / IDOR y Multi-Tenant (`V4.2`):**
  - Filtrar toda lectura o mutación por `id`/`uuid`/`slug` junto con `owner_id` y/o `tenant_id` del contexto autenticado.
  - Si aplica RLS en base de datos, verificar política activa y propagación transaccional del tenant.

- [ ] **Anti-BOPLA / Mass Assignment (`V4.2`):**
  - Usar DTOs cerrados por comando; nunca enlazar payloads externos directo a entidades ORM.
  - Rechazar campos privilegiados no autorizados (`role`, `permissions`, `tenant_id`, `balance`, `status`).

- [ ] **Tokens y Sesiones Seguras (`V2, V3`):**
  - Hashear contraseñas con Argon2id/bcrypt/scrypt; validar JWT con lista cerrada de `alg`, `iss`, `aud` y `exp` corto.
  - Marcar cookies con `Secure`, `HttpOnly`, `SameSite=Lax|Strict` y rotar sesión tras cambio de privilegios.

## 2. Frontera Productora e Inyecciones (`OWASP A03` · `ASVS V5`)

- [ ] **Validación en Frontera Productora (`V5.1`):**
  - Validar esquema, tipos, rangos, longitudes máximas, formatos y `enum` en un único adaptador de entrada.
  - Rechazar propiedades desconocidas o malformadas en la frontera (`400`/`422`) antes de tocar el dominio.

- [ ] **Parametrización SQL y NoSQL (`V5.3`):**
  - Ejecutar el `100%` de consultas con parámetros enlazados o constructores tipados.
  - Restringir `ORDER BY`/columnas dinámicos por *allowlist* constante y bloquear operadores NoSQL inyectados (`$ne`, `$gt`, `$where`).

- [ ] **Subprocesos del Sistema Operativo (`V5.3`):**
  - Invocar comandos con vector de argumentos tipado sin shell (`shell=False`, `execFile`).
  - Bloquear cualquier interpolación de datos externos en rutas, nombres de binarios o flags.

## 3. Prevención SSRF, XXE, XSS, CSRF y Uploads (`OWASP A01, A03, A05, A08, A10` · `ASVS V4, V5, V12–V14`)

- [ ] **Prevención SSRF (`V12.6`):**
  - Exigir `https`, validar host por *allowlist* y deshabilitar redirecciones abiertas en clientes HTTP dinámicos.
  - Resolver DNS bloqueando loopback, rangos privados, link-local y metadata cloud (`127.0.0.0/8`, `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `169.254.0.0/16`, `::1`, `fc00::/7`).

- [ ] **Prevención XXE y Deserialización (`V5.5`):**
  - Deshabilitar DTD y entidades externas en parsers XML (`defusedxml` o equivalente seguro).
  - Prohibir deserialización ejecutable (`pickle`, `yaml.load` inseguro, `eval`, `new Function`) sobre datos externos.

- [ ] **Prevención XSS y Cabeceras (`V5.3, V14.4`):**
  - Mantener auto-escape contextual y prohibir HTML crudo sin sanitizador aprobado en `specs/STACK.md`.
  - Restringir esquemas en URLs dinámicas (`https:`/`mailto:`, bloqueando `javascript:`/`data:`) y emitir `Content-Security-Policy` + `X-Content-Type-Options: nosniff`.

- [ ] **Prevención CSRF y CORS (`V4.2, V13.2, V14.5`):**
  - Proteger mutaciones con sesión en cookie mediante token anti-CSRF, `SameSite` y verificación de `Origin`.
  - Prohibir orígenes comodín o reflejados cuando `Access-Control-Allow-Credentials: true`.

- [ ] **Uploads y Path Traversal (`V12.1–V12.5`):**
  - Aplicar cota de bytes, validar *magic bytes* y renombrar en servidor con UUID/hash.
  - Verificar `Path.resolve().is_relative_to(base_dir)` sin symlinks y servir con `Content-Disposition: attachment`.

## 4. Secretos, SCA/SBOM y Privacidad en Logs/Errores (`OWASP A02, A06, A08, A09` · `ASVS V6, V7, V8, V14.2`)

- [ ] **Higiene de Secretos y Cripto (`V6`):**
  - Verificar cero claves, tokens o credenciales reales en código, tests o contenedores (`.agents/rules/05-security-and-secrets.md`).
  - Conservar `.env.example` con valores ficticios y usar CSPRNG (`secrets` / `crypto.randomBytes`).

- [ ] **SCA y SBOM sobre `specs/STACK.md` (`V14.2`):**
  - Confirmar que toda dependencia está aprobada en `specs/STACK.md` y fijada en lockfile determinista.
  - Ejecutar SCA (`pip-audit`/`uv`, `npm audit`, `govulncheck`, `cargo audit`, `trivy`) sin CVEs `CRITICAL`/`HIGH` explotables y preservar metadatos para SBOM (`CycloneDX`/`SPDX`).

- [ ] **Cero PII y Credenciales en Logs y Errores (`V7, V8`):**
  - Redactar `Authorization`, cookies, API keys, contraseñas, tokens, tarjetas/IBAN y PII en logs, trazas y métricas.
  - Devolver errores HTTP canónicos opacos sin stacktraces, rutas internas ni fragmentos SQL.

## 5. Evidencia Determinista Requerida en Gate 4

| Área | Evidencia Mínima (`@qa-tester` / `@security-reviewer`) | Señal `FAIL` Bloqueante |
| :--- | :--- | :--- |
| **BOLA / Tenant** | Test negativo cruzado (`Actor A` / `Tenant A` $\rightarrow$ recurso `B` responde `403`/`404`). | Acceso cruzado exitoso o falta de test negativo en recursos con propietario. |
| **Frontera / Inyección** | Test rechazando campos extra, tipos inválidos y vectores de inyección/traversal (`400`/`422`). | Queries concatenadas, `shell=True`, SSRF sin bloqueo interno o DTO abierto. |
| **Secretos y SCA** | Escaneo de secretos limpio + paquetes en `specs/STACK.md` y SCA sin `CRITICAL`/`HIGH`. | Secreto literal, dependencia no aprobada en `STACK.md` o CVE crítico activo. |
| **PII / Errores** | Verificación de loggers y manejadores de error con redacción y salida externa opaca. | Exposición de headers/tokens/PII en logs o trazas internas devueltas al cliente. |

## 6. Remediación Fail-Closed Antes de Gate 5

1. Emitir `FAIL` ante cualquier incumplimiento aplicable citando `archivo:línea`, control `OWASP`/`ASVS` e impacto.
2. Reparar sin expandir alcance, añadir test negativo de regresión y re-ejecutar el DoD de `specs/STACK.md §2.5` antes de `santa-method` (`GATE_4`) y `Gate 5`.
