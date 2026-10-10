"""Surveillance service layer."""
from __future__ import annotations
from datetime import datetime, timedelta, timezone

async def get_surveillance_status(db):
    return {"is_running": True, "last_ingest_at": None, "sequences_seen_24h": 0, "sequences_seen_7d": 0, "active_alerts": 0, "critical_alerts": 0}
