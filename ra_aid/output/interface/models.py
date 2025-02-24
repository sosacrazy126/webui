from dataclasses import dataclass
from typing import Optional

@dataclass
class MarkdownPanel:
    content: str
    title: Optional[str] = None
    icon: Optional[str] = None
    border_style: Optional[str] = None

@dataclass
class StageHeader:
    text: str
    icon: Optional[str] = None

@dataclass
class TaskHeader:
    text: str
    icon: Optional[str] = None

@dataclass
class StatusMessage:
    text: str
    style: Optional[str] = None
