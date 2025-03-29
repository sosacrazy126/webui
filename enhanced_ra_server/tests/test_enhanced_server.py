"""
Integration tests for the Enhanced RA.Aid Server.
"""

import pytest
import tempfile
import os
from fastapi.testclient import TestClient

from enhanced_ra_server.enhanced_server import EnhancedRAServer
from enhanced_ra_server.websocket_manager import ConnectionState


class TestEnhancedServer:
    """Integration tests for the Enhanced RA.Aid Server."""

    @pytest.fixture
    def test_config(self):
        """Create test configuration."""
        # Create a temporary directory for memory DB
        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "test_memory.db")
        
        # Test configuration
        config = {
            "host": "127.0.0.1",
            "port": 8000,
            "memory_path": db_path,
            "model": "test-model",
            "research_only": False,
            "expert_enabled": True,
            "hil": False,
            "provider": "anthropic",
            "anthropic_api_key": "test-key"  # Fake key for tests
        }
        
        yield config
        
        # Clean up
        if os.path.exists(db_path):
            os.unlink(db_path)
        os.rmdir(temp_dir)

    @pytest.fixture
    def test_client(self, test_config):
        """Create a test client for the FastAPI app."""
        server = EnhancedRAServer(test_config)
        return TestClient(server.app)

    def test_health_check(self, test_client):
        """Test the health check endpoint."""
        response = test_client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

    def test_config_endpoint(self, test_client, test_config):
        """Test the config information endpoint."""
        response = test_client.get("/config")
        assert response.status_code == 200
        
        # Check for expected fields
        data = response.json()
        assert "host" in data
        assert "port" in data
        assert "version" in data
        
        # Sensitive information should not be exposed
        assert "anthropic_api_key" not in data
        
    def test_task_queue_functionality(self):
        """Test task queue functionality."""
        # Create a test state
        state = ConnectionState(
            model="test-model",
            research_only=False,
            client_id="test-client"
        )
        
        # Initially, queue should be empty
        assert not state.has_pending_tasks()
        assert state.get_next_task() is None
        
        # Add a task
        task1 = {
            "content": "Test task 1",
            "task_id": "task-1",
            "created_at": "timestamp",
            "status": "pending"
        }
        state.add_task(task1)
        
        # Queue should have one task now
        assert state.has_pending_tasks()
        assert state.get_next_task() == task1
        
        # Add another task
        task2 = {
            "content": "Test task 2",
            "task_id": "task-2",
            "created_at": "timestamp",
            "status": "pending"
        }
        state.add_task(task2)
        
        # Pop the first task
        popped_task = state.pop_next_task()
        assert popped_task == task1
        
        # Queue should still have the second task
        assert state.has_pending_tasks()
        assert state.get_next_task() == task2
        
        # Pop the second task
        popped_task = state.pop_next_task()
        assert popped_task == task2
        
        # Queue should be empty now
        assert not state.has_pending_tasks()
        assert state.get_next_task() is None
        
        # Test marking a task as complete
        state.current_task_id = task2["task_id"]
        state.is_processing = True
        state.mark_task_complete(task2["task_id"])
        
        # Processing should be false now
        assert not state.is_processing
        assert task2["task_id"] in state.completed_tasks


# WebSocket tests require more setup due to their asynchronous nature
# These would typically use pytest-asyncio and a WebSocket client library
# A simplified example is shown below, but real tests would be more complex
@pytest.mark.asyncio
class TestWebSocketEndpoint:
    """Tests for WebSocket functionality."""

    @pytest.fixture
    def test_config(self):
        """Create test configuration."""
        # Create a temporary directory for memory DB
        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "test_memory.db")
        
        # Test configuration
        config = {
            "host": "127.0.0.1",
            "port": 8000,
            "memory_path": db_path,
            "model": "test-model",
            "research_only": False,
            "expert_enabled": True,
            "hil": False,
            "provider": "anthropic",
            "anthropic_api_key": "test-key"  # Fake key for tests
        }
        
        yield config
        
        # Clean up
        if os.path.exists(db_path):
            os.unlink(db_path)
        os.rmdir(temp_dir)

    @pytest.mark.skip(reason="Requires WebSocket client setup")
    async def test_websocket_connection(self):
        """Test WebSocket connection and basic message exchange."""
        # This would use a WebSocket client to connect to the server
        # and test the message exchange protocol
        
        # Example pseudo-code:
        # async with websockets.connect("ws://localhost:8000/ws/test-client") as websocket:
        #     # Test connection established message
        #     response = await websocket.recv()
        #     data = json.loads(response)
        #     assert data["type"] == "connection_established"
        #     
        #     # Test ping/pong
        #     await websocket.send(json.dumps({"type": "ping"}))
        #     response = await websocket.recv()
        #     data = json.loads(response)
        #     assert data["type"] == "pong"
        
        # For now, we'll skip this test until we have proper async test setup
        pass

    @pytest.mark.skip(reason="Requires WebSocket client setup")
    async def test_task_execution(self):
        """Test task execution through WebSocket."""
        # This would connect to the WebSocket endpoint and send a task
        # then verify the sequence of messages for all phases
        
        # Example pseudo-code:
        # async with websockets.connect("ws://localhost:8000/ws/test-client") as websocket:
        #     # Skip connection message
        #     await websocket.recv()
        #     
        #     # Send task
        #     await websocket.send(json.dumps({
        #         "type": "task",
        #         "content": "Test task"
        #     }))
        #     
        #     # Verify task_received
        #     response = await websocket.recv()
        #     data = json.loads(response)
        #     assert data["type"] == "task_received"
        #     
        #     # Verify phase_started (research)
        #     response = await websocket.recv()
        #     data = json.loads(response)
        #     assert data["type"] == "phase_started"
        #     assert data["phase"] == "research"
        #     
        #     # Continue verifying all expected messages...
        
        # For now, we'll skip this test until we have proper async test setup
        pass 