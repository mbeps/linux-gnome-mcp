from __future__ import annotations

import ast
import configparser
from pathlib import Path
from typing import Iterable, Literal, Optional, Sequence

from mcp_server.models import ApplicationInfo, SystemDetails
from mcp_server.utils.logger import configure_logging
from mcp_server.utils.shell import run_command

logger = configure_logging(__name__)

# Common search locations for .desktop entries
DESKTOP_PATHS = [
    Path("/usr/share/applications"),
    Path.home() / ".local/share/applications",
    Path("/var/lib/snapd/desktop/applications"),
]


def set_color_scheme(preference: Literal["default", "prefer-dark"]) -> str:
    """
    Toggle GNOME's color scheme using gsettings.
    """
    result = run_command(
        ["gsettings", "set", "org.gnome.desktop.interface", "color-scheme", preference]
    )
    if not result.success:
        raise RuntimeError(f"Failed to set color scheme: {result.stderr or result.stdout}")
    return f"Color scheme set to {preference}."


def set_wallpaper_mode(
    option: Literal["none", "wallpaper", "centered", "scaled", "stretched", "zoom", "spanned"]
) -> str:
    """
    Update how the wallpaper is rendered (zoom, centered, spanned, etc.).
    """
    _gsettings_set("org.gnome.desktop.background", "picture-options", option)
    return f"Wallpaper rendering set to {option}."


def set_wallpaper(image_path: str) -> str:
    """
    Update wallpaper for both light and dark keys to keep them in sync.
    """
    resolved = Path(image_path).expanduser().resolve()
    if not resolved.is_file():
        raise ValueError(f"Image not found at {resolved}")

    uri = resolved.as_uri()
    schema = "org.gnome.desktop.background"
    for key in ("picture-uri", "picture-uri-dark"):
        result = run_command(["gsettings", "set", schema, key, uri])
        if not result.success:
            raise RuntimeError(
                f"Failed to set wallpaper ({key}): {result.stderr or result.stdout}"
            )
    return f"Wallpaper set to {uri} for light and dark modes."


def set_gtk_theme(theme: str) -> str:
    """
    Set the GTK theme for legacy/non-libadwaita applications.
    """
    _gsettings_set("org.gnome.desktop.interface", "gtk-theme", theme)
    return f"GTK theme set to {theme}."


def set_icon_theme(icon_theme: str) -> str:
    """
    Set the icon theme.
    """
    _gsettings_set("org.gnome.desktop.interface", "icon-theme", icon_theme)
    return f"Icon theme set to {icon_theme}."


def set_font(
    font_type: Literal["interface", "monospace", "document"], font_value: str
) -> str:
    """
    Update GNOME font preferences (interface, monospace, or document).
    """
    key = {
        "interface": "font-name",
        "monospace": "monospace-font-name",
        "document": "document-font-name",
    }[font_type]
    _gsettings_set("org.gnome.desktop.interface", key, font_value)
    return f"Set {font_type} font to {font_value}."


def set_text_scaling(factor: float) -> str:
    """
    Adjust the global text scaling factor (commonly for HiDPI displays).
    """
    if factor <= 0:
        raise ValueError("Scaling factor must be greater than zero.")
    _gsettings_set("org.gnome.desktop.interface", "text-scaling-factor", str(factor))
    return f"Text scaling factor set to {factor}."


def set_night_light(enabled: bool) -> str:
    """
    Enable or disable Night Light.
    """
    value = "true" if enabled else "false"
    result = run_command(
        [
            "gsettings",
            "set",
            "org.gnome.settings-daemon.plugins.color",
            "night-light-enabled",
            value,
        ]
    )
    if not result.success:
        raise RuntimeError(
            f"Failed to update Night Light: {result.stderr or result.stdout}"
        )
    return f"Night Light set to {enabled}."


def set_night_light_temperature(kelvin: int) -> str:
    """
    Configure the Night Light temperature in Kelvin.
    """
    if kelvin < 1000 or kelvin > 10000:
        raise ValueError("Night Light temperature should be between 1000 and 10000 Kelvin.")
    _gsettings_set("org.gnome.settings-daemon.plugins.color", "night-light-temperature", str(kelvin))
    return f"Night Light temperature set to {kelvin}K."


def set_night_light_schedule_automatic(enabled: bool) -> str:
    """
    Toggle automatic Night Light scheduling.
    """
    _gsettings_set(
        "org.gnome.settings-daemon.plugins.color",
        "night-light-schedule-automatic",
        _bool_value(enabled),
    )
    return f"Night Light automatic scheduling set to {enabled}."


