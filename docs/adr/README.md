# Architecture Decision Records (ADR)

This directory documents the architectural decisions made on the
VaxGenesis AI project.

## Index

| # | Title | Status | Date |
|---|-------|--------|------|
| [0001](0001-hexagonal-architecture.md) | Adopt Hexagonal Architecture (Ports & Adapters) | Accepted | 2026-02-15 |
| [0002](0002-dependency-injection.md) | Dependency Injection via `dependency-injector` | Accepted | 2026-02-15 |
| [0003](0003-async-first.md) | Async-First with `httpx` and `asyncio` | Accepted | 2026-02-15 |
| [0004](0004-pydantic-domain-models.md) | Pydantic v2 for Domain Models | Accepted | 2026-02-15 |
| [0005](0005-test-strategy.md) | Test Strategy — Unit + Integration + Property-Based + Benchmark | Accepted | 2026-02-15 |

## Format

Each ADR follows the Michael Nygard template:

- **Title** — short noun phrase
- **Context** — what is the issue being addressed?
- **Decision** — what is the change we're making?
- **Status** — Proposed / Accepted / Deprecated / Superseded
- **Consequences** — what becomes easier or harder?
- **References** — links to external sources

## When to write an ADR

Write an ADR when you make a decision that:

- Affects the structure of the codebase (e.g., new architectural pattern)
- Is hard to reverse (e.g., choosing a database)
- Has trade-offs that future engineers need to understand
- Resolves an open question raised in code review

ADRs are immutable once Accepted; supersede with a new ADR that
references the old one.
