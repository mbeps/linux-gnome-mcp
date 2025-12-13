from mcp.server.fastmcp import FastMCP

from mcp_server.models import AnalysisResult, SystemMetrics
from mcp_server.tools.system import calculate_health
from mcp_server.utils.logger import configure_logging

mcp = FastMCP("Linux-GNOME-Automations", dependencies=["pydantic"])
logger = configure_logging("mcp_server.main")


@mcp.tool()
def analyze_metrics(metrics: SystemMetrics) -> AnalysisResult:
    """
    Analyze provided system metrics and return a health assessment.
    """
    logger.info("Received analyze_metrics request")
    return calculate_health(metrics)


@mcp.resource("config://app/defaults")
def get_default_config() -> str:
    """
    Return a simple default configuration payload.
    """
    logger.info("Serving default config resource")
    return """
    {
        "poll_interval_seconds": 60,
        "cpu_threshold_warning": 70.0,
        "cpu_threshold_critical": 90.0
    }
    """


def run() -> None:
    """
    Entrypoint for launching the MCP server.
    """
    try:
        mcp.run()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception:
        logger.critical("Fatal server error", exc_info=True)
        raise


if __name__ == "__main__":
    run()
