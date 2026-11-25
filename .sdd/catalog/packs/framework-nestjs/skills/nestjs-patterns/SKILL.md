---
name: nestjs-patterns
description: Production NestJS backend patterns covering domain-oriented modules with explicit exports, cycle-free dependency injection (forwardRef treated as a code smell), strict boundary validation with Zod or class-validator, the deterministic request lifecycle (Middleware, Guards, Interceptors, Pipes, Handler, Exception Filters), graceful shutdown hooks, and deterministic TestingModule verification with Prisma, Drizzle, or TypeORM. Use when designing or implementing NestJS APIs, workers, or microservices under SDD Gate 2 and Gate 4.
---

# NestJS Production Patterns

Opinionated playbook for building NestJS services that stay modular, cycle-free, validated at every boundary, observable, and safely terminable under orchestrators such as Kubernetes or ECS.

## 1. When to Activate

Activate this skill whenever a Work Item (`FEAT-XXX`, `CR-XXX`, or `BUG-XXX`) involves:

- Creating or refactoring NestJS modules, providers, controllers, resolvers, gateways, or microservice handlers.
- Designing dependency injection graphs, custom providers (`useFactory`, `useClass`, `useValue`), injection tokens, or dynamic modules (`forRoot` / `forRootAsync` / `register`).
- Validating HTTP, GraphQL, WebSocket, or message payloads with `ValidationPipe` (`class-validator`) or Zod schemas.
- Implementing authentication/authorization guards, logging/timeout interceptors, or exception filters.
- Wiring persistence through Prisma, Drizzle, or TypeORM and configuring connection lifecycle.
- Hardening startup and shutdown behaviour (config validation at boot, `enableShutdownHooks`, draining in-flight work).
- Writing unit, integration, or e2e tests with `@nestjs/testing` and `TestingModule`.

## 2. Production Architecture & Patterns

### 2.1. Domain-Oriented Modules with Explicit Exports

Organise code by **bounded context**, never by technical layer (`controllers/`, `services/`, `repositories/` at the root is an anti-pattern).

```text
src/
  main.ts
  app.module.ts
  config/            # typed config + env schema validated at boot
  common/            # cross-cutting: filters, interceptors, guards, pipes (no domain logic)
  orders/
    orders.module.ts
    application/     # use cases (OrdersService, commands, queries)
    domain/          # entities, value objects, domain events, ports (interfaces)
    infrastructure/  # adapters: OrdersPrismaRepository, HTTP clients, publishers
    interface/       # controllers, DTOs/schemas, resolvers
  payments/
    payments.module.ts
    ...
```

- **Explicit public surface:** each module exports only the providers other contexts may consume (usually one facade or port token). Everything else stays private.
- **Ports as injection tokens:** depend on abstractions, bind adapters in the owning module.

```typescript
// orders/domain/orders.repository.ts
export const ORDERS_REPOSITORY = Symbol('ORDERS_REPOSITORY');
export interface OrdersRepository {
  findById(tenantId: string, id: string): Promise<Order | null>;
  save(order: Order): Promise<void>;
}

// orders/orders.module.ts
@Module({
  imports: [PrismaModule],
  controllers: [OrdersController],
  providers: [
    OrdersService,
    { provide: ORDERS_REPOSITORY, useClass: OrdersPrismaRepository },
  ],
  exports: [OrdersService], // repository stays private to the context
})
export class OrdersModule {}
```

### 2.2. Cycle-Free Dependency Injection (`forwardRef` Is a Code Smell)

A circular import between modules (`OrdersModule <-> PaymentsModule`) or providers signals a broken boundary. `forwardRef(() => X)` only hides the cycle, produces `undefined` injections at runtime, and blocks tree-shaking and isolated tests.

Refactor cycles with one of these strategies (in order of preference):

1. **Extract a shared lower-level module** containing the jointly used abstraction (e.g., `PricingModule` consumed by both contexts).
2. **Invert the dependency through a port:** the upstream context declares an interface + token; the downstream context provides the adapter.
3. **Decouple via domain events:** emit `OrderPlaced` through `@nestjs/event-emitter`, `@nestjs/cqrs` `EventBus`, or a Transactional Outbox, and let the other context react asynchronously.

