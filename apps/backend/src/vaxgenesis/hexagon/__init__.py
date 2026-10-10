"""Hexagonal architecture package for VaxGenesis AI.

This package implements the Ports & Adapters pattern (Cockburn 2005)
as a parallel API surface to the existing v1.0/v1.1 code. It does NOT
modify any existing module; instead it wraps them behind formal
interfaces (ports) and provides adapter implementations.

Layering (dependencies point inward only):

    ┌────────────────────────────────────────────────────────┐
    │  api/          FastAPI routers (thin, no business logic)│
    ├────────────────────────────────────────────────────────┤
    │  use_cases/    Application services (orchestration)     │
    ├────────────────────────────────────────────────────────┤
    │  ports/        Interfaces (abstract base classes)       │
    ├────────────────────────────────────────────────────────┤
    │  domain/       Pure domain: entities, value objects     │
    └────────────────────────────────────────────────────────┘
                           ▲
                           │ implements
                           │
    ┌──────────────────────┴─────────────────────────────────┐
    │  adapters/     Concrete: ORM, memory, external APIs    │
    └────────────────────────────────────────────────────────┘

See docs/adr/0001-hexagonal-architecture.md for the full rationale.
"""
__all__ = ["domain", "ports", "adapters", "use_cases", "containers", "api"]
