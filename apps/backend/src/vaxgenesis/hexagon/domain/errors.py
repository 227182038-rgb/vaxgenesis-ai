"""Domain errors — exceptions that represent domain rule violations.

These are distinct from infrastructure errors (HTTP 500, DB connection
failure) which are handled by the adapter layer.
"""
from __future__ import annotations


class DomainError(Exception):
    """Base class for all domain rule violations."""


class InvalidStateTransitionError(DomainError):
    """Raised when an entity state transition is not allowed."""


class InvariantViolationError(DomainError):
    """Raised when a domain invariant is violated."""


class EntityNotFoundError(DomainError):
    """Raised when a requested entity does not exist."""


class DuplicateEntityError(DomainError):
    """Raised when attempting to create an entity that already exists."""


class InsufficientEvidenceError(DomainError):
    """Raised when a clinical claim is made without wet-lab validation."""


class ConfidenceIntervalExceededError(DomainError):
    """Raised when a prediction's uncertainty exceeds the action threshold."""