```typescript
// Instead of PaymentsService injecting OrdersService (and vice versa):
@Injectable()
export class OrdersService {
  constructor(
    @Inject(ORDERS_REPOSITORY) private readonly repo: OrdersRepository,
    private readonly events: EventEmitter2,
  ) {}

  async place(cmd: PlaceOrderCommand): Promise<OrderId> {
    const order = Order.place(cmd);
    await this.repo.save(order);
    this.events.emit('orders.placed', new OrderPlacedEvent(order.id, cmd.tenantId));
    return order.id;
  }
}
```

- Prefer **singleton (default) scope**. `Scope.REQUEST` propagates up the whole injection chain and degrades throughput; use `AsyncLocalStorage` (e.g., `nestjs-cls`) for request context such as `tenantId` or `correlationId` instead.

### 2.3. Strict Boundary Validation (class-validator or Zod)

Every external input (body, query, params, headers, message payloads) is validated **before** reaching the handler. Never trust TypeScript types alone: they vanish at runtime.

```typescript
// main.ts
app.useGlobalPipes(
  new ValidationPipe({
    whitelist: true,              // strip properties without decorators
    forbidNonWhitelisted: true,   // reject unknown properties with 400
    transform: true,              // instantiate DTO classes, coerce primitives
  }),
);
```

When the stack in `specs/STACK.md` mandates Zod, use a dedicated pipe and share the schema with the contract:

```typescript
@Injectable()
export class ZodValidationPipe<T> implements PipeTransform<unknown, T> {
  constructor(private readonly schema: ZodType<T>) {}

  transform(value: unknown): T {
    const result = this.schema.safeParse(value);
    if (!result.success) {
      throw new BadRequestException({ code: 'VALIDATION_FAILED', issues: result.error.issues });
    }
    return result.data;
  }
}

export const CreateOrderSchema = z
  .object({
    sku: z.string().min(1).max(64),
    quantity: z.number().int().positive().max(1000),
  })
  .strict(); // equivalent of forbidNonWhitelisted
```

- Validate **configuration at boot** (`ConfigModule.forRoot({ validate })` with Zod or Joi) so a missing secret aborts startup instead of failing at first request.
- Response DTOs must be explicit (`ClassSerializerInterceptor` + `@Exclude()` or Zod output schemas) to avoid leaking internal fields such as `passwordHash`.

### 2.4. Deterministic Request Lifecycle

NestJS executes enhancers in a fixed order. Place each concern in the correct layer:

```text
Incoming request
  -> Middleware        (global, then module-bound: raw req/res, correlation id, helmet)
  -> Guards            (global -> controller -> route: authentication, RBAC/ABAC, tenant checks)
  -> Interceptors pre  (global -> controller -> route: logging, timeout, tracing span)
  -> Pipes             (global -> controller -> route -> param: validation, transformation)
  -> Route handler     (controller method delegating to an application service)
  -> Interceptors post (route -> controller -> global: response mapping, metrics)
  -> Exception Filters (route -> controller -> global: map errors to RFC 9457 responses)
Outgoing response
```

- **Guards** decide access and must fail closed (return `false` / throw `ForbiddenException` when metadata is missing). Register a global `AuthGuard` and opt out explicitly with an `@Public()` decorator, never the reverse.
- **Interceptors** apply cross-cutting behaviour (`timeout(5000)` via RxJS, structured logs, OpenTelemetry spans) and must never swallow errors.
- **Pipes** only validate and transform; no authorization or I/O.
- **Exception Filters** map domain and infrastructure errors to stable error codes and `application/problem+json` without exposing stack traces, SQL, or secrets.

```typescript
@Catch()
export class ProblemDetailsFilter implements ExceptionFilter {
  private readonly logger = new Logger(ProblemDetailsFilter.name);

  catch(exception: unknown, host: ArgumentsHost): void {
    const res = host.switchToHttp().getResponse<Response>();
    const status = exception instanceof HttpException ? exception.getStatus() : 500;
    if (status >= 500) this.logger.error(exception); // logged, never silently dropped
    res.status(status).type('application/problem+json').json({
      type: 'about:blank',
      title: status >= 500 ? 'Internal Server Error' : (exception as HttpException).message,
      status,
    });
  }
}
```

