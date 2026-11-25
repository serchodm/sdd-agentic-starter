# Referencia `sdd-security-audit`: Modelado de Amenazas STRIDE en Gate 2

Playbook bajo demanda para `@architect` al redactar `02-tech-spec.md` (`Gate 2` y `PRE_GATE_2` en `santa-method`).
Complementa `.agents/rules/05-security-and-secrets.md` sin duplicar sus reglas base.

## 1. Triggers de Activación en Gate 2

Incluir la sección **Fronteras de Confianza y Matriz STRIDE** en `02-tech-spec.md` cuando el Work Item toque:
- **AuthN / AuthZ:** login, sesiones, OAuth2/OIDC, JWT, API keys, RBAC/ABAC o cambios de permisos.
- **Multi-tenancy:** particionado por `tenant_id`, políticas RLS o cachés, colas y buckets compartidos.
- **Pagos y Saldos:** cobros, suscripciones, facturación, ledger, reembolsos o cupos financieros.
- **Webhooks e Integraciones:** callbacks entrantes, clientes HTTP salientes o ingesta de URLs externas.
- **Subida de Ficheros:** multipart, URLs prefirmadas, archivos comprimidos, imágenes, PDFs o CSV/XML.
- **Secretos y KMS:** rotación de claves, cifrado de campos, firmas criptográficas o tokens entre servicios.
- **Datos Personales (`PII`):** identificadores de identidad, contacto, finanzas, salud o telemetría sensible.

## 2. Fronteras de Confianza (*Trust Boundaries*)

Identificar explícitamente cada frontera atravesada por datos o comandos:

| ID | Frontera | Controles Exigibles en Diseño |
| :--- | :--- | :--- |
| `TB-01` | **Cliente Público $\leftrightarrow$ Edge / API** | TLS, CORS con *allowlist*, anti-CSRF, rate-limit y cota de payload. |
| `TB-02` | **Frontera Productora $\leftrightarrow$ Dominio** | Adaptador DTO único cerrado + identidad y `tenant_id` desde sesión verificada. |
| `TB-03` | **Dominio / Workers $\leftrightarrow$ Persistencia** | Predicado obligatorio por `owner_id`/`tenant_id` (o RLS), cifrado y rutas confinadas. |
| `TB-04` | **Sistema $\leftrightarrow$ Terceros / Webhooks** | Firma HMAC con ventana anti-replay o JWKS/mTLS, egress *allowlist* e idempotencia. |
| `TB-05` | **CI/CD, KMS y Secretos $\leftrightarrow$ Runtime** | Federación OIDC sin claves estáticas, mínimo privilegio IAM y `.env.example` ficticio. |

## 3. Las 6 Categorías STRIDE y Mitigaciones *Fail-Closed*

Documentar para cada categoría aplicable el vector concreto y su respuesta *fail-closed*:

### S — Spoofing (Suplantación de Identidad)
- **Riesgo:** JWT con `alg` débil o sin validar `iss`/`aud`, cabeceras `X-Tenant-Id` manipuladas, webhooks sin firma.
- **Mitigación *fail-closed*:** Fijar algoritmos permitidos, resolver actor/`tenant_id` solo del token autenticado y validar HMAC en tiempo constante + timestamp; ante fallo responder `401` sin ejecutar lógica.

### T — Tampering (Manipulación de Datos o Estado)
- **Riesgo:** Mass assignment (`role`, `price`), carrera TOCTOU en saldos/pagos, *path traversal* en ficheros.
- **Mitigación *fail-closed*:** DTOs cerrados por operación, importes/roles calculados en servidor, bloqueo transaccional (`FOR UPDATE` + `Idempotency-Key`), validación de *magic bytes* y `Path.resolve().is_relative_to(...)`.

### R — Repudiation (Repudio de Acciones Críticas)
- **Riesgo:** Mutaciones privilegiadas, pagos o accesos a PII sin rastro verificable o con inyección en logs.
- **Mitigación *fail-closed*:** Auditoría estructurada *append-only* con `actor_id`, `tenant_id`, `action`, `resource_id`, `correlation_id` y `timestamp` UTC, neutralizando saltos de línea y caracteres de control.

### I — Information Disclosure (Fuga de Información)
- **Riesgo:** Lectura cruzada BOLA/IDOR, stacktraces/SQL en errores HTTP, timing leaks, PII en logs o caché compartida.
- **Mitigación *fail-closed*:** Errores externos canónicos opacos (`401`/`403`/`404`), `Cache-Control: no-store` en datos sensibles, redacción automática de secretos/PII y clasificación en `DATA_MODELS.md`.

### D — Denial of Service (Agotamiento de Recursos)
- **Riesgo:** Payloads gigantes, zip/XML bombs, ReDoS, consultas sin paginar o reintentos sin límite ni DLQ.
- **Mitigación *fail-closed*:** Cotas duras (`max_bytes`, `max_items`, longitud de cadenas), paginación obligatoria, *timeouts* explícitos en red/BD, rate-limit por actor/tenant y envío a DLQ tras tope de reintentos.

### E — Elevation of Privilege (Escalada de Privilegios)
- **Riesgo:** Operaciones sin guard RBAC/ABAC, salto entre roles/tenants, SSRF a metadata cloud o prompt injection.
- **Mitigación *fail-closed*:** Autorización *deny-by-default* en capa de aplicación (permiso + propiedad), bloqueo de IPs internas en egress y tratamiento hostil de entradas externas (`.agents/rules/05-security-and-secrets.md`).

## 4. Plantilla para `02-tech-spec.md` (DoR hacia Gate 3)

````markdown
### Seguridad y Modelo de Amenazas STRIDE (`sdd-security-audit`)
- **Activos y PII:** `<campos sensibles, retención y política de redacción>`
- **Fronteras activas:** `<TB-01, TB-02, ...>`
- **Mitigaciones Fail-Closed:**
  - `Spoofing`: `<AuthN / firma verificada -> 401>`
  - `Tampering`: `<DTO cerrado / lock + idempotencia -> 400|409|422>`
  - `Repudiation`: `<evento auditable estructurado sin PII cruda>`
  - `Information Disclosure`: `<filtro owner/tenant + error opaco -> 403|404>`
  - `Denial of Service`: `<cotas de tamaño, paginación, timeouts y rate-limit -> 413|429>`
  - `Elevation of Privilege`: `<guard RBAC/ABAC + egress confinado -> 403>`
- **Tests negativos Gate 4:** `<BOLA/tenant cruzado, firma inválida, payload fuera de cota>`
````

## 5. Parada Pre-Gate 2 (`RN-SDD-FAIL-CLOSED`)

1. **Propiedad indefinida:** Bloquear si algún recurso carece de regla explícita de resolución de propietario/`tenant_id`.
2. **Paquetes no aprobados:** Prohibido asumir librerías de criptografía/auth ausentes de `specs/STACK.md` sin ADR.
3. **PII sin contrato:** Exigir política de cifrado, enmascaramiento en logs y ciclo de borrado antes de abrir `Gate 3`.
