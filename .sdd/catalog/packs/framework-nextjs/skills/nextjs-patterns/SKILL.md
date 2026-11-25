---
name: nextjs-patterns
description: Production Next.js App Router (15+) patterns covering the React Server Components vs. Client Components boundary with minimal "use client" leaves, fail-closed Server Actions with Zod input validation and per-invocation AuthN/AuthZ, caching directives (use cache, cacheTag, revalidateTag, revalidatePath), Partial Prerendering, lightweight middleware, and server-only protection of secrets and the Data Access Layer. Use when designing or implementing Next.js web applications under SDD Gate 2 and Gate 4.
---

# Next.js App Router Patterns

Server-first playbook for Next.js 15+ App Router applications: render on the server by default, ship the smallest possible client JavaScript, treat every Server Action as a public HTTP endpoint, cache deliberately with explicit invalidation, and keep secrets and data access physically unreachable from client bundles.

## 1. When to Activate

Activate this skill whenever a Work Item (`FEAT-XXX`, `CR-XXX`, or `BUG-XXX`) involves:

- Creating or restructuring routes, layouts, loading/error boundaries, or route handlers under `app/`.
- Deciding where the Server Component / Client Component boundary sits for a page or widget.
- Implementing mutations through Server Actions (`"use server"`), forms, or `useActionState`.
- Configuring data caching, `use cache`, tag/path revalidation, or Partial Prerendering (PPR).
- Adding or changing `middleware.ts` (renamed `proxy.ts` in Next.js 16) for redirects, locale, or optimistic session checks.
- Auditing a Next.js codebase for leaked secrets, unauthenticated actions, waterfalls, or oversized client bundles.

Pair with `typescript-patterns` for strict typing and `react-patterns` for component composition; this skill covers only the Next.js-specific runtime and security contract.

## 2. Production Architecture & Patterns

### 2.1. Recommended Project Layout

```text
src/
  app/
    (marketing)/page.tsx          # Static or PPR shell
    dashboard/
      layout.tsx                  # Server Component, verifies session
      page.tsx                    # Server Component, reads via DAL
      loading.tsx                 # Suspense fallback
      error.tsx                   # "use client" error boundary
      _components/
        invoice-table.tsx         # Server Component
        status-filter.tsx         # "use client" leaf (interactivity only)
    api/webhooks/stripe/route.ts  # Route Handler (signature-verified)
  server/
    dal/invoices.ts               # import "server-only"; authZ + queries
    actions/invoices.ts           # "use server"; Zod + authZ + revalidate
    auth/session.ts               # import "server-only"; verifySession()
  lib/
    schemas/invoice.ts            # Zod schemas shared by client and server
  middleware.ts                   # Lightweight, no DB, no secrets
```

- Colocate private route components in `_components/` (underscore folders are excluded from routing).
- Keep `server/` modules guarded by `import "server-only"` so any accidental client import fails the build.
- Shared Zod schemas live in a neutral module (no secrets, no DB imports) so forms can reuse them for client-side hints.

### 2.2. Server Components by Default, Minimal `"use client"` Leaves

Every file under `app/` is a Server Component unless it declares `"use client"`. The directive marks a **bundle boundary**: the file and everything it imports ship to the browser. Push it down to the smallest interactive leaf and pass server-rendered content through `children`.

```tsx
// app/dashboard/page.tsx (Server Component)
import { Suspense } from "react";
import { listInvoices } from "@/server/dal/invoices";
import { StatusFilter } from "./_components/status-filter";
import { InvoiceTable } from "./_components/invoice-table";

type PageProps = { searchParams: Promise<{ status?: string }> };

export default async function DashboardPage({ searchParams }: PageProps) {
  const { status } = await searchParams; // async request APIs (15+)
  return (
    <section>
      <StatusFilter initialStatus={status ?? "all"} />
      <Suspense fallback={<p>Loading invoices...</p>}>
        <InvoiceTable invoices={await listInvoices({ status })} />
      </Suspense>
    </section>
  );
}
```

