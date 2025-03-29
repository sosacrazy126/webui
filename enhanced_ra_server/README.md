# Enhanced RA.Aid Server

Real-time WebSocket interface for RA.Aid with a three-phase task execution model.

## Overview

Enhanced RA.Aid Server provides a modern, event-driven WebSocket interface that integrates with RA.Aid's existing modules. The server supports a three-phase task execution model (Research, Planning, Implementation) with proper memory integration and error handling.

## Features

- **Real-time Communication**: WebSocket-based interface for immediate feedback
- **Three-phase Task Execution**:
  - **Research**: Gathering context and information
  - **Planning**: Creating execution strategy
  - **Implementation**: Executing the planned changes
- **Memory Management**: Persistent storage across task phases with thread isolation
- **Error Handling**: Robust error isolation for each phase
- **Configuration System**: Flexible configuration through CLI, environment variables, and client settings

## Installation

### Prerequisites

- Python 3.8 or higher
- RA.Aid installed (for agent functionality)

### Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd enhanced-ra-server
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Starting the Server

```bash
# Basic usage
python run_server.py

# Specify host and port
python run_server.py --host 127.0.0.1 --port 8080

# Enable research-only mode
python run_server.py --research-only

# Specify a custom model
python run_server.py --model "claude-3-opus-20240229"
```

### Command-line Options

- `--host`: Host to bind server (default: 0.0.0.0)
- `--port`: Port to bind server (default: 8000)
- `--model`: Override default language model
- `--research-only`: Run in research-only mode (skip planning and implementation)
- `--no-expert`: Disable expert mode for simpler queries
- `--no-hil`: Disable human-in-the-loop confirmations
- `--memory-path`: Path to memory database
- `--version`: Show version information

## Architecture

The Enhanced RA.Aid Server is built with a modular architecture:

- **main.py**: CLI entry point with argument parsing
- **config.py**: Configuration handling
- **enhanced_server.py**: FastAPI application with WebSocket support
- **websocket_manager.py**: Connection state management
- **agents/**: Task phase execution agents
- **repositories/**: Data storage and persistence
- **models/**: Data models and schemas
- **utils/**: Helper utilities

## WebSocket API

Clients can connect to the WebSocket endpoint at `/ws/{client_id}` where `client_id` is a unique identifier for the client. The server supports the following message types:

- **task**: Execute a task with the provided content
- **cancel**: Cancel a running task
- **config_update**: Update connection-specific configuration
- **ping**: Test connection

## Status Events

The server sends the following event types to clients:

- **connection_established**: Sent when a client connects
- **task_received**: Acknowledges receipt of a task request
- **phase_started**: Indicates the start of a task phase
- **research_complete**: Contains research phase results
- **planning_complete**: Contains planning phase results
- **implementation_complete**: Contains implementation phase results
- **task_complete**: Indicates task completion
- **task_cancelled**: Confirms task cancellation
- **config_updated**: Confirms configuration updates
- **error**: Contains error information

## Development

### Project Structure

```
enhanced_ra_server/
├── agents/
│   ├── research_agent.py
│   ├── planning_agent.py
│   └── implementation_agent.py
├── models/
│   └── schema.py
├── repositories/
│   └── memory_repository.py
├── utils/
│   └── logging.py
├── config.py
├── enhanced_server.py
├── main.py
└── websocket_manager.py
```

### Adding New Features

Follow these guidelines when adding new features:

1. Keep the modular architecture
2. Write comprehensive docstrings
3. Use type hints
4. Add appropriate error handling
5. Include tests for new functionality

## License

[License information] 