from typing import Protocol
from .models import MarkdownPanel, StageHeader, TaskHeader, StatusMessage

class OutputRenderer(Protocol):
    def render_panel(self, panel: MarkdownPanel) -> None: ...
    def render_stage(self, header: StageHeader) -> None: ...
    def render_task(self, header: TaskHeader) -> None: ...
    def render_status(self, message: StatusMessage) -> None: ...
