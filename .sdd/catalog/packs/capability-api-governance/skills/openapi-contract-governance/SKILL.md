---
name: openapi-contract-governance
description: Contract-first OpenAPI 3.1 governance covering explicit versioning, backward-compatible evolution, oasdiff breaking-change gates, cursor pagination, RFC 9457 Problem Details, OAuth2/JWT security, and SDD API catalog alignment.
---

# OpenAPI Contract Governance

Production standard for designing, versioning, validating, and evolving HTTP/REST APIs under a strict **Contract-First OpenAPI 3.1** lifecycle aligned with SDD Gate 2, Gate 4, and Gate 5.

## 1. When to Activate

Activate this skill whenever a Work Item (`FEAT-XXX`, `CR-XXX`, or `BUG-XXX`) touches HTTP/REST interfaces:

- Creating or modifying public, partner, or internal HTTP API endpoints in `02-tech-spec.md`.
- Designing OpenAPI 3.1 specifications (`openapi.yaml` / `openapi.json`), reusable DTO schemas, or SDK generation pipelines.
- Evolving existing endpoints, response payloads, query parameters, status codes, or pagination contracts.
- Defining authentication/authorization schemes (`OAuth2`, `OIDC`, `JWT` bearer tokens, API scopes) or standardizing error responses.
- Reviewing API changes during Pre-Gate 2 (`santa-method` with `backward-compatibility` lens), Gate 4 (`sdd-spec-compliance-audit`), or Gate 5 (`docs/knowledge/API_CATALOG.md`).

## 2. Production Architecture & Patterns

### 2.1. Contract-First OpenAPI 3.1 Specification

Treat the OpenAPI 3.1 document as the single source of truth approved at Gate 2 before writing server handlers or client SDKs:

- Declare `openapi: 3.1.0` and use JSON Schema Draft 2020-12 semantics: express nullable properties with `type: ["string", "null"]` instead of legacy OpenAPI 3.0 `nullable: true`.
- Assign a globally unique, deterministic `operationId` (`camelCase` verb+resource, e.g., `listOrders`, `createInvoice`) to every operation for stable SDK and test generation.
- Centralize reusable schemas, parameters, headers, responses, and security schemes under `components/` via `$ref`; never inline duplicated request or error objects across paths.
- Use explicit formats and bounds on every field (`format: uuid`, `format: date-time`, `minLength`, `maxLength`, `minimum`, `maximum`, `maxItems`, `additionalProperties: false` on request bodies).

### 2.2. Explicit Versioning & Backward-Compatible Evolution

- **Major version in URI or media type:** Follow the strategy frozen in `specs/STACK.md` (default: explicit URI major prefix `/v1/orders`). Minor and patch evolutions remain backward compatible inside `/v1` without bumping the path.
- **Additive-only evolution inside a major version:**
  - Safe changes: adding new endpoints, adding optional request properties, adding optional query parameters, adding new response fields (when clients ignore unknown fields), relaxing validation bounds.
  - Breaking changes (forbidden inside an active major version): removing or renaming fields/endpoints, tightening request constraints, changing field data types or formats, adding required request fields without server defaults, removing enum values returned to clients or accepted in requests.
- **Expand-and-Contract deprecation lifecycle:** Mark superseded endpoints or fields with `deprecated: true`, emit RFC 8594 `Deprecation` and `Sunset` HTTP headers plus a `Link` header pointing to the successor doc, monitor consumer traffic, and remove only in the next major version or after the announced sunset window.

### 2.3. Cursor-Based Pagination

Use opaque cursor pagination for all collection endpoints with unbounded or shifting datasets; reserve `offset`/`limit` only for small, static admin lookups explicitly justified in `02-tech-spec.md`.

```yaml
openapi: 3.1.0
info:
  title: Orders API
  version: 1.2.0
paths:
  /v1/orders:
    get:
      operationId: listOrders
      summary: List orders with deterministic cursor pagination
      security:
        - oauth2Bearer: ["orders:read"]
      parameters:
        - name: cursor
          in: query
          required: false
          schema:
            type: string
            maxLength: 512
        - name: limit
          in: query
          required: false
          schema:
            type: integer
            minimum: 1
            maximum: 100
            default: 25
      responses:
        "200":
          description: Paginated orders slice
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/OrderPage"
        "400":
          $ref: "#/components/responses/BadRequestProblem"
        "401":
          $ref: "#/components/responses/UnauthorizedProblem"
        "403":
          $ref: "#/components/responses/ForbiddenProblem"
```

- Encode cursors as opaque base64url tokens containing the deterministic sort key plus unique tie-breaker (for example `(created_at, id)`), never raw SQL fragments.
- Return `items`, `next_cursor` (`type: ["string", "null"]`), and `has_more` (`boolean`), enforcing a strict server-side maximum `limit` (e.g., `<= 100`).

### 2.4. RFC 9457 Problem Details Errors

Standardize all `4xx` and `5xx` error payloads with media type `application/problem+json` conforming to RFC 9457:

```yaml
components:
  schemas:
    ProblemDetails:
      type: object
      required: [type, title, status, detail, instance]
      additionalProperties: false
      properties:
        type:
          type: string
          format: uri
          example: "https://api.example.com/problems/validation-failed"
        title:
          type: string
          example: "Request validation failed"
        status:
          type: integer
          minimum: 400
          maximum: 599
        detail:
          type: string
        instance:
          type: string
          format: uri-reference
        correlation_id:
          type: string
          format: uuid
        errors:
          type: array
          items:
            type: object
            required: [pointer, code, message]
            additionalProperties: false
            properties:
              pointer:
                type: string
                example: "/items/0/quantity"
              code:
                type: string
                example: "min_value"
              message:
                type: string
```

