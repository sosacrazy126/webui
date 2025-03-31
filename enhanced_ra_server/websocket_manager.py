"""
WebSocket connection state management for Enhanced RA.Aid Server.

This module provides connection state tracking and management for WebSocket clients.
"""

from typing import Dict, Any, Optional, List, Deque
from collections import deque


class ConnectionState:
    """
    Manages per-connection state for a WebSocket client.
    
    This class tracks client-specific settings and context information
    for an individual WebSocket connection.
    """
    
    def __init__(
        self,
        model: Optional[str] = None,
        research_only: bool = False,
        client_id: Optional[str] = None
    ):
        """
        Initialize connection state with client-specific settings.
        
        Args:
            model: Language model override for this connection
            research_only: Whether this connection is in research-only mode
            client_id: Unique identifier for the client connection
        """
        self.model = model
        self.research_only = research_only
        self.client_id = client_id
        self.current_phase = None
        self.current_task_id = None
        self.task_queue: Deque[Dict[str, Any]] = deque()  # Queue of pending tasks
        self.completed_tasks: List[str] = []  # List of completed task IDs
        self.is_processing = False  # Whether a task is currently being processed
        self.metadata = {}  # Holds additional client-specific data
    
    def add_task(self, task: Dict[str, Any]) -> None:
        """
        Add a task to the queue.
        
        Args:
            task: Task details including content and task_id
        """
        self.task_queue.append(task)
        
    def get_next_task(self) -> Optional[Dict[str, Any]]:
        """
        Get the next task from the queue without removing it.
        
        Returns:
            The next task or None if queue is empty
        """
        if not self.task_queue:
            return None
        return self.task_queue[0]
    
    def pop_next_task(self) -> Optional[Dict[str, Any]]:
        """
        Remove and return the next task from the queue.
        
        Returns:
            The next task or None if queue is empty
        """
        if not self.task_queue:
            return None
        return self.task_queue.popleft()
    
    def mark_task_complete(self, task_id: str) -> None:
        """
        Mark a task as complete.
        
        Args:
            task_id: ID of the completed task
        """
        if task_id == self.current_task_id:
            self.current_task_id = None
            self.is_processing = False
            self.completed_tasks.append(task_id)
    
    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a task if it's in the queue or currently processing.
        
        Args:
            task_id: ID of the task to cancel
            
        Returns:
            True if the task was found and canceled, False otherwise
        """
        # Check if the task is currently processing
        if task_id == self.current_task_id:
            self.current_task_id = None
            self.is_processing = False
            return True
            
        # Check if the task is in the queue
        for i, task in enumerate(self.task_queue):
            if task["task_id"] == task_id:
                # Remove the task from the queue
                self.task_queue.remove(task)
                return True
                
        return False
    
    def has_pending_tasks(self) -> bool:
        """
        Check if there are pending tasks in the queue.
        
        Returns:
            True if there are pending tasks, False otherwise
        """
        return len(self.task_queue) > 0
    
    def update_metadata(self, key: str, value: Any) -> None:
        """
        Store additional metadata for this connection.
        
        Args:
            key: Metadata key
            value: Metadata value
        """
        self.metadata[key] = value
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """
        Retrieve connection metadata.
        
        Args:
            key: Metadata key to retrieve
            default: Default value if key doesn't exist
            
        Returns:
            The stored value or default if not found
        """
        return self.metadata.get(key, default)


class WebSocketManager:
    """
    Manages active WebSocket connections and their associated state.
    """
    
    def __init__(self):
        """Initialize the WebSocket manager."""
        self.active_connections: Dict[str, Any] = {}  # client_id -> WebSocket
        self.connection_states: Dict[str, ConnectionState] = {}  # client_id -> ConnectionState
    
    def add_connection(self, client_id: str, websocket: Any, state: ConnectionState) -> None:
        """
        Register a new WebSocket connection.
        
        Args:
            client_id: Unique client identifier
            websocket: WebSocket connection object
            state: Initial connection state
        """
        self.active_connections[client_id] = websocket
        self.connection_states[client_id] = state
    
    def remove_connection(self, client_id: str) -> None:
        """
        Remove a WebSocket connection.
        
        Args:
            client_id: Client identifier to remove
        """
        self.active_connections.pop(client_id, None)
        self.connection_states.pop(client_id, None)
    
    def get_connection(self, client_id: str) -> Optional[Any]:
        """
        Get the WebSocket connection for a client.
        
        Args:
            client_id: Client identifier
            
        Returns:
            WebSocket connection or None if not found
        """
        return self.active_connections.get(client_id)
    
    def get_state(self, client_id: str) -> Optional[ConnectionState]:
        """
        Get the connection state for a client.
        
        Args:
            client_id: Client identifier
            
        Returns:
            ConnectionState object or None if not found
        """
        return self.connection_states.get(client_id)
    
    def get_all_client_ids(self) -> list:
        """
        Get all active client IDs.
        
        Returns:
            List of all active client IDs
        """
        return list(self.active_connections.keys()) 