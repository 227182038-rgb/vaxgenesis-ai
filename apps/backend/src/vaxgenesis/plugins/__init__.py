"""Plugin architecture — third-party module discovery and loading.

Plugins are Python packages that register themselves via the
`vaxgenesis.modules` entry point group. At startup, the core
platform discovers all installed plugins and registers them in the
module catalog.

A plugin package's `pyproject.toml` declares its entry point:

    [project.entry-points."vaxgenesis.modules"]
    my-module = "my_plugin.module:MyModule"

The plugin module must export a class that inherits from
`vaxgenesis.modules.base.BaseModule`.

This enables third-party labs to add new computational biology modules
without modifying the core platform.
"""
from __future__ import annotations

import importlib
import importlib.metadata
from typing import Any

from pydantic import BaseModel

from vaxgenesis.core.logging import get_logger

logger = get_logger(__name__)


class PluginInfo(BaseModel):
    """Metadata about a discovered plugin."""

    entry_point_name: str
    module_path: str
    class_name: str
    package_name: str
    package_version: str
    is_loaded: bool = False
    load_error: str | None = None


class PluginRegistry:
    """Discovers and loads VaxGenesis plugins via Python entry points."""

    ENTRY_POINT_GROUP = "vaxgenesis.modules"

    def __init__(self) -> None:
        self._plugins: dict[str, PluginInfo] = {}
        self._classes: dict[str, type] = {}

    def discover(self) -> list[PluginInfo]:
        """Discover all installed plugins via entry points."""
        self._plugins.clear()

        try:
            eps = importlib.metadata.entry_points(group=self.ENTRY_POINT_GROUP)
        except Exception as exc:
            logger.warning("plugins.discovery_failed", error=str(exc))
            return []

        for ep in eps:
            info = PluginInfo(
                entry_point_name=ep.name,
                module_path=ep.value.split(":")[0],
                class_name=ep.value.split(":")[1] if ":" in ep.value else "",
                package_name=ep.dist.metadata["Name"] if ep.dist else "unknown",
                package_version=ep.dist.version if ep.dist else "unknown",
            )
            self._plugins[ep.name] = info

        logger.info("plugins.discovered", count=len(self._plugins))
        return list(self._plugins.values())

    def load(self, name: str) -> type | None:
        """Load a specific plugin by entry point name.

        Returns the module class, or None on failure.
        """
        info = self._plugins.get(name)
        if not info:
            logger.warning("plugins.not_found", name=name)
            return None

        try:
            cls = info.load() if hasattr(info, "load") else None
            if cls is None:
                # Fall back to manual import
                module = importlib.import_module(info.module_path)
                cls = getattr(module, info.class_name)
            self._classes[name] = cls
            info.is_loaded = True
            info.load_error = None
            logger.info("plugins.loaded", name=name, version=info.package_version)
            return cls
        except Exception as exc:
            info.is_loaded = False
            info.load_error = str(exc)
            logger.error("plugins.load_failed", name=name, error=str(exc))
            return None

    def load_all(self) -> dict[str, type]:
        """Load all discovered plugins."""
        for name in list(self._plugins.keys()):
            self.load(name)
        return dict(self._classes)

    def get_plugin_class(self, name: str) -> type | None:
        return self._classes.get(name)

    def list_plugins(self) -> list[PluginInfo]:
        return list(self._plugins.values())

    def list_loaded(self) -> list[PluginInfo]:
        return [p for p in self._plugins.values() if p.is_loaded]


# Singleton
plugin_registry = PluginRegistry()
