from pathlib import Path
from typing import List

import pytest

from mcp_server.models import CommandResult
from mcp_server.tools import gnome


def test_normalize_desktop_id_appends_suffix() -> None:
    assert gnome._normalize_desktop_id("org.gnome.Nautilus") == "org.gnome.Nautilus.desktop"
    assert gnome._normalize_desktop_id("org.gnome.Nautilus.desktop") == "org.gnome.Nautilus.desktop"


def test_format_gsettings_list_and_deduplicate() -> None:
    items = ["app.desktop", "app.desktop", "other.desktop"]
    deduped = gnome._deduplicate(items)
    assert deduped == ["app.desktop", "other.desktop"]
    formatted = gnome._format_gsettings_list(deduped)
    assert formatted == "['app.desktop', 'other.desktop']"


def test_bool_value_roundtrip() -> None:
    assert gnome._bool_value(True) == "true"
    assert gnome._bool_value(False) == "false"


def test_resolve_target_prefers_existing_path(tmp_path: Path) -> None:
    file_path = tmp_path / "wallpaper.png"
    file_path.write_text("data")
    resolved = gnome._resolve_target(str(file_path))
    assert resolved == str(file_path.resolve())
    assert gnome._resolve_target("https://example.com") == "https://example.com"


def test_validation_errors() -> None:
    with pytest.raises(ValueError):
        gnome.set_text_scaling(0)
    with pytest.raises(ValueError):
        gnome.set_night_light_temperature(999)
    with pytest.raises(ValueError):
        gnome.set_touchpad_speed(2.0)
    with pytest.raises(ValueError):
        gnome.set_volume_percent(-1)


def test_move_to_trash_missing_path() -> None:
    missing = "/tmp/definitely_missing_file_or_dir"
    with pytest.raises(ValueError):
        gnome.move_to_trash(missing)


def test_command_output_fallback(monkeypatch) -> None:
    def fake_run_command(command):
        return CommandResult(
            success=False,
            command=" ".join(command),
            stdout="",
            stderr="error here",
            returncode=1,
        )

    monkeypatch.setattr(gnome, "run_command", fake_run_command)
    assert gnome._command_output(["failing", "cmd"]) == "error here"


def test_set_color_scheme(monkeypatch) -> None:
    calls: List[list[str]] = []

    def fake_run_command(command):
        calls.append(command)
        return CommandResult(
            success=True,
            command=" ".join(command),
            stdout="",
            stderr="",
            returncode=0,
        )

    monkeypatch.setattr(gnome, "run_command", fake_run_command)
    message = gnome.set_color_scheme("prefer-dark")
    assert "prefer-dark" in message
    assert calls[0][:4] == ["gsettings", "set", "org.gnome.desktop.interface", "color-scheme"]


def test_set_color_scheme_failure(monkeypatch) -> None:
    def fake_run_command(command):
        return CommandResult(
            success=False,
            command=" ".join(command),
            stdout="",
            stderr="boom",
            returncode=1,
        )

    monkeypatch.setattr(gnome, "run_command", fake_run_command)
    with pytest.raises(RuntimeError):
        gnome.set_color_scheme("default")


def test_set_wallpaper_not_found(monkeypatch) -> None:
    with pytest.raises(ValueError):
        gnome.set_wallpaper("/tmp/does-not-exist.png")


def test_set_wallpaper_success(monkeypatch, tmp_path: Path) -> None:
    image = tmp_path / "wall.png"
    image.write_text("data")
    calls: List[list[str]] = []

    def fake_run_command(command):
        calls.append(command)
        return CommandResult(
            success=True,
            command=" ".join(command),
            stdout="",
            stderr="",
            returncode=0,
        )

    monkeypatch.setattr(gnome, "run_command", fake_run_command)
    message = gnome.set_wallpaper(str(image))
    assert "Wallpaper set" in message
    assert len(calls) == 2
    for cmd in calls:
        assert cmd[:3] == ["gsettings", "set", "org.gnome.desktop.background"]


def test_set_text_scaling_success(monkeypatch) -> None:
    calls: List[list[str]] = []

    def fake_run_command(command):
        calls.append(command)
        return CommandResult(
            success=True,
            command=" ".join(command),
            stdout="",
            stderr="",
            returncode=0,
        )

    monkeypatch.setattr(gnome, "run_command", fake_run_command)
    gnome.set_text_scaling(1.25)
    assert calls and calls[0][-1] == "1.25"


