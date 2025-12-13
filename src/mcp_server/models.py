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


class CommandResult(BaseModel):
    """
    Normalized output from a shell command invocation.
    """

    success: bool = Field(..., description="True when the command exit code is 0.")
    command: str = Field(..., description="The executed command string.")
    stdout: str = Field("", description="Captured standard output.")
    stderr: str = Field("", description="Captured standard error.")
    returncode: int = Field(..., description="Raw process return code.")


class ApplicationInfo(BaseModel):
    """
    Minimal representation of an installed application discovered via .desktop files.
    """

    desktop_id: str = Field(..., description="Desktop file identifier, e.g. org.gnome.Nautilus.desktop.")
    name: Optional[str] = Field(None, description="Human-readable application name from the desktop file.")
    exec_cmd: Optional[str] = Field(None, description="Exec command from the desktop file, if present.")
    source: str = Field(..., description="Directory where the desktop file was found.")


class SystemDetails(BaseModel):
    """
    High-level system information snapshot.
    """

    kernel_version: str = Field(..., description="Running kernel version.")
    os_name: str = Field(..., description="Operating system name.")
    os_version: str = Field(..., description="Operating system version or codename.")
    uptime: str = Field(..., description="Human-readable uptime string.")
    memory: str = Field(..., description="Memory usage summary (free -h).")
    storage: str = Field(..., description="Block devices summary (lsblk).")
