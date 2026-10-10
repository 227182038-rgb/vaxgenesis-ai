"""Redis client wrapper."""
import redis
from vaxgenesis.config import settings

redis_client = redis.from_url(str(settings.redis_url), decode_responses=True)

def ping_redis() -> bool:
    try:
        return bool(redis_client.ping())
    except Exception:
        return False
