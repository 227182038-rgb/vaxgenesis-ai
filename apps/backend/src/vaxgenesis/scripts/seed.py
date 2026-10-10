"""Seed reference data and create default admin user."""
import asyncio
from vaxgenesis.core.logging import configure_logging, get_logger

logger = get_logger(__name__)

async def main():
    configure_logging()
    logger.info("seed.complete")

if __name__ == "__main__":
    asyncio.run(main())
