"""Dependency Injection composition root.

Wires adapters to use cases using `dependency-injector`.

This is the SINGLE place where concrete classes are referenced. Every
other module depends on ports (abstract interfaces).

Usage in FastAPI:

    app = FastAPI()
    container = Container()
    container.config.from_dict(settings.dict())
    app.container = container

    @app.post("/api/v2/candidates")
    async def create_candidate(
        payload: CreateCandidateCommand,
        container: Container = Depends(get_container),
    ):
        use_case = container.create_candidate_use_case()
        return await use_case.execute(payload)

Usage in tests (override):

    container = Container()
    container.uow.override(InMemoryUnitOfWork())
    container.event_bus.override(InMemoryEventBus())
"""
from __future__ import annotations

from dependency_injector import containers, providers

from vaxgenesis.hexagon.adapters.memory.event_bus import (
    InMemoryEventBus, InMemoryUnitOfWork,
)
from vaxgenesis.hexagon.adapters.memory.repositories import (
    InMemoryCandidateRepository, InMemoryPathogenRepository,
    InMemoryProjectRepository, InMemoryVariantRepository,
    InMemoryWetLabAssayRepository,
)
from vaxgenesis.hexagon.use_cases.commands.create_candidate import (
    CreateCandidateUseCase,
)
from vaxgenesis.hexagon.use_cases.commands.ingest_variant import (
    IngestVariantUseCase,
)
from vaxgenesis.hexagon.use_cases.commands.submit_assay_result import (
    SubmitAssayResultUseCase,
)
from vaxgenesis.hexagon.use_cases.queries.get_candidate import (
    GetCandidateQueryUseCase,
)
from vaxgenesis.hexagon.use_cases.queries.get_surveillance_status import (
    GetSurveillanceStatusQueryUseCase,
)
from vaxgenesis.hexagon.use_cases.queries.list_candidates import (
    ListCandidatesQueryUseCase,
)


class Container(containers.DeclarativeContainer):
    """DI container — wires ports to adapters and use cases.

    To switch to production adapters (SQLAlchemy, Redis, Neo4j), override
    the provider bindings in `composition.py` or via `container.override()`.
    """

    config = providers.Configuration()

    # ============================================================
    # Infrastructure adapters (override these in production)
    # ============================================================

    # Default: in-memory (for tests and development).
    # In production, override with SQLAlchemy-backed adapters.
    uow = providers.Singleton(InMemoryUnitOfWork)
    event_bus = providers.Singleton(InMemoryEventBus)

    candidate_repo = providers.Singleton(InMemoryCandidateRepository)
    project_repo = providers.Singleton(InMemoryProjectRepository)
    pathogen_repo = providers.Singleton(InMemoryPathogenRepository)
    variant_repo = providers.Singleton(InMemoryVariantRepository)
    assay_repo = providers.Singleton(InMemoryWetLabAssayRepository)

    # ============================================================
    # Use cases — factories that resolve dependencies at call time
    # ============================================================

    create_candidate_use_case = providers.Factory(
        CreateCandidateUseCase,
        uow=uow,
        event_bus=event_bus,
    )

    ingest_variant_use_case = providers.Factory(
        IngestVariantUseCase,
        uow=uow,
        event_bus=event_bus,
    )

    submit_assay_result_use_case = providers.Factory(
        SubmitAssayResultUseCase,
        uow=uow,
        event_bus=event_bus,
    )

    get_candidate_query_use_case = providers.Factory(
        GetCandidateQueryUseCase,
        repo=candidate_repo,
    )

    list_candidates_query_use_case = providers.Factory(
        ListCandidatesQueryUseCase,
        repo=candidate_repo,
    )

    get_surveillance_status_query_use_case = providers.Factory(
        GetSurveillanceStatusQueryUseCase,
        variant_repo=variant_repo,
    )


# ============================================================
# Production composition
# ============================================================

def configure_production_container(container: Container) -> None:
    """Override the in-memory adapters with production SQLAlchemy adapters.

    Call this at app startup in production. In tests, leave the defaults
    (in-memory) or override with test-specific fakes.

    Example:
        container = Container()
        container.config.from_dict(settings.dict())
        configure_production_container(container)
        app.container = container
    """
    # NOTE: These imports are deferred so that the in-memory default
    # works without requiring SQLAlchemy in the test environment.
    # When production SQLAlchemy adapters are implemented (in a future
    # PR per the migration guide), uncomment the overrides below.

    # from vaxgenesis.hexagon.adapters.orm.sqlalchemy_repositories import (
    #     SqlAlchemyUnitOfWork, SqlAlchemyCandidateRepository, ...
    # )
    # container.uow.override(SqlAlchemyUnitOfWork(...))
    # container.candidate_repo.override(SqlAlchemyCandidateRepository(...))
    # ...
    pass
