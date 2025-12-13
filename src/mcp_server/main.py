from typing import Literal

from mcp.server.fastmcp import FastMCP

from mcp_server.models import AnalysisResult, ApplicationInfo, SystemMetrics
from mcp_server.tools import gnome
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


@mcp.tool()
def set_color_scheme(preference: Literal["default", "prefer-dark"]) -> str:
    """
    Switch between GNOME light and dark color schemes using gsettings.
    """
    return gnome.set_color_scheme(preference)


@mcp.tool()
def set_wallpaper(image_path: str) -> str:
    """
    Set the desktop wallpaper for both light and dark modes.
    """
    return gnome.set_wallpaper(image_path)


@mcp.tool()
def set_night_light(enabled: bool) -> str:
    """
    Enable or disable Night Light to adjust display color temperature.
    """
    return gnome.set_night_light(enabled)


@mcp.tool()
def list_applications(limit: int = 50) -> list[ApplicationInfo]:
    """
    List installed applications discovered from .desktop files.
    """
    return gnome.list_applications(limit=limit)


@mcp.tool()
def launch_application(desktop_id: str) -> str:
    """
    Launch an application by its desktop identifier using gtk-launch.
    """
    return gnome.launch_application(desktop_id)


@mcp.tool()
def set_volume(volume_percent: int) -> str:
    """
    Set system output volume percentage (0-150).
    """
    return gnome.set_volume_percent(volume_percent)


@mcp.tool()
def update_mute(action: Literal["toggle", "mute", "unmute"]) -> str:
    """
    Toggle or force mute state on the default output sink.
    """
    return gnome.set_mute_state(action)


@mcp.tool()
def control_media(action: Literal["play-pause", "next", "previous", "stop"]) -> str:
    """
    Control media playback through playerctl.
    """
    return gnome.media_control(action)


@mcp.tool()
def lock_screen() -> str:
    """
    Lock the current GNOME session screen.
    """
    return gnome.lock_screen()


@mcp.tool()
def open_with_default(target: str) -> str:
    """
    Open a file path or URL with the default GNOME handler via gio.
    """
    return gnome.open_with_default(target)


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
