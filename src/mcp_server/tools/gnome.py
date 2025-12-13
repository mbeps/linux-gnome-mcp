from __future__ import annotations

import ast
import configparser
from logging import Logger
from pathlib import Path
from typing import Iterable, Literal, Optional, Sequence

from mcp_server.models import ApplicationInfo, CommandResult, SystemDetails
from mcp_server.utils.logger import configure_logging
from mcp_server.utils.shell import run_command

logger: Logger = configure_logging(__name__)

# Common search locations for .desktop entries
DESKTOP_PATHS: list[Path] = [
    Path("/usr/share/applications"),
    Path.home() / ".local/share/applications",
    Path("/var/lib/snapd/desktop/applications"),
]


def set_color_scheme(preference: Literal["default", "prefer-dark"]) -> str:
    """Update GNOME's color scheme via ``gsettings``.

    Args:
        preference: ``"default"`` follows the system accent; ``"prefer-dark"`` forces dark mode.

    Returns:
        Confirmation message after the schema update.

    Raises:
        RuntimeError: If the underlying ``gsettings`` command fails.

    References:
        - GNOME color-scheme key: https://wiki.gnome.org/Initiatives/Wayland/ColorManagement#User-facing_APIs
    """
    result: CommandResult = run_command(
        ["gsettings", "set", "org.gnome.desktop.interface", "color-scheme", preference]
    )
    if not result.success:
        raise RuntimeError(
            f"Failed to set color scheme: {result.stderr or result.stdout}"
        )
    return f"Color scheme set to {preference}."


def set_wallpaper_mode(
    option: Literal[
        "none", "wallpaper", "centered", "scaled", "stretched", "zoom", "spanned"
    ],
) -> str:
    """Control how the wallpaper is rendered.

    Args:
        option: Rendering strategy supported by ``org.gnome.desktop.background/picture-options``.

    Returns:
        Confirmation message describing the new mode.

    Raises:
        RuntimeError: If the ``gsettings`` write fails.
    """
    _gsettings_set("org.gnome.desktop.background", "picture-options", option)
    return f"Wallpaper rendering set to {option}."


def set_wallpaper(image_path: str) -> str:
    """Update wallpaper for both light and dark variants.

    Args:
        image_path: Path to the image file; ``~`` is expanded and the file must exist.

    Returns:
        URI used for both ``picture-uri`` and ``picture-uri-dark`` keys.

    Raises:
        ValueError: If the provided image cannot be found.
        RuntimeError: If a ``gsettings`` call fails.
    """
    resolved: Path = Path(image_path).expanduser().resolve()
    if not resolved.is_file():
        raise ValueError(f"Image not found at {resolved}")

    uri: str = resolved.as_uri()
    schema: str = "org.gnome.desktop.background"
    for key in ("picture-uri", "picture-uri-dark"):
        result: CommandResult = run_command(["gsettings", "set", schema, key, uri])
        if not result.success:
            raise RuntimeError(
                f"Failed to set wallpaper ({key}): {result.stderr or result.stdout}"
            )
    return f"Wallpaper set to {uri} for light and dark modes."


def set_gtk_theme(theme: str) -> str:
    """Set the GTK theme for legacy/non-libadwaita applications.

    Args:
        theme: GTK theme name available in ``/usr/share/themes`` or ``~/.themes``.

    Returns:
        Confirmation string for the applied theme.

    Raises:
        RuntimeError: If the ``gsettings`` write fails.
    """
    _gsettings_set("org.gnome.desktop.interface", "gtk-theme", theme)
    return f"GTK theme set to {theme}."


def set_icon_theme(icon_theme: str) -> str:
    """Set the icon theme.

    Args:
        icon_theme: Icon theme name discoverable by GNOME.

    Returns:
        Confirmation string for the applied icon theme.

    Raises:
        RuntimeError: If the ``gsettings`` write fails.
    """
    _gsettings_set("org.gnome.desktop.interface", "icon-theme", icon_theme)
    return f"Icon theme set to {icon_theme}."