### 2.5. Graceful Shutdown

Containers receive `SIGTERM` before being killed. Without shutdown hooks, in-flight requests, open transactions, and broker consumers are cut abruptly.

```typescript
// main.ts
async function bootstrap(): Promise<void> {
  const app = await NestFactory.create(AppModule, { bufferLogs: true });
  app.enableShutdownHooks(); // listens to SIGTERM / SIGINT
  await app.listen(process.env.PORT ?? 3000);
}

// infrastructure/prisma.service.ts
@Injectable()
export class PrismaService extends PrismaClient implements OnModuleInit, OnApplicationShutdown {
  async onModuleInit(): Promise<void> {
    await this.$connect();
  }

  async onApplicationShutdown(_signal?: string): Promise<void> {
    await this.$disconnect(); // release pool after in-flight work drains
  }
}
```

- Hook order on shutdown: `onModuleDestroy` -> `beforeApplicationShutdown` -> (connections closed) -> `onApplicationShutdown`.
- Stop consuming queues in `beforeApplicationShutdown`, finish in-flight messages, then close DB/Redis/broker clients in `onApplicationShutdown`.
- Align the orchestrator `terminationGracePeriodSeconds` with the worst-case drain time and fail readiness probes (`@nestjs/terminus`) as soon as shutdown begins.

### 2.6. Persistence Adapters (Prisma, Drizzle, TypeORM)

- Keep ORM types inside `infrastructure/`; map rows to domain entities so the ORM is replaceable.
- Wrap multi-aggregate mutations in a single transaction (`prisma.$transaction`, `db.transaction` in Drizzle, `DataSource.transaction` in TypeORM) and never call external services inside it.
- Scope every query by `tenantId` taken from the validated request context, not from client-supplied body fields.
- Run schema changes only through versioned migrations (`prisma migrate deploy`, `drizzle-kit migrate`, TypeORM migrations with `synchronize: false` in every non-local environment).

## 3. SDD Gate 2 & Gate 4 Contract Alignment

- **Gate 2 (`02-tech-spec.md`, owned by `@architect`):** document for every NestJS change:
  1. Module map: owning bounded context, exported providers, imported modules, and confirmation that the graph stays acyclic.
  2. Endpoint or message contract: route, method, DTO/Zod schema, validation constraints, error codes, and authorization rule (synchronised with `docs/knowledge/API_CATALOG.md`).
  3. Lifecycle placement: which guard, interceptor, pipe, and filter applies to each route, including the global defaults.
  4. Persistence contract: tables/entities, transaction boundaries, migrations, and tenant scoping (tracked in `docs/knowledge/DATA_MODELS.md`).
  5. Shutdown and resilience behaviour: timeouts, retries, drain strategy, and readiness/liveness probes.
- **Gate 4 (`@back-engineer` implements, `@qa-tester` verifies):**
  - Implement strictly against the approved contract; any deviation triggers Stop-the-Line and a return to `@architect`.
  - Prove with tests that unknown properties are rejected (`400`), unauthenticated calls fail (`401`), cross-tenant access fails (`403`/`404`), and unexpected errors return a sanitised `500`.
  - Enforce `.agents/rules/05-security-and-secrets.md` and `.agents/rules/07-engineering-baseline.md`: `helmet`, CORS allowlist, `@nestjs/throttler`, secrets only via validated config, no secrets or PII in logs. `@security-reviewer` audits authentication, authorization, and injection surfaces with `sdd-security-audit`.
  - `@orchestrator` blocks Gate 4 closure until the deterministic commands in Section 5 are green.

### 3.1. Deterministic Testing with TestingModule

```typescript
describe('OrdersController (e2e)', () => {
  let app: INestApplication;
  const repo: jest.Mocked<OrdersRepository> = { findById: jest.fn(), save: jest.fn() };

  beforeAll(async () => {
    const moduleRef: TestingModule = await Test.createTestingModule({ imports: [OrdersModule] })
      .overrideProvider(ORDERS_REPOSITORY)
      .useValue(repo)
      .compile();

    app = moduleRef.createNestApplication();
    app.useGlobalPipes(new ValidationPipe({ whitelist: true, forbidNonWhitelisted: true, transform: true }));
    await app.init();
  });

  afterAll(async () => {
    await app.close(); // triggers shutdown hooks, no leaked handles
  });

  it('rejects unknown properties with 400', async () => {
    await request(app.getHttpServer())
      .post('/orders')
      .send({ sku: 'A-1', quantity: 1, isAdmin: true })
      .expect(400);
    expect(repo.save).not.toHaveBeenCalled();
  });
});
```