def test_set_volume_percent_runtime_error(monkeypatch) -> None:
    def fake_run_command(command):
        return CommandResult(
            success=False,
            command=" ".join(command),
            stdout="",
            stderr="fail",
            returncode=1,
        )

    monkeypatch.setattr(gnome, "run_command", fake_run_command)
    with pytest.raises(RuntimeError):
        gnome.set_volume_percent(50)


def test_get_favorite_apps_success(monkeypatch) -> None:
    def fake_run_command(command):
        return CommandResult(
            success=True,
            command=" ".join(command),
            stdout="['a.desktop', 'b.desktop']",
            stderr="",
            returncode=0,
        )

    monkeypatch.setattr(gnome, "run_command", fake_run_command)
    assert gnome.get_favorite_apps() == ["a.desktop", "b.desktop"]


def test_get_favorite_apps_parse_error(monkeypatch) -> None:
    def fake_run_command(command):
        return CommandResult(
            success=True,
            command=" ".join(command),
            stdout="not-a-list",
            stderr="",
            returncode=0,
        )

    monkeypatch.setattr(gnome, "run_command", fake_run_command)
    with pytest.raises(RuntimeError):
        gnome.get_favorite_apps()


def test_set_favorite_apps_deduplicates(monkeypatch) -> None:
    calls: List[list[str]] = []

    def fake_run_command(command):
        calls.append(command)
        return CommandResult(
            success=True,
            command=" ".join(command),
            stdout="",
            stderr="",
            returncode=0,
        )

    monkeypatch.setattr(gnome, "run_command", fake_run_command)
    gnome.set_favorite_apps(["a.desktop", "a.desktop", "b.desktop"])
    assert calls
    assert calls[0][-1] == "['a.desktop', 'b.desktop']"


def test_add_favorite_app_appends(monkeypatch) -> None:
    captured: List[list[str]] = []

    def fake_get_favorite_apps():
        return ["existing.desktop"]

    def fake_set_favorite_apps(apps):
        captured.append(list(apps))
        return "ok"

    monkeypatch.setattr(gnome, "get_favorite_apps", fake_get_favorite_apps)
    monkeypatch.setattr(gnome, "set_favorite_apps", fake_set_favorite_apps)
    result = gnome.add_favorite_app("new.desktop")
    assert result == ["existing.desktop", "new.desktop"]
    assert captured[-1] == ["existing.desktop", "new.desktop"]


def test_move_to_trash_success(monkeypatch, tmp_path: Path) -> None:
    file_path = tmp_path / "file.txt"
    file_path.write_text("content")
    calls: List[list[str]] = []

    def fake_run_command(command):
        calls.append(command)
        return CommandResult(
            success=True,
            command=" ".join(command),
            stdout="",
            stderr="",
            returncode=0,
        )

    monkeypatch.setattr(gnome, "run_command", fake_run_command)
    message = gnome.move_to_trash(str(file_path))
    assert "Moved" in message
    assert calls and calls[0][0:2] == ["gio", "trash"]


def test_read_os_release(monkeypatch) -> None:
    class FakePath:
        def __init__(self, path: str) -> None:
            self.path = path

        def exists(self) -> bool:
            return True

        def read_text(self) -> str:
            return 'NAME="Fedora"\nVERSION="40"\n'

    monkeypatch.setattr(gnome, "Path", FakePath)
    data = gnome._read_os_release()
    assert data["NAME"] == "Fedora"
    assert data["VERSION"] == "40"


def test_set_gtk_and_icon_theme(monkeypatch) -> None:
    calls: List[list[str]] = []

    def fake_run_command(command):
        calls.append(command)
        return CommandResult(
            success=True,
            command=" ".join(command),
            stdout="",
            stderr="",
            returncode=0,
        )

    monkeypatch.setattr(gnome, "run_command", fake_run_command)
    gnome.set_gtk_theme("Adwaita")
    gnome.set_icon_theme("Papirus")
    assert calls[0][:3] == ["gsettings", "set", "org.gnome.desktop.interface"]
    assert "gtk-theme" in calls[0]
    assert "icon-theme" in calls[1]


def test_set_night_light_toggle_failure(monkeypatch) -> None:
    def fake_run_command(command):
        return CommandResult(
            success=False,
            command=" ".join(command),
            stdout="",
            stderr="fail",
            returncode=1,
        )

    monkeypatch.setattr(gnome, "run_command", fake_run_command)
    with pytest.raises(RuntimeError):
        gnome.set_night_light(True)