def set_night_light_schedule(start_hour: float, end_hour: float) -> str:
    """
    Set a manual Night Light schedule in 24-hour time.
    """
    for value in (start_hour, end_hour):
        if value < 0 or value > 24:
            raise ValueError("Night Light schedule hours must be between 0 and 24.")

    schema = "org.gnome.settings-daemon.plugins.color"
    _gsettings_set(schema, "night-light-schedule-automatic", "false")
    _gsettings_set(schema, "night-light-schedule-from", str(start_hour))
    _gsettings_set(schema, "night-light-schedule-to", str(end_hour))
    return f"Night Light schedule set from {start_hour} to {end_hour}."


def get_system_details() -> SystemDetails:
    """
    Collect basic system information (kernel, OS, uptime, memory, storage).
    """
    os_info = _read_os_release()
    return SystemDetails(
        kernel_version=_command_output(["uname", "-r"]),
        os_name=os_info.get("NAME", "Unknown"),
        os_version=os_info.get("VERSION", os_info.get("VERSION_ID", "Unknown")),
        uptime=_command_output(["uptime", "-p"]),
        memory=_command_output(["free", "-h"]),
        storage=_command_output(["lsblk", "-o", "NAME,SIZE,TYPE,MOUNTPOINT"]),
    )


def list_applications(limit: int = 50) -> list[ApplicationInfo]:
    """
    Discover installed applications from desktop entry locations.
    """
    applications: dict[str, ApplicationInfo] = {}
    for base in DESKTOP_PATHS:
        if not base.exists():
            continue
        for entry in _iter_desktop_files(base):
            if 0 < limit <= len(applications):
                break
            info = _parse_desktop_entry(entry, source=base)
            if info and info.desktop_id not in applications:
                applications[info.desktop_id] = info

    sorted_apps = sorted(
        applications.values(),
        key=lambda app: (app.name or app.desktop_id).lower(),
    )
    if limit > 0:
        return sorted_apps[:limit]
    return sorted_apps


def launch_application(desktop_id: str) -> str:
    """
    Launch an application using gtk-launch.
    """
    normalized = _normalize_desktop_id(desktop_id)
    result = run_command(["gtk-launch", normalized])
    if not result.success:
        raise RuntimeError(
            f"Failed to launch {normalized}: {result.stderr or result.stdout}"
        )
    return f"Launched {normalized}."


def get_favorite_apps() -> list[str]:
    """
    Retrieve the current GNOME Shell favorites list.
    """
    raw = _gsettings_get("org.gnome.shell", "favorite-apps")
    try:
        parsed = ast.literal_eval(raw)
        return [str(item) for item in parsed if isinstance(item, str)]
    except (ValueError, SyntaxError):
        raise RuntimeError(f"Unable to parse favorite apps from: {raw}")


def set_favorite_apps(apps: Sequence[str]) -> str:
    """
    Overwrite the GNOME Shell favorites list.
    """
    normalized = _deduplicate([_normalize_desktop_id(app) for app in apps])
    payload = _format_gsettings_list(normalized)
    _gsettings_set("org.gnome.shell", "favorite-apps", payload)
    return f"Updated favorites with {len(normalized)} entries."


def add_favorite_app(desktop_id: str) -> list[str]:
    """
    Append a desktop id to favorites if not already present.
    """
    favorites = get_favorite_apps()
    normalized = _normalize_desktop_id(desktop_id)
    if normalized not in favorites:
        favorites.append(normalized)
        set_favorite_apps(favorites)
    return favorites


def shutdown_system() -> str:
    """
    Request a system shutdown without prompting.
    """
    result = run_command(["gnome-session-quit", "--power-off", "--no-prompt"])
    if not result.success:
        raise RuntimeError(f"Failed to initiate shutdown: {result.stderr or result.stdout}")
    return "Shutdown initiated."


def reboot_system() -> str:
    """
    Request a system reboot without prompting.
    """
    result = run_command(["gnome-session-quit", "--reboot", "--no-prompt"])
    if not result.success:
        raise RuntimeError(f"Failed to initiate reboot: {result.stderr or result.stdout}")
    return "Reboot initiated."


def set_wifi_enabled(enabled: bool) -> str:
    """
    Turn Wi-Fi on or off via nmcli radio.
    """
    state = "on" if enabled else "off"
    result = run_command(["nmcli", "radio", "wifi", state])
    if not result.success:
        raise RuntimeError(f"Failed to set Wi-Fi {state}: {result.stderr or result.stdout}")
    return f"Wi-Fi turned {state}."


def set_bluetooth_enabled(enabled: bool) -> str:
    """
    Turn Bluetooth on or off via bluetoothctl.
    """
    state = "on" if enabled else "off"
    result = run_command(["bluetoothctl", "--timeout", "5", "power", state])
    if not result.success:
        raise RuntimeError(f"Failed to set Bluetooth {state}: {result.stderr or result.stdout}")
    return f"Bluetooth turned {state}."


