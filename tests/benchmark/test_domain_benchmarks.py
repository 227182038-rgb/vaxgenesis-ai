"""Benchmark tests for domain operations (ADR-0005, Tier 4).

Run: pytest tests/benchmark/ -v --benchmark-only

These benchmarks detect performance regressions in hot paths:
  - Sequence construction and validation
  - Candidate state transitions
  - In-memory repository save/get
  - DI container use case resolution
"""
from __future__ import annotations

from uuid import uuid4

import pytest


# ============================================================
# Sequence construction
# ============================================================

def test_benchmark_sequence_construction_short(benchmark):
    """Benchmark constructing a 100-char DNA sequence."""
    from vaxgenesis.hexagon.domain.value_objects import Sequence
    seq_str = "ATCG" * 25  # 100 bp

    def construct():
        return Sequence(value=seq_str, alphabet="dna")

    result = benchmark(construct)
    assert result.length == 100


def test_benchmark_sequence_construction_long(benchmark):
    """Benchmark constructing a 10kb DNA sequence."""
    from vaxgenesis.hexagon.domain.value_objects import Sequence
    seq_str = "ATCG" * 2500  # 10,000 bp

    def construct():
        return Sequence(value=seq_str, alphabet="dna")

    result = benchmark(construct)
    assert result.length == 10000


def test_benchmark_sequence_kmers(benchmark):
    """Benchmark k-mer extraction from a 1000-char sequence."""
    from vaxgenesis.hexagon.domain.value_objects import Sequence
    s = Sequence(value="ATCGATCG" * 125, alphabet="dna")

    def extract():
        return s.kmers(9)

    result = benchmark(extract)
    assert len(result) == 992


def test_benchmark_sequence_gc_content(benchmark):
    """Benchmark GC content calculation."""
    from vaxgenesis.hexagon.domain.value_objects import Sequence
    s = Sequence(value="ATCGATCG" * 125, alphabet="dna")

    def gc():
        return s.gc_content()

    result = benchmark(gc)
    assert 0.0 <= result <= 1.0


def test_benchmark_sequence_reverse_complement(benchmark):
    """Benchmark reverse complement."""
    from vaxgenesis.hexagon.domain.value_objects import Sequence
    s = Sequence(value="ATCGATCG" * 125, alphabet="dna")

    def rc():
        return s.reverse_complement()

    result = benchmark(rc)
    assert result.length == 1000


# ============================================================
# Candidate state machine
# ============================================================

def test_benchmark_candidate_creation(benchmark):
    """Benchmark constructing a Candidate aggregate."""
    from vaxgenesis.hexagon.domain.entities import Candidate, VaccinePlatform
    from vaxgenesis.hexagon.domain.value_objects import ProjectId
    pid = ProjectId(value=uuid4())

    def construct():
        return Candidate(project_id=pid, name="Benchmark Cand", platform=VaccinePlatform.MULTI_EPITOPE)

    result = benchmark(construct)
    assert result.status.value == "draft"


def test_benchmark_candidate_advance_to_predicted(benchmark):
    """Benchmark the state transition DRAFT → PREDICTED."""
    from vaxgenesis.hexagon.domain.entities import Candidate, CandidateStatus, VaccinePlatform
    from vaxgenesis.hexagon.domain.value_objects import (
        ConfidenceInterval, ProjectId, UncertaintyScore,
    )

    def transition():
        c = Candidate(
            project_id=ProjectId(value=uuid4()),
            name="Bench",
            platform=VaccinePlatform.MULTI_EPITOPE,
        )
        c.set_predictions(
            0.75,
            ConfidenceInterval(low=0.65, high=0.85),
            UncertaintyScore(value=0.3, method="heuristic"),
        )
        c.advance_status(CandidateStatus.PREDICTED)
        return c

    result = benchmark(transition)
    assert result.status == CandidateStatus.PREDICTED


# ============================================================
# In-memory repository
# ============================================================

def test_benchmark_in_memory_repo_save(benchmark):
    """Benchmark saving a candidate to the in-memory repository."""
    from vaxgenesis.hexagon.adapters.memory.repositories import InMemoryCandidateRepository
    from vaxgenesis.hexagon.domain.entities import Candidate, VaccinePlatform
    from vaxgenesis.hexagon.domain.value_objects import ProjectId
    import asyncio

    repo = InMemoryCandidateRepository()
    pid = ProjectId(value=uuid4())

    def save():
        c = Candidate(project_id=pid, name="Bench", platform=VaccinePlatform.MULTI_EPITOPE)
        return asyncio.run(repo.save(c))

    result = benchmark(save)
    assert result.id is not None


def test_benchmark_in_memory_repo_get(benchmark):
    """Benchmark fetching a candidate from the in-memory repository."""
    from vaxgenesis.hexagon.adapters.memory.repositories import InMemoryCandidateRepository
    from vaxgenesis.hexagon.domain.entities import Candidate, VaccinePlatform
    from vaxgenesis.hexagon.domain.value_objects import ProjectId
    import asyncio

    repo = InMemoryCandidateRepository()
    c = Candidate(project_id=ProjectId(value=uuid4()), name="Bench", platform=VaccinePlatform.MULTI_EPITOPE)
    asyncio.run(repo.save(c))

    def get():
        return asyncio.run(repo.get(c.id))

    result = benchmark(get)
    assert result.id == c.id


# ============================================================
# DI container use case resolution
# ============================================================

def test_benchmark_container_resolve_use_case(benchmark):
    """Benchmark resolving a use case from the DI container."""
    from vaxgenesis.hexagon.containers.composition import Container

    container = Container()

    def resolve():
        return container.create_candidate_use_case()

    result = benchmark(resolve)
    assert result is not None


# ============================================================
# End-to-end use case execution
# ============================================================

def test_benchmark_create_candidate_use_case(benchmark):
    """Benchmark the full CreateCandidate use case execution."""
    from vaxgenesis.hexagon.containers.composition import Container
    from vaxgenesis.hexagon.use_cases.dtos import CreateCandidateCommand
    from vaxgenesis.hexagon.domain.entities import Project
    from vaxgenesis.hexagon.domain.value_objects import ProjectId
    import asyncio

    container = Container()

    def setup_and_execute():
        project_id = uuid4()
        # Pre-create the project in the UoW's project repo
        uow = container.uow()
        project = Project(
            id=ProjectId(value=project_id),
            name="Bench Project",
            owner_id=uuid4(),
        )
        asyncio.run(uow.projects.save(project))

        cmd = CreateCandidateCommand(project_id=project_id, name="Bench Cand")
        use_case = container.create_candidate_use_case()
        return asyncio.run(use_case.execute(cmd))

    result = benchmark(setup_and_execute)
    assert result.name == "Bench Cand"
