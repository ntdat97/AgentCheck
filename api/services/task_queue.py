"""
Task Queue Service
Simple in-memory task queue for verification workflows.
For production, this would be replaced with Celery, Redis Queue, or similar.
"""
import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Callable, Any
from queue import Queue, Empty
import threading
import uuid

from api.models.schemas import VerificationTask, TaskStatus


class TaskQueue:
    """
    Simple task queue for managing verification workflows.
    
    In production, this would be replaced with:
    - Celery + Redis/RabbitMQ
    - AWS SQS
    - Google Cloud Tasks
    - Temporal.io
    """
    
    def __init__(self, data_dir: str = "./data"):
        self.data_dir = Path(data_dir)
        self.queue_dir = self.data_dir / "queue"
        self.queue_dir.mkdir(parents=True, exist_ok=True)
        
        self._queue: Queue = Queue()
        self._tasks: Dict[str, VerificationTask] = {}
        self._handlers: Dict[str, Callable] = {}
        self._running = False
        self._worker_thread: Optional[threading.Thread] = None
        
        # Load any pending tasks from disk
        self._load_pending_tasks()
    
    def _load_pending_tasks(self) -> None:
        """Load pending tasks from disk on startup."""
        for filepath in self.queue_dir.glob("*.json"):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    task = VerificationTask(**data)
                    
                    # Re-queue pending tasks
                    if task.status in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS]:
                        task.status = TaskStatus.PENDING
                        self._tasks[task.id] = task
                        self._queue.put(task.id)
            except Exception as e:
                print(f"Error loading task from {filepath}: {e}")
    
    def register_handler(self, handler: Callable[[VerificationTask], Any]) -> None:
        """Register the task handler function."""
        self._handlers['default'] = handler
    
    def enqueue(self, pdf_path: str) -> VerificationTask:
        """
        Add a new verification task to the queue.
        
        Args:
            pdf_path: Path to the PDF to verify
            
        Returns:
            The created task
        """
        task = VerificationTask(
            pdf_path=pdf_path,
            status=TaskStatus.PENDING
        )
        
        self._tasks[task.id] = task
        self._save_task(task)
        self._queue.put(task.id)
        
        return task
    
    def _save_task(self, task: VerificationTask) -> None:
        """Persist task to disk."""
        filepath = self.queue_dir / f"{task.id}.json"
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(task.model_dump(mode='json'), f, indent=2, default=str)
    
    def get_task(self, task_id: str) -> Optional[VerificationTask]:
        """Get task by ID."""
        if task_id in self._tasks:
            return self._tasks[task_id]
        
        # Try loading from disk
        filepath = self.queue_dir / f"{task_id}.json"
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                task = VerificationTask(**data)
                self._tasks[task_id] = task
                return task
        
        return None
    
    def update_task(
        self,
        task_id: str,
        status: Optional[TaskStatus] = None,
        report_id: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> Optional[VerificationTask]:
        """Update task status and metadata."""
        task = self.get_task(task_id)
        if not task:
            return None
        
        if status:
            task.status = status
            
            if status == TaskStatus.IN_PROGRESS and not task.started_at:
                task.started_at = datetime.utcnow()
            elif status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                task.completed_at = datetime.utcnow()
        
        if report_id:
            task.report_id = report_id
        
        if error_message:
            task.error_message = error_message
        
        self._tasks[task_id] = task
        self._save_task(task)
        
        return task
    
    def process_one(self) -> Optional[VerificationTask]:
        """
        Process a single task from the queue.
        
        Returns:
            The processed task, or None if queue is empty
        """
        try:
            task_id = self._queue.get_nowait()
        except Empty:
            return None
        
        task = self.get_task(task_id)
        if not task:
            return None
        
        # Update status
        self.update_task(task_id, status=TaskStatus.IN_PROGRESS)
        
        try:
            # Run handler
            handler = self._handlers.get('default')
            if handler:
                result = handler(task)
                
                # Extract report_id if returned
                report_id = None
                if isinstance(result, dict):
                    report_id = result.get('report_id')
                elif hasattr(result, 'id'):
                    report_id = result.id
                
                self.update_task(
                    task_id,
                    status=TaskStatus.COMPLETED,
                    report_id=report_id
                )
            else:
                self.update_task(
                    task_id,
                    status=TaskStatus.FAILED,
                    error_message="No handler registered"
                )
        
        except Exception as e:
            self.update_task(
                task_id,
                status=TaskStatus.FAILED,
                error_message=str(e)
            )
        
        return self.get_task(task_id)
    
    def start_worker(self) -> None:
        """Start background worker thread."""
        if self._running:
            return
        
        self._running = True
        self._worker_thread = threading.Thread(
            target=self._worker_loop,
            daemon=True
        )
        self._worker_thread.start()
    
    def stop_worker(self) -> None:
        """Stop background worker thread."""
        self._running = False
        if self._worker_thread:
            self._worker_thread.join(timeout=5)
    
    def _worker_loop(self) -> None:
        """Background worker loop."""
        while self._running:
            task = self.process_one()
            if not task:
                # No tasks, wait a bit
                threading.Event().wait(1)
    
    def list_tasks(
        self,
        status: Optional[TaskStatus] = None,
        limit: int = 50
    ) -> List[VerificationTask]:
        """List tasks, optionally filtered by status."""
        tasks = list(self._tasks.values())
        
        if status:
            tasks = [t for t in tasks if t.status == status]
        
        # Sort by created_at descending
        tasks.sort(key=lambda t: t.created_at, reverse=True)
        
        return tasks[:limit]
    
    def queue_size(self) -> int:
        """Get current queue size."""
        return self._queue.qsize()
    
    def clear_completed(self) -> int:
        """Remove completed tasks from memory and disk."""
        count = 0
        for task_id in list(self._tasks.keys()):
            task = self._tasks[task_id]
            if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                del self._tasks[task_id]
                filepath = self.queue_dir / f"{task_id}.json"
                if filepath.exists():
                    filepath.unlink()
                count += 1
        return count
