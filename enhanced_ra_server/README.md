# Enhanced RA.Aid Server

The Enhanced RA.Aid Server provides an advanced API and WebSocket interface for managing research agent tasks with robust task queuing, task management, and monitoring capabilities.

## Features

- **WebSocket-Based Communication**: Real-time bidirectional communication with clients
- **Task Management System**: 
  - Queue tasks for processing
  - Retrieve task status and history
  - Get detailed task logs
  - Cancel tasks (current or queued)
- **Task History Persistence**: All tasks are stored with their metadata and status
- **Multi-Client Support**: Each client maintains its own connection state and task queue
- **RESTful API**: HTTP endpoints for retrieving task history and configuration

## WebSocket Message Types

### Client to Server

- **`task`**: Submit a new task for processing
  ```json
  {
    "type": "task",
    "content": "Your task description here",
    "task_id": "optional-custom-task-id"
  }
  ```

- **`ping`**: Check connection status
  ```json
  {
    "type": "ping"
  }
  ```

- **`get_task_status`**: Retrieve status of a specific task or all tasks
  ```json
  {
    "type": "get_task_status",
    "task_id": "optional-task-id"
  }
  ```

- **`get_task_logs`**: Retrieve logs for a specific task
  ```json
  {
    "type": "get_task_logs",
    "task_id": "task-id",
    "limit": 100,
    "offset": 0,
    "message_type": "optional-filter"
  }
  ```

- **`cancel`**: Cancel a specific task or all tasks
  ```json
  {
    "type": "cancel",
    "task_id": "optional-task-id"
  }
  ```

- **`config_update`**: Update connection-specific configuration
  ```json
  {
    "type": "config_update",
    "config": {
      "model": "claude-3-sonnet-20240229",
      "research_only": true
    }
  }
  ```

### Server to Client

- **`connection_established`**: Sent when WebSocket connection is established
- **`pong`**: Response to ping message
- **`task_received`**: Acknowledges receipt of a new task
- **`phase_started`**: Indicates the start of a task phase (research, planning, implementation)
- **`phase_completed`**: Indicates the completion of a task phase with results
- **`task_completed`**: Indicates successful completion of a task
- **`task_queued`**: Indicates a task has been queued due to another task in progress
- **`task_status`**: Returns the status of a specific task
- **`all_task_status`**: Returns the status of all tasks
- **`task_logs`**: Returns logs for a specific task
- **`task_cancelled`**: Confirms a task has been cancelled
- **`all_tasks_cancelled`**: Confirms all tasks have been cancelled
- **`error`**: Indicates an error occurred
- **`update`**: Provides progress updates during task execution

## REST API Endpoints

- **`GET /health`**: Health check endpoint
- **`GET /config`**: Get server configuration information
- **`GET /task-history/{client_id}`**: Get task history for a specific client
- **`GET /task/{client_id}/{task_id}`**: Get detailed information about a specific task

## Task Cancellation

The Enhanced RA.Aid Server supports both individual and bulk task cancellation:

### Individual Task Cancellation
- Cancel a specific task by its ID while it's in the queue or actively processing
- Tasks in progress will stop immediately
- Queued tasks will be removed from the queue
- After cancellation, the next task in the queue will automatically start processing

### Bulk Task Cancellation
- Cancel all tasks for a specific client
- This cancels both the currently processing task and all queued tasks
- The task queue will be completely cleared

### WebSocket Messages for Cancellation

- To cancel a specific task:
  ```json
  {
    "type": "cancel",
    "task_id": "task-id-to-cancel"
  }
  ```

- To cancel all tasks:
  ```json
  {
    "type": "cancel"
  }
  ```

### Cancellation Responses

- For individual task cancellation:
  ```json
  {
    "type": "task_cancelled",
    "content": {"task_id": "cancelled-task-id"}
  }
  ```

- For bulk cancellation:
  ```json
  {
    "type": "all_tasks_cancelled"
  }
  ```

## Setup and Configuration

### Installation

1. Clone the repository and navigate to the project directory:
   ```bash
   git clone <repository-url>
   cd RA.Aid
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Server

There are multiple ways to run the Enhanced RA.Aid Server:

1. Using the package entry point:
   ```bash
   python -m enhanced_ra_server --host 127.0.0.1 --port 8000 --memory-path memory.db
   ```

2. Using the convenience script:
   ```bash
   python run_server.py --host 127.0.0.1 --port 8000 --memory-path memory.db
   ```

3. Directly using the main module:
   ```bash
   python enhanced_ra_server/main.py --host 127.0.0.1 --port 8000 --memory-path memory.db
   ```

### Command-line Arguments

- `--host`: Host to bind the server (default: 0.0.0.0)
- `--port`: Port to bind the server (default: 8000)
- `--model`: Override default language model
- `--research-only`: Run in research-only mode (skip planning and implementation)
- `--no-expert`: Disable expert mode for simpler queries
- `--no-hil`: Disable human-in-the-loop confirmations
- `--memory-path`: Path to memory database
- `--version`: Show version information 