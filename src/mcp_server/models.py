from typing import Literal, Optional

from pydantic import BaseModel, Field


class SystemMetrics(BaseModel):
    """
    Snapshot of system resource usage.
    """

    cpu_percent: float = Field(..., description="Current CPU load percentage (0-100).")
    memory_gb: float = Field(..., description="RAM in use in gigabytes.")
    process_count: int = Field(..., description="Number of running processes.")


class AnalysisResult(BaseModel):
    """
    Structured result for system health analysis.
    """

    status: Literal["healthy", "warning", "critical"] = Field(
        ..., description="Overall system health rating."
    )
    recommendation: Optional[str] = Field(
        None, description="Actionable advice when health is not healthy."
    )
