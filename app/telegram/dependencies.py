"""Dependency helpers for Telegram runtime wiring."""

from __future__ import annotations

import logging
from collections.abc import Sequence

from app.config.tool_settings import ToolSettings
from app.llm.pydanticai_runtime import PydanticAIToolRuntime
from app.llm.tool_context import ToolRequestContext
from app.llm.tool_contracts import RegisteredTool, ToolsetFactory
from app.llm.tool_loader import load_toolset_factory

logger = logging.getLogger(__name__)


def _empty_toolset_factory(_: ToolRequestContext) -> Sequence[RegisteredTool]:
    return ()


_toolset_factory_override: ToolsetFactory | None = None
_loaded_toolset_factory: ToolsetFactory | None = None


def set_toolset_factory(factory: ToolsetFactory | None) -> None:
    """Testing seam for overriding request-scoped toolset construction."""
    global _toolset_factory_override, _loaded_toolset_factory
    _toolset_factory_override = factory
    _loaded_toolset_factory = None


def get_toolset_factory() -> ToolsetFactory:
    """Resolve toolset factory from config with safe fallback to empty toolset."""
    global _loaded_toolset_factory
    if _toolset_factory_override is not None:
        return _toolset_factory_override
    if _loaded_toolset_factory is not None:
        return _loaded_toolset_factory

    import_path = ToolSettings().toolset_factory_import_path
    try:
        _loaded_toolset_factory = load_toolset_factory(import_path)
        logger.info("Toolset factory loaded", extra={"import_path": import_path})
    except Exception:
        logger.exception(
            "Failed to load toolset factory, continuing with empty toolset",
            extra={"import_path": import_path},
        )
        _loaded_toolset_factory = _empty_toolset_factory
    return _loaded_toolset_factory


def build_tool_runtime(llm_client) -> PydanticAIToolRuntime:
    return PydanticAIToolRuntime(llm_client)
