"""Pytest config — ensures src/ is on the path for all tests."""
import os
import sys
from pathlib import Path

# Add apps/backend/src to the path so `import vaxgenesis` works
BACKEND_SRC = Path(__file__).parent / "apps" / "backend" / "src"
if BACKEND_SRC.exists() and str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))

# Add services/mock_lims for the LIMS integration tests
MOCK_LIMS = Path(__file__).parent / "services" / "mock_lims"
if MOCK_LIMS.exists() and str(MOCK_LIMS.parent) not in sys.path:
    sys.path.insert(0, str(MOCK_LIMS.parent))

# Set minimal env for tests
os.environ.setdefault("SECRET_KEY", "test-secret-key-must-be-at-least-32-characters-long")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/15")


# pytest-asyncio configuration
def pytest_collection_modifyitems(config, items):
    """Auto-mark async tests so pytest-asyncio runs them."""
    import inspect
    for item in items:
        if inspect.iscoroutinefunction(getattr(item, "function", None)):
            item.add_marker("asyncio")
