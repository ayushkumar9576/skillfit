"""
app/analysis/engines/executor.py
--------------------------------
Analysis Executor abstraction for the Drive Intelligence Engine.

This decouples the FastAPI web worker from the background execution logic.
Currently delegates to FastAPI's BackgroundTasks, but provides a clean
seam to drop in Celery, Redis Queue (RQ), or any async task runner in Phase 5.
"""

from uuid import UUID
from fastapi import BackgroundTasks

from app.db.database import SessionLocal
from app.services import drive_analysis_service


class AnalysisExecutor:
    """
    Abstracts background execution for Drive Intelligence analysis.
    """

    def __init__(self, background_tasks: BackgroundTasks):
        self._background_tasks = background_tasks

    def submit_analysis(self, analysis_id: UUID) -> None:
        """
        Submit a PENDING analysis for background execution.
        """
        self._background_tasks.add_task(self._execute_analysis_task, analysis_id)

    @staticmethod
    async def _execute_analysis_task(analysis_id: UUID) -> None:
        """
        The background task payload.
        Opens a new DB session since the request session is closed.
        """
        db = SessionLocal()
        try:
            await drive_analysis_service.execute_analysis_background(db, analysis_id)
        finally:
            db.close()
