"""FastAPI shared dependencies."""
from vaxgenesis.hexagon.containers.composition import Container

def get_container() -> Container:
    """Return the DI container."""
    return Container()
