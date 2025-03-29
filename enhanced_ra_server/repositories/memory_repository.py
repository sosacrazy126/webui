"""
Memory repository for Enhanced RA.Aid Server.

This module provides persistent storage for task contexts, research results,
planning outputs, and implementation details across task phases.
"""

import json
import os
import sqlite3
import threading
import time
from typing import Dict, Any, Optional, List, Union
from pathlib import Path


class MemorySaver:
    """
    Global memory management for RA.Aid tasks and results.
    
    This class provides persistent storage of task-related information with
    thread/client isolation for multi-user scenarios.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the memory system with the given database path.
        
        Args:
            db_path: Path to SQLite database file (default: ~/.ra_aid/memory.db)
        """
        if db_path is None:
            db_path = os.path.expanduser("~/.ra_aid/memory.db")
        
        self.db_path = db_path
        self._init_db()
        self._lock = threading.RLock()  # Reentrant lock for thread safety
    
    def _init_db(self) -> None:
        """Initialize the SQLite database with required tables."""
        # Create directory if it doesn't exist
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        
        # Connect to database and create tables
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create table for general key-value storage
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS memory (
                    thread_id TEXT NOT NULL,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    timestamp INTEGER NOT NULL,
                    PRIMARY KEY (thread_id, key)
                )
            ''')
            
            # Create table for task phase results
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS phase_results (
                    thread_id TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    phase TEXT NOT NULL,
                    result TEXT NOT NULL,
                    timestamp INTEGER NOT NULL,
                    PRIMARY KEY (thread_id, task_id, phase)
                )
            ''')
            
            # Create table for task history
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS task_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    thread_id TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at INTEGER NOT NULL,
                    completed_at INTEGER,
                    metadata TEXT
                )
            ''')
            
            # Create table for task logs
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS task_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    thread_id TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    message TEXT NOT NULL,
                    message_type TEXT NOT NULL,
                    timestamp INTEGER NOT NULL
                )
            ''')
            
            # Create index for faster queries
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_memory_thread_id ON memory (thread_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_phase_results_thread_id ON phase_results (thread_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_task_history_thread_id ON task_history (thread_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_task_history_task_id ON task_history (task_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_task_logs_task_id ON task_logs (task_id)')
            
            conn.commit()
    
    def store(self, key: str, value: Any, thread_id: str = "global") -> None:
        """
        Store a value in memory.
        
        Args:
            key: Storage key
            value: Value to store (will be JSON serialized)
            thread_id: Thread/client identifier for isolation (default: "global")
        
        Raises:
            ValueError: If value cannot be JSON serialized
        """
        with self._lock:
            # Serialize the value to JSON
            try:
                serialized_value = json.dumps(value)
            except TypeError as e:
                raise ValueError(f"Cannot serialize value to JSON: {e}")
            
            # Store in database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'INSERT OR REPLACE INTO memory (thread_id, key, value, timestamp) VALUES (?, ?, ?, strftime("%s"))',
                    (thread_id, key, serialized_value)
                )
                conn.commit()
    
    def retrieve(self, key: str, thread_id: str = "global", default: Any = None) -> Any:
        """
        Retrieve a value from memory.
        
        Args:
            key: Storage key to retrieve
            thread_id: Thread/client identifier (default: "global")
            default: Default value if key doesn't exist
        
        Returns:
            The stored value (JSON deserialized) or default if not found
        """
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # First check thread-specific value
                cursor.execute(
                    'SELECT value FROM memory WHERE thread_id = ? AND key = ?',
                    (thread_id, key)
                )
                result = cursor.fetchone()
                
                # If not found and thread_id isn't "global", check global value
                if result is None and thread_id != "global":
                    cursor.execute(
                        'SELECT value FROM memory WHERE thread_id = "global" AND key = ?',
                        (key,)
                    )
                    result = cursor.fetchone()
                
                if result is not None:
                    try:
                        return json.loads(result[0])
                    except json.JSONDecodeError:
                        return result[0]  # Return as string if not valid JSON
                
                return default
    
    def store_phase_result(
        self,
        phase: str,
        result: Any,
        task_id: str = "default",
        thread_id: str = "global"
    ) -> None:
        """
        Store a task phase result.
        
        Args:
            phase: Phase name (e.g., "research", "planning", "implementation")
            result: Phase result (will be JSON serialized)
            task_id: Task identifier
            thread_id: Thread/client identifier for isolation
        
        Raises:
            ValueError: If result cannot be JSON serialized
        """
        with self._lock:
            # Serialize the result to JSON
            try:
                serialized_result = json.dumps(result)
            except TypeError as e:
                raise ValueError(f"Cannot serialize result to JSON: {e}")
            
            # Store in database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    '''
                    INSERT OR REPLACE INTO phase_results 
                    (thread_id, task_id, phase, result, timestamp) 
                    VALUES (?, ?, ?, ?, strftime("%s"))
                    ''',
                    (thread_id, task_id, phase, serialized_result)
                )
                conn.commit()
    
    def retrieve_phase_result(
        self,
        phase: str,
        task_id: str = "default",
        thread_id: str = "global",
        default: Any = None
    ) -> Any:
        """
        Retrieve a task phase result.
        
        Args:
            phase: Phase name to retrieve
            task_id: Task identifier
            thread_id: Thread/client identifier
            default: Default value if result doesn't exist
        
        Returns:
            The stored phase result (JSON deserialized) or default if not found
        """
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # First check thread-specific result
                cursor.execute(
                    'SELECT result FROM phase_results WHERE thread_id = ? AND task_id = ? AND phase = ?',
                    (thread_id, task_id, phase)
                )
                result = cursor.fetchone()
                
                # If not found and thread_id isn't "global", check global result
                if result is None and thread_id != "global":
                    cursor.execute(
                        'SELECT result FROM phase_results WHERE thread_id = "global" AND task_id = ? AND phase = ?',
                        (task_id, phase)
                    )
                    result = cursor.fetchone()
                
                if result is not None:
                    try:
                        return json.loads(result[0])
                    except json.JSONDecodeError:
                        return result[0]  # Return as string if not valid JSON
                
                return default
    
    def store_task(
        self,
        task_id: str,
        content: str,
        thread_id: str = "global",
        status: str = "pending",
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Store a task in the task history.
        
        Args:
            task_id: Task identifier
            content: Task content/description
            thread_id: Thread/client identifier
            status: Task status (e.g., "pending", "in_progress", "completed")
            metadata: Additional task metadata
        """
        with self._lock:
            # Serialize metadata to JSON if provided
            serialized_metadata = None
            if metadata is not None:
                try:
                    serialized_metadata = json.dumps(metadata)
                except TypeError as e:
                    raise ValueError(f"Cannot serialize metadata to JSON: {e}")
            
            # Store in database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if task already exists
                cursor.execute(
                    'SELECT id FROM task_history WHERE thread_id = ? AND task_id = ?',
                    (thread_id, task_id)
                )
                result = cursor.fetchone()
                
                if result is None:
                    # Task doesn't exist, insert new record
                    cursor.execute(
                        '''
                        INSERT INTO task_history 
                        (thread_id, task_id, content, status, created_at, metadata) 
                        VALUES (?, ?, ?, ?, ?, ?)
                        ''',
                        (thread_id, task_id, content, status, int(time.time()), serialized_metadata)
                    )
                else:
                    # Task exists, update status
                    cursor.execute(
                        '''
                        UPDATE task_history 
                        SET status = ?, metadata = ?
                        WHERE thread_id = ? AND task_id = ?
                        ''',
                        (status, serialized_metadata, thread_id, task_id)
                    )
                
                conn.commit()
    
    def mark_task_complete(
        self,
        task_id: str,
        thread_id: str = "global",
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Mark a task as completed in the task history.
        
        Args:
            task_id: Task identifier
            thread_id: Thread/client identifier
            metadata: Additional task metadata to store
        """
        with self._lock:
            # Serialize metadata to JSON if provided
            serialized_metadata = None
            if metadata is not None:
                try:
                    serialized_metadata = json.dumps(metadata)
                except TypeError as e:
                    raise ValueError(f"Cannot serialize metadata to JSON: {e}")
            
            # Update task in database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if serialized_metadata is not None:
                    cursor.execute(
                        '''
                        UPDATE task_history 
                        SET status = 'completed', completed_at = ?, metadata = ?
                        WHERE thread_id = ? AND task_id = ?
                        ''',
                        (int(time.time()), serialized_metadata, thread_id, task_id)
                    )
                else:
                    cursor.execute(
                        '''
                        UPDATE task_history 
                        SET status = 'completed', completed_at = ?
                        WHERE thread_id = ? AND task_id = ?
                        ''',
                        (int(time.time()), thread_id, task_id)
                    )
                
                conn.commit()
    
    def get_task_history(
        self,
        thread_id: str = "global",
        limit: int = 100,
        offset: int = 0,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve task history for a thread.
        
        Args:
            thread_id: Thread/client identifier
            limit: Maximum number of tasks to retrieve
            offset: Number of tasks to skip
            status: Filter by task status
        
        Returns:
            List of task history records
        """
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                # Set row factory to get dictionary results
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Build query based on parameters
                query = 'SELECT task_id, content, status, created_at, completed_at, metadata FROM task_history WHERE thread_id = ?'
                params = [thread_id]
                
                if status is not None:
                    query += ' AND status = ?'
                    params.append(status)
                
                # Order by ID to ensure consistent results
                query += ' ORDER BY id DESC LIMIT ? OFFSET ?'
                params.extend([limit, offset])
                
                cursor.execute(query, params)
                
                results = []
                for row in cursor.fetchall():
                    # Parse metadata JSON if it exists
                    metadata = row["metadata"]
                    parsed_metadata = None
                    if metadata:
                        try:
                            parsed_metadata = json.loads(metadata)
                        except json.JSONDecodeError:
                            parsed_metadata = {}
                    
                    results.append({
                        "task_id": row["task_id"],
                        "content": row["content"],
                        "status": row["status"],
                        "created_at": row["created_at"],
                        "completed_at": row["completed_at"],
                        "metadata": parsed_metadata
                    })
                
                return results
    
    def get_task(self, task_id: str, thread_id: str = "global") -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific task from the task history.
        
        Args:
            task_id: Task identifier
            thread_id: Thread/client identifier
        
        Returns:
            Task record or None if not found
        """
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute(
                    '''
                    SELECT task_id, content, status, created_at, completed_at, metadata
                    FROM task_history
                    WHERE thread_id = ? AND task_id = ?
                    ''',
                    (thread_id, task_id)
                )
                
                row = cursor.fetchone()
                if row is None:
                    return None
                
                task_id, content, status, created_at, completed_at, metadata = row
                
                # Parse metadata JSON if it exists
                parsed_metadata = None
                if metadata:
                    try:
                        parsed_metadata = json.loads(metadata)
                    except json.JSONDecodeError:
                        parsed_metadata = {}
                
                return {
                    "task_id": task_id,
                    "content": content,
                    "status": status,
                    "created_at": created_at,
                    "completed_at": completed_at,
                    "metadata": parsed_metadata
                }
    
    def log_task_message(
        self,
        task_id: str,
        message: str,
        message_type: str,
        thread_id: str = "global"
    ) -> None:
        """
        Log a message for a task.
        
        Args:
            task_id: Task identifier
            message: Message content
            message_type: Message type (e.g., "info", "error", "phase_change")
            thread_id: Thread/client identifier
        """
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    '''
                    INSERT INTO task_logs
                    (thread_id, task_id, message, message_type, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                    ''',
                    (thread_id, task_id, message, message_type, int(time.time()))
                )
                conn.commit()
    
    def get_task_logs(
        self,
        task_id: str,
        thread_id: str = "global",
        limit: int = 100,
        offset: int = 0,
        message_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve logs for a specific task.
        
        Args:
            task_id: Task identifier
            thread_id: Thread/client identifier
            limit: Maximum number of logs to retrieve
            offset: Number of logs to skip
            message_type: Filter by message type
        
        Returns:
            List of log records
        """
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                # Set row factory to get dictionary results
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Build query based on parameters
                query = 'SELECT id, message, message_type, timestamp FROM task_logs WHERE thread_id = ? AND task_id = ?'
                params = [thread_id, task_id]
                
                if message_type is not None:
                    query += ' AND message_type = ?'
                    params.append(message_type)
                
                # Order by ID to ensure consistent results
                query += ' ORDER BY id DESC LIMIT ? OFFSET ?'
                params.extend([limit, offset])
                
                cursor.execute(query, params)
                
                results = []
                for row in cursor.fetchall():
                    results.append({
                        "id": row["id"],
                        "message": row["message"],
                        "message_type": row["message_type"],
                        "timestamp": row["timestamp"]
                    })
                
                return results
    
    def list_keys(self, thread_id: Optional[str] = None) -> List[str]:
        """
        List all keys in memory for a thread or all threads.
        
        Args:
            thread_id: Thread/client identifier or None for all threads
        
        Returns:
            List of keys
        """
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if thread_id is not None:
                    cursor.execute('SELECT key FROM memory WHERE thread_id = ?', (thread_id,))
                else:
                    cursor.execute('SELECT key FROM memory')
                
                return [row[0] for row in cursor.fetchall()]
    
    def clear_thread(self, thread_id: str) -> None:
        """
        Clear all memory for a specific thread.
        
        Args:
            thread_id: Thread/client identifier to clear
        """
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM memory WHERE thread_id = ?', (thread_id,))
                cursor.execute('DELETE FROM phase_results WHERE thread_id = ?', (thread_id,))
                cursor.execute('DELETE FROM task_history WHERE thread_id = ?', (thread_id,))
                cursor.execute('DELETE FROM task_logs WHERE thread_id = ?', (thread_id,))
                conn.commit()
    
    def clear_all(self) -> None:
        """Clear all memory for all threads."""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM memory')
                cursor.execute('DELETE FROM phase_results')
                cursor.execute('DELETE FROM task_history')
                cursor.execute('DELETE FROM task_logs')
                conn.commit() 