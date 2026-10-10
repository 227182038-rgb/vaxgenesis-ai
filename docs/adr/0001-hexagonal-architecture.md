# ADR-0001: Adopt Hexagonal Architecture (Ports & Adapters)

Date: 2026-02-15
Status: Accepted
Decider: VaxGenesis AI Architecture Board
Supersedes: None
Relates-to: ADR-0002 (DI container), ADR-0003 (async-first), ADR-0004 (Pydantic v2 domain models)

## Context

The VaxGenesis AI codebase grew organically through v1.0 (27 pipeline
modules) and v1.1 (audit response adding 4 more modules + security
hardening). The current architecture is layered but informal:

- SQLAlchemy ORM models double as domain entities, coupling domain
  logic to a specific persistence technology.
- Pipeline modules directly import Redis, Neo4j, and MinIO clients,
  making them untestable in isolation without heavy mocking.
- The 5-agent orchestrator calls module classes directly rather than
  through interfaces, preventing substitution.
- API route handlers contain business logic, violating the dependency
  rule (outer layers should depend on inner layers, never the reverse).

The external audit (v1.1) did not flag this as a defect because the
codebase is functional, but a pharmaceutical R&D deployment demands
stronger separation of concerns to:

1. Enable unit testing without infrastructure dependencies.
2. Allow swapping persistence layers (e.g., Postgres → Spanner) without
   touching domain logic.
3. Make the domain model explicit and persistence-agnostic.
4. Support multiple adapters per port (e.g., a "PredictionRepository"
   port with both Postgres and in-memory adapters for tests).

## Decision

We will adopt **Hexagonal Architecture** (a.k.a. Ports & Adapters,
Alistair Cockburn 2005) for all new feature development, applied via
a new `vaxgenesis.hexagon` package that wraps — but does not modify —
existing modules.

### Structure

```
vaxgenesis/hexagon/
├── domain/           # Pure domain: entities, value objects, events
│   ├── entities.py   # Candidate, Pathogen, Epitope, Variant, Assay
│   ├── value_objects.py  # Sequence, HlaAllele, ConfidenceInterval, ...
│   └── events.py     # CandidateCreated, EscapeDetected, AssayCompleted
├── ports/            # Interfaces (abstract base classes)
│   ├── repositories.py   # CandidateRepository, PathogenRepository, ...
│   ├── services.py       # SequenceAnalyzer, StructurePredictor, ...
│   └── unit_of_work.py   # Transaction boundary
├── adapters/         # Concrete implementations of ports
│   ├── orm/              # SQLAlchemy adapters (wraps v1.0 models)
│   ├── memory/           # In-memory adapters for tests
│   └── external/         # External API adapters (GISAID, IEDB, LIMS)
├── use_cases/        # Application services (commands + queries)
│   ├── commands/         # CreateCandidate, RunPipeline, SubmitAssay
│   └── queries/          # GetCandidate, ListPredictions, GetSurveillanceStatus
├── containers/       # DI composition root
│   └── composition.py    # Wires adapters to use cases
└── api/              # Thin FastAPI routers that invoke use cases
    └── routes.py
```

### Dependency rule

Dependencies point **inward** only:
- `api/` → `use_cases/` → `domain/` + `ports/`
- `adapters/` → `ports/` + `domain/` (implements ports)
- `domain/` depends on **nothing** (no SQLAlchemy, no Redis, no FastAPI)

### Backward compatibility

- All existing v1.0/v1.1 modules remain untouched and operational.
- New hexagonal routes are exposed under `/api/v2/` (parallel to
  existing `/api/v1/`).
- Existing v1 routes continue to work unchanged.
- A migration guide (`docs/MIGRATION_v1_to_v2.md`) will document how
  to progressively move endpoints from v1 to v2.

## Consequences

**Positive:**
- Domain logic becomes independently testable (no DB, no Redis needed).
- New persistence backends can be added by implementing a port.
- Clear separation makes onboarding easier for new engineers.
- Property-based tests can target pure domain functions directly.

**Negative:**
- More files and indirection for new features.
- Two parallel API versions during the migration window.
- Engineers must learn the ports/adapters pattern.

**Mitigation:**
- ADRs (this document series) codify the patterns.
- The DI container (`containers/composition.py`) makes wiring explicit.
- Existing v1 code is not forced to migrate; new features use v2.

## References

- Cockburn, A. "Hexagonal Architecture" (2005)
- Vernon, V. "Implementing Domain-Driven Design" (2013)
- Fowler, M. "Patterns of Enterprise Application Architecture" (2002)
