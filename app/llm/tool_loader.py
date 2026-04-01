"""Dynamic loader for toolset factory callables."""

from __future__ import annotations

import importlib

from app.llm.tool_contracts import ToolsetFactory


def load_toolset_factory(import_path: str) -> ToolsetFactory:
    """Load a toolset factory from ``module.path:attribute`` string."""
    module_name, separator, attr_name = import_path.partition(":")
    if not separator or not module_name or not attr_name:
        raise ValueError(
            "Toolset factory import path must use 'module.path:attribute' format; "
            f"got: {import_path!r}"
        )

    try:
        module = importlib.import_module(module_name)
    except Exception as exc:  # pragma: no cover - importlib error details vary by python/runtime
        raise ValueError(f"Could not import toolset factory module {module_name!r}") from exc

    try:
        factory = getattr(module, attr_name)
    except AttributeError as exc:
        raise ValueError(f"Module {module_name!r} does not define attribute {attr_name!r}") from exc

    if not callable(factory):
        raise ValueError(f"Imported toolset factory {import_path!r} is not callable")

    return factory
