from typing import Literal, Optional

from pydantic import BaseModel, Field


class SystemMetrics(BaseModel):
    """Snapshot of resource usage used to assess host health.

    Attributes:
        cpu_percent: Current CPU load percentage (0-100).
        memory_gb: RAM usage in gigabytes as reported by the OS.
        process_count: Number of running processes at sample time.
    """

    cpu_percent: float = Field(..., description="Current CPU load percentage (0-100).")
    memory_gb: float = Field(..., description="RAM in use in gigabytes.")
    process_count: int = Field(..., description="Number of running processes.")


class AnalysisResult(BaseModel):
    """Structured result for system health analysis.

    Attributes:
        status: Health rating used to drive follow-up actions.
        recommendation: Optional remediation text for non-healthy states.
    """

    status: Literal["healthy", "warning", "critical"] = Field(
        ..., description="Overall system health rating."
    )
    recommendation: Optional[str] = Field(
        None, description="Actionable advice when health is not healthy."
    )


class CommandResult(BaseModel):
    """Normalized output from a shell command invocation.

    Attributes:
        success: True when the command exit code is 0.
        command: The executed command string with arguments quoted.
        stdout: Captured standard output with trailing whitespace trimmed.
        stderr: Captured standard error with trailing whitespace trimmed.
        returncode: Raw process return code from ``subprocess``.
    """

    success: bool = Field(..., description="True when the command exit code is 0.")
    command: str = Field(..., description="The executed command string.")
    stdout: str = Field("", description="Captured standard output.")
    stderr: str = Field("", description="Captured standard error.")
    returncode: int = Field(..., description="Raw process return code.")


class ApplicationInfo(BaseModel):
    """Installed application discovered via ``.desktop`` files.

    Attributes:
        desktop_id: Desktop file identifier, e.g. ``org.gnome.Nautilus.desktop``.
        name: Human-readable application name from the desktop file.
        exec_cmd: Raw Exec command from the desktop file, if present.
        source: Directory where the desktop file was found.
    """

    desktop_id: str = Field(..., description="Desktop file identifier, e.g. org.gnome.Nautilus.desktop.")
    name: Optional[str] = Field(None, description="Human-readable application name from the desktop file.")
    exec_cmd: Optional[str] = Field(None, description="Exec command from the desktop file, if present.")
    source: str = Field(..., description="Directory where the desktop file was found.")


class SystemDetails(BaseModel):
    """High-level system information snapshot.

    Attributes:
        kernel_version: Running kernel version.
        os_name: Operating system name.
        os_version: Operating system version or codename.
        uptime: Human-readable uptime string (``uptime -p``).
        memory: Memory usage summary (``free -h`` output).
        storage: Block devices summary (``lsblk`` output).
    """

    kernel_version: str = Field(..., description="Running kernel version.")
    os_name: str = Field(..., description="Operating system name.")
    os_version: str = Field(..., description="Operating system version or codename.")
    uptime: str = Field(..., description="Human-readable uptime string.")
    memory: str = Field(..., description="Memory usage summary (free -h).")
    storage: str = Field(..., description="Block devices summary (lsblk).")


class ExtensionInfo(BaseModel):
    """GNOME Shell extension metadata snapshot.

    Attributes:
        uuid: Unique extension identifier, e.g. ``blur-my-shell@aunetx``.
        name: Human-readable extension name, if available.
        description: Short description of the extension, if available.
        enabled: True if the extension is enabled in GNOME Shell.
        state: Current extension runtime state, e.g. ``ACTIVE``, ``INITIALIZED``, ``DISABLED``.
        path: Installation directory path, if available.
        url: Project homepage or repository URL, if available.
        version: Extension version string or integer, if available.
    """

    uuid: str = Field(..., description="Unique extension identifier, e.g. blur-my-shell@aunetx.")
    name: Optional[str] = Field(None, description="Human-readable extension name.")
    description: Optional[str] = Field(None, description="Short description of the extension.")
    enabled: bool = Field(False, description="True if the extension is enabled.")
    state: Optional[str] = Field(None, description="Current runtime state, e.g. ACTIVE, DISABLED.")
    path: Optional[str] = Field(None, description="Installation directory path.")
    url: Optional[str] = Field(None, description="Homepage or repository URL.")
    version: Optional[str] = Field(None, description="Extension version.")

