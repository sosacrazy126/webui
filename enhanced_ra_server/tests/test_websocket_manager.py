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