def test_set_night_light_temperature_success(monkeypatch) -> None:
    calls: List[list[str]] = []

    def fake_run_command(command):
        calls.append(command)
        return CommandResult(
            success=True,
            command=" ".join(command),
            stdout="",
            stderr="",
            returncode=0,
        )

    monkeypatch.setattr(gnome, "run_command", fake_run_command)
    message = gnome.set_night_light_temperature(4000)
    assert "4000" in message
    assert calls and calls[0][-1] == "4000"


def test_set_night_light_schedule_range(monkeypatch) -> None:
    with pytest.raises(ValueError):
        gnome.set_night_light_schedule(-1, 10)
    with pytest.raises(ValueError):
        gnome.set_night_light_schedule(1, 25)


def test_set_night_light_schedule_success(monkeypatch) -> None:
    calls: List[list[str]] = []

    def fake_run_command(command):
        calls.append(command)
        return CommandResult(
            success=True,
            command=" ".join(command),
            stdout="",
            stderr="",
            returncode=0,
        )

    monkeypatch.setattr(gnome, "run_command", fake_run_command)
    gnome.set_night_light_schedule(20, 6)
    assert calls[0][-1] == "false"
    assert calls[1][-1] == "20"
    assert calls[2][-1] == "6"


def test_set_night_light_schedule_automatic(monkeypatch) -> None:
    calls: List[list[str]] = []

    def fake_run_command(command):
        calls.append(command)
        return CommandResult(
            success=True,
            command=" ".join(command),
            stdout="",
            stderr="",
            returncode=0,
        )

    monkeypatch.setattr(gnome, "run_command", fake_run_command)
    gnome.set_night_light_schedule_automatic(True)
    assert calls and calls[0][-1] == "true"


def test_network_controls(monkeypatch) -> None:
    calls: List[list[str]] = []

    def fake_run_command(command):
        calls.append(command)
        return CommandResult(
            success=True,
            command=" ".join(command),
            stdout="",
            stderr="",
            returncode=0,
        )

    monkeypatch.setattr(gnome, "run_command", fake_run_command)
    gnome.set_wifi_enabled(True)
    gnome.set_bluetooth_enabled(False)
    gnome.set_networking_enabled(True)
    gnome.set_airplane_mode(True)
    assert ["nmcli", "radio", "wifi", "on"] in calls
    assert ["bluetoothctl", "--timeout", "5", "power", "off"] in calls
    assert ["nmcli", "networking", "on"] in calls
    assert ["nmcli", "radio", "all", "off"] in calls


def test_power_and_media_controls(monkeypatch) -> None:
    calls: List[list[str]] = []

    def fake_run_command(command):
        calls.append(command)
        return CommandResult(
            success=True,
            command=" ".join(command),
            stdout="",
            stderr="",
            returncode=0,
        )

    monkeypatch.setattr(gnome, "run_command", fake_run_command)
    gnome.set_power_profile("balanced")
    gnome.media_control("next")
    assert ["powerprofilesctl", "set", "balanced"] in calls
    assert ["playerctl", "next"] in calls


def test_lock_and_logout(monkeypatch) -> None:
    calls: List[list[str]] = []

    def fake_run_command(command):
        calls.append(command)
        return CommandResult(
            success=True,
            command=" ".join(command),
            stdout="",
            stderr="",
            returncode=0,
        )

    monkeypatch.setattr(gnome, "run_command", fake_run_command)
    gnome.lock_screen()
    gnome.logout_session()
    assert any(cmd[0] == "dbus-send" for cmd in calls)
    assert ["gnome-session-quit", "--no-prompt"] in calls


def test_brightness_adjustment_failure(monkeypatch) -> None:
    def fake_run_command(command):
        return CommandResult(
            success=False,
            command=" ".join(command),
            stdout="",
            stderr="boom",
            returncode=1,
        )

    monkeypatch.setattr(gnome, "run_command", fake_run_command)
    with pytest.raises(RuntimeError):
        gnome.brightness_step_up()


def test_open_with_default_resolves_path(monkeypatch, tmp_path: Path) -> None:
    target = tmp_path / "file.txt"
    target.write_text("hi")
    calls: List[list[str]] = []

    def fake_run_command(command):
        calls.append(command)
        return CommandResult(
            success=True,
            command=" ".join(command),
            stdout="",
            stderr="",
            returncode=0,
        )

    monkeypatch.setattr(gnome, "run_command", fake_run_command)
    gnome.open_with_default(str(target))
    assert calls and calls[0][:2] == ["gio", "open"]
    assert calls[0][-1] == str(target.resolve())


