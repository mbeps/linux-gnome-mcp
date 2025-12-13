import shlex
import subprocess
from typing import Sequence

from mcp_server.models import CommandResult
from mcp_server.utils.logger import configure_logging

logger = configure_logging(__name__)


def run_command(command: Sequence[str]) -> CommandResult:
    """
    Execute a command and normalize output without raising on non-zero exit codes.
    """
    command_str = " ".join(shlex.quote(part) for part in command)
    completed = subprocess.run(command, check=False, capture_output=True, text=True)

    stdout: str = completed.stdout.strip()
    stderr: str = completed.stderr.strip()
    success: bool = completed.returncode == 0

    log_extra = {"cmd": command_str, "returncode": completed.returncode}
    if success:
        logger.info("Command succeeded", extra=log_extra)
    else:
        logger.warning("Command failed", extra={**log_extra, "stderr": stderr})

    return CommandResult(
        success=success,
        command=command_str,
        stdout=stdout,
        stderr=stderr,
        returncode=completed.returncode,
    )
