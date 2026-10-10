"""In-memory event bus and unit of work for tests."""
from __future__ import annotations

from typing import Any
from collections import defaultdict

from vaxgenesis.hexagon.domain.events import DomainEvent
from vaxgenesis.hexagon.ports.services import EventBus, UnitOfWork
from vaxgenesis.hexagon.adapters.memory.repositories import (
    InMemoryCandidateRepository, InMemoryPathogenRepository,
    InMemoryProjectRepository, InMemoryVariantRepository,
    InMemoryWetLabAssayRepository,
)


class InMemoryEventBus(EventBus):
    """Synchronous in-memory event bus for tests."""

    def __init__(self) -> None:
        self._handlers: dict[type[DomainEvent], list[Any]] = defaultdict(list)
        self.published: list[DomainEvent] = []

    async def publish(self, event: DomainEvent) -> None:
        self.published.append(event)
        for handler in self._handlers.get(type(event), []):
            await handler(event)

    def subscribe(self, event_type: type[DomainEvent], handler: Any) -> None:
        self._handlers[event_type].append(handler)


class InMemoryUnitOfWork(UnitOfWork):
    """In-memory UnitOfWork.

    Since the in-memory repositories don't have real transactions, this
    is essentially a no-op boundary that just holds references to the
    repositories. It exists so that use cases can depend on the
    `UnitOfWork` port uniformly.
    """

    def __init__(self) -> None:
        self.candidates = InMemoryCandidateRepository()
        self.pathogens = InMemoryPathogenRepository()
        self.variants = InMemoryVariantRepository()
        self.assays = InMemoryWetLabAssayRepository()
        self.projects = InMemoryProjectRepository()
        self._committed = False

    async def __aenter__(self) -> "InMemoryUnitOfWork":
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        if exc is None:
            await self.commit()
        else:
            await self.rollback()

    async def commit(self) -> None:
        self._committed = True

    async def rollback(self) -> None:
        # In-memory: nothing to roll back (no snapshots)
        pass
