from logging import Logger
from typing import Literal, Optional

from mcp.server.fastmcp import FastMCP

from mcp_server.models import AnalysisResult, ApplicationInfo, SystemDetails, SystemMetrics
from mcp_server.tools import gnome
from mcp_server.tools.system import calculate_health
from mcp_server.utils.logger import configure_logging

mcp: FastMCP = FastMCP("Linux-GNOME-Automations", dependencies=["pydantic"])
logger: Logger = configure_logging("mcp_server.main")


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


@mcp.tool()
def set_color_scheme(preference: Literal["default", "prefer-dark"]) -> str:
    """Switch between GNOME light and dark color schemes.

    Args:
        preference: ``"default"`` tracks system style; ``"prefer-dark"`` forces dark mode.

    Returns:
        Confirmation string from the GNOME tooling layer.
    """
    return gnome.set_color_scheme(preference)


@mcp.tool()
def set_wallpaper(image_path: str) -> str:
    """Set the desktop wallpaper for both light and dark modes.

    Args:
        image_path: Absolute or user-relative path to the wallpaper image.

    Returns:
        URI used for GNOME background keys.
    """
    return gnome.set_wallpaper(image_path)


@mcp.tool()
def set_night_light(enabled: bool) -> str:
    """Enable or disable Night Light to adjust display color temperature.

    Args:
        enabled: ``True`` turns Night Light on; ``False`` turns it off.

    Returns:
        Confirmation string from the GNOME tooling layer.
    """
    return gnome.set_night_light(enabled)


@mcp.tool()
def set_wallpaper_mode(
    option: Literal["none", "wallpaper", "centered", "scaled", "stretched", "zoom", "spanned"]
) -> str:
    """Configure how the wallpaper is rendered (zoom, centered, spanned, etc.).

    Args:
        option: Rendering mode supported by GNOME backgrounds.

    Returns:
        Confirmation string from the GNOME tooling layer.
    """
    return gnome.set_wallpaper_mode(option)


@mcp.tool()
def set_gtk_theme(theme: str) -> str:
    """Set the GTK theme for legacy/non-libadwaita applications.

    Args:
        theme: Theme name available to GTK.

    Returns:
        Confirmation string from the GNOME tooling layer.
    """
    return gnome.set_gtk_theme(theme)


@mcp.tool()
def set_icon_theme(icon_theme: str) -> str:
    """Set the icon theme.

    Args:
        icon_theme: Icon theme name discoverable by GNOME.

    Returns:
        Confirmation string from the GNOME tooling layer.
    """
    return gnome.set_icon_theme(icon_theme)


@mcp.tool()
def set_font(font_type: Literal["interface", "monospace", "document"], font_value: str) -> str:
    """Update GNOME interface, monospace, or document font values.

    Args:
        font_type: Font category to change (interface, monospace, document).
        font_value: Font description, e.g. ``'Cantarell 11'``.

    Returns:
        Confirmation string from the GNOME tooling layer.
    """
    return gnome.set_font(font_type, font_value)


@mcp.tool()
def set_text_scaling(factor: float) -> str:
    """Adjust the global text scaling factor.

    Args:
        factor: Scaling multiplier; values greater than 1.0 enlarge text.

    Returns:
        Confirmation string from the GNOME tooling layer.
    """
    return gnome.set_text_scaling(factor)


@mcp.tool()
def set_night_light_temperature(kelvin: int) -> str:
    """Set the Night Light temperature in Kelvin.

    Args:
        kelvin: Color temperature between 1000 and 10000.

    Returns:
        Confirmation string from the GNOME tooling layer.
    """
    return gnome.set_night_light_temperature(kelvin)


@mcp.tool()
def set_night_light_schedule_automatic(enabled: bool) -> str:
    """Enable or disable automatic Night Light scheduling.

    Args:
        enabled: ``True`` follows sunrise/sunset; ``False`` disables auto scheduling.

    Returns:
        Confirmation string from the GNOME tooling layer.
    """
    return gnome.set_night_light_schedule_automatic(enabled)


@mcp.tool()
def set_night_light_schedule(start_hour: float, end_hour: float) -> str:
    """Define a manual Night Light schedule (24h format).

    Args:
        start_hour: Start of the warm color period (0-24).
        end_hour: End of the warm color period (0-24).

    Returns:
        Confirmation string from the GNOME tooling layer.
    """
    return gnome.set_night_light_schedule(start_hour, end_hour)


