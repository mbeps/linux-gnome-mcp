"""Entrypoint and tool registration for the Linux GNOME Automations MCP server."""

from __future__ import annotations

import argparse
import os
from collections.abc import Sequence
from logging import Logger

from mcp.server.mcpserver import MCPServer
from starlette.applications import Starlette

from mcp_server.models import AnalysisResult, SystemMetrics
from mcp_server.tools import gnome
from mcp_server.tools.system import calculate_health
from mcp_server.utils.logger import configure_logging

logger: Logger = configure_logging("mcp_server.main")

# Initialize MCP Server using SDK v2 stateless architecture
mcp: MCPServer = MCPServer(
    name="Linux-GNOME-Automations",
    version="0.1.0",
    description="GNOME & Fedora desktop automation MCP server",
)


# Register System Assessment Tool
@mcp.tool()
def analyze_metrics(metrics: SystemMetrics) -> AnalysisResult:
    """Analyze provided system metrics and return a health assessment.

    Args:
        metrics: CPU, memory, and process metrics describing the host.

    Returns:
        Health classification with optional recommendations.
    """
    logger.info("Received analyze_metrics request")
    return calculate_health(metrics)


# Register Configuration Resource
@mcp.resource("config://app/defaults")
def get_default_config() -> str:
    """Return a simple default configuration payload.

    Returns:
        JSON string representing suggested monitoring defaults.
    """
    logger.info("Serving default config resource")
    return """
    {
        "poll_interval_seconds": 60,
        "cpu_threshold_warning": 70.0,
        "cpu_threshold_critical": 90.0
    }
    """


# Register GNOME desktop automation tools directly
_GNOME_TOOLS = (
    gnome.set_color_scheme,
    gnome.set_wallpaper,
    gnome.set_night_light,
    gnome.set_wallpaper_mode,
    gnome.set_gtk_theme,
    gnome.set_icon_theme,
    gnome.set_font,
    gnome.set_text_scaling,
    gnome.set_night_light_temperature,
    gnome.set_night_light_schedule_automatic,
    gnome.set_night_light_schedule,
    gnome.list_applications,
    gnome.launch_application,
    gnome.get_favorite_apps,
    gnome.set_favorite_apps,
    gnome.add_favorite_app,
    gnome.shutdown_system,
    gnome.reboot_system,
    gnome.get_system_details,
    gnome.set_wifi_enabled,
    gnome.set_bluetooth_enabled,
    gnome.set_networking_enabled,
    gnome.set_airplane_mode,
    gnome.set_power_profile,
    gnome.lock_screen,
    gnome.logout_session,
    gnome.open_with_default,
    gnome.brightness_step_up,
    gnome.brightness_step_down,
    gnome.move_to_trash,
    gnome.empty_trash,
    gnome.send_notification,
    gnome.copy_to_clipboard,
    gnome.paste_from_clipboard,
    gnome.set_tap_to_click,
    gnome.set_natural_scroll,
    gnome.set_touchpad_speed,
    gnome.get_user_extensions_enabled,
    gnome.set_user_extensions_enabled,
    gnome.list_extensions,
    gnome.get_extension_info,
    gnome.enable_extension,
    gnome.disable_extension,
)

for _tool_fn in _GNOME_TOOLS:
    mcp.add_tool(_tool_fn)

# Register GNOME tools with custom public tool names
mcp.add_tool(gnome.set_volume_percent, name="set_volume")
mcp.add_tool(gnome.set_mute_state, name="update_mute")
mcp.add_tool(gnome.media_control, name="control_media")


# Export ASGI application configured for stateless Streamable HTTP
app: Starlette = mcp.streamable_http_app(stateless_http=True)


def parse_args(args: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command line arguments for the MCP server.

    Args:
        args: Optional sequence of argument strings to parse. If None, sys.argv is used.

    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(description="Linux GNOME Automations MCP Server (v2 Stateless)")
    parser.add_argument(
        "--transport",
        choices=["stdio", "streamable-http", "sse"],
        default=os.environ.get("MCP_TRANSPORT", "stdio"),
        help="Transport protocol to use (default: stdio, env: MCP_TRANSPORT)",
    )
    parser.add_argument(
        "--host",
        default=os.environ.get("MCP_HOST", "127.0.0.1"),
        help="Host address for HTTP/SSE transports (default: 127.0.0.1, env: MCP_HOST)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("MCP_PORT", "8000")),
        help="Port number for HTTP/SSE transports (default: 8000, env: MCP_PORT)",
    )
    parser.add_argument(
        "--stateless",
        action=argparse.BooleanOptionalAction,
        default=os.environ.get("MCP_STATELESS_HTTP", "true").lower() in ("true", "1", "yes"),
        help="Enable stateless HTTP mode for streamable-http (default: True, env: MCP_STATELESS_HTTP)",
    )
    return parser.parse_args(args)


def run(args: Sequence[str] | None = None) -> None:
    """Entrypoint for launching the MCP server.

    Args:
        args: Optional CLI arguments. If None, command line arguments are parsed.

    Returns:
        Nothing.
    """
    parsed = parse_args(args)
    logger.info("Starting MCP server with transport: %s", parsed.transport)
    try:
        if parsed.transport == "stdio":
            mcp.run(transport="stdio")
        elif parsed.transport == "streamable-http":
            logger.info("Stateless HTTP mode: %s", parsed.stateless)
            mcp.run(
                transport="streamable-http",
                host=parsed.host,
                port=parsed.port,
                stateless_http=parsed.stateless,
            )
        elif parsed.transport == "sse":
            mcp.run(transport="sse", host=parsed.host, port=parsed.port)
        else:
            raise ValueError(f"Unsupported transport: {parsed.transport}")
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception:
        logger.critical("Fatal server error", exc_info=True)
        raise


if __name__ == "__main__":
    run()