def set_networking_enabled(enabled: bool) -> str:
    """
    Enable or disable all networking (affects wired and Wi-Fi) via nmcli.
    """
    state = "on" if enabled else "off"
    result = run_command(["nmcli", "networking", state])
    if not result.success:
        raise RuntimeError(f"Failed to set networking {state}: {result.stderr or result.stdout}")
    return f"Networking turned {state}."


def set_airplane_mode(enabled: bool) -> str:
    """
    Toggle airplane mode (turns all radios off/on) via nmcli.
    """
    state = "off" if enabled else "on"
    result = run_command(["nmcli", "radio", "all", state])
    if not result.success:
        raise RuntimeError(f"Failed to toggle airplane mode: {result.stderr or result.stdout}")
    return "Airplane mode enabled." if enabled else "Airplane mode disabled."


def set_power_profile(mode: Literal["power-saver", "balanced", "performance"]) -> str:
    """
    Switch power profile using powerprofilesctl (if available).
    """
    result = run_command(["powerprofilesctl", "set", mode])
    if not result.success:
        raise RuntimeError(f"Failed to set power profile: {result.stderr or result.stdout}")
    return f"Power profile set to {mode}."


def set_volume_percent(volume_percent: int) -> str:
    """
    Set system output volume via pactl.
    """
    if volume_percent < 0 or volume_percent > 150:
        raise ValueError("Volume percent must be between 0 and 150.")

    result = run_command(
        ["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{volume_percent}%"]
    )
    if not result.success:
        raise RuntimeError(
            f"Failed to set volume: {result.stderr or result.stdout}"
        )
    return f"Volume set to {volume_percent}%."


def set_mute_state(action: Literal["toggle", "mute", "unmute"]) -> str:
    """
    Toggle or set mute state on the default sink.
    """
    value = {
        "toggle": "toggle",
        "mute": "1",
        "unmute": "0",
    }[action]
    result = run_command(["pactl", "set-sink-mute", "@DEFAULT_SINK@", value])
    if not result.success:
        raise RuntimeError(f"Failed to update mute state: {result.stderr or result.stdout}")
    return f"Mute state updated with action '{action}'."


def media_control(action: Literal["play-pause", "next", "previous", "stop"]) -> str:
    """
    Control media playback via playerctl.
    """
    result = run_command(["playerctl", action])
    if not result.success:
        raise RuntimeError(
            f"Media command failed: {result.stderr or result.stdout}"
        )
    return f"Executed media action '{action}'."


def lock_screen() -> str:
    """
    Lock the session screen.
    """
    result = run_command(
        [
            "dbus-send",
            "--type=method_call",
            "--dest=org.gnome.ScreenSaver",
            "/org/gnome/ScreenSaver",
            "org.gnome.ScreenSaver.Lock",
        ]
    )
    if not result.success:
        raise RuntimeError(f"Failed to lock screen: {result.stderr or result.stdout}")
    return "Screen locked."


def logout_session() -> str:
    """
    Log out of the current GNOME session without prompting.
    """
    result = run_command(["gnome-session-quit", "--no-prompt"])
    if not result.success:
        raise RuntimeError(f"Failed to log out: {result.stderr or result.stdout}")
    return "Logout initiated."


def open_with_default(target: str) -> str:
    """
    Open a file path or URL with the default handler via gio.
    """
    resolved = _resolve_target(target)
    result = run_command(["gio", "open", resolved])
    if not result.success:
        raise RuntimeError(f"Failed to open {resolved}: {result.stderr or result.stdout}")
    return f"Opened {resolved} with the default application."


def brightness_step_up() -> str:
    """
    Increase screen brightness one step via the Settings Daemon.
    """
    _call_power_method("StepUp")
    return "Increased brightness by one step."


def brightness_step_down() -> str:
    """
    Decrease screen brightness one step via the Settings Daemon.
    """
    _call_power_method("StepDown")
    return "Decreased brightness by one step."


def move_to_trash(path: str) -> str:
    """
    Move a file or directory to the Trash using gio.
    """
    resolved = Path(path).expanduser().resolve()
    if not resolved.exists():
        raise ValueError(f"Path does not exist: {resolved}")

    result = run_command(["gio", "trash", str(resolved)])
    if not result.success:
        raise RuntimeError(f"Failed to trash {resolved}: {result.stderr or result.stdout}")
    return f"Moved {resolved} to Trash."


def empty_trash() -> str:
    """
    Empty the Trash using gio.
    """
    result = run_command(["gio", "trash", "--empty"])
    if not result.success:
        raise RuntimeError(f"Failed to empty Trash: {result.stderr or result.stdout}")
    return "Trash emptied."