- Never expose stack traces, SQL errors, internal hostnames, or raw PII in `detail` or extension fields (aligned with `.agents/rules/05-security-and-secrets.md`).

### 2.5. OAuth2 & JWT Security Schemes

- Declare `securitySchemes` explicitly under `components.securitySchemes` (`type: http`, `scheme: bearer`, `bearerFormat: JWT`, or `type: oauth2` with `authorizationCode` / `clientCredentials` flows and granular scopes such as `orders:read`, `orders:write`).
- Set root-level default `security` so every endpoint is **fail-closed** by default; explicitly opt out public endpoints (`/healthz`, login callbacks) with `security: []` and document the justification in `02-tech-spec.md`.
- Document exact HTTP status semantics: `401 Unauthorized` (missing/expired/invalid JWT signature, issuer, or audience), `403 Forbidden` (valid token lacking scope or tenant/object ownership), and `429 Too Many Requests` with `Retry-After`.

## 3. SDD Gate 2 & Gate 4 Contract Alignment

| SDD Gate | Owner | Mandatory Artifact & Verification |
| :--- | :--- | :--- |
| **Gate 2** | `@architect` | Freeze OpenAPI 3.1 contract paths, schemas, RFC 9457 error types, cursor pagination, OAuth2/JWT scopes, and `oasdiff` baseline in `02-tech-spec.md`. Run `sdd-security-audit` STRIDE review for auth/tenant boundaries. |
| **Pre-Gate 2** | `santa-method` | Execute adversarial dual review with the `backward-compatibility` lens whenever modifying an existing API contract via `CR-XXX`. |
| **Gate 4** | `@back-engineer`, `@front-engineer`, `@qa-tester` | Implement server validation and typed client DTOs 1:1 with the OpenAPI contract. Run `oasdiff breaking`, contract tests, `sdd-spec-compliance-audit`, and `sdd-security-audit` OWASP/ASVS checks (BOLA/IDOR, mass assignment). |
| **Gate 5** | `@documentator` | Synchronize every added, modified, or deprecated endpoint, version, auth scope, and error code in `docs/knowledge/API_CATALOG.md` and `docs/traceability/TRACEABILITY-MATRIX.md`. |

## 4. Anti-Patterns & Fail-Closed Guards

- **Code-First Drift:** Generating OpenAPI specs post-hoc from undocumented controller annotations causes silent client breakage. *Guard:* Author or update the OpenAPI 3.1 spec first in Gate 2 and fail CI when runtime schema diverges from the committed spec.
- **Unbounded Offset Pagination:** Accepting `offset=500000&limit=10000` causes database full-scans and duplicate/skipped rows under concurrent writes. *Guard:* Enforce cursor pagination with strict `limit` ceilings (`1..100`) and reject out-of-range inputs with `400` RFC 9457 `ProblemDetails`.
- **Ad-Hoc Error Shapes:** Returning `{ "error": "bad" }` on one endpoint and `{ "msg": "fail" }` on another breaks SDK error handling. *Guard:* Require `application/problem+json` across all `4xx`/`5xx` responses via reusable `$ref` components.
- **Silent Breaking Changes:** Changing an optional field to required, narrowing an enum, or changing `integer` to `string` inside `/v1`. *Guard:* Block merges automatically when `oasdiff breaking` reports any error-level incompatibility.
- **Open-by-Default Security:** Omitting top-level `security` allows newly added endpoints to ship unauthenticated. *Guard:* Enforce root `security` and verify in `sdd-security-audit` that every `security: []` override is explicitly approved in `02-tech-spec.md`.
- **Unrestricted `additionalProperties`:** Silently accepting unknown request fields masks typos and enables mass-assignment vulnerabilities. *Guard:* Set `additionalProperties: false` on request DTOs and enforce strict schema validation at the HTTP boundary.

## 5. Deterministic Verification Commands

Run these deterministic checks in Gate 4 and CI (adapting paths to the locations declared in `specs/STACK.md`):

```bash
# 1. Lint OpenAPI 3.1 document structure, operationIds, security, and RFC 9457 conventions
npx --yes @redocly/cli lint openapi/openapi.yaml

# 2. Alternative Spectral ruleset validation (when configured in specs/STACK.md)
npx --yes @stoplight/spectral-cli lint openapi/openapi.yaml

# 3. Fail-closed breaking-change detection against the base branch OpenAPI contract
oasdiff breaking --fail-on ERR openapi/baseline/openapi.yaml openapi/openapi.yaml

# 4. Generate human-readable API changelog for Gate 5 API_CATALOG.md review
oasdiff changelog openapi/baseline/openapi.yaml openapi/openapi.yaml

# 5. Validate live/test server responses strictly against the OpenAPI 3.1 contract
uv run pytest tests/contract/test_openapi_contract.py -q
```

- **Exit criteria (DoD):** Lint exits `0` with zero errors, `oasdiff breaking --fail-on ERR` exits `0` (unless an approved new major version `/vN+1` is explicitly scoped in `02-tech-spec.md`), contract tests pass for success + RFC 9457 error paths + `401`/`403` auth boundaries, and `docs/knowledge/API_CATALOG.md` is updated at Gate 5.