def set_font(
    font_type: Literal["interface", "monospace", "document"], font_value: str
) -> str:
    """Update GNOME font preferences (interface, monospace, or document).

    Args:
        font_type: Which font category to adjust (interface, monospace, document).
        font_value: Full font spec, e.g. ``'Cantarell 11'``.

    Returns:
        Confirmation of the updated font.

    Raises:
        RuntimeError: If the ``gsettings`` write fails.
    """
    key = {
        "interface": "font-name",
        "monospace": "monospace-font-name",
        "document": "document-font-name",
    }[font_type]
    _gsettings_set("org.gnome.desktop.interface", key, font_value)
    return f"Set {font_type} font to {font_value}."


def set_text_scaling(factor: float) -> str:
    """Adjust the global text scaling factor.

    Args:
        factor: Scaling multiplier; values greater than 1.0 enlarge text.

    Returns:
        Confirmation string with the applied factor.

    Raises:
        ValueError: If ``factor`` is not greater than zero.
        RuntimeError: If the ``gsettings`` write fails.
    """
    if factor <= 0:
        raise ValueError("Scaling factor must be greater than zero.")
    _gsettings_set("org.gnome.desktop.interface", "text-scaling-factor", str(factor))
    return f"Text scaling factor set to {factor}."


def set_night_light(enabled: bool) -> str:
    """Enable or disable Night Light.

    Args:
        enabled: ``True`` turns Night Light on, ``False`` turns it off.

    Returns:
        Confirmation string describing the new state.

    Raises:
        RuntimeError: If the ``gsettings`` call fails.

    References:
        - Night Light schema: https://gitlab.gnome.org/GNOME/gnome-settings-daemon/-/blob/main/plugins/color/gsd-color-plugin.c
    """
    value = "true" if enabled else "false"
    result: CommandResult = run_command(
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
    """Configure the Night Light temperature.

    Args:
        kelvin: Desired color temperature between 1000 and 10000.

    Returns:
        Confirmation string with the applied temperature.

    Raises:
        ValueError: If the temperature is outside the supported range.
        RuntimeError: If the ``gsettings`` write fails.
    """
    if kelvin < 1000 or kelvin > 10000:
        raise ValueError(
            "Night Light temperature should be between 1000 and 10000 Kelvin."
        )
    _gsettings_set(
        "org.gnome.settings-daemon.plugins.color",
        "night-light-temperature",
        str(kelvin),
    )
    return f"Night Light temperature set to {kelvin}K."


def set_night_light_schedule_automatic(enabled: bool) -> str:
    """Toggle automatic Night Light scheduling.

    Args:
        enabled: ``True`` follows location-based sunrise/sunset; ``False`` disables auto scheduling.

    Returns:
        Confirmation string with the new scheduling mode.

    Raises:
        RuntimeError: If the ``gsettings`` write fails.
    """
    _gsettings_set(
        "org.gnome.settings-daemon.plugins.color",
        "night-light-schedule-automatic",
        _bool_value(enabled),
    )
    return f"Night Light automatic scheduling set to {enabled}."


def set_night_light_schedule(start_hour: float, end_hour: float) -> str:
    """Set a manual Night Light schedule in 24-hour time.

    Args:
        start_hour: Start of the warm color period (0-24).
        end_hour: End of the warm color period (0-24).

    Returns:
        Confirmation string describing the schedule.

    Raises:
        ValueError: If either hour is outside the range [0, 24].
        RuntimeError: If any ``gsettings`` write fails.
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
    """Collect basic system information.

    Returns:
        Kernel, OS, uptime, memory, and storage snapshot.

    References:
        - ``lsblk`` usage: https://man7.org/linux/man-pages/man8/lsblk.8.html
    """
    os_info: dict[str, str] = _read_os_release()
    return SystemDetails(
        kernel_version=_command_output(["uname", "-r"]),
        os_name=os_info.get("NAME", "Unknown"),
        os_version=os_info.get("VERSION", os_info.get("VERSION_ID", "Unknown")),
        uptime=_command_output(["uptime", "-p"]),
        memory=_command_output(["free", "-h"]),
        storage=_command_output(["lsblk", "-o", "NAME,SIZE,TYPE,MOUNTPOINT"]),
    )


def list_applications(limit: int = 50) -> list[ApplicationInfo]:
    """Discover installed applications from desktop entry locations.

    Args:
        limit: Maximum number of entries to return; ``<=0`` returns all.

    Returns:
        Sorted list of application metadata.
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

    sorted_apps: list[ApplicationInfo] = sorted(
        applications.values(),
        key=lambda app: (app.name or app.desktop_id).lower(),
    )
    if limit > 0:
        return sorted_apps[:limit]
    return sorted_apps


def launch_application(desktop_id: str) -> str:
    """Launch an application using ``gtk-launch``.

    Args:
        desktop_id: Desktop identifier with or without the ``.desktop`` suffix.

    Returns:
        Confirmation string after attempting launch.

    Raises:
        RuntimeError: If the application fails to start.

    References:
        - gtk-launch: https://developer.gnome.org/gtk3/stable/gtk-launch.html
    """
    normalized: str = _normalize_desktop_id(desktop_id)
    result: CommandResult = run_command(["gtk-launch", normalized])
    if not result.success:
        raise RuntimeError(
            f"Failed to launch {normalized}: {result.stderr or result.stdout}"
        )
    return f"Launched {normalized}."


def get_favorite_apps() -> list[str]:
    """Retrieve the current GNOME Shell favorites list.

    Returns:
        Favorite desktop IDs as stored by GNOME Shell.

    Raises:
        RuntimeError: If favorites cannot be parsed from ``gsettings`` output.
    """
    raw: str = _gsettings_get("org.gnome.shell", "favorite-apps")
    try:
        parsed: list[str] | tuple[str, ...] = ast.literal_eval(raw)
        return [str(item) for item in parsed if isinstance(item, str)]
    except (ValueError, SyntaxError):
        raise RuntimeError(f"Unable to parse favorite apps from: {raw}")


def set_favorite_apps(apps: Sequence[str]) -> str:
    """Overwrite the GNOME Shell favorites list.

    Args:
        apps: Sequence of desktop IDs; duplicates are removed.

    Returns:
        Confirmation including the final favorite count.

    Raises:
        RuntimeError: If the ``gsettings`` write fails.
    """
    normalized: list[str] = _deduplicate([_normalize_desktop_id(app) for app in apps])
    payload: str = _format_gsettings_list(normalized)
    _gsettings_set("org.gnome.shell", "favorite-apps", payload)
    return f"Updated favorites with {len(normalized)} entries."


def add_favorite_app(desktop_id: str) -> list[str]:
    """Append a desktop ID to favorites if not already present.

    Args:
        desktop_id: Identifier of the launcher to add.

    Returns:
        Updated favorites list after mutation.
    """
    favorites: list[str] = get_favorite_apps()
    normalized: str = _normalize_desktop_id(desktop_id)
    if normalized not in favorites:
        favorites.append(normalized)
        set_favorite_apps(favorites)
    return favorites


def shutdown_system() -> str:
    """Request a system shutdown without prompting.

    Returns:
        Confirmation message on successful request submission.

    Raises:
        RuntimeError: If the session manager rejects the command.
    """
    result: CommandResult = run_command(
        ["gnome-session-quit", "--power-off", "--no-prompt"]
    )
    if not result.success:
        raise RuntimeError(
            f"Failed to initiate shutdown: {result.stderr or result.stdout}"
        )
    return "Shutdown initiated."


def reboot_system() -> str:
    """Request a system reboot without prompting.

    Returns:
        Confirmation message on successful request submission.

    Raises:
        RuntimeError: If the session manager rejects the command.
    """
    result: CommandResult = run_command(
        ["gnome-session-quit", "--reboot", "--no-prompt"]
    )
    if not result.success:
        raise RuntimeError(
            f"Failed to initiate reboot: {result.stderr or result.stdout}"
        )
    return "Reboot initiated."


def set_wifi_enabled(enabled: bool) -> str:
    """Turn Wi-Fi on or off via ``nmcli radio``.

    Args:
        enabled: ``True`` to enable, ``False`` to disable.

    Returns:
        Confirmation string describing the new Wi-Fi state.

    Raises:
        RuntimeError: If NetworkManager rejects the change.

    References:
        - nmcli radio: https://networkmanager.dev/docs/api/latest/nmcli.html#nmcli-radio
    """
    state = "on" if enabled else "off"
    result: CommandResult = run_command(["nmcli", "radio", "wifi", state])
    if not result.success:
        raise RuntimeError(
            f"Failed to set Wi-Fi {state}: {result.stderr or result.stdout}"
        )
    return f"Wi-Fi turned {state}."


def set_bluetooth_enabled(enabled: bool) -> str:
    """Turn Bluetooth on or off via ``bluetoothctl``.

    Args:
        enabled: ``True`` to power on, ``False`` to power off.

    Returns:
        Confirmation string describing the new Bluetooth state.

    Raises:
        RuntimeError: If ``bluetoothctl`` returns an error.
    """
    state = "on" if enabled else "off"
    result: CommandResult = run_command(
        ["bluetoothctl", "--timeout", "5", "power", state]
    )
    if not result.success:
        raise RuntimeError(
            f"Failed to set Bluetooth {state}: {result.stderr or result.stdout}"
        )
    return f"Bluetooth turned {state}."


def set_networking_enabled(enabled: bool) -> str:
    """Enable or disable all networking via ``nmcli networking``.

    Args:
        enabled: ``True`` to turn networking on, ``False`` to turn it off.

    Returns:
        Confirmation string describing the new networking state.

    Raises:
        RuntimeError: If NetworkManager rejects the change.
    """
    state = "on" if enabled else "off"
    result: CommandResult = run_command(["nmcli", "networking", state])
    if not result.success:
        raise RuntimeError(
            f"Failed to set networking {state}: {result.stderr or result.stdout}"
        )
    return f"Networking turned {state}."


def set_airplane_mode(enabled: bool) -> str:
    """Toggle airplane mode via ``nmcli radio all``.

    Args:
        enabled: ``True`` disables radios; ``False`` re-enables them.

    Returns:
        Confirmation string describing the radio state.

    Raises:
        RuntimeError: If NetworkManager rejects the change.
    """
    state = "off" if enabled else "on"
    result: CommandResult = run_command(["nmcli", "radio", "all", state])
    if not result.success:
        raise RuntimeError(
            f"Failed to toggle airplane mode: {result.stderr or result.stdout}"
        )
    return "Airplane mode enabled." if enabled else "Airplane mode disabled."


def set_power_profile(mode: Literal["power-saver", "balanced", "performance"]) -> str:
    """Switch power profile using ``powerprofilesctl``.

    Args:
        mode: Target profile supported by the daemon (power-saver, balanced, performance).

    Returns:
        Confirmation string describing the active profile.

    Raises:
        RuntimeError: If ``powerprofilesctl`` returns an error.

    References:
        - Power Profiles daemon: https://gitlab.freedesktop.org/hadess/power-profiles-daemon
    """
    result: CommandResult = run_command(["powerprofilesctl", "set", mode])
    if not result.success:
        raise RuntimeError(
            f"Failed to set power profile: {result.stderr or result.stdout}"
        )
    return f"Power profile set to {mode}."


def set_volume_percent(volume_percent: int) -> str:
    """Set system output volume via ``pactl``.

    Args:
        volume_percent: Desired volume percent; values above 100 may clip audio.

    Returns:
        Confirmation string describing the new volume.

    Raises:
        ValueError: If ``volume_percent`` is outside 0-150.
        RuntimeError: If ``pactl`` fails to update the sink.
    """
    if volume_percent < 0 or volume_percent > 150:
        raise ValueError("Volume percent must be between 0 and 150.")

    result: CommandResult = run_command(
        ["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{volume_percent}%"]
    )
    if not result.success:
        raise RuntimeError(f"Failed to set volume: {result.stderr or result.stdout}")
    return f"Volume set to {volume_percent}%."


def set_mute_state(action: Literal["toggle", "mute", "unmute"]) -> str:
    """Toggle or set mute state on the default sink.

    Args:
        action: Desired mute change (toggle, mute, unmute).

    Returns:
        Confirmation string describing the applied action.

    Raises:
        RuntimeError: If ``pactl`` fails to update the sink mute state.
    """
    value = {
        "toggle": "toggle",
        "mute": "1",
        "unmute": "0",
    }[action]
    result: CommandResult = run_command(
        ["pactl", "set-sink-mute", "@DEFAULT_SINK@", value]
    )
    if not result.success:
        raise RuntimeError(
            f"Failed to update mute state: {result.stderr or result.stdout}"
        )
    return f"Mute state updated with action '{action}'."


def media_control(action: Literal["play-pause", "next", "previous", "stop"]) -> str:
    """Control media playback via ``playerctl``.

    Args:
        action: Media command to execute against the default player.

    Returns:
        Confirmation string describing the executed action.

    Raises:
        RuntimeError: If the player command fails.
    """
    result: CommandResult = run_command(["playerctl", action])
    if not result.success:
        raise RuntimeError(f"Media command failed: {result.stderr or result.stdout}")
    return f"Executed media action '{action}'."


def lock_screen() -> str:
    """Lock the session screen via the GNOME ScreenSaver DBus API.

    Returns:
        Confirmation string once the DBus call succeeds.

    Raises:
        RuntimeError: If the DBus invocation fails.
    """
    result: CommandResult = run_command(
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
    """Log out of the current GNOME session without prompting.

    Returns:
        Confirmation string once logout is requested.

    Raises:
        RuntimeError: If the session manager rejects the request.
    """
    result: CommandResult = run_command(["gnome-session-quit", "--no-prompt"])
    if not result.success:
        raise RuntimeError(f"Failed to log out: {result.stderr or result.stdout}")
    return "Logout initiated."


def open_with_default(target: str) -> str:
    """Open a file path or URL with the default handler via ``gio``.

    Args:
        target: Path or URL to open; filesystem paths are resolved.

    Returns:
        Confirmation string describing the opened target.

    Raises:
        RuntimeError: If ``gio`` fails to open the resource.
    """
    resolved: str = _resolve_target(target)
    result: CommandResult = run_command(["gio", "open", resolved])
    if not result.success:
        raise RuntimeError(
            f"Failed to open {resolved}: {result.stderr or result.stdout}"
        )
    return f"Opened {resolved} with the default application."


def brightness_step_up() -> str:
    """Increase screen brightness one step via the Settings Daemon.

    Returns:
        Confirmation string after the brightness adjustment.

    Raises:
        RuntimeError: If the DBus call fails.
    """
    _call_power_method("StepUp")
    return "Increased brightness by one step."


def brightness_step_down() -> str:
    """Decrease screen brightness one step via the Settings Daemon.

    Returns:
        Confirmation string after the brightness adjustment.

    Raises:
        RuntimeError: If the DBus call fails.
    """
    _call_power_method("StepDown")
    return "Decreased brightness by one step."


def move_to_trash(path: str) -> str:
    """Move a file or directory to the Trash using ``gio``.

    Args:
        path: File or directory to trash; ``~`` is expanded.

    Returns:
        Confirmation string describing the trashed path.

    Raises:
        ValueError: If the path does not exist.
        RuntimeError: If ``gio`` fails to move the item.
    """
    resolved: Path = Path(path).expanduser().resolve()
    if not resolved.exists():
        raise ValueError(f"Path does not exist: {resolved}")

    result: CommandResult = run_command(["gio", "trash", str(resolved)])
    if not result.success:
        raise RuntimeError(
            f"Failed to trash {resolved}: {result.stderr or result.stdout}"
        )
    return f"Moved {resolved} to Trash."


def empty_trash() -> str:
    """Empty the Trash using ``gio``.

    Returns:
        Confirmation string on success.

    Raises:
        RuntimeError: If ``gio`` fails to empty Trash.
    """
    result: CommandResult = run_command(["gio", "trash", "--empty"])
    if not result.success:
        raise RuntimeError(f"Failed to empty Trash: {result.stderr or result.stdout}")
    return "Trash emptied."


def send_notification(
    summary: str,
    body: Optional[str] = None,
    urgency: Literal["low", "normal", "critical"] = "normal",
) -> str:
    """Display a desktop notification via ``notify-send``.

    Args:
        summary: Notification title.
        body: Optional body text for the notification.
        urgency: Notification urgency hint (low, normal, critical).

    Returns:
        Confirmation string after dispatching the notification.

    Raises:
        RuntimeError: If ``notify-send`` fails.

    References:
        - Desktop Notifications spec: https://specifications.freedesktop.org/notification-spec/latest/
    """
    command = ["notify-send"]
    if urgency != "normal":
        command.extend(["-u", urgency])
    command.append(summary)
    if body:
        command.append(body)

    result: CommandResult = run_command(command)
    if not result.success:
        raise RuntimeError(
            f"Failed to send notification: {result.stderr or result.stdout}"
        )
    return "Notification sent."


def copy_to_clipboard(text: str) -> str:
    """Copy plain text to the clipboard using ``wl-copy``.

    Args:
        text: Text to place on the Wayland clipboard.

    Returns:
        Confirmation string after the copy operation.

    Raises:
        RuntimeError: If ``wl-copy`` fails.
    """
    result: CommandResult = run_command(["wl-copy", text])
    if not result.success:
        raise RuntimeError(
            f"Failed to copy to clipboard: {result.stderr or result.stdout}"
        )
    return "Copied text to clipboard."


def paste_from_clipboard() -> str:
    """Retrieve clipboard contents using ``wl-paste``.

    Returns:
        Clipboard contents as returned by ``wl-paste``.

    Raises:
        RuntimeError: If ``wl-paste`` fails.
    """
    result: CommandResult = run_command(["wl-paste"])
    if not result.success:
        raise RuntimeError(
            f"Failed to read clipboard: {result.stderr or result.stdout}"
        )
    return result.stdout


def set_tap_to_click(enabled: bool) -> str:
    """Enable or disable touchpad tap-to-click.

    Args:
        enabled: ``True`` turns tap-to-click on; ``False`` turns it off.

    Returns:
        Confirmation string describing the new state.

    Raises:
        RuntimeError: If the ``gsettings`` write fails.
    """
    _gsettings_set(
        "org.gnome.desktop.peripherals.touchpad", "tap-to-click", _bool_value(enabled)
    )
    return f"Tap-to-click set to {enabled}."


def set_natural_scroll(enabled: bool) -> str:
    """Enable or disable natural scrolling for the touchpad.

    Args:
        enabled: ``True`` enables natural (inverted) scrolling.

    Returns:
        Confirmation string describing the new state.

    Raises:
        RuntimeError: If the ``gsettings`` write fails.
    """
    _gsettings_set(
        "org.gnome.desktop.peripherals.touchpad", "natural-scroll", _bool_value(enabled)
    )
    return f"Natural scrolling set to {enabled}."


def set_touchpad_speed(speed: float) -> str:
    """Set touchpad pointer speed.

    Args:
        speed: Pointer speed between -1.0 (slow) and 1.0 (fast).

    Returns:
        Confirmation string describing the new speed.

    Raises:
        ValueError: If speed falls outside [-1.0, 1.0].
        RuntimeError: If the ``gsettings`` write fails.
    """
    if speed < -1.0 or speed > 1.0:
        raise ValueError("Touchpad speed must be between -1.0 and 1.0.")
    _gsettings_set("org.gnome.desktop.peripherals.touchpad", "speed", str(speed))
    return f"Touchpad speed set to {speed}."


def _command_output(command: Sequence[str]) -> str:
    """Execute a command and return stdout, falling back to stderr on failure.

    Args:
        command: Command to run with arguments.

    Returns:
        Process stdout on success or best-effort error text on failure.
    """
    result: CommandResult = run_command(command)
    if result.success:
        return result.stdout
    logger.warning(
        "Command failed", extra={"cmd": result.command, "stderr": result.stderr}
    )
    return result.stderr or result.stdout or "Unavailable"


def _resolve_target(target: str) -> str:
    """Resolve a filesystem path if it exists.

    Args:
        target: Raw path or URL provided by the caller.

    Returns:
        Absolute path when the target exists locally; otherwise the original input.
    """
    path: Path = Path(target).expanduser()
    if path.exists():
        return str(path.resolve())
    return target


def _iter_desktop_files(base: Path) -> Iterable[Path]:
    """Yield desktop files under the provided directory recursively.

    Args:
        base: Directory to search for ``.desktop`` files.

    Returns:
        Generator over matching paths.
    """
    return base.rglob("*.desktop")


class _CaseSensitiveConfigParser(configparser.ConfigParser):
    """ConfigParser variant that preserves option casing.

    GNOME desktop entries use mixed-case keys that should not be lowercased.
    """

    def optionxform(self, optionstr: str) -> str:
        """Return options unchanged to maintain case sensitivity.

        Args:
            optionstr: Option name from the config file.

        Returns:
            Unmodified option name.
        """
        return optionstr


def _parse_desktop_entry(path: Path, source: Path) -> Optional[ApplicationInfo]:
    """Parse a ``.desktop`` entry into ``ApplicationInfo``.

    Args:
        path: Path to the desktop file.
        source: Base directory where the file was discovered.

    Returns:
        Parsed application metadata or ``None`` when invalid.

    References:
        - Desktop Entry spec: https://specifications.freedesktop.org/desktop-entry-spec/latest/
    """
    parser: configparser.ConfigParser = _CaseSensitiveConfigParser(interpolation=None)
    try:
        parser.read(path)
    except (configparser.Error, OSError):
        logger.warning("Failed to read desktop file", extra={"path": str(path)})
        return None

    if "Desktop Entry" not in parser:
        return None

    entry = parser["Desktop Entry"]
    name: Optional[str] = entry.get("Name")
    exec_cmd: Optional[str] = entry.get("Exec")
    desktop_id: str = path.name

    return ApplicationInfo(
        desktop_id=desktop_id, name=name, exec_cmd=exec_cmd, source=str(source)
    )


def _normalize_desktop_id(desktop_id: str) -> str:
    """Ensure desktop IDs include the ``.desktop`` suffix.

    Args:
        desktop_id: Identifier provided by the caller.

    Returns:
        Normalized identifier ending with ``.desktop``.
    """
    desktop_id = desktop_id.strip()
    if not desktop_id.endswith(".desktop"):
        return f"{desktop_id}.desktop"
    return desktop_id


def _format_gsettings_list(values: Sequence[str]) -> str:
    """Format a Python sequence into the list syntax expected by gsettings.

    Args:
        values: Entries to serialize.

    Returns:
        gsettings-compatible list literal.
    """
    return "[" + ", ".join(f"'{value}'" for value in values) + "]"


def _deduplicate(items: Sequence[str]) -> list[str]:
    """Preserve order while removing duplicate items.

    Args:
        items: Sequence that may contain duplicates.

    Returns:
        Ordered list containing each value once.
    """
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def _gsettings_set(schema: str, key: str, value: str) -> None:
    """Set a gsettings key and raise on failure.

    Args:
        schema: Schema path, e.g. ``org.gnome.desktop.interface``.
        key: Key under the schema to update.
        value: Literal value to set.

    Raises:
        RuntimeError: If the gsettings invocation fails.
    """
    result = run_command(["gsettings", "set", schema, key, value])
    if not result.success:
        raise RuntimeError(
            f"gsettings set failed ({schema} {key}): {result.stderr or result.stdout}"
        )


def _gsettings_get(schema: str, key: str) -> str:
    """Retrieve a gsettings value and raise on failure.

    Args:
        schema: Schema path, e.g. ``org.gnome.shell``.
        key: Key under the schema to read.

    Returns:
        Raw value returned by gsettings.

    Raises:
        RuntimeError: If the gsettings invocation fails.
    """
    result = run_command(["gsettings", "get", schema, key])
    if not result.success:
        raise RuntimeError(
            f"gsettings get failed ({schema} {key}): {result.stderr or result.stdout}"
        )
    return result.stdout


def _read_os_release() -> dict[str, str]:
    """Read ``/etc/os-release`` into a mapping of key/value pairs.

    Returns:
        Parsed OS metadata keys and values.
    """
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
    """Invoke a GNOME Settings Daemon power DBus method by name.

    Args:
        method: Power screen method name such as ``StepUp`` or ``StepDown``.

    Raises:
        RuntimeError: If the DBus call fails.
    """
    result: CommandResult = run_command(
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
        raise RuntimeError(
            f"Brightness adjustment failed: {result.stderr or result.stdout}"
        )


def _bool_value(value: bool) -> str:
    """Return ``"true"`` or ``"false"`` for gsettings-compatible booleans.

    Args:
        value: Boolean value to convert.

    Returns:
        gsettings-compatible boolean string.
    """
    return "true" if value else "false"