- Props crossing the boundary must be serializable (plain objects, strings, numbers, Dates, Promises). Never pass functions, class instances, or ORM entities; map to DTOs in the DAL.
- `params`, `searchParams`, `cookies()`, `headers()`, and `draftMode()` are asynchronous in Next.js 15+; always `await` them.
- Start independent fetches in parallel (`Promise.all`) or stream them behind separate `<Suspense>` boundaries to avoid request waterfalls.

### 2.3. Fail-Closed Server Actions (Zod + Per-Invocation AuthN/AuthZ)

A Server Action is a publicly reachable `POST` endpoint with a stable action ID. Page-level or layout-level checks do **not** protect it. Every action re-validates input, re-authenticates, and re-authorizes on every invocation.

```ts
// src/server/actions/invoices.ts
"use server";

import { z } from "zod";
import { revalidateTag } from "next/cache";
import { verifySession } from "@/server/auth/session";
import { markInvoicePaid } from "@/server/dal/invoices";

const MarkPaidInput = z.object({
  invoiceId: z.string().uuid(),
  paidAt: z.coerce.date(),
});

export type ActionResult =
  | { ok: true }
  | { ok: false; error: "INVALID_INPUT" | "UNAUTHENTICATED" | "FORBIDDEN" | "CONFLICT" };

export async function markPaidAction(_prev: ActionResult | null, formData: FormData): Promise<ActionResult> {
  const parsed = MarkPaidInput.safeParse(Object.fromEntries(formData));
  if (!parsed.success) return { ok: false, error: "INVALID_INPUT" };

  const session = await verifySession(); // returns null when absent or expired
  if (!session) return { ok: false, error: "UNAUTHENTICATED" };
  if (!session.permissions.includes("invoice:write")) return { ok: false, error: "FORBIDDEN" };

  const outcome = await markInvoicePaid(session, parsed.data); // DAL re-checks tenant ownership
  if (outcome === "not_found_or_forbidden") return { ok: false, error: "FORBIDDEN" };
  if (outcome === "conflict") return { ok: false, error: "CONFLICT" };

  revalidateTag(`invoices:${session.tenantId}`);
  return { ok: true };
}
```

- Validate with `safeParse` against an allow-list schema; never spread raw `FormData` into ORM calls (mass-assignment).
- Derive `tenantId` and `userId` from the verified session, never from hidden form fields or client arguments.
- Return a discriminated union of stable error codes; never return stack traces, SQL errors, or internal IDs. Unexpected exceptions propagate to `error.tsx` and server logs (no silent `catch {}`).
- Closure-captured variables in inline actions are encrypted, but still treat them as untrusted and keep them free of secrets.
- Rate-limit sensitive actions (login, password reset, payments) server-side.

### 2.4. Data Access Layer and `server-only` Boundary

```ts
// src/server/dal/invoices.ts
import "server-only";
import { cache } from "react";
import { db } from "@/server/db";
import type { Session } from "@/server/auth/session";

export type InvoiceDTO = { id: string; number: string; totalCents: number; status: "open" | "paid" };

export const listInvoicesForTenant = cache(async (session: Session): Promise<InvoiceDTO[]> => {
  const rows = await db.invoice.findMany({ where: { tenantId: session.tenantId } });
  return rows.map(({ id, number, totalCents, status }) => ({ id, number, totalCents, status }));
});
```

- `import "server-only"` makes the build fail if a Client Component imports the module, directly or transitively. Use `import "client-only"` symmetrically for browser-only modules.
- Only variables prefixed `NEXT_PUBLIC_` are inlined into client bundles. Secrets (`DATABASE_URL`, API keys, signing keys) must never carry that prefix and must be read only inside `server-only` modules.
- Authorization lives in the DAL next to the query, so every caller (page, action, route handler) inherits it.
- Return minimal DTOs; never serialize full ORM rows (password hashes, tokens, internal flags) into RSC payloads.

