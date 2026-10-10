# ADR-0002: Dependency Injection via `dependency-injector`

Date: 2026-02-15
Status: Accepted
Relates-to: ADR-0001

## Context

Hexagonal architecture requires a composition root where adapters are
wired to use cases. Three options were considered:

1. **Manual wiring** — each use case receives its dependencies via
   constructor parameters, wired at app startup. Simple but verbose
   and error-prone as the codebase grows.
2. **FastAPI's `Depends()`** — leverage FastAPI's built-in DI. Works
   for HTTP-scoped dependencies but doesn't help with background tasks
   (Celery workers) or the agent orchestrator.
3. **`dependency-injector` library** — a mature DI framework with
   containers, providers, and overriding for tests.

## Decision

Use **`dependency-injector`** for the composition root.

### Rationale

- Single source of truth for wiring (`containers/composition.py`).
- Works in both FastAPI and Celery contexts.
- Built-in test overrides: `container.override(providers)` swaps
  adapters for mocks/fakes without monkey-patching.
- Lifecycle management: singleton vs factory providers are explicit.
- Used by production systems at scale (Alibaba, BMW, Rakuten).

### Container structure

```python
class Container(DeclarativeContainer):
    config = providers.Configuration()

    # Infrastructure adapters
    db_session_factory = providers.Singleton(SessionLocal)
    redis_client = providers.Singleton(redis_from_url, url=config.redis_url)
    kg_client = providers.Singleton(KnowledgeGraph, uri=config.neo4j_uri)

    # Repositories (ports implemented by adapters)
    candidate_repo = providers.Singleton(
        SqlAlchemyCandidateRepository,
        session_factory=db_session_factory,
    )

    # Use cases
    create_candidate = providers.Factory(
        CreateCandidateUseCase,
        repo=candidate_repo,
        uow=unit_of_work,
    )
```

### Wiring FastAPI

```python
app = FastAPI()
container = Container()
container.config.from_dict(settings.dict())
app.container = container

@app.post("/api/v2/candidates")
async def create_candidate(payload: CandidateCreate, container=Depends(get_container)):
    use_case = container.create_candidate()
    return await use_case.execute(payload)
```

### Wiring Celery

```python
@celery_app.task
def run_pipeline(candidate_id: str):
    container = Container()
    container.config.from_env()
    use_case = container.run_pipeline()
    use_case.execute(candidate_id)
```

## Consequences

**Positive:**
- Single wiring point; easy to audit.
- Test overrides are explicit and reversible.
- Works across HTTP and async contexts.

**Negative:**
- Additional dependency (`dependency-injector ~= 4.41`).
- Learning curve for engineers unfamiliar with DI containers.

## References

- `dependency-injector` docs: https://python-dependency-injector.ets-labs.org/
- Fowler, M. "Inversion of Control Containers and the Dependency Injection pattern" (2004)
