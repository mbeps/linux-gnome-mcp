import logging
import sys


def configure_logging(name: str = "mcp_server") -> logging.Logger:
    """
    Configure a logger that writes to stderr to avoid polluting stdout-based MCP IO.
    """
    logger: logging.Logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if not logger.handlers:
        handler: logging.StreamHandler = logging.StreamHandler(sys.stderr)
        formatter: logging.Formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
