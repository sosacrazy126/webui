# KODING.md

## Commands

- **Run tests:** `pytest tests/`
- **Run specific test:** `pytest tests/test_agents.py -k test_research_agent` (replace `test_agents.py` and `test_research_agent` as needed)
- **Run linting:** No specific linting command found. Consider using `ruff check .` or `pylint enhanced_ra_server tests`.
- **Run type checking:** No specific type checking command found. Consider using `mypy enhanced_ra_server`.
- **Run server:** `python -m enhanced_ra_server --host 127.0.0.1 --port 8000` (see `README.md` for more options)

## Code Style

- **Imports:** Standard Python imports, grouped as standard library, third-party, and local modules. Use absolute imports where possible (e.g., `from enhanced_ra_server.models import schema`).
- **Formatting:** Follow PEP 8 guidelines. Use tools like `black` or `autopep8` for automatic formatting.
- **Types:** Use type hints extensively (`typing` module). All function signatures and major variables should have type hints.
- **Naming:**
    - Classes: `CamelCase` (e.g., `WebSocketManager`)
    - Functions/Methods: `snake_case` (e.g., `run_task_implementation_agent`)
    - Variables: `snake_case`
    - Constants: `UPPER_SNAKE_CASE`
- **Error Handling:** Use standard Python exceptions. Log errors appropriately using the `utils/logging.py` module if applicable. Use `try...except` blocks for operations that might fail (e.g., database interactions, WebSocket communication).
- **Docstrings:** Use Google-style docstrings for modules, classes, and functions.
- **Async:** Use `async/await` for I/O-bound operations, especially in FastAPI routes and WebSocket handling.