def test_command_output_success(monkeypatch) -> None:
    def fake_run_command(command):
        return CommandResult(
            success=True,
            command=" ".join(command),
            stdout="ok",
            stderr="",
            returncode=0,
        )

    monkeypatch.setattr(gnome, "run_command", fake_run_command)
    assert gnome._command_output(["echo", "ok"]) == "ok"


def test_list_applications_reads_desktop_files(monkeypatch, tmp_path: Path) -> None:
    base = tmp_path / "apps"
    base.mkdir()
    desktop = base / "demo.desktop"
    desktop.write_text("[Desktop Entry]\nName=Demo\nExec=/usr/bin/demo\n")

    monkeypatch.setattr(gnome, "DESKTOP_PATHS", [base])
    apps = gnome.list_applications()
    assert len(apps) == 1
    assert apps[0].desktop_id == "demo.desktop"
    assert apps[0].name == "Demo"


def test_touchpad_controls(monkeypatch) -> None:
    calls: List[list[str]] = []

    def fake_run_command(command):
        calls.append(command)
        return CommandResult(
            success=True,
            command=" ".join(command),
            stdout="",
            stderr="",
            returncode=0,
        )

    monkeypatch.setattr(gnome, "run_command", fake_run_command)
    gnome.set_tap_to_click(True)
    gnome.set_natural_scroll(False)
    gnome.set_touchpad_speed(0.5)
    assert ["gsettings", "set", "org.gnome.desktop.peripherals.touchpad", "tap-to-click", "true"] in calls
    assert ["gsettings", "set", "org.gnome.desktop.peripherals.touchpad", "natural-scroll", "false"] in calls
    assert ["gsettings", "set", "org.gnome.desktop.peripherals.touchpad", "speed", "0.5"] in calls


def test_touchpad_speed_out_of_range(monkeypatch) -> None:
    with pytest.raises(ValueError):
        gnome.set_touchpad_speed(-2.0)
    with pytest.raises(ValueError):
        gnome.set_touchpad_speed(2.0)


def test_volume_percent_success(monkeypatch) -> None:
    calls: List[list[str]] = []

    def fake_run_command(command):
        calls.append(command)
        return CommandResult(
            success=True,
            command=" ".join(command),
            stdout="",
            stderr="",
            returncode=0,
        )

    monkeypatch.setattr(gnome, "run_command", fake_run_command)
    gnome.set_volume_percent(42)
    assert ["pactl", "set-sink-volume", "@DEFAULT_SINK@", "42%"] in calls


def test_shutdown_and_reboot(monkeypatch) -> None:
    calls: List[list[str]] = []

    def fake_run_command(command):
        calls.append(command)
        return CommandResult(
            success=True,
            command=" ".join(command),
            stdout="",
            stderr="",
            returncode=0,
        )

    monkeypatch.setattr(gnome, "run_command", fake_run_command)
    gnome.shutdown_system()
    gnome.reboot_system()
    assert ["gnome-session-quit", "--power-off", "--no-prompt"] in calls
    assert ["gnome-session-quit", "--reboot", "--no-prompt"] in calls


def test_send_notification_and_clipboard(monkeypatch) -> None:
    calls: List[list[str]] = []

    def fake_run_command(command):
        calls.append(command)
        # Return content when pasting
        stdout = "pasted" if command[:2] == ["wl-paste"] else ""
        return CommandResult(
            success=True,
            command=" ".join(command),
            stdout=stdout,
            stderr="",
            returncode=0,
        )

    monkeypatch.setattr(gnome, "run_command", fake_run_command)
    gnome.send_notification("Title", "Body", "low")
    gnome.copy_to_clipboard("hello")
    pasted = gnome.paste_from_clipboard()
    assert ["notify-send", "-u", "low", "Title", "Body"] in calls
    assert ["wl-copy", "hello"] in calls
    assert ["wl-paste"] in calls
    assert pasted == "pasted"


def test_send_notification_failure(monkeypatch) -> None:
    def fake_run_command(command):
        return CommandResult(
            success=False,
            command=" ".join(command),
            stdout="",
            stderr="fail",
            returncode=1,
        )

    monkeypatch.setattr(gnome, "run_command", fake_run_command)
    with pytest.raises(RuntimeError):
        gnome.send_notification("Title")
