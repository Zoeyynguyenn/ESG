from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Literal, Optional

JobStatus = Literal["queued", "running", "completed", "failed"]


@dataclass
class IngestJob:
    job_id: str
    company_id: str
    status: JobStatus = "queued"
    message: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))


class IngestJobStore:
    def __init__(self) -> None:
        self._jobs: Dict[str, IngestJob] = {}
        self._lock = threading.Lock()

    def create(self, company_id: str) -> IngestJob:
        job = IngestJob(job_id=uuid.uuid4().hex[:12], company_id=company_id)
        with self._lock:
            self._jobs[job.job_id] = job
        return job

    def get(self, job_id: str) -> Optional[IngestJob]:
        with self._lock:
            return self._jobs.get(job_id)

    def update(self, job_id: str, *, status: JobStatus, message: str = "") -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return
            job.status = status
            job.message = message
            job.updated_at = datetime.now().isoformat(timespec="seconds")
