# Enhanced RA.Aid Server Architecture

This document outlines the architecture and flow diagrams for the Enhanced RA.Aid Server implementation.

## Component Dependency Graph

```
                                    ┌─────────────────┐
                                    │   Package Init  │
                                    │  (__init__.py)  │
                                    └────────┬────────┘
                                            │
                                            ▼
                                    ┌─────────────────┐
                                    │  Configuration  │◄──────────────┐
                                    │   (config.py)   │              │
                                    └────────┬────────┘              │
                                            │                        │
                                            ▼                        │
┌─────────────────┐              ┌─────────────────┐       ┌───────┴───────┐
│   WebSocket     │◄─────────────┤ Enhanced Server │◄──────┤    Agents     │
│    Manager      │              │(enhanced_server)│       │    Module     │
│(websocket_mgr.py)├─────┐       └────────┬────────┘       │(agents/*.py)  │
└─────────┬───────┘     │                 │                └───────┬───────┘
          │             │                 │                        │
          ▼             │                 ▼                        │
┌─────────────────┐     │         ┌─────────────────┐            │
│  Connection     │     │         │     Memory      │◄───────────┘
│     State       │     └────────►│   Repository    │
│  (conn_state)   │               │(memory_repo.py) │
└─────────────────┘               └─────────────────┘
```

## Detailed Flow Diagrams

### 1. Client Connection and Task Submission Flow

```
Client          WebSocket         Connection         Task Queue         Memory
  │                │                 │                  │                 │
  │    connect     │                 │                  │                 │
  │───────────────►│    create      │                  │                 │
  │                │───────────────►│                  │                 │
  │                │                 │                  │                 │
  │  submit task   │                 │                  │                 │
  │───────────────►│  validate msg   │                 │                 │
  │                │───────────────►│                  │                 │
  │                │                 │   queue task    │                 │
  │                │                 │───────────────►│                  │
  │                │                 │                 │   save task     │
  │                │                 │                 │───────────────►│
  │   queued msg   │                 │                 │                 │
  │◄───────────────│                 │                 │                 │
  │                │                 │                 │                 │
```

### 2. Task Processing Flow (Three-Phase Execution)

```
Task Queue     Enhanced Server    Research Agent    Planning Agent    Impl Agent
    │               │                  │                │                │
    │  next task    │                  │                │                │
    │──────────────►│                  │                │                │
    │               │                  │                │                │
    │               │ research phase   │                │                │
    │               │─────────────────►│                │                │
    │               │                  │                │                │
    │               │   findings       │                │                │
    │               │◄─────────────────│                │                │
    │               │                  │                │                │
    │               │ planning phase   │                │                │
    │               │────────────────────────────────►│                │
    │               │                  │                │                │
    │               │     plan         │                │                │
    │               │◄───────────────────────────────│                │
    │               │                  │                │                │
    │               │ implement phase  │                │                │
    │               │───────────────────────────────────────────────►│
    │               │                  │                │                │
    │               │    results       │                │                │
    │               │◄──────────────────────────────────────────────│
    │               │                  │                │                │
```

### 3. Real-time Update Flow

```
Enhanced Server    WebSocket Mgr     Connection      Memory          Client
       │               │                │              │               │
       │  phase start  │                │              │               │
       │──────────────►│                │              │               │
       │               │   update msg   │              │               │
       │               │───────────────►│              │               │
       │               │                │  save log    │               │
       │               │                │─────────────►│               │
       │               │    notify      │              │               │
       │               │───────────────────────────────────────────►│
       │               │                │              │               │
       │  phase end    │                │              │               │
       │──────────────►│                │              │               │
       │               │  update state  │              │               │
       │               │───────────────►│              │               │
       │               │                │  save result │               │
       │               │                │─────────────►│               │
       │               │    notify      │              │               │
       │               │───────────────────────────────────────────►│
       │               │                │              │               │
```

### 4. Task Cancellation Flow

```
Client          WebSocket         Connection         Task Queue      Agents
  │                │                 │                  │              │
  │ cancel request │                 │                  │              │
  │───────────────►│                 │                  │              │
  │                │  find task      │                  │              │
  │                │───────────────►│                  │              │
  │                │                 │  remove task     │              │
  │                │                 │───────────────►│              │
  │                │                 │                  │ stop agent   │
  │                │                 │                  │────────────►│
  │                │                 │  update state    │              │
  │                │                 │◄───────────────│              │
  │ cancel confirm │                 │                  │              │
  │◄───────────────│                 │                  │              │
  │                │                 │                  │              │
```

### 5. Error Handling Flow

```
Component         Error Handler     Connection         Memory         Client
     │                │                │                 │              │
     │   error       │                │                 │              │
     │───────────────►│                │                 │              │
     │                │  update state  │                 │              │
     │                │───────────────►│                 │              │
     │                │                │   log error     │              │
     │                │                │───────────────►│              │
     │                │  notify client │                 │              │
     │                │────────────────────────────────────────────►│
     │                │                │                 │              │
     │                │ cleanup state  │                 │              │
     │                │───────────────►│                 │              │
     │                │                │                 │              │
```

## State Transitions

```
┌─────────────────┐
│    QUEUED       │──────┐
└─────────────────┘      │
                         ▼
┌─────────────────┐    ┌─────────────────┐
│   CANCELLED     │◄───│   PROCESSING    │
└─────────────────┘    └─────────────────┘
                         │
                         ▼
┌─────────────────┐    ┌─────────────────┐
│     ERROR       │◄───│   COMPLETED     │
└─────────────────┘    └─────────────────┘
```

## Message Types

### 1. Control Messages
- `connection_established`
- `ping/pong`
- `error`

### 2. Task Messages
- `task_received`
- `task_queued`
- `task_started`
- `task_completed`
- `task_cancelled`

### 3. Phase Messages
- `phase_started`
- `phase_update`
- `phase_completed`
- `phase_error`

### 4. Query Messages
- `get_task_status`
- `get_task_logs`
- `config_update`

## Implementation Notes

1. Each component is designed to be modular and independently testable
2. The WebSocket Manager handles all real-time communication
3. The Connection State maintains client-specific settings and task queues
4. The Memory Repository provides persistent storage for tasks and logs
5. Agents are dynamically loaded based on the task phase
6. Error handling is implemented at multiple levels for robustness
7. Task cancellation can occur at any phase of execution 