import pytest

from app.llm.tool_loader import load_toolset_factory


def test_load_toolset_factory_success() -> None:
    factory = load_toolset_factory("math:sqrt")

    assert callable(factory)
    assert factory(9) == 3


@pytest.mark.parametrize(
    "import_path, expected_message",
    [
        ("math.sqrt", "module.path:attribute"),
        ("missing.module:factory", "Could not import toolset factory module"),
        ("math:missing", "does not define attribute"),
        ("math:pi", "is not callable"),
    ],
)
def test_load_toolset_factory_clear_errors(import_path: str, expected_message: str) -> None:
    with pytest.raises(ValueError, match=expected_message):
        load_toolset_factory(import_path)
