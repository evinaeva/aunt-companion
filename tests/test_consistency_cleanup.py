from pathlib import Path


def test_message_schema_uses_direction_not_role() -> None:
    schema = Path("contract/schemas/message.schema.json").read_text(encoding="utf-8")

    assert '"direction"' in schema
    assert '"role"' not in schema


def test_memory_model_uses_direction_terminology() -> None:
    memory_model = Path("docs/memory-model.md").read_text(encoding="utf-8")

    assert "direction (`incoming`, `outgoing`)" in memory_model
    assert "role (`user`, `assistant`, `system`)" not in memory_model
