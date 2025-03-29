"""
Enhanced RA.Aid Server implementation.

This module provides the core FastAPI application with WebSocket support
for real-time communication with clients.
"""

from typing import Dict, Any, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import os
import uuid
from pathlib import Path

from enhanced_ra_server.websocket_manager import WebSocketManager, ConnectionState
from enhanced_ra_server.repositories.memory_repository import MemorySaver


class EnhancedRAServer:
    """
    Enhanced RA.Aid Server with real-time WebSocket communication.
    
    This class provides the main FastAPI application with WebSocket endpoints,
    static file serving, and integration with the memory system.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Enhanced RA.Aid Server.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.app = FastAPI(
            title="Enhanced RA.Aid Server",
            description="Real-time WebSocket interface for RA.Aid",
            version="0.1.0"
        )
        
        # Set up CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # In production, replace with specific origins
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Initialize WebSocket manager
        self.websocket_manager = WebSocketManager()
        
        # Initialize memory system
        memory_path = config.get("memory_path")
        self.memory = MemorySaver(memory_path)
        
        # Set up routes
        self.setup_routes()
    
    def setup_routes(self):
        """Set up HTTP and WebSocket routes."""
        
        # Health check endpoint
        @self.app.get("/health")
        async def health_check():
            return {"status": "healthy"}
        
        # Config information endpoint
        @self.app.get("/config")
        async def get_config():
            # Return a safe subset of configuration
            safe_config = {
                "host": self.config.get("host"),
                "port": self.config.get("port"),
                "version": self.app.version
            }
            return safe_config
            
        # Task history endpoint
        @self.app.get("/task-history/{client_id}")
        async def get_task_history(client_id: str, limit: int = 20, offset: int = 0, status: str = None):
            """
            Get task history for a client.
            
            Args:
                client_id: Client identifier
                limit: Maximum number of tasks to retrieve
                offset: Number of tasks to skip
                status: Filter by task status
            
            Returns:
                List of task history records
            """
            try:
                tasks = self.memory.get_task_history(
                    thread_id=client_id,
                    limit=limit,
                    offset=offset,
                    status=status
                )
                return {"tasks": tasks}
            except Exception as e:
                return {"error": str(e)}
                
        # Task details endpoint
        @self.app.get("/task/{client_id}/{task_id}")
        async def get_task_detail(client_id: str, task_id: str):
            """
            Get details for a specific task.
            
            Args:
                client_id: Client identifier
                task_id: Task identifier
            
            Returns:
                Task details and logs
            """
            try:
                task = self.memory.get_task(
                    task_id=task_id,
                    thread_id=client_id
                )
                
                if task is None:
                    return {"error": "Task not found"}
                
                # Get task logs
                logs = self.memory.get_task_logs(
                    task_id=task_id,
                    thread_id=client_id
                )
                
                # Get phase results if available
                phases = {}
                for phase in ["research", "planning", "implementation"]:
                    result = self.memory.retrieve_phase_result(
                        phase=phase,
                        task_id=task_id,
                        thread_id=client_id
                    )
                    if result:
                        phases[phase] = result
                
                return {
                    "task": task,
                    "logs": logs,
                    "phases": phases
                }
            except Exception as e:
                return {"error": str(e)}
        
        # WebSocket endpoint
        @self.app.websocket("/ws/{client_id}")
        async def websocket_endpoint(websocket: WebSocket, client_id: str):
            """
            WebSocket endpoint for real-time communication.
            
            Args:
                websocket: WebSocket connection
                client_id: Unique client identifier
            """
            await websocket.accept()
            
            # Create connection-specific state
            state = ConnectionState(
                model=self.config.get("model"),
                research_only=self.config.get("research_only", False),
                client_id=client_id
            )
            
            # Register the connection
            self.websocket_manager.add_connection(client_id, websocket, state)
            
            try:
                # Send confirmation of connection
                await websocket.send_json({
                    "type": "connection_established",
                    "client_id": client_id
                })
                
                # Process messages
                while True:
                    message = await websocket.receive_json()
                    await self.process_message(client_id, message, state)
                    
            except WebSocketDisconnect:
                # Clean up when client disconnects
                self.websocket_manager.remove_connection(client_id)
                
            except Exception as e:
                # Log the error
                print(f"Error in websocket connection: {str(e)}")
                # Try to send error to client
                try:
                    await websocket.send_json({
                        "type": "error", 
                        "content": f"Server error: {str(e)}"
                    })
                except:
                    pass
                # Clean up connection
                self.websocket_manager.remove_connection(client_id)
        
        # Mount static files for web interface
        # Only mount if the directory exists
        static_dir = Path(__file__).parent / "static"
        if static_dir.exists():
            self.app.mount("/static", StaticFiles(directory=static_dir), name="static")
    
    async def process_message(self, client_id: str, message: Dict[str, Any], state: ConnectionState):
        """
        Process an incoming WebSocket message.
        
        Args:
            client_id: Client identifier
            message: Message content
            state: Client connection state
        """
        message_type = message.get("type")
        
        if message_type == "ping":
            # Simple ping message for testing connection
            await self.send_update(client_id, {"type": "pong"})
            
        elif message_type == "task":
            # Task execution request
            content = message.get("content")
            
            # Input validation
            if not content:
                await self.send_update(client_id, {
                    "type": "error",
                    "content": "Task content is required"
                })
                return
            
            # Generate task ID if not provided
            task_id = message.get("task_id", str(uuid.uuid4()))
            
            # Create task object
            task = {
                "content": content,
                "task_id": task_id,
                "created_at": str(uuid.uuid1()),  # Timestamp
                "status": "pending"
            }
            
            # Add to the task queue
            state.add_task(task)
            
            # Store in task history
            self.memory.store_task(
                task_id=task_id,
                content=content,
                thread_id=client_id,
                status="pending"
            )
            
            # Log task creation event
            self.memory.log_task_message(
                task_id=task_id,
                message=f"Task created: {content[:50]}...",
                message_type="create",
                thread_id=client_id
            )
            
            # Send acknowledgment that task was received
            await self.send_update(client_id, {
                "type": "task_received",
                "content": {"task": content, "task_id": task_id}
            })
            
            # If no task is currently being processed, start processing
            if not state.is_processing:
                await self.process_next_task(client_id, state)
            else:
                # Otherwise, notify the client that the task is queued
                await self.send_update(client_id, {
                    "type": "task_queued",
                    "content": {
                        "task_id": task_id,
                        "position": len(state.task_queue)
                    }
                })
                
                # Log task queued event
                self.memory.log_task_message(
                    task_id=task_id,
                    message=f"Task queued at position {len(state.task_queue)}",
                    message_type="queue",
                    thread_id=client_id
                )
                
        elif message_type == "mark_complete":
            # Mark a task as complete
            task_id = message.get("task_id")
            
            # Input validation
            if not task_id:
                await self.send_update(client_id, {
                    "type": "error",
                    "content": "Task ID is required"
                })
                return
            
            # Mark the task as complete in state
            state.mark_task_complete(task_id)
            
            # Mark the task as complete in database
            self.memory.mark_task_complete(
                task_id=task_id,
                thread_id=client_id
            )
            
            # Log task completion event
            self.memory.log_task_message(
                task_id=task_id,
                message="Task marked as complete by user",
                message_type="complete",
                thread_id=client_id
            )
            
            # Send confirmation
            await self.send_update(client_id, {
                "type": "task_marked_complete",
                "content": {"task_id": task_id}
            })
            
            # If there are pending tasks, start processing the next one
            if state.has_pending_tasks():
                await self.process_next_task(client_id, state)
                
        elif message_type == "get_task_status":
            # Get status of all tasks for this client
            task_id = message.get("task_id")
            
            if task_id:
                # Get status of specific task from database
                task_info = self.memory.get_task(
                    task_id=task_id,
                    thread_id=client_id
                )
                
                if task_info:
                    status = task_info.get("status")
                    
                    # If task is currently processing, get the current phase
                    if task_id == state.current_task_id:
                        status = "in_progress"
                        phase = state.current_phase
                    else:
                        phase = None
                    
                    position = None
                    # Check if task is in queue
                    for i, task in enumerate(state.task_queue):
                        if task.get("task_id") == task_id:
                            status = "queued"
                            position = i + 1
                            break
                    
                    await self.send_update(client_id, {
                        "type": "task_status",
                        "content": {
                            "task_id": task_id,
                            "status": status,
                            "phase": phase,
                            "position": position,
                            "created_at": task_info.get("created_at"),
                            "completed_at": task_info.get("completed_at"),
                            "content": task_info.get("content")
                        }
                    })
                else:
                    await self.send_update(client_id, {
                        "type": "error",
                        "content": f"Task {task_id} not found"
                    })
            else:
                # Get recent task history from database
                tasks = self.memory.get_task_history(thread_id=client_id, limit=20)
                
                # Get current task info
                current_task = {
                    "task_id": state.current_task_id,
                    "status": "in_progress",
                    "phase": state.current_phase
                } if state.current_task_id else None
                
                # Get queued tasks
                queued_tasks = [
                    {
                        "task_id": task.get("task_id"),
                        "content": task.get("content"),
                        "status": "queued",
                        "position": i + 1
                    }
                    for i, task in enumerate(state.task_queue)
                ]
                
                await self.send_update(client_id, {
                    "type": "all_task_status",
                    "content": {
                        "current_task": current_task,
                        "queued_tasks": queued_tasks,
                        "task_history": tasks
                    }
                })
                
        elif message_type == "get_task_logs":
            # Get logs for a specific task
            task_id = message.get("task_id")
            
            if not task_id:
                await self.send_update(client_id, {
                    "type": "error",
                    "content": "Task ID is required"
                })
                return
            
            # Get logs from database
            logs = self.memory.get_task_logs(
                task_id=task_id,
                thread_id=client_id,
                limit=message.get("limit", 100),
                offset=message.get("offset", 0),
                message_type=message.get("message_type")
            )
            
            await self.send_update(client_id, {
                "type": "task_logs",
                "content": {
                    "task_id": task_id,
                    "logs": logs
                }
            })
            
        elif message_type == "cancel":
            # Check if a specific task ID is provided
            task_id = message.get("task_id")
            
            if task_id:
                # Cancel a specific task
                if task_id == state.current_task_id:
                    # Cancel the current task
                    # In future, implement actual cancellation of running agent tasks
                    state.current_task_id = None
                    state.is_processing = False
                    
                    # Update task status in database
                    self.memory.store_task(
                        task_id=task_id,
                        content="", # Existing content will be preserved
                        thread_id=client_id,
                        status="cancelled"
                    )
                    
                    # Log cancellation
                    self.memory.log_task_message(
                        task_id=task_id,
                        message="Task cancelled by user while in progress",
                        message_type="cancel",
                        thread_id=client_id
                    )
                    
                    await self.send_update(client_id, {
                        "type": "task_cancelled",
                        "content": {"task_id": task_id}
                    })
                    
                    # Start processing the next task
                    if state.has_pending_tasks():
                        await self.process_next_task(client_id, state)
                else:
                    # Try to remove the task from the queue
                    for i, task in enumerate(state.task_queue):
                        if task.get("task_id") == task_id:
                            state.task_queue.remove(task)
                            
                            # Update task status in database
                            self.memory.store_task(
                                task_id=task_id,
                                content="", # Existing content will be preserved
                                thread_id=client_id,
                                status="cancelled"
                            )
                            
                            # Log cancellation
                            self.memory.log_task_message(
                                task_id=task_id,
                                message="Task cancelled by user while queued",
                                message_type="cancel",
                                thread_id=client_id
                            )
                            
                            await self.send_update(client_id, {
                                "type": "task_cancelled",
                                "content": {"task_id": task_id}
                            })
                            break
                    else:
                        await self.send_update(client_id, {
                            "type": "error",
                            "content": f"Task {task_id} not found"
                        })
            else:
                # Cancel all tasks for this client
                state.current_task_id = None
                state.is_processing = False
                
                # Update status for all queued tasks
                for task in state.task_queue:
                    task_id = task.get("task_id")
                    self.memory.store_task(
                        task_id=task_id,
                        content="", # Existing content will be preserved
                        thread_id=client_id,
                        status="cancelled"
                    )
                    
                    # Log cancellation
                    self.memory.log_task_message(
                        task_id=task_id,
                        message="Task cancelled as part of bulk cancellation",
                        message_type="cancel",
                        thread_id=client_id
                    )
                
                state.task_queue.clear()
                await self.send_update(client_id, {"type": "all_tasks_cancelled"})
            
        elif message_type == "config_update":
            # Update connection-specific configuration
            for key, value in message.get("config", {}).items():
                if key in ["model", "research_only"]:
                    setattr(state, key, value)
            
            await self.send_update(client_id, {
                "type": "config_updated", 
                "content": {"model": state.model, "research_only": state.research_only}
            })
        
        else:
            # Unknown message type
            await self.send_update(client_id, {
                "type": "error",
                "content": f"Unknown message type: {message_type}"
            })
    
    async def send_update(self, client_id: str, data: Dict[str, Any]):
        """
        Send a JSON update to a specific client.
        
        Args:
            client_id: Client identifier
            data: Data to send
        """
        websocket = self.websocket_manager.get_connection(client_id)
        if websocket:
            try:
                await websocket.send_json(data)
            except Exception as e:
                print(f"Error sending update to client {client_id}: {str(e)}")
                # Try to remove the connection if it's broken
                self.websocket_manager.remove_connection(client_id)
        else:
            print(f"Cannot send update: Client {client_id} not found")
    
    async def process_next_task(self, client_id: str, state: ConnectionState) -> None:
        """
        Process the next task in the queue.
        
        Args:
            client_id: Client identifier
            state: Connection state with task queue
        """
        # Check if we're already processing a task
        if state.is_processing:
            return
            
        # Get the next task from the queue
        task = state.pop_next_task()
        if not task:
            return  # No tasks in queue
            
        # Set the current task
        state.current_task_id = task.get("task_id")
        state.is_processing = True
        
        # Get task details
        task_id = task.get("task_id")
        content = task.get("content")
        
        # Update task status in database
        self.memory.store_task(
            task_id=task_id,
            content=content,
            thread_id=client_id,
            status="in_progress"
        )
        
        try:
            # Start research phase
            state.current_phase = "research"
            
            # Log phase change
            self.memory.log_task_message(
                task_id=task_id,
                message="Starting research phase",
                message_type="phase_change",
                thread_id=client_id
            )
            
            await self.send_update(client_id, {
                "type": "phase_started", 
                "phase": "research",
                "task_id": task_id
            })
            
            # Import research agent here to avoid circular imports
            from enhanced_ra_server.agents import run_research_agent
            
            # Execute research phase
            research_result = await run_research_agent(
                base_task_or_query=content,
                model=state.model,
                expert_enabled=self.config.get("expert_enabled", True),
                research_only=state.research_only,
                hil=self.config.get("hil", True),
                memory=self.memory,
                thread_id=client_id,
                task_id=task_id
            )
            
            # Log research completion
            self.memory.log_task_message(
                task_id=task_id,
                message="Research phase completed",
                message_type="phase_complete",
                thread_id=client_id
            )
            
            # Send research results
            await self.send_update(client_id, {
                "type": "research_complete", 
                "content": research_result,
                "task_id": task_id
            })
            
            # Skip planning and implementation if in research-only mode
            if state.research_only:
                # Log task completion
                self.memory.log_task_message(
                    task_id=task_id,
                    message="Task completed in research-only mode",
                    message_type="complete",
                    thread_id=client_id
                )
                
                await self.send_update(client_id, {
                    "type": "task_complete", 
                    "content": "Research-only mode",
                    "task_id": task_id
                })
                
                # Mark task as complete in database
                self.memory.mark_task_complete(
                    task_id=task_id,
                    thread_id=client_id,
                    metadata={"research_only": True}
                )
                
                # Mark task as complete and start next task
                state.mark_task_complete(task_id)
                if state.has_pending_tasks():
                    await self.process_next_task(client_id, state)
                return
            
            # Start planning phase
            state.current_phase = "planning"
            
            # Log phase change
            self.memory.log_task_message(
                task_id=task_id,
                message="Starting planning phase",
                message_type="phase_change",
                thread_id=client_id
            )
            
            await self.send_update(client_id, {
                "type": "phase_started", 
                "phase": "planning",
                "task_id": task_id
            })
            
            # Import planning agent
            from enhanced_ra_server.agents import run_planning_agent
            
            # Execute planning phase
            planning_result = await run_planning_agent(
                research_result=research_result,
                model=state.model,
                expert_enabled=self.config.get("expert_enabled", True),
                hil=self.config.get("hil", True),
                memory=self.memory,
                thread_id=client_id,
                task_id=task_id
            )
            
            # Log planning completion
            self.memory.log_task_message(
                task_id=task_id,
                message="Planning phase completed",
                message_type="phase_complete",
                thread_id=client_id
            )
            
            # Send planning results
            await self.send_update(client_id, {
                "type": "planning_complete", 
                "content": planning_result,
                "task_id": task_id
            })
            
            # Start implementation phase
            state.current_phase = "implementation"
            
            # Log phase change
            self.memory.log_task_message(
                task_id=task_id,
                message="Starting implementation phase",
                message_type="phase_change",
                thread_id=client_id
            )
            
            await self.send_update(client_id, {
                "type": "phase_started", 
                "phase": "implementation",
                "task_id": task_id
            })
            
            # Import implementation agent
            from enhanced_ra_server.agents import run_task_implementation_agent
            
            # Execute implementation phase
            implementation_result = await run_task_implementation_agent(
                planning_result=planning_result,
                model=state.model,
                expert_enabled=self.config.get("expert_enabled", True),
                hil=self.config.get("hil", True),
                memory=self.memory,
                thread_id=client_id,
                task_id=task_id
            )
            
            # Log implementation completion
            self.memory.log_task_message(
                task_id=task_id,
                message="Implementation phase completed",
                message_type="phase_complete",
                thread_id=client_id
            )
            
            # Send implementation results
            await self.send_update(client_id, {
                "type": "implementation_complete", 
                "content": implementation_result,
                "task_id": task_id
            })
            
            # Log task completion
            self.memory.log_task_message(
                task_id=task_id,
                message="Task completed successfully",
                message_type="complete",
                thread_id=client_id
            )
            
            # Final task completion notification
            await self.send_update(client_id, {
                "type": "task_complete",
                "task_id": task_id
            })
            
            # Mark task as complete in database
            self.memory.mark_task_complete(
                task_id=task_id,
                thread_id=client_id,
                metadata={
                    "phases_completed": ["research", "planning", "implementation"],
                    "model": state.model
                }
            )
            
            # Mark task as complete
            state.mark_task_complete(task_id)
            
            # Process next task if available
            if state.has_pending_tasks():
                await self.process_next_task(client_id, state)
                
        except Exception as e:
            # Log error in task history
            self.memory.log_task_message(
                task_id=task_id,
                message=f"Error during task execution: {str(e)}",
                message_type="error",
                thread_id=client_id
            )
            
            # Update task status to error
            self.memory.store_task(
                task_id=task_id,
                content=content,
                thread_id=client_id,
                status="error",
                metadata={"error": str(e), "phase": state.current_phase}
            )
            
            # Send error message to client
            await self.send_update(client_id, {
                "type": "error",
                "content": f"Error during task execution: {str(e)}",
                "task_id": task_id
            })
            
            # Mark the task as failed and continue with next task
            state.mark_task_complete(task_id)
            if state.has_pending_tasks():
                await self.process_next_task(client_id, state) 