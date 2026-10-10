"""Ports — abstract interfaces defining what the domain needs.

Ports are abstract base classes (ABCs) that the domain layer defines
to express its dependencies. Adapters in `adapters/` implement these
ports.

A port is a contract: "the domain needs to be able to do X." The
domain doesn't care HOW X is accomplished, only that the contract
is honored.

All port methods are async (per ADR-0003).
"""
