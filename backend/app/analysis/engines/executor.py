"""
app/analysis/engines/executor.py
--------------------------------
Analysis Executor abstraction for the Drive Intelligence Engine.

This decouples the FastAPI web worker from the background execution logic.
Currently delegates to FastAPI's BackgroundTasks, but provides a clean
seam to drop in Celery, Redis Queue (RQ), or any async task runner in Phase 5.
"""

import asyncio
from threading import Lock
from uuid import UUID
from fastapi import BackgroundTasks

from app.db.database import SessionLocal
from app.services import drive_analysis_service


class AnalysisExecutor:
    """
    Abstracts background execution for Drive Intelligence analysis.
    """

    _active_tasks: dict[UUID, tuple[asyncio.AbstractEventLoop, asyncio.Task]] = {}
    _active_tasks_lock = Lock()

    def __init__(self, background_tasks: BackgroundTasks):
        self._background_tasks = background_tasks

    def submit_analysis(self, analysis_id: UUID) -> None:
        """
        Submit a PENDING analysis for background execution.
        """
        self._background_tasks.add_task(self._execute_analysis_task, analysis_id)

    @classmethod
    def cancel_analysis(cls, analysis_id: UUID) -> bool:
        """Request cancellation of an analysis running in this process."""
        with cls._active_tasks_lock:
            active = cls._active_tasks.get(analysis_id)
        if active is None:
            return False
        loop, task = active
        loop.call_soon_threadsafe(task.cancel)
        return True

    @staticmethod
    async def _execute_analysis_task(analysis_id: UUID) -> None:
        """
        The background task payload.
        Opens a new DB session since the request session is closed.
        """
        db = SessionLocal()
        task = asyncio.create_task(drive_analysis_service.execute_analysis_background(db, analysis_id))
        loop = asyncio.get_running_loop()
        if task is not None:
            with AnalysisExecutor._active_tasks_lock:
                AnalysisExecutor._active_tasks[analysis_id] = (loop, task)

        try:
            await task
        except asyncio.CancelledError:
            # Cancellation belongs to the analysis task, not the ASGI response task.
            db.rollback()
            from app.core.enums import DriveAnalysisStatus
            from app.models.drive_analysis import DriveAnalysis

            analysis = db.get(DriveAnalysis, analysis_id)
            if analysis is not None and analysis.status != DriveAnalysisStatus.cancelled.value:
                raise
        finally:
            db.close()
            with AnalysisExecutor._active_tasks_lock:
                AnalysisExecutor._active_tasks.pop(analysis_id, None)
