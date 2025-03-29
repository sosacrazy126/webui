"""
Unit tests for the memory management system.
"""

import os
import tempfile
import pytest
import sqlite3
import json
import time

from enhanced_ra_server.repositories.memory_repository import MemorySaver


class TestMemorySaver:
    """Test cases for the MemorySaver class."""

    @pytest.fixture
    def temp_db_path(self):
        """Create a temporary database file."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        yield path
        os.unlink(path)  # Clean up after test

    def test_init_creates_db(self, temp_db_path):
        """Test that initialization creates the database and tables."""
        # Initialize memory saver with temp path
        memory = MemorySaver(temp_db_path)
        
        # Check that the database file exists
        assert os.path.exists(temp_db_path)
        
        # Check that tables were created
        with sqlite3.connect(temp_db_path) as conn:
            cursor = conn.cursor()
            
            # Check memory table
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='memory'")
            assert cursor.fetchone() is not None
            
            # Check phase_results table
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='phase_results'")
            assert cursor.fetchone() is not None

    def test_store_and_retrieve(self, temp_db_path):
        """Test storing and retrieving values."""
        memory = MemorySaver(temp_db_path)
        
        # Store various types of data
        memory.store("string_key", "string_value")
        memory.store("int_key", 42)
        memory.store("dict_key", {"nested": "value"})
        memory.store("list_key", [1, 2, 3])
        
        # Retrieve the values
        assert memory.retrieve("string_key") == "string_value"
        assert memory.retrieve("int_key") == 42
        assert memory.retrieve("dict_key") == {"nested": "value"}
        assert memory.retrieve("list_key") == [1, 2, 3]
        
        # Test nonexistent key
        assert memory.retrieve("nonexistent") is None

    def test_store_and_retrieve_with_thread_isolation(self, temp_db_path):
        """Test thread isolation for storing and retrieving values."""
        memory = MemorySaver(temp_db_path)
        
        # Store values in different threads
        memory.store("key", "global_value", thread_id="global")
        memory.store("key", "thread1_value", thread_id="thread1")
        memory.store("key", "thread2_value", thread_id="thread2")
        
        # Retrieve values
        assert memory.retrieve("key", thread_id="global") == "global_value"
        assert memory.retrieve("key", thread_id="thread1") == "thread1_value"
        assert memory.retrieve("key", thread_id="thread2") == "thread2_value"
        
        # Test fallback to global
        memory.store("global_only", "global_value", thread_id="global")
        assert memory.retrieve("global_only", thread_id="thread1") == "global_value"

    def test_store_and_retrieve_phase_result(self, temp_db_path):
        """Test storing and retrieving phase results."""
        memory = MemorySaver(temp_db_path)
        
        # Store phase results
        memory.store_phase_result(
            phase="research",
            result={"findings": "Research findings"},
            task_id="task1"
        )
        memory.store_phase_result(
            phase="planning",
            result={"plan": "Execution plan"},
            task_id="task1"
        )
        
        # Retrieve phase results
        research_result = memory.retrieve_phase_result(phase="research", task_id="task1")
        planning_result = memory.retrieve_phase_result(phase="planning", task_id="task1")
        
        assert research_result == {"findings": "Research findings"}
        assert planning_result == {"plan": "Execution plan"}
        
        # Test nonexistent phase
        assert memory.retrieve_phase_result(phase="implementation", task_id="task1") is None

    def test_store_and_retrieve_phase_result_with_thread_isolation(self, temp_db_path):
        """Test thread isolation for phase results."""
        memory = MemorySaver(temp_db_path)
        
        # Store phase results in different threads
        memory.store_phase_result(
            phase="research",
            result={"findings": "Global findings"},
            task_id="task1",
            thread_id="global"
        )
        memory.store_phase_result(
            phase="research",
            result={"findings": "Thread1 findings"},
            task_id="task1",
            thread_id="thread1"
        )
        
        # Retrieve phase results
        global_result = memory.retrieve_phase_result(
            phase="research", 
            task_id="task1", 
            thread_id="global"
        )
        thread1_result = memory.retrieve_phase_result(
            phase="research", 
            task_id="task1", 
            thread_id="thread1"
        )
        
        assert global_result == {"findings": "Global findings"}
        assert thread1_result == {"findings": "Thread1 findings"}
        
        # Test fallback to global
        memory.store_phase_result(
            phase="planning",
            result={"plan": "Global plan"},
            task_id="task1",
            thread_id="global"
        )
        thread2_result = memory.retrieve_phase_result(
            phase="planning", 
            task_id="task1", 
            thread_id="thread2"
        )
        
        assert thread2_result == {"plan": "Global plan"}

    def test_list_keys(self, temp_db_path):
        """Test listing keys in memory."""
        memory = MemorySaver(temp_db_path)
        
        # Store values
        memory.store("key1", "value1", thread_id="thread1")
        memory.store("key2", "value2", thread_id="thread1")
        memory.store("key3", "value3", thread_id="thread2")
        
        # List keys for specific thread
        thread1_keys = memory.list_keys(thread_id="thread1")
        assert set(thread1_keys) == {"key1", "key2"}
        
        thread2_keys = memory.list_keys(thread_id="thread2")
        assert set(thread2_keys) == {"key3"}
        
        # List all keys
        all_keys = memory.list_keys()
        assert set(all_keys) == {"key1", "key2", "key3"}

    def test_clear_thread(self, temp_db_path):
        """Test clearing memory for a specific thread."""
        memory = MemorySaver(temp_db_path)
        
        # Store values in different threads
        memory.store("key1", "value1", thread_id="thread1")
        memory.store("key2", "value2", thread_id="thread1")
        memory.store("key3", "value3", thread_id="thread2")
        
        memory.store_phase_result(
            phase="research",
            result={"findings": "Thread1 findings"},
            task_id="task1",
            thread_id="thread1"
        )
        memory.store_phase_result(
            phase="research",
            result={"findings": "Thread2 findings"},
            task_id="task1",
            thread_id="thread2"
        )
        
        # Clear thread1
        memory.clear_thread("thread1")
        
        # Check that thread1 values are gone
        assert memory.retrieve("key1", thread_id="thread1") is None
        assert memory.retrieve("key2", thread_id="thread1") is None
        assert memory.retrieve_phase_result(phase="research", task_id="task1", thread_id="thread1") is None
        
        # Check that thread2 values remain
        assert memory.retrieve("key3", thread_id="thread2") == "value3"
        assert memory.retrieve_phase_result(phase="research", task_id="task1", thread_id="thread2") == {"findings": "Thread2 findings"}

    def test_clear_all(self, temp_db_path):
        """Test clearing all memory."""
        memory = MemorySaver(temp_db_path)
        
        # Store values in different threads
        memory.store("key1", "value1", thread_id="thread1")
        memory.store("key2", "value2", thread_id="thread2")
        
        memory.store_phase_result(
            phase="research",
            result={"findings": "Thread1 findings"},
            task_id="task1",
            thread_id="thread1"
        )
        memory.store_phase_result(
            phase="research",
            result={"findings": "Thread2 findings"},
            task_id="task1",
            thread_id="thread2"
        )
        
        # Clear all
        memory.clear_all()
        
        # Check that all values are gone
        assert memory.retrieve("key1", thread_id="thread1") is None
        assert memory.retrieve("key2", thread_id="thread2") is None
        assert memory.retrieve_phase_result(phase="research", task_id="task1", thread_id="thread1") is None
        assert memory.retrieve_phase_result(phase="research", task_id="task1", thread_id="thread2") is None
        
        # Check that database tables are empty
        with sqlite3.connect(temp_db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM memory")
            assert cursor.fetchone()[0] == 0
            cursor.execute("SELECT COUNT(*) FROM phase_results")
            assert cursor.fetchone()[0] == 0

    def test_store_retrieve_task(self, temp_db_path):
        """Test storing and retrieving tasks."""
        memory = MemorySaver(temp_db_path)
        
        # Store a task
        task_id = "test-task-1"
        content = "Test task 1"
        thread_id = "test-thread"
        
        memory.store_task(task_id, content, thread_id)
        
        # Retrieve the task
        task = memory.get_task(task_id, thread_id)
        
        # Check task data
        assert task is not None
        assert task["task_id"] == task_id
        assert task["content"] == content
        assert task["status"] == "pending"
        assert "created_at" in task
        
        # Update task status
        memory.store_task(
            task_id=task_id,
            content=content,
            thread_id=thread_id,
            status="in_progress"
        )
        
        # Retrieve updated task
        task = memory.get_task(task_id, thread_id)
        
        # Check updated status
        assert task["status"] == "in_progress"
        
        # Mark task as complete
        memory.mark_task_complete(
            task_id=task_id,
            thread_id=thread_id,
            metadata={"result": "success"}
        )
        
        # Retrieve completed task
        task = memory.get_task(task_id, thread_id)
        
        # Check completed status
        assert task["status"] == "completed"
        assert task["completed_at"] is not None
        assert task["metadata"] == {"result": "success"}

    def test_task_history(self, temp_db_path):
        """Test retrieving task history."""
        memory = MemorySaver(temp_db_path)
        
        thread_id = "test-thread"
        
        # Store multiple tasks in reverse order (4 to 0)
        for i in range(4, -1, -1):
            memory.store_task(
                task_id=f"task-{i}",
                content=f"Task {i}",
                thread_id=thread_id,
                status="pending"
            )
            
            # Add small delay to ensure different timestamps
            time.sleep(0.1)
        
        # Mark some tasks as complete
        memory.mark_task_complete("task-1", thread_id)
        memory.store_task("task-2", "Task 2", thread_id, "error")
        
        # Get all task history
        history = memory.get_task_history(thread_id)
        
        # Check we have all tasks
        assert len(history) == 5
        
        # Tasks are returned in ID order (most recent first)
        # With our current implementation, task-0 should be first (ID 5)
        assert history[0]["task_id"] == "task-0"
        
        # Get only completed tasks
        completed = memory.get_task_history(thread_id, status="completed")
        
        # Check we only have completed tasks
        assert len(completed) == 1
        assert completed[0]["task_id"] == "task-1"
        
        # Get only error tasks
        error_tasks = memory.get_task_history(thread_id, status="error")
        
        # Check we only have error tasks
        assert len(error_tasks) == 1
        assert error_tasks[0]["task_id"] == "task-2"

    def test_task_logs(self, temp_db_path):
        """Test storing and retrieving task logs."""
        memory = MemorySaver(temp_db_path)
        
        task_id = "test-task"
        thread_id = "test-thread"
        
        # Log messages in chronological order
        # First: create
        memory.log_task_message(
            task_id=task_id,
            message="Task created",
            message_type="create",
            thread_id=thread_id
        )
        
        time.sleep(0.1)
        
        # Second: phase_change
        memory.log_task_message(
            task_id=task_id,
            message="Starting research phase",
            message_type="phase_change",
            thread_id=thread_id
        )
        
        time.sleep(0.1)
        
        # Last: error
        memory.log_task_message(
            task_id=task_id,
            message="Error occurred",
            message_type="error",
            thread_id=thread_id
        )
        
        # Get all logs
        logs = memory.get_task_logs(task_id, thread_id)
        
        # Check we have all logs
        assert len(logs) == 3
        
        # Logs should be in reverse chronological order (most recent first)
        # We inserted: create → phase_change → error
        # So we expect: error → phase_change → create
        assert logs[0]["message_type"] == "error"
        assert logs[1]["message_type"] == "phase_change"
        assert logs[2]["message_type"] == "create"
        
        # Get only error logs
        error_logs = memory.get_task_logs(
            task_id=task_id,
            thread_id=thread_id,
            message_type="error"
        )
        
        # Check we only have error logs
        assert len(error_logs) == 1
        assert error_logs[0]["message"] == "Error occurred"

    def test_clear_task_data(self, temp_db_path):
        """Test clearing task data with thread clearing."""
        memory = MemorySaver(temp_db_path)
        
        thread_id = "test-thread"
        
        # Store a task and logs
        memory.store_task(
            task_id="test-task",
            content="Test task",
            thread_id=thread_id
        )
        
        memory.log_task_message(
            task_id="test-task",
            message="Test log",
            message_type="info",
            thread_id=thread_id
        )
        
        # Clear the thread
        memory.clear_thread(thread_id)
        
        # Check task and logs are cleared
        assert memory.get_task("test-task", thread_id) is None
        assert memory.get_task_logs("test-task", thread_id) == [] 