@mcp.tool()
def list_applications(limit: int = 50) -> list[ApplicationInfo]:
    """List installed applications discovered from .desktop files.

    Args:
        limit: Max number of applications to return; ``<=0`` returns all.

    Returns:
        Sorted application metadata.
    """
    return gnome.list_applications(limit=limit)


@mcp.tool()
def launch_application(desktop_id: str) -> str:
    """Launch an application by its desktop identifier using gtk-launch.

    Args:
        desktop_id: Desktop ID with or without the ``.desktop`` suffix.

    Returns:
        Confirmation string from the GNOME tooling layer.
    """
    return gnome.launch_application(desktop_id)


@mcp.tool()
def get_favorite_apps() -> list[str]:
    """Return the current GNOME Shell favorite applications list.

    Returns:
        Desktop IDs stored in GNOME favorites.
    """
    return gnome.get_favorite_apps()


@mcp.tool()
def set_favorite_apps(apps: list[str]) -> str:
    """Overwrite the GNOME favorites list with the provided entries.

    Args:
        apps: Desktop IDs to store; duplicates are removed.

    Returns:
        Confirmation string from the GNOME tooling layer.
    """
    return gnome.set_favorite_apps(apps)


@mcp.tool()
def add_favorite_app(desktop_id: str) -> list[str]:
    """Add a desktop id to the GNOME favorites list if not already present.

    Args:
        desktop_id: Identifier to add to favorites.

    Returns:
        Updated favorites list.
    """
    return gnome.add_favorite_app(desktop_id)


@mcp.tool()
def shutdown_system() -> str:
    """Initiate a system shutdown without prompting.

    Returns:
        Confirmation string from the GNOME tooling layer.
    """
    return gnome.shutdown_system()


@mcp.tool()
def reboot_system() -> str:
    """Initiate a system reboot without prompting.

    Returns:
        Confirmation string from the GNOME tooling layer.
    """
    return gnome.reboot_system()


@mcp.tool()
def get_system_details() -> SystemDetails:
    """Return basic system information (kernel, OS, uptime, memory, storage).

    Returns:
        Snapshot of host details from standard CLI tools.
    """
    return gnome.get_system_details()


@mcp.tool()
def set_wifi_enabled(enabled: bool) -> str:
    """Turn Wi-Fi on or off via nmcli.

    Args:
        enabled: ``True`` enables Wi-Fi; ``False`` disables it.

    Returns:
        Confirmation string from the GNOME tooling layer.
    """
    return gnome.set_wifi_enabled(enabled)


@mcp.tool()
def set_bluetooth_enabled(enabled: bool) -> str:
    """Turn Bluetooth on or off via bluetoothctl.

    Args:
        enabled: ``True`` powers Bluetooth on; ``False`` powers it off.

    Returns:
        Confirmation string from the GNOME tooling layer.
    """
    return gnome.set_bluetooth_enabled(enabled)


@mcp.tool()
def set_networking_enabled(enabled: bool) -> str:
    """Enable or disable all networking (wired and Wi-Fi) via nmcli.

    Args:
        enabled: ``True`` enables networking; ``False`` disables it.

    Returns:
        Confirmation string from the GNOME tooling layer.
    """
    return gnome.set_networking_enabled(enabled)


@mcp.tool()
def set_airplane_mode(enabled: bool) -> str:
    """Toggle airplane mode (all radios off/on) via nmcli.

    Args:
        enabled: ``True`` turns all radios off; ``False`` turns them on.

    Returns:
        Confirmation string from the GNOME tooling layer.
    """
    return gnome.set_airplane_mode(enabled)


@mcp.tool()
def set_power_profile(mode: Literal["power-saver", "balanced", "performance"]) -> str:
    """Switch between power profiles (power-saver, balanced, performance).

    Args:
        mode: Power profile supported by powerprofilesctl.

    Returns:
        Confirmation string from the GNOME tooling layer.
    """
    return gnome.set_power_profile(mode)


@mcp.tool()
def set_volume(volume_percent: int) -> str:
    """Set system output volume percentage (0-150).

    Args:
        volume_percent: Target volume percent; supports amplification up to 150.

    Returns:
        Confirmation string from the GNOME tooling layer.
    """
    return gnome.set_volume_percent(volume_percent)