### 2.5. Caching, Revalidation, and Partial Prerendering

| Mechanism | Purpose | Guardrail |
| :--- | :--- | :--- |
| `"use cache"` + `cacheLife()` + `cacheTag()` | Cache a component or async function result across requests (`cacheComponents: true` in Next.js 16; `experimental.useCache` / `dynamicIO` in 15). | Cache keys include serialized arguments; never read `cookies()` or `headers()` inside a cached scope; scope tags per tenant. |
| `revalidateTag(tag)` | Invalidate every cached entry carrying a tag after a mutation. | Call only after the write commits; tag names come from a typed helper, not ad-hoc strings. |
| `revalidatePath(path)` | Invalidate a route segment when tags are impractical. | Prefer tags for data; use paths for layout-level changes. |
| `fetch(url, { next: { tags, revalidate } })` | Opt-in fetch caching (uncached by default since 15). | Explicit `revalidate` window documented in Gate 2. |
| Partial Prerendering | Serve a static shell instantly and stream dynamic holes wrapped in `<Suspense>`. | Dynamic APIs only below a Suspense boundary; verify the route symbol in `next build`. |

```tsx
// src/app/products/[slug]/page.tsx
import { Suspense } from "react";
import { cacheLife, cacheTag } from "next/cache";
import { CartBadge } from "./_components/cart-badge"; // reads cookies() -> dynamic hole

async function getProduct(slug: string) {
  "use cache";
  cacheLife("hours");
  cacheTag(`product:${slug}`);
  return fetchCatalogProduct(slug); // public, tenant-agnostic data only
}

export default async function ProductPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const product = await getProduct(slug);
  return (
    <main>
      <h1>{product.name}</h1>
      <Suspense fallback={<span>Cart</span>}>
        <CartBadge />
      </Suspense>
    </main>
  );
}
```

- In Next.js 15, enable PPR incrementally with `experimental.ppr: "incremental"` and `export const experimental_ppr = true` per route; Next.js 16 folds it into `cacheComponents`.
- Never place per-user or per-tenant data in a shared cached scope without the identifier in the arguments and tag.

### 2.6. Lightweight `middleware.ts`

```ts
// src/middleware.ts
import { NextResponse, type NextRequest } from "next/server";

export function middleware(request: NextRequest) {
  const hasSession = request.cookies.has("session"); // optimistic presence check only
  if (!hasSession && request.nextUrl.pathname.startsWith("/dashboard")) {
    return NextResponse.redirect(new URL("/login", request.url));
  }
  return NextResponse.next();
}

export const config = { matcher: ["/dashboard/:path*"] };
```

- Middleware runs on every matched request; keep it to redirects, rewrites, locale, headers (CSP nonce), and optimistic cookie presence checks.
- No database queries, no heavy SDKs, no long-lived secrets, no full session decryption fan-out in edge middleware.
- Middleware is never the sole authorization layer (see CVE-2025-29927 header bypass); the DAL and every Server Action re-verify.
- Always declare a narrow `matcher`, excluding `_next/static`, `_next/image`, and public assets.

## 3. SDD Gate 2 & Gate 4 Contract Alignment

- **Gate 2 (`02-tech-spec.md`, owned by `@architect`):** Document for every route and mutation:
  1. Route map with rendering mode per segment (static, PPR, dynamic) and the exact `<Suspense>` boundaries.
  2. Server/Client boundary table listing every `"use client"` file and why it needs interactivity.
  3. Server Action contracts: Zod input schema, required permission, tenant scoping rule, `ActionResult` error codes, and revalidated tags or paths.
  4. Cache contract: `cacheLife` profile, tag naming scheme (including tenant scope), and invalidation triggers.
  5. DAL DTO shapes synchronized with `docs/knowledge/API_CATALOG.md` and `docs/knowledge/DATA_MODELS.md`.
