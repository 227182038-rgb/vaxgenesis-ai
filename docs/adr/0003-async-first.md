# ADR-0003: Async-First with `httpx` and `asyncio`

Date: 2026-02-15
Status: Accepted
Relates-to: ADR-0001

## Context

The v1.0 codebase uses a mix of sync (SQLAlchemy, Redis client) and
async (FastAPI route handlers) code. This forces `asyncio.run()` calls
inside Celery tasks and creates blocking I/O in async contexts.

The audit (v1.1) noted that the LIMS client (`learning/lims_client.py`)
is async, but the underlying SQLAlchemy session is sync, creating
friction at the boundary.

## Decision

All new hexagonal code will be **async-first**:

1. **HTTP client:** `httpx.AsyncClient` for all external API calls.
2. **Database:** SQLAlchemy 2.0 async ORM (`AsyncSession`).
3. **Redis:** `redis.asyncio.Redis`.
4. **Repository ports:** all methods are `async def`.
5. **Use cases:** all `execute()` methods are `async def`.

### Migration path for existing modules

Existing v1.0 modules remain sync. The hexagonal adapters wrap them
with `asyncio.to_thread()` so they can be called from async contexts
without blocking the event loop:

```python
class SyncModuleAdapter:
    async def run(self, inputs: dict) -> ModuleResult:
        return await asyncio.to_thread(self._sync_module.execute, inputs)
```

### When to use sync vs async

| Code path | Sync | Async |
|-----------|------|-------|
| HTTP route handler | | ✅ |
| Use case `execute()` | | ✅ |
| Repository port method | | ✅ |
| External API call | | ✅ `httpx.AsyncClient` |
| Celery task body | ✅ (Celery is sync) | wraps async via `asyncio.run()` |
| CPU-bound ML inference | ✅ `torch`, `esm` | via `asyncio.to_thread()` |
| SQLAlchemy ORM | ✅ v1.0 models | ✅ new hexagonal adapters |

## Consequences

**Positive:**
- No event-loop blocking under load.
- Single I/O model in the hexagonal layer.
- Better utilization of async web servers (uvicorn workers).

**Negative:**
- Two ORM sessions during migration (sync v1.0 + async v2).
- Engineers must understand `asyncio.to_thread` boundary.

## References

- SQLAlchemy 2.0 async: https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
- `httpx` async: https://www.python-httpx.org/async/
