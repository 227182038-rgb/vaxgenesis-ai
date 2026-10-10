# ADR-0005: Test Strategy — Unit + Integration + Property-Based + Benchmark

Date: 2026-02-15
Status: Accepted
Relates-to: ADR-0001

## Context

The v1.0/v1.1 codebase has 63 tests, all example-based. While these
catch regressions, they:

1. Don't explore the input space systematically.
2. Don't enforce performance contracts.
3. Don't validate domain invariants across edge cases.

For a pharmaceutical R&D deployment, we need stronger guarantees.

## Decision

Adopt a **four-tier test strategy**:

### Tier 1: Unit tests (pytest)

- Target: pure domain functions, value objects, use cases with fakes.
- No I/O, no network, no DB.
- Goal: 100% branch coverage on `domain/` and `use_cases/`.
- Tools: `pytest`, `pytest-cov`.

### Tier 2: Integration tests (pytest + testcontainers)

- Target: adapters against real infrastructure (Postgres, Redis, Neo4j).
- Use `testcontainers-python` to spin up ephemeral containers per test
  session.
- Goal: every adapter has at least one integration test.
- Tools: `pytest`, `testcontainers`, `httpx.AsyncClient`.

### Tier 3: Property-based tests (Hypothesis)

- Target: domain invariants that must hold for ALL valid inputs.
- Example: "For any valid DNA sequence, `Sequence(value, 'dna').length`
  equals `len(value)`."
- Example: "For any candidate, `advance_status()` either succeeds or
  raises `DomainError` — never silently corrupts state."
- Goal: every value object and state machine has at least one property
  test.
- Tools: `hypothesis`, `pytest`.

### Tier 4: Benchmark tests (pytest-benchmark)

- Target: performance-critical paths (sequence alignment, HLA binding
  prediction, knowledge graph queries).
- Goal: detect regressions; track p50/p95/p99 over time.
- Tools: `pytest-benchmark`, stored as JSON for trend analysis.
- Thresholds: documented per benchmark; CI fails on >20% regression.

### CI workflow integration

```yaml
test-unit:          # tier 1 — every PR
test-integration:   # tier 2 — every PR (services in GH Actions)
test-property:      # tier 3 — every PR (Hypothesis, 100 examples default)
test-benchmark:     # tier 4 — nightly on main; compare against baseline
```

## Consequences

**Positive:**
- Property tests catch edge cases humans miss.
- Benchmark tests catch perf regressions before production.
- Clear tier separation makes test failures easier to diagnose.

**Negative:**
- Longer CI runtime (property tests are 2-3x slower than example tests).
- Benchmark tests are flaky on shared CI runners; mitigated by
  comparing against a stored baseline with 20% tolerance.

## References

- Hypothesis: https://hypothesis.readthedocs.io/
- pytest-benchmark: https://pytest-benchmark.readthedocs.io/
- testcontainers: https://testcontainers-python.readthedocs.io/
