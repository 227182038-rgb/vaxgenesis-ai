# Migration Guide: v1 → v2 (Hexagonal Architecture)

This guide helps you progressively migrate from the v1 API
(`/api/v1/...`) to the v2 hexagonal API (`/api/v2/...`).

## Why Migrate?

The v2 API offers:

1. **Stronger testability** — domain logic is pure Python, no DB/Redis needed.
2. **Cleaner separation** — business logic lives in use cases, not route handlers.
3. **Property-based testing** — Hypothesis can target pure domain functions.
4. **Swappable adapters** — switch Postgres → Spanner by implementing a port.
5. **Explicit transactions** — `UnitOfWork` enforces atomicity.

## Compatibility Guarantee

- **v1 API is NOT deprecated.** It will continue to work indefinitely.
- v1 and v2 can coexist on the same backend instance.
- No database migrations are required — both APIs read/write the same tables.
- The v2 API currently uses in-memory adapters by default. To use the
  production SQLAlchemy adapters, call `configure_production_container()`
  at app startup.

## Migration Steps

### Step 1: Try the v2 API (no changes needed)

The v2 router is auto-mounted at `/api/v2/`. Try it:

```bash
# Login (still v1 — auth is shared)
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@vaxgenesis.ai","password":"admin123"}' \
  | python -c "import json,sys; print(json.load(sys.stdin)['access_token'])")

# Create a candidate via v2
curl -X POST http://localhost:8000/api/v2/candidates \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"project_id":"<your-project-id>","name":"v2 Candidate"}'
```

### Step 2: Use v2 for new features

When building a new feature, use the hexagonal pattern:

1. **Define the domain entity** in `hexagon/domain/entities.py`.
2. **Define value objects** in `hexagon/domain/value_objects.py`.
3. **Define the port** (interface) in `hexagon/ports/`.
4. **Implement the adapter** in `hexagon/adapters/`.
5. **Write the use case** in `hexagon/use_cases/commands/` or `queries/`.
6. **Add the route** in `hexagon/api/routes.py`.
7. **Wire it** in `hexagon/containers/composition.py`.
8. **Write tests**: unit (example-based), property (Hypothesis), benchmark.

### Step 3: Progressively migrate v1 endpoints

For each v1 endpoint:

1. Identify the use case it implements.
2. Extract the business logic into a hexagonal use case.
3. Add a v2 route that calls the use case.
4. Keep the v1 route as a thin wrapper that calls the same use case.
5. Mark the v1 route as `@deprecated` in the OpenAPI docs.
6. After one release cycle, remove the v1 route.

### Step 4: Switch to production adapters

In production, override the in-memory adapters with SQLAlchemy ones:

```python
# In your app startup (e.g., main.py)
from vaxgenesis.hexagon.containers.composition import (
    Container, configure_production_container,
)

container = Container()
container.config.from_dict(settings.dict())
configure_production_container(container)
app.container = container
```

## Endpoint Mapping

| v1 Endpoint | v2 Endpoint | Status |
|-------------|-------------|--------|
| `POST /api/v1/candidates` | `POST /api/v2/candidates` | ✅ Available |
| `GET /api/v1/candidates/{id}` | `GET /api/v2/candidates/{id}` | ✅ Available |
| `GET /api/v1/candidates` | `GET /api/v2/candidates` | ✅ Available |
| `POST /api/v1/surveillance/ingest` | `POST /api/v2/variants/ingest` | ✅ Available |
| `GET /api/v1/surveillance/status` | `GET /api/v2/surveillance/status` | ✅ Available |
| `POST /api/v1/learning/assays/{id}/result` | `POST /api/v2/assays/{id}/result` | ✅ Available |
| `POST /api/v1/projects` | (planned) | 🚧 Not yet migrated |
| `POST /api/v1/pathogens` | (planned) | 🚧 Not yet migrated |
| `POST /api/v1/candidates/run-pipeline` | (planned) | 🚧 Not yet migrated |

## Testing the Migration

After migrating an endpoint:

1. **Unit tests** — verify the use case with in-memory adapters.
2. **Property tests** — verify domain invariants with Hypothesis.
3. **Integration tests** — verify the adapter against real Postgres.
4. **Contract tests** — verify the v2 response schema matches v1.
5. **Benchmark** — verify no performance regression.

## Rollback

If v2 causes issues:

1. Remove the v2 router from `main.py`.
2. The v1 API continues to work unaffected.
3. No database changes to undo.

## FAQ

**Q: Can I use v1 and v2 in the same request?**
A: Yes. They share the same database. A candidate created via v1 can be
fetched via v2 and vice versa.

**Q: Do I need to change my frontend?**
A: No. The frontend continues to use v1. When you're ready, update the
API client to call v2 endpoints instead.

**Q: What about authentication?**
A: Auth is shared. The same JWT works for both v1 and v2.
