from __future__ import annotations

import configparser
from pathlib import Path
from typing import Iterable, Literal, Optional

from mcp_server.models import ApplicationInfo
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


def open_with_default(target: str) -> str:
    """
    Open a file path or URL with the default handler via gio.
    """
    resolved = _resolve_target(target)
    result = run_command(["gio", "open", resolved])
    if not result.success:
        raise RuntimeError(f"Failed to open {resolved}: {result.stderr or result.stdout}")
    return f"Opened {resolved} with the default application."


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
