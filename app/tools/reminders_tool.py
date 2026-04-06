"""Executable reminders tool binding."""

from __future__ import annotations

from dataclasses import dataclass

from app.llm.tool_context import ToolRequestContext
from app.llm.tool_contracts import RegisteredTool, ToolDefinition
from app.tools.reminder_service import ReminderService

REMINDERS_DEFINITION = ToolDefinition(
    name="reminders",
    description="Create personal reminders.",
    input_schema={
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "Reminder text."},
            "remind_at": {
                "type": "string",
                "description": "ISO-8601 local datetime in user's timezone, e.g. 2026-04-05T18:30:00",
            },
        },
        "required": ["title", "remind_at"],
        "additionalProperties": False,
    },
)


@dataclass(slots=True)
class RemindersTool:
    service: ReminderService

    async def __call__(self, context: ToolRequestContext, arguments: dict[str, object]) -> dict[str, object]:
        title = str(arguments.get("title") or "")
        remind_at = str(arguments.get("remind_at") or "")

        reminder = await self.service.create_reminder(
            user_id=context.user_id,
            timezone=context.timezone,
            title=title,
            remind_at_local=remind_at,
        )

        return {
            "status": "scheduled",
            "reminder": {
                "id": reminder.id,
                "title": reminder.title,
                "remind_at_utc": reminder.remind_at_utc.isoformat(),
                "timezone": reminder.timezone,
            },
        }


def build_reminders_tool(service: ReminderService) -> RegisteredTool:
    return RegisteredTool(definition=REMINDERS_DEFINITION, handler=RemindersTool(service=service))