def send_notification(
    summary: str, body: Optional[str] = None, urgency: Literal["low", "normal", "critical"] = "normal"
) -> str:
    """
    Display a desktop notification via notify-send.
    """
    command = ["notify-send"]
    if urgency != "normal":
        command.extend(["-u", urgency])
    command.append(summary)
    if body:
        command.append(body)

    result = run_command(command)
    if not result.success:
        raise RuntimeError(f"Failed to send notification: {result.stderr or result.stdout}")
    return "Notification sent."


def copy_to_clipboard(text: str) -> str:
    """
    Copy plain text to the clipboard using wl-copy.
    """
    result = run_command(["wl-copy", text])
    if not result.success:
        raise RuntimeError(f"Failed to copy to clipboard: {result.stderr or result.stdout}")
    return "Copied text to clipboard."


def paste_from_clipboard() -> str:
    """
    Retrieve clipboard contents using wl-paste.
    """
    result = run_command(["wl-paste"])
    if not result.success:
        raise RuntimeError(f"Failed to read clipboard: {result.stderr or result.stdout}")
    return result.stdout


def set_tap_to_click(enabled: bool) -> str:
    """
    Enable or disable touchpad tap-to-click.
    """
    _gsettings_set("org.gnome.desktop.peripherals.touchpad", "tap-to-click", _bool_value(enabled))
    return f"Tap-to-click set to {enabled}."


def set_natural_scroll(enabled: bool) -> str:
    """
    Enable or disable natural scrolling for the touchpad.
    """
    _gsettings_set("org.gnome.desktop.peripherals.touchpad", "natural-scroll", _bool_value(enabled))
    return f"Natural scrolling set to {enabled}."


def set_touchpad_speed(speed: float) -> str:
    """
    Set touchpad pointer speed (-1.0 to 1.0).
    """
    if speed < -1.0 or speed > 1.0:
        raise ValueError("Touchpad speed must be between -1.0 and 1.0.")
    _gsettings_set("org.gnome.desktop.peripherals.touchpad", "speed", str(speed))
    return f"Touchpad speed set to {speed}."


def _command_output(command: Sequence[str]) -> str:
    result = run_command(command)
    if result.success:
        return result.stdout
    logger.warning("Command failed", extra={"cmd": result.command, "stderr": result.stderr})
    return result.stderr or result.stdout or "Unavailable"


def _resolve_target(target: str) -> str:
    path = Path(target).expanduser()
    if path.exists():
        return str(path.resolve())
    return target


def _iter_desktop_files(base: Path) -> Iterable[Path]:
    return base.rglob("*.desktop")


def _parse_desktop_entry(path: Path, source: Path) -> Optional[ApplicationInfo]:
    parser = configparser.ConfigParser(interpolation=None)
    parser.optionxform = str  # preserve case
    try:
        parser.read(path)
    except (configparser.Error, OSError):
        logger.warning("Failed to read desktop file", extra={"path": str(path)})
        return None

    if "Desktop Entry" not in parser:
        return None

    entry = parser["Desktop Entry"]
    name = entry.get("Name")
    exec_cmd = entry.get("Exec")
    desktop_id = path.name

    return ApplicationInfo(
        desktop_id=desktop_id, name=name, exec_cmd=exec_cmd, source=str(source)
    )


def _normalize_desktop_id(desktop_id: str) -> str:
    desktop_id = desktop_id.strip()
    if not desktop_id.endswith(".desktop"):
        return f"{desktop_id}.desktop"
    return desktop_id


def _format_gsettings_list(values: Sequence[str]) -> str:
    return "[" + ", ".join(f"'{value}'" for value in values) + "]"


def _deduplicate(items: Sequence[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def _gsettings_set(schema: str, key: str, value: str) -> None:
    result = run_command(["gsettings", "set", schema, key, value])
    if not result.success:
        raise RuntimeError(
            f"gsettings set failed ({schema} {key}): {result.stderr or result.stdout}"
        )


def _gsettings_get(schema: str, key: str) -> str:
    result = run_command(["gsettings", "get", schema, key])
    if not result.success:
        raise RuntimeError(
            f"gsettings get failed ({schema} {key}): {result.stderr or result.stdout}"
        )
    return result.stdout


def _read_os_release() -> dict[str, str]:
    path = Path("/etc/os-release")
    if not path.exists():
        return {}

    data: dict[str, str] = {}
    for line in path.read_text().splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        data[key.strip()] = value.strip().strip('"')
    return data


def _call_power_method(method: str) -> None:
    result = run_command(
        [
            "gdbus",
            "call",
            "--session",
            "--dest",
            "org.gnome.SettingsDaemon.Power",
            "--object-path",
            "/org/gnome/SettingsDaemon/Power",
            "--method",
            f"org.gnome.SettingsDaemon.Power.Screen.{method}",
        ]
    )
    if not result.success:
        raise RuntimeError(f"Brightness adjustment failed: {result.stderr or result.stdout}")


def _bool_value(value: bool) -> str:
    return "true" if value else "false"
