"""Use cases package — application services that orchestrate domain logic.

Use cases are the entry points for all business operations. Each use
case:
  - Has a single `execute()` method
  - Takes a command/query DTO as input
  - Returns a result DTO
  - Depends on ports (never on concrete adapters)
  - Publishes domain events when state changes

Naming convention:
  - Commands (write): `CreateCandidateUseCase`, `RunPipelineUseCase`
  - Queries (read): `GetCandidateQuery`, `ListCandidatesQuery`
"""
