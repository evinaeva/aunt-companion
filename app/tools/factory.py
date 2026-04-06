"""Default request-scoped toolset factory."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from app.db.repositories.reminders import RemindersRepository
from app.db.sqlite import connect
from app.llm.tool_context import ToolRequestContext
from app.llm.tool_contracts import RegisteredTool
from app.tools.reminder_scheduler import InMemoryReminderScheduler
from app.tools.reminder_service import ReminderService
from app.tools.reminders_tool import REMINDERS_DEFINITION, RemindersTool
from app.tools.weather_tool import build_weather_tool
from app.tools.web_search_tool import build_web_search_tool


@dataclass(slots=True)
class DeferredRemindersHandler:
    scheduler: InMemoryReminderScheduler

    async def __call__(self, context: ToolRequestContext, arguments: dict[str, object]) -> dict[str, object]:
        db_path = context.metadata.get("db_path")
        if not isinstance(db_path, str) or not db_path:
            raise ValueError("db_path metadata is required for reminders tool")

        conn = await connect(Path(db_path))
        try:
            repository = RemindersRepository(conn)
            service = ReminderService(reminders_repository=repository, scheduler=self.scheduler)
            return await RemindersTool(service=service)(context, arguments)
        finally:
            await conn.close()


def build_default_toolset_factory(context: ToolRequestContext) -> Sequence[RegisteredTool]:
    _ = context
    return (
        build_weather_tool(),
        RegisteredTool(definition=REMINDERS_DEFINITION, handler=DeferredRemindersHandler(scheduler=InMemoryReminderScheduler())),
        build_web_search_tool(),
    )