@mcp.tool()
def update_mute(action: Literal["toggle", "mute", "unmute"]) -> str:
    """Toggle or force mute state on the default output sink.

    Args:
        action: Mute action to apply (toggle, mute, unmute).

    Returns:
        Confirmation string from the GNOME tooling layer.
    """
    return gnome.set_mute_state(action)


@mcp.tool()
def control_media(action: Literal["play-pause", "next", "previous", "stop"]) -> str:
    """Control media playback through playerctl.

    Args:
        action: Media command to send to the default player.

    Returns:
        Confirmation string from the GNOME tooling layer.
    """
    return gnome.media_control(action)


@mcp.tool()
def lock_screen() -> str:
    """Lock the current GNOME session screen.

    Returns:
        Confirmation string from the GNOME tooling layer.
    """
    return gnome.lock_screen()


@mcp.tool()
def logout_session() -> str:
    """Log out of the current session without prompting.

    Returns:
        Confirmation string from the GNOME tooling layer.
    """
    return gnome.logout_session()


@mcp.tool()
def open_with_default(target: str) -> str:
    """Open a file path or URL with the default GNOME handler via gio.

    Args:
        target: Path or URL to open.

    Returns:
        Confirmation string from the GNOME tooling layer.
    """
    return gnome.open_with_default(target)


@mcp.tool()
def brightness_step_up() -> str:
    """Increase brightness one step via the GNOME Settings Daemon.

    Returns:
        Confirmation string from the GNOME tooling layer.
    """
    return gnome.brightness_step_up()


@mcp.tool()
def brightness_step_down() -> str:
    """Decrease brightness one step via the GNOME Settings Daemon.

    Returns:
        Confirmation string from the GNOME tooling layer.
    """
    return gnome.brightness_step_down()


@mcp.tool()
def move_to_trash(path: str) -> str:
    """Move a file or directory to the Trash via gio.

    Args:
        path: Path to the file or directory to trash.

    Returns:
        Confirmation string from the GNOME tooling layer.
    """
    return gnome.move_to_trash(path)


@mcp.tool()
def empty_trash() -> str:
    """Empty the Trash via gio.

    Returns:
        Confirmation string from the GNOME tooling layer.
    """
    return gnome.empty_trash()


@mcp.tool()
def send_notification(
    summary: str,
    body: Optional[str] = None,
    urgency: Literal["low", "normal", "critical"] = "normal",
) -> str:
    """Send a desktop notification with optional body and urgency.

    Args:
        summary: Notification title.
        body: Optional body text.
        urgency: Urgency hint understood by ``notify-send``.

    Returns:
        Confirmation string from the GNOME tooling layer.
    """
    return gnome.send_notification(summary, body, urgency)


@mcp.tool()
def copy_to_clipboard(text: str) -> str:
    """Copy plain text to the clipboard using wl-copy.

    Args:
        text: Text to copy to the clipboard.

    Returns:
        Confirmation string from the GNOME tooling layer.
    """
    return gnome.copy_to_clipboard(text)


@mcp.tool()
def paste_from_clipboard() -> str:
    """Read text from the clipboard using wl-paste.

    Returns:
        Clipboard contents from the GNOME tooling layer.
    """
    return gnome.paste_from_clipboard()


@mcp.tool()
def set_tap_to_click(enabled: bool) -> str:
    """Enable or disable touchpad tap-to-click.

    Args:
        enabled: ``True`` enables tap-to-click; ``False`` disables it.

    Returns:
        Confirmation string from the GNOME tooling layer.
    """
    return gnome.set_tap_to_click(enabled)


@mcp.tool()
def set_natural_scroll(enabled: bool) -> str:
    """Enable or disable natural scrolling for the touchpad.

    Args:
        enabled: ``True`` enables natural scrolling; ``False`` disables it.

    Returns:
        Confirmation string from the GNOME tooling layer.
    """
    return gnome.set_natural_scroll(enabled)


@mcp.tool()
def set_touchpad_speed(speed: float) -> str:
    """Set touchpad pointer speed (-1.0 to 1.0).

    Args:
        speed: Pointer speed; negative slows, positive accelerates.

    Returns:
        Confirmation string from the GNOME tooling layer.
    """
    return gnome.set_touchpad_speed(speed)


def run() -> None:
    """Entrypoint for launching the MCP server.

    Returns:
        Nothing.
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
