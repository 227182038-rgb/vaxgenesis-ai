# ADR-0004: Pydantic v2 for Domain Models

Date: 2026-02-15
Status: Accepted
Relates-to: ADR-0001

## Context

The v1.0 codebase uses Pydantic v2 for API schemas but SQLAlchemy ORM
models for domain entities. This couples domain logic to the database
schema and prevents validation at the domain layer.

## Decision

All hexagonal domain entities and value objects will be **Pydantic v2
BaseModel subclasses**, not SQLAlchemy ORM models.

### Pattern

```python
# domain/value_objects.py
class Sequence(BaseModel):
    """Amino acid or nucleotide sequence."""
    value: str
    alphabet: Literal["dna", "rna", "protein"]

    @field_validator("value")
    @classmethod
    def validate_alphabet(cls, v, info):
        allowed = {"dna": "ATCGN", "rna": "AUCGN", "protein": "ACDEFGHIKLMNPQRSTVWYBXZJUO"}
        valid = set(allowed[info.data["alphabet"]])
        if not set(v.upper()).issubset(valid):
            raise ValueError(f"Invalid characters for {info.data['alphabet']} alphabet")
        return v.upper()

    @property
    def length(self) -> int:
        return len(self.value)


# domain/entities.py
class Candidate(BaseModel):
    """A vaccine candidate (aggregate root)."""
    id: UUID
    project_id: UUID
    version: int = 1
    name: str
    platform: VaccinePlatform
    status: CandidateStatus = CandidateStatus.DRAFT
    overall_score: float | None = None
    confidence_interval: ConfidenceInterval | None = None
    construct: Construct | None = None

    def advance_status(self, new_status: CandidateStatus) -> None:
        """State transition with invariant enforcement."""
        allowed = {
            CandidateStatus.DRAFT: {CandidateStatus.PREDICTED},
            CandidateStatus.PREDICTED: {CandidateStatus.VALIDATED, CandidateStatus.REJECTED},
            CandidateStatus.VALIDATED: {CandidateStatus.IN_TRIAL},
        }
        if new_status not in allowed.get(self.status, set()):
            raise DomainError(f"Cannot transition from {self.status} to {new_status}")
        self.status = new_status
```

### Why Pydantic v2 (not dataclasses or attrs)

1. **Built-in validation** — `@field_validator` enforces invariants at
   construction time. No invalid domain object can exist.
2. **JSON serialization** — Pydantic models serialize to/from JSON
   natively, useful for event sourcing and audit logs.
3. **Immutable mode** — `model_config = ConfigDict(frozen=True)` makes
   value objects truly immutable.
4. **Already a dependency** — v1.0 uses Pydantic v2; no new dependency.
5. **Performance** — Pydantic v2 uses a Rust core (`pydantic-core`)
   that is 5-50x faster than v1.

### Boundary with SQLAlchemy

Adapters convert between Pydantic domain models and SQLAlchemy ORM
rows at the repository boundary:

```python
class SqlAlchemyCandidateRepository:
    async def get(self, id: UUID) -> Candidate:
        orm = await self.session.get(CandidateORM, id)
        return Candidate.model_validate(orm, from_attributes=True)

    async def save(self, candidate: Candidate) -> None:
        orm = CandidateORM(**candidate.model_dump())
        await self.session.merge(orm)
```

## Consequences

**Positive:**
- Domain layer has zero ORM imports.
- Validation happens at the domain boundary, not the API boundary.
- Immutable value objects prevent accidental mutation.

**Negative:**
- Conversion overhead at repository boundary (negligible; Pydantic v2
  is fast).
- Two model definitions during migration (ORM + Pydantic).

## References

- Pydantic v2: https://docs.pydantic.dev/latest/
- Evans, E. "Domain-Driven Design" (2003) — value objects and entities