- **Unit tests:** instantiate providers through `Test.createTestingModule` with in-memory fakes for ports; no network or database.
- **Integration tests:** run real Prisma/Drizzle/TypeORM against an ephemeral PostgreSQL (Testcontainers or the compose service declared in `specs/STACK.md`), applying migrations before the suite and truncating tables between tests.
- Reuse the **same global pipes, guards, and filters** as `main.ts` (export a `configureApp(app)` helper) so e2e tests exercise production behaviour.

## 4. Anti-Patterns & Fail-Closed Guards

| Anti-Pattern | Failure Mode | Fail-Closed Guard |
| :--- | :--- | :--- |
| `forwardRef(() => OtherModule)` to silence a cycle | Undefined injections at runtime, hidden coupling, untestable modules. | Refactor via shared module, port token, or domain events; fail CI on `madge --circular`. |
| `ValidationPipe` without `whitelist` / `forbidNonWhitelisted` | Mass assignment (`isAdmin`, `tenantId`, `role`) reaches persistence. | Global `ValidationPipe` with `whitelist: true`, `forbidNonWhitelisted: true`, `transform: true`, or `.strict()` Zod schemas. |
| Authorization implemented in interceptors or services ad hoc | Inconsistent checks; some routes ship unprotected. | Global guard deny-by-default with explicit `@Public()` opt-out and metadata-driven RBAC. |
| `@Global()` domain modules and barrel re-exports of everything | Invisible dependency graph, accidental cycles. | Explicit `exports` arrays per module; lint rule forbidding deep cross-context imports. |
| `Scope.REQUEST` providers for tenant context | Per-request instantiation of entire chains, latency spikes. | Singleton providers + `AsyncLocalStorage` request context. |
| Empty `catch {}` or filters returning `200` on error | Silent data loss with green dashboards. | Log and rethrow or map to explicit error codes; audit with `sdd-silent-failure-audit`. |
| Missing `enableShutdownHooks` / `$disconnect` | Dropped requests and leaked connections during deploys. | Shutdown hooks + `onApplicationShutdown` closing every client; `jest --detectOpenHandles`. |
| `synchronize: true` in TypeORM outside local dev | Destructive automatic schema changes in production. | Versioned migrations only; config validation rejects `synchronize` outside `local`. |
| Stack traces or ORM errors returned to clients | Information disclosure (OWASP A05). | Global Problem Details filter with sanitised messages. |

## 5. Deterministic Verification Commands

Use these deterministic commands during Gate 4 DoD verification (align package manager and paths with Section 2.5 of `specs/STACK.md`):

```bash
# 1. Typecheck and lint (strict mode, no emit)
npx tsc --noEmit -p tsconfig.json
npx eslint "src/**/*.ts" --max-warnings 0

# 2. Fail on circular module/provider imports and on forwardRef usage
npx madge --circular --extensions ts src/
! grep -rn "forwardRef(" src/

# 3. Confirm the shared configureApp() helper hardens validation (expect 3 matches)
grep -A8 "new ValidationPipe" src/configure-app.ts \
  | grep -cE "whitelist: true|forbidNonWhitelisted: true|transform: true"

# 4. Fast unit tests (TestingModule with in-memory fakes, no DB/network)
npx jest --testPathPattern "\.spec\.ts$" --runInBand

# 5. Integration and e2e tests against ephemeral PostgreSQL, detecting leaked handles
npx prisma migrate deploy   # or: npx drizzle-kit migrate / npm run typeorm migration:run
npx jest --config test/jest-e2e.json --runInBand --detectOpenHandles

# 6. Production build
npm run build
```

## Related Skills

- `typescript-patterns`
- `prisma-patterns`
- `database-migrations`
- `sdd-security-audit`
- `sdd-test-quality-audit`
- `sdd-spec-compliance-audit`
- `sdd-silent-failure-audit`
- `santa-method`