- **Gate 4 (`@front-engineer`, `@back-engineer`, `@qa-tester`, `@security-reviewer`):**
  - Prove every Server Action rejects invalid input (`INVALID_INPUT`), missing sessions (`UNAUTHENTICATED`), and cross-tenant IDs (`FORBIDDEN`) with dedicated negative tests.
  - Prove `server-only` modules are not reachable from client bundles (build passes; a deliberate client import fails).
  - Prove cached reads are invalidated after mutations (tag revalidation test) and never leak data across tenants.
  - Enforce `.agents/rules/05-security-and-secrets.md`, `sdd-security-audit` (OWASP A01 Broken Access Control, A03 Injection), and `sdd-test-quality-audit` for non-tautological action tests; use `santa-method` for high-risk auth flows.

## 4. Anti-Patterns & Fail-Closed Guards

| Anti-Pattern | Failure Mode | Fail-Closed Guard |
| :--- | :--- | :--- |
| `"use client"` at the top of `page.tsx` or `layout.tsx` | Whole subtree ships to the browser; data fetching moves client-side; bundle bloat. | Keep pages as Server Components; isolate interactivity in leaf components receiving serializable props. |
| Server Action without its own session and permission check | Any client can invoke the action ID directly and bypass page-level guards. | `verifySession()` + permission + tenant ownership inside every action and DAL call. |
| Trusting `tenantId` or `userId` from `FormData` | Horizontal privilege escalation (IDOR). | Derive identity exclusively from the verified session. |
| DB client or secret imported in a module without `server-only` | Secret or query logic bundled into client JavaScript. | `import "server-only"` in every DAL, auth, and secret-reading module; CI greps the `.next/static` output. |
| `NEXT_PUBLIC_` prefix on API keys or tokens | Value inlined into public bundles permanently. | Only publishable identifiers use `NEXT_PUBLIC_`; secret scanners block the rest. |
| Reading `cookies()` inside a `"use cache"` scope | Build error, or one user's data cached for everyone. | Read request data outside the cached function and pass only non-sensitive keys as arguments. |
| DB lookups or token introspection in `middleware.ts` | Latency on every request, edge runtime failures, secret sprawl. | Optimistic cookie checks only; real verification in the DAL. |
| Silent `try { ... } catch { return null }` in actions | Failures disappear with green UI (violates `sdd-silent-failure-audit`). | Return typed error codes for expected failures; rethrow unexpected errors to `error.tsx` and logs. |
| Sequential `await` of independent fetches | Request waterfalls and slow TTFB. | `Promise.all` or parallel Suspense boundaries. |

## 5. Deterministic Verification Commands

Use these deterministic commands during Gate 4 DoD verification (adapt paths and package manager to `specs/STACK.md` section 2.5):

```bash
# 1. Strict typecheck and lint
npx tsc --noEmit
npx eslint . --max-warnings=0

# 2. Production build (fails if a client module imports "server-only");
#    inspect route symbols: static, partial prerender, or dynamic
npx next build

# 3. Every DAL/auth module must declare the server-only guard (expect empty output)
grep -rL 'import "server-only"' src/server/dal src/server/auth

# 4. Every Server Action file must validate with Zod (expect empty output)
grep -rL "safeParse" src/server/actions

# 5. No secrets or server env names in client bundles (expect no matches)
grep -rEn "DATABASE_URL|sk_live_|BEGIN PRIVATE KEY" .next/static || echo "OK: no secrets in client bundle"

# 6. No NEXT_PUBLIC_ secrets declared (review any match)
grep -rEn "NEXT_PUBLIC_[A-Z_]*(SECRET|TOKEN|PRIVATE|PASSWORD)" --include="*.ts" --include="*.tsx" --include=".env*" . || echo "OK"

# 7. Unit tests for actions and DAL (negative authZ cases included)
npx vitest run src/server

# 8. End-to-end flows across the RSC/Client boundary
npx playwright test
```
