"""
Unit tests for the WebSocket connection state management.
"""

import pytest
from enhanced_ra_server.websocket_manager import ConnectionState, WebSocketManager


class TestConnectionState:
    """Test cases for the ConnectionState class."""

    def test_init_default_values(self):
        """Test initialization with default values."""
        state = ConnectionState()
        
        assert state.model is None
        assert state.research_only is False
        assert state.client_id is None
        assert state.current_phase is None
        assert state.metadata == {}

    def test_init_custom_values(self):
        """Test initialization with custom values."""
        state = ConnectionState(
            model="custom-model",
            research_only=True,
            client_id="test-client"
        )
        
        assert state.model == "custom-model"
        assert state.research_only is True
        assert state.client_id == "test-client"
        assert state.current_phase is None
        assert state.metadata == {}

    def test_update_metadata(self):
        """Test updating metadata."""
        state = ConnectionState()
        
        state.update_metadata("key1", "value1")
        assert state.get_metadata("key1") == "value1"
        
        state.update_metadata("key2", {"nested": "value"})
        assert state.get_metadata("key2") == {"nested": "value"}

    def test_get_metadata_default(self):
        """Test retrieving metadata with default value."""
        state = ConnectionState()
        
        assert state.get_metadata("nonexistent") is None
        assert state.get_metadata("nonexistent", "default") == "default"

    def test_mark_task_complete(self):
        """Test marking a task as complete."""
        state = ConnectionState()
        state.current_task_id = "task-1"
        state.is_processing = True
        
        # Mark task as complete
        state.mark_task_complete("task-1")
        
        # Current task should be cleared and processing set to false
        assert state.current_task_id is None
        assert not state.is_processing
        assert "task-1" in state.completed_tasks
        
        # Mark another task as complete (not currently processing)
        state.mark_task_complete("task-2")
        
        # Should have no effect on state
        assert state.current_task_id is None
        assert not state.is_processing
        assert "task-2" not in state.completed_tasks
    
    def test_cancel_task_current(self):
        """Test cancelling the current task."""
        state = ConnectionState()
        state.current_task_id = "task-1"
        state.is_processing = True
        
        # Cancel the current task
        result = state.cancel_task("task-1")
        
        # Current task should be cleared and processing set to false
        assert result is True
        assert state.current_task_id is None
        assert not state.is_processing
        
    def test_cancel_task_queued(self):
        """Test cancelling a queued task."""
        state = ConnectionState()
        
        # Add tasks to queue
        task1 = {"task_id": "task-1", "content": "Test task 1"}
        task2 = {"task_id": "task-2", "content": "Test task 2"}
        state.add_task(task1)
        state.add_task(task2)
        
        # Cancel the first task
        result = state.cancel_task("task-1")
        
        # Task should be removed from queue
        assert result is True
        assert len(state.task_queue) == 1
        assert state.task_queue[0]["task_id"] == "task-2"
        
    def test_cancel_task_not_found(self):
        """Test cancelling a non-existent task."""
        state = ConnectionState()
        
        # Add a task to queue
        task = {"task_id": "task-1", "content": "Test task"}
        state.add_task(task)
        
        # Try to cancel a non-existent task
        result = state.cancel_task("non-existent")
        
        # Method should return False and queue should remain unchanged
        assert result is False
        assert len(state.task_queue) == 1


class TestWebSocketManager:
    """Test cases for the WebSocketManager class."""

    def test_init(self):
        """Test initialization."""
        manager = WebSocketManager()
        
        assert manager.active_connections == {}
        assert manager.connection_states == {}

    def test_add_connection(self):
        """Test adding a connection."""
        manager = WebSocketManager()
        websocket = "mock-websocket"  # Mock websocket object
        state = ConnectionState(client_id="test-client")
        
        manager.add_connection("test-client", websocket, state)
        
        assert manager.active_connections["test-client"] == websocket
        assert manager.connection_states["test-client"] == state

    def test_remove_connection(self):
        """Test removing a connection."""
        manager = WebSocketManager()
        websocket = "mock-websocket"  # Mock websocket object
        state = ConnectionState(client_id="test-client")
        
        manager.add_connection("test-client", websocket, state)
        manager.remove_connection("test-client")
        
        assert "test-client" not in manager.active_connections
        assert "test-client" not in manager.connection_states

    def test_remove_nonexistent_connection(self):
        """Test removing a connection that doesn't exist."""
        manager = WebSocketManager()
        
        # Should not raise an exception
        manager.remove_connection("nonexistent")

    def test_get_connection(self):
        """Test getting a connection."""
        manager = WebSocketManager()
        websocket = "mock-websocket"  # Mock websocket object
        state = ConnectionState(client_id="test-client")
        
        manager.add_connection("test-client", websocket, state)
        
        assert manager.get_connection("test-client") == websocket
        assert manager.get_connection("nonexistent") is None

    def test_get_state(self):
        """Test getting a connection state."""
        manager = WebSocketManager()
        websocket = "mock-websocket"  # Mock websocket object
        state = ConnectionState(client_id="test-client")
        
        manager.add_connection("test-client", websocket, state)
        
        assert manager.get_state("test-client") == state
        assert manager.get_state("nonexistent") is None

    def test_get_all_client_ids(self):
        """Test getting all client IDs."""
        manager = WebSocketManager()
        websocket = "mock-websocket"  # Mock websocket object
        state = ConnectionState()
        
        manager.add_connection("client1", websocket, state)
        manager.add_connection("client2", websocket, state)
        
        client_ids = manager.get_all_client_ids()
        assert len(client_ids) == 2
        assert "client1" in client_ids
        assert "client2" in client_ids 