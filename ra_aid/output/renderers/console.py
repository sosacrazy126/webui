"""Console renderer implementation using Rich."""

from rich.markdown import Markdown
from rich.panel import Panel

from ra_aid.console.formatting import console
from ra_aid.output.interface.base import OutputRenderer
from ra_aid.output.interface.models import (
    MarkdownPanel,
    StageHeader,
    TaskHeader,
    StatusMessage,
)


class ConsoleRenderer(OutputRenderer):
    """Rich console implementation of the OutputRenderer interface."""

    def render_panel(self, panel: MarkdownPanel) -> None:
        """Render a markdown panel using Rich.
        
        Args:
            panel: Panel configuration containing content and styling
        """
        console.print(
            Panel(
                Markdown(panel.content),
                title=f"{panel.icon + ' ' if panel.icon else ''}{panel.title or ''}".strip() or None,
                border_style=panel.border_style or "bright_blue",
            )
        )

    def render_stage(self, header: StageHeader) -> None:
        """Render a stage header.
        
        Args:
            header: Stage header configuration
        """
        icon = f"{header.icon} " if header.icon else "🚀 "  # Default icon
        panel_content = f"{icon}{header.text.title()}"
        console.print(Panel(panel_content, style="green bold", padding=0))

    def render_task(self, header: TaskHeader) -> None:
        """Render a task header with markdown support.
        
        Args:
            header: Task header configuration
        """
        icon = f"{header.icon} " if header.icon else "🔧 "  # Default icon
        console.print(Panel(Markdown(header.text), title=f"{icon}Task", border_style="yellow bold"))

    def render_status(self, message: StatusMessage) -> None:
        """Render a status message.
        
        Args:
            message: Status message configuration
        """
        console.print(message.text, style=message.style or "blue")
