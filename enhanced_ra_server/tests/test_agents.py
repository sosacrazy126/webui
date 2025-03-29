"""
Tests for the agent modules.
"""

import pytest
import tempfile
import os
import asyncio

from enhanced_ra_server.agents.research_agent import run_research_agent
from enhanced_ra_server.agents.planning_agent import run_planning_agent
from enhanced_ra_server.agents.implementation_agent import run_task_implementation_agent
from enhanced_ra_server.repositories.memory_repository import MemorySaver


class TestAgents:
    """Test cases for the agent modules."""

    @pytest.fixture
    def memory(self):
        """Create a temporary memory repository."""
        # Create a temporary database file
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        
        # Initialize memory with temp path
        memory = MemorySaver(path)
        
        yield memory
        
        # Clean up
        os.unlink(path)

    @pytest.mark.asyncio
    async def test_research_agent(self, memory):
        """Test research agent execution."""
        task_id = "test-task-id"
        result = await run_research_agent(
            base_task_or_query="Test research task",
            model="test-model",
            expert_enabled=True,
            research_only=False,
            hil=False,
            memory=memory,
            thread_id="test-thread",
            task_id=task_id
        )
        
        # Check that result has expected keys
        assert "task" in result
        assert "findings" in result
        assert "context" in result
        
        # Check that memory was updated
        stored_result = memory.retrieve_phase_result(
            phase="research",
            task_id=task_id,
            thread_id="test-thread"
        )
        assert stored_result is not None
        assert "task" in stored_result
        assert "findings" in stored_result

    @pytest.mark.asyncio
    async def test_planning_agent(self, memory):
        """Test planning agent execution."""
        task_id = "test-task-id"
        
        # Create research result
        research_result = {
            "task": "Test planning task",
            "findings": "Test research findings",
            "context": {
                "model": "test-model",
                "expert_enabled": True
            }
        }
        
        # Store research result in memory
        memory.store_phase_result(
            phase="research",
            result=research_result,
            task_id=task_id,
            thread_id="test-thread"
        )
        
        result = await run_planning_agent(
            research_result=research_result,
            model="test-model",
            expert_enabled=True,
            hil=False,
            memory=memory,
            thread_id="test-thread",
            task_id=task_id
        )
        
        # Check that result has expected keys
        assert "task" in result
        assert "plan" in result
        assert "context" in result
        
        # Check that memory was updated
        stored_result = memory.retrieve_phase_result(
            phase="planning",
            task_id=task_id,
            thread_id="test-thread"
        )
        assert stored_result is not None
        assert "task" in stored_result
        assert "steps" in stored_result

    @pytest.mark.asyncio
    async def test_implementation_agent(self, memory):
        """Test implementation agent execution."""
        task_id = "test-task-id"
        
        # Create planning result
        plan = {
            "task": "Test implementation task",
            "steps": [
                {"id": 1, "title": "Step 1", "description": "First step of the plan"},
                {"id": 2, "title": "Step 2", "description": "Second step of the plan"}
            ]
        }
        
        planning_result = {
            "task": "Test implementation task",
            "plan": plan,
            "context": {
                "model": "test-model",
                "expert_enabled": True
            }
        }
        
        # Store planning result in memory
        memory.store_phase_result(
            phase="planning",
            result=plan,
            task_id=task_id,
            thread_id="test-thread"
        )
        
        result = await run_task_implementation_agent(
            planning_result=planning_result,
            model="test-model",
            expert_enabled=True,
            web_research_enabled=False,
            memory=memory,
            thread_id="test-thread",
            task_id=task_id
        )
        
        # Check that result has expected keys
        assert "task" in result
        assert "results" in result
        assert "context" in result
        
        # Check that memory was updated
        stored_result = memory.retrieve_phase_result(
            phase="implementation",
            task_id=task_id,
            thread_id="test-thread"
        )
        assert stored_result is not None
        assert "task" in stored_result
        assert "executed_steps" in stored_result
        assert "status" in stored_result 