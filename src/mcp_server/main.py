from typing import Literal, Optional

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
def set_wallpaper_mode(
    option: Literal["none", "wallpaper", "centered", "scaled", "stretched", "zoom", "spanned"]
) -> str:
    """
    Configure how the wallpaper is rendered (zoom, centered, spanned, etc.).
    """
    return gnome.set_wallpaper_mode(option)


@mcp.tool()
def set_gtk_theme(theme: str) -> str:
    """
    Set the GTK theme for legacy/non-libadwaita applications.
    """
    return gnome.set_gtk_theme(theme)


@mcp.tool()
def set_icon_theme(icon_theme: str) -> str:
    """
    Set the icon theme.
    """
    return gnome.set_icon_theme(icon_theme)


@mcp.tool()
def set_font(font_type: Literal["interface", "monospace", "document"], font_value: str) -> str:
    """
    Update GNOME interface, monospace, or document font values.
    """
    return gnome.set_font(font_type, font_value)


@mcp.tool()
def set_text_scaling(factor: float) -> str:
    """
    Adjust the global text scaling factor.
    """
    return gnome.set_text_scaling(factor)


@mcp.tool()
def set_night_light_temperature(kelvin: int) -> str:
    """
    Set the Night Light temperature in Kelvin.
    """
    return gnome.set_night_light_temperature(kelvin)


@mcp.tool()
def set_night_light_schedule_automatic(enabled: bool) -> str:
    """
    Enable or disable automatic Night Light scheduling.
    """
    return gnome.set_night_light_schedule_automatic(enabled)


@mcp.tool()
def set_night_light_schedule(start_hour: float, end_hour: float) -> str:
    """
    Define a manual Night Light schedule (24h format).
    """
    return gnome.set_night_light_schedule(start_hour, end_hour)


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
def get_favorite_apps() -> list[str]:
    """
    Return the current GNOME Shell favorite applications list.
    """
    return gnome.get_favorite_apps()


@mcp.tool()
def set_favorite_apps(apps: list[str]) -> str:
    """
    Overwrite the GNOME favorites list with the provided entries.
    """
    return gnome.set_favorite_apps(apps)


@mcp.tool()
def add_favorite_app(desktop_id: str) -> list[str]:
    """
    Add a desktop id to the GNOME favorites list if not already present.
    """
    return gnome.add_favorite_app(desktop_id)


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
def logout_session() -> str:
    """
    Log out of the current session without prompting.
    """
    return gnome.logout_session()


@mcp.tool()
def open_with_default(target: str) -> str:
    """
    Open a file path or URL with the default GNOME handler via gio.
    """
    return gnome.open_with_default(target)


@mcp.tool()
def brightness_step_up() -> str:
    """
    Increase brightness one step via the GNOME Settings Daemon.
    """
    return gnome.brightness_step_up()


@mcp.tool()
def brightness_step_down() -> str:
    """
    Decrease brightness one step via the GNOME Settings Daemon.
    """
    return gnome.brightness_step_down()


@mcp.tool()
def move_to_trash(path: str) -> str:
    """
    Move a file or directory to the Trash via gio.
    """
    return gnome.move_to_trash(path)


@mcp.tool()
def empty_trash() -> str:
    """
    Empty the Trash via gio.
    """
    return gnome.empty_trash()


@mcp.tool()
def send_notification(
    summary: str,
    body: Optional[str] = None,
    urgency: Literal["low", "normal", "critical"] = "normal",
) -> str:
    """
    Send a desktop notification with optional body and urgency.
    """
    return gnome.send_notification(summary, body, urgency)


@mcp.tool()
def copy_to_clipboard(text: str) -> str:
    """
    Copy plain text to the clipboard using wl-copy.
    """
    return gnome.copy_to_clipboard(text)


@mcp.tool()
def paste_from_clipboard() -> str:
    """
    Read text from the clipboard using wl-paste.
    """
    return gnome.paste_from_clipboard()


@mcp.tool()
def set_tap_to_click(enabled: bool) -> str:
    """
    Enable or disable touchpad tap-to-click.
    """
    return gnome.set_tap_to_click(enabled)


@mcp.tool()
def set_natural_scroll(enabled: bool) -> str:
    """
    Enable or disable natural scrolling for the touchpad.
    """
    return gnome.set_natural_scroll(enabled)


@mcp.tool()
def set_touchpad_speed(speed: float) -> str:
    """
    Set touchpad pointer speed (-1.0 to 1.0).
    """
    return gnome.set_touchpad_speed(speed)


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
