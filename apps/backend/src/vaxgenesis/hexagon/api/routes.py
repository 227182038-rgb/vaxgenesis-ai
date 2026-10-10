"""Hexagonal API routes — v2 endpoints that use use cases.

These routes are intentionally thin: they parse the request, invoke
the use case, and return the result. No business logic here.

All routes are mounted under /api/v2/ to coexist with the v1 API
without breaking backward compatibility.
"""
from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from vaxgenesis.hexagon.containers.composition import Container
from vaxgenesis.hexagon.domain.errors import (
    DomainError, EntityNotFoundError, InvalidStateTransitionError,
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
from vaxgenesis.hexagon.use_cases.dtos import (
    CreateCandidateCommand, IngestVariantCommand, ListCandidatesQuery,
    SubmitAssayResultCommand,
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


router = APIRouter(prefix="/v2", tags=["v2 — Hexagonal"])


# ============================================================
# Container dependency
# ============================================================

def get_container() -> Container:
    """FastAPI dependency that returns the app's DI container.

    In production, this is overridden via `app.dependency_overrides` to
    return the container attached to the FastAPI app instance.
    """
    from vaxgenesis.hexagon.containers.composition import Container
    return Container()


ContainerDep = Annotated[Container, Depends(get_container)]


# ============================================================
# Domain error → HTTP status mapping
# ============================================================

def _domain_error_to_http(exc: DomainError) -> HTTPException:
    if isinstance(exc, EntityNotFoundError):
        return HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, InvalidStateTransitionError):
        return HTTPException(status_code=409, detail=str(exc))
    return HTTPException(status_code=400, detail=str(exc))


# ============================================================
# Candidate endpoints
# ============================================================

@router.post("/candidates", status_code=status.HTTP_201_CREATED)
async def create_candidate(
    payload: CreateCandidateCommand,
    container: ContainerDep,
) -> dict:
    """Create a new vaccine candidate (hexagonal v2)."""
    use_case: CreateCandidateUseCase = container.create_candidate_use_case()
    try:
        result = await use_case.execute(payload)
        return result.model_dump(mode="json")
    except DomainError as exc:
        raise _domain_error_to_http(exc) from exc


@router.get("/candidates/{candidate_id}")
async def get_candidate(
    candidate_id: UUID,
    container: ContainerDep,
) -> dict:
    """Fetch a single candidate by ID."""
    use_case: GetCandidateQueryUseCase = container.get_candidate_query_use_case()
    try:
        result = await use_case.execute(query=type("Q", (), {"candidate_id": candidate_id})())
        return result.model_dump(mode="json")
    except DomainError as exc:
        raise _domain_error_to_http(exc) from exc


@router.get("/candidates")
async def list_candidates(
    container: ContainerDep,
    project_id: UUID | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> dict:
    """List candidates, optionally filtered by project."""
    use_case: ListCandidatesQueryUseCase = container.list_candidates_query_use_case()
    result = await use_case.execute(
        ListCandidatesQuery(project_id=project_id, limit=limit, offset=offset)
    )
    return result.model_dump(mode="json")


# ============================================================
# Variant / surveillance endpoints
# ============================================================

@router.post("/variants/ingest", status_code=status.HTTP_201_CREATED)
async def ingest_variant(
    payload: IngestVariantCommand,
    container: ContainerDep,
) -> dict:
    """Ingest a new pathogen variant into the surveillance subsystem."""
    use_case: IngestVariantUseCase = container.ingest_variant_use_case()
    try:
        result = await use_case.execute(payload)
        return result.model_dump(mode="json")
    except DomainError as exc:
        raise _domain_error_to_http(exc) from exc


@router.get("/surveillance/status")
async def surveillance_status(container: ContainerDep) -> dict:
    """Get current surveillance subsystem status."""
    use_case: GetSurveillanceStatusQueryUseCase = (
        container.get_surveillance_status_query_use_case()
    )
    result = await use_case.execute()
    return result.model_dump(mode="json")


# ============================================================
# Assay endpoints
# ============================================================

@router.post("/assays/{assay_id}/result")
async def submit_assay_result(
    assay_id: UUID,
    payload: SubmitAssayResultCommand,
    container: ContainerDep,
) -> dict:
    """Submit a wet-lab assay result (triggers Bayesian model update)."""
    # Override the assay_id from the path
    cmd = payload.model_copy(update={"assay_id": assay_id})
    use_case: SubmitAssayResultUseCase = container.submit_assay_result_use_case()
    try:
        result = await use_case.execute(cmd)
        return result.model_dump(mode="json")
    except DomainError as exc:
        raise _domain_error_to_http(exc) from exc
