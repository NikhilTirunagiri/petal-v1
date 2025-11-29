"""Simple background task queue for async processing."""

import asyncio
import logging
from typing import Callable, Any
from asyncio import Queue

logger = logging.getLogger(__name__)


class BackgroundTaskQueue:
    """Simple in-memory task queue for background processing."""

    def __init__(self, num_workers: int = 2):
        """Initialize task queue with worker pool."""
        self.queue: Queue = Queue()
        self.num_workers = num_workers
        self.workers = []
        self.is_running = False

    async def start(self):
        """Start background workers."""
        if self.is_running:
            return

        self.is_running = True
        logger.info(f"Starting background task queue with {self.num_workers} workers")

        # Start worker tasks
        for i in range(self.num_workers):
            worker = asyncio.create_task(self._worker(i))
            self.workers.append(worker)

    async def stop(self):
        """Stop background workers."""
        if not self.is_running:
            return

        self.is_running = False
        logger.info("Stopping background task queue")

        # Wait for queue to be empty
        await self.queue.join()

        # Cancel workers
        for worker in self.workers:
            worker.cancel()

        # Wait for workers to finish
        await asyncio.gather(*self.workers, return_exceptions=True)
        self.workers = []

    async def enqueue(self, task_func: Callable, *args, **kwargs) -> str:
        """
        Add a task to the queue.

        Args:
            task_func: Async function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function

        Returns:
            Task ID (for tracking)
        """
        import uuid
        task_id = str(uuid.uuid4())

        await self.queue.put({
            "id": task_id,
            "func": task_func,
            "args": args,
            "kwargs": kwargs
        })

        logger.debug(f"Enqueued task {task_id}")
        return task_id

    async def _worker(self, worker_id: int):
        """Background worker that processes tasks."""
        logger.info(f"Worker {worker_id} started")

        while self.is_running:
            try:
                # Get task from queue (with timeout to allow shutdown)
                try:
                    task = await asyncio.wait_for(self.queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue

                task_id = task["id"]
                task_func = task["func"]
                args = task["args"]
                kwargs = task["kwargs"]

                logger.info(f"Worker {worker_id} processing task {task_id}")

                try:
                    # Execute the task
                    await task_func(*args, **kwargs)
                    logger.info(f"Worker {worker_id} completed task {task_id}")
                except Exception as e:
                    logger.error(f"Worker {worker_id} task {task_id} failed: {e}", exc_info=True)
                finally:
                    self.queue.task_done()

            except asyncio.CancelledError:
                logger.info(f"Worker {worker_id} cancelled")
                break
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}", exc_info=True)

        logger.info(f"Worker {worker_id} stopped")


# Global task queue instance
task_queue = BackgroundTaskQueue(num_workers=2)
