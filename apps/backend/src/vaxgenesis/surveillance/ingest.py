"""Variant sequence ingestion."""
from __future__ import annotations
import hashlib
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

async def ingest_variant_sequence(payload, db):
    """Ingest a new variant sequence."""
    return {"id": str(UUID(int=0)), "name": payload.name, "mutations": []}

def call_mutations(reference, variant_seq):
    mutations = []
    for i in range(min(len(reference), len(variant_seq))):
        if reference[i].upper() != variant_seq[i].upper() and reference[i] != "N" and variant_seq[i] != "N":
            mutations.append({"position": i+1, "ref": reference[i], "var": variant_seq[i], "type": "substitution"})
    return mutations
