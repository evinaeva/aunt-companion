"""Settings for tool runtime composition."""

from __future__ import annotations

from pydantic import BaseModel, Field


DEFAULT_TOOLSET_FACTORY_IMPORT_PATH = "app.tools.factory:build_default_toolset_factory"


class ToolSettings(BaseModel):
    """Configuration for resolving the request-scoped toolset factory."""

    toolset_factory_import_path: str = Field(default=DEFAULT_TOOLSET_FACTORY_IMPORT_PATH)
