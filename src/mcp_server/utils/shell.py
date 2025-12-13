import shlex
import subprocess
from logging import Logger
from subprocess import CompletedProcess
from typing import Sequence

from mcp_server.models import CommandResult
from mcp_server.utils.logger import configure_logging

logger: Logger = configure_logging(__name__)


def run_command(command: Sequence[str]) -> CommandResult:
    """Execute a command and normalize its output.

    Args:
        command: Command and arguments to execute. Elements are shell-escaped for logging.

    Returns:
        Structured output containing stdout, stderr, and return code.

    References:
        - subprocess.run: https://docs.python.org/3/library/subprocess.html#subprocess.run
    """
    command_str: str = " ".join(shlex.quote(part) for part in command)
    completed: CompletedProcess[str] = subprocess.run(
        command, check=False, capture_output=True, text=True
    )

    stdout: str = completed.stdout.strip()
    stderr: str = completed.stderr.strip()
    success: bool = completed.returncode == 0

    log_extra: dict[str, int | str] = {
        "cmd": command_str,
        "returncode": completed.returncode,
    }
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
