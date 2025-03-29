"""
Schema definitions for data structures.

This module defines Pydantic models for various data structures used in the application.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class TaskRequest(BaseModel):
    """Task execution request."""
    content: str = Field(..., description="Task description or query")
    research_only: Optional[bool] = Field(False, description="Whether to run in research-only mode")
    task_id: Optional[str] = Field(None, description="Optional task identifier")


class ConfigUpdate(BaseModel):
    """Configuration update request."""
    model: Optional[str] = Field(None, description="Override model for this connection")
    research_only: Optional[bool] = Field(None, description="Whether to run in research-only mode")


class TaskStep(BaseModel):
    """Step in a task execution plan."""
    id: int = Field(..., description="Step identifier")
    title: str = Field(..., description="Step title")
    description: str = Field(..., description="Step description")
    status: Optional[str] = Field("pending", description="Step status")
    output: Optional[str] = Field(None, description="Step execution output")


class Plan(BaseModel):
    """Task execution plan."""
    task: str = Field(..., description="Task description")
    steps: List[TaskStep] = Field([], description="Plan steps")


class ResearchResult(BaseModel):
    """Result of research phase."""
    task: str = Field(..., description="Task description")
    findings: str = Field(..., description="Research findings")
    context: Optional[Dict[str, Any]] = Field({}, description="Additional context")


class PlanningResult(BaseModel):
    """Result of planning phase."""
    task: str = Field(..., description="Task description")
    plan: Plan = Field(..., description="Execution plan")
    context: Optional[Dict[str, Any]] = Field({}, description="Additional context")


class ImplementationResult(BaseModel):
    """Result of implementation phase."""
    task: str = Field(..., description="Task description")
    results: Dict[str, Any] = Field(..., description="Implementation results")
    context: Optional[Dict[str, Any]] = Field({}, description="Additional context")


class WebSocketMessage(BaseModel):
    """Base WebSocket message structure."""
    type: str = Field(..., description="Message type")
    content: Optional[Any] = Field(None, description="Message content")


class ErrorMessage(BaseModel):
    """Error message."""
    type: str = Field("error", description="Message type")
    content: str = Field(..., description="Error description")
    phase: Optional[str] = Field(None, description="Phase where error occurred")
    task_id: Optional[str] = Field(None, description="Task identifier") 