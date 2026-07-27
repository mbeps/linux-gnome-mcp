from typing import List

import pytest

from mcp_server import main
from mcp_server.models import CommandResult, ExtensionInfo
from mcp_server.tools import gnome

SAMPLE_EXTENSIONS_OUTPUT = """blur-my-shell@aunetx
  Name: Blur my Shell
  Description: Adds a blur look to different parts of the GNOME Shell.
  Path: /home/user/.local/share/gnome-shell/extensions/blur-my-shell@aunetx
  URL: https://github.com/aunetx/blur-my-shell
  Version: 72
  Enabled: Yes
  State: ACTIVE

user-theme@gnome-shell-extensions.gcampax.github.com
  Name: User Themes
  Description: Load shell themes from user directory.
  Path: /usr/share/gnome-shell/extensions/user-theme@gnome-shell-extensions.gcampax.github.com
  URL: https://gitlab.gnome.org/GNOME/gnome-shell-extensions
  Version: 50.2
  Enabled: No
  State: INITIALIZED
"""


def test_get_user_extensions_enabled_true(monkeypatch) -> None:
    def fake_run_command(command):
        assert command == ["gsettings", "get", "org.gnome.shell", "disable-user-extensions"]
        return CommandResult(success=True, command=" ".join(command), stdout="false", stderr="", returncode=0)

    monkeypatch.setattr(gnome, "run_command", fake_run_command)
    assert gnome.get_user_extensions_enabled() is True


def test_get_user_extensions_enabled_false(monkeypatch) -> None:
    def fake_run_command(command):
        return CommandResult(success=True, command=" ".join(command), stdout="true", stderr="", returncode=0)

    monkeypatch.setattr(gnome, "run_command", fake_run_command)
    assert gnome.get_user_extensions_enabled() is False


def test_set_user_extensions_enabled(monkeypatch) -> None:
    calls: List[list[str]] = []

    def fake_run_command(command):
        calls.append(command)
        return CommandResult(success=True, command=" ".join(command), stdout="", stderr="", returncode=0)

    monkeypatch.setattr(gnome, "run_command", fake_run_command)

    msg1 = gnome.set_user_extensions_enabled(True)
    assert "enabled" in msg1
    assert calls[0] == ["gsettings", "set", "org.gnome.shell", "disable-user-extensions", "false"]

    msg2 = gnome.set_user_extensions_enabled(False)
    assert "disabled" in msg2
    assert calls[1] == ["gsettings", "set", "org.gnome.shell", "disable-user-extensions", "true"]


def test_verify_user_extensions_enabled_raises(monkeypatch) -> None:
    monkeypatch.setattr(gnome, "get_user_extensions_enabled", lambda: False)
    with pytest.raises(RuntimeError, match="globally disabled"):
        gnome._verify_user_extensions_enabled()


def test_parse_extension_blocks() -> None:
    extensions = gnome._parse_extension_blocks(SAMPLE_EXTENSIONS_OUTPUT)
    assert len(extensions) == 2

    ext1 = extensions[0]
    assert ext1.uuid == "blur-my-shell@aunetx"
    assert ext1.name == "Blur my Shell"
    assert ext1.enabled is True
    assert ext1.state == "ACTIVE"
    assert ext1.version == "72"

    ext2 = extensions[1]
    assert ext2.uuid == "user-theme@gnome-shell-extensions.gcampax.github.com"
    assert ext2.name == "User Themes"
    assert ext2.enabled is False
    assert ext2.state == "INITIALIZED"


def test_list_extensions_success(monkeypatch) -> None:
    monkeypatch.setattr(gnome, "get_user_extensions_enabled", lambda: True)

    def fake_run_command(command):
        if command == ["gnome-extensions", "list"]:
            return CommandResult(
                success=True,
                command=" ".join(command),
                stdout="blur-my-shell@aunetx\nuser-theme@gnome-shell-extensions.gcampax.github.com",
                stderr="",
                returncode=0,
            )
        assert command == ["gnome-extensions", "list", "-d"]
        return CommandResult(
            success=True,
            command=" ".join(command),
            stdout=SAMPLE_EXTENSIONS_OUTPUT,
            stderr="",
            returncode=0,
        )

    monkeypatch.setattr(gnome, "run_command", fake_run_command)
    exts = gnome.list_extensions()
    assert len(exts) == 2
    assert exts[0].uuid == "blur-my-shell@aunetx"


def test_list_extensions_globally_disabled(monkeypatch) -> None:
    monkeypatch.setattr(gnome, "get_user_extensions_enabled", lambda: False)
    with pytest.raises(RuntimeError, match="globally disabled"):
        gnome.list_extensions()


def test_get_extension_info_success(monkeypatch) -> None:
    monkeypatch.setattr(gnome, "get_user_extensions_enabled", lambda: True)

    def fake_run_command(command):
        assert command == ["gnome-extensions", "info", "blur-my-shell@aunetx"]
        return CommandResult(
            success=True,
            command=" ".join(command),
            stdout=SAMPLE_EXTENSIONS_OUTPUT.split("\n\n")[0],
            stderr="",
            returncode=0,
        )

    monkeypatch.setattr(gnome, "run_command", fake_run_command)
    info = gnome.get_extension_info("blur-my-shell@aunetx")
    assert info.uuid == "blur-my-shell@aunetx"
    assert info.name == "Blur my Shell"


def test_get_extension_info_not_found(monkeypatch) -> None:
    monkeypatch.setattr(gnome, "get_user_extensions_enabled", lambda: True)

    def fake_run_command(command):
        return CommandResult(
            success=False,
            command=" ".join(command),
            stdout="",
            stderr="Extension does not exist",
            returncode=2,
        )

    monkeypatch.setattr(gnome, "run_command", fake_run_command)
    with pytest.raises(ValueError, match="not found"):
        gnome.get_extension_info("nonexistent@id")


def test_enable_extension_success(monkeypatch) -> None:
    monkeypatch.setattr(gnome, "get_user_extensions_enabled", lambda: True)
    calls: List[list[str]] = []

    def fake_run_command(command):
        calls.append(command)
        if command[:2] == ["gnome-extensions", "info"]:
            return CommandResult(
                success=True,
                command=" ".join(command),
                stdout=SAMPLE_EXTENSIONS_OUTPUT.split("\n\n")[0],
                stderr="",
                returncode=0,
            )
        return CommandResult(
            success=True,
            command=" ".join(command),
            stdout="",
            stderr="",
            returncode=0,
        )

    monkeypatch.setattr(gnome, "run_command", fake_run_command)
    res = gnome.enable_extension("blur-my-shell@aunetx")
    assert "enabled" in res
    assert len(calls) == 2
    assert calls[1] == ["gnome-extensions", "enable", "blur-my-shell@aunetx"]


def test_disable_extension_success(monkeypatch) -> None:
    monkeypatch.setattr(gnome, "get_user_extensions_enabled", lambda: True)
    calls: List[list[str]] = []

    def fake_run_command(command):
        calls.append(command)
        if command[:2] == ["gnome-extensions", "info"]:
            return CommandResult(
                success=True,
                command=" ".join(command),
                stdout=SAMPLE_EXTENSIONS_OUTPUT.split("\n\n")[0],
                stderr="",
                returncode=0,
            )
        return CommandResult(
            success=True,
            command=" ".join(command),
            stdout="",
            stderr="",
            returncode=0,
        )

    monkeypatch.setattr(gnome, "run_command", fake_run_command)
    res = gnome.disable_extension("blur-my-shell@aunetx")
    assert "disabled" in res
    assert len(calls) == 2
    assert calls[1] == ["gnome-extensions", "disable", "blur-my-shell@aunetx"]


def test_enable_extension_globally_disabled(monkeypatch) -> None:
    monkeypatch.setattr(gnome, "get_user_extensions_enabled", lambda: False)
    with pytest.raises(RuntimeError, match="globally disabled"):
        gnome.enable_extension("blur-my-shell@aunetx")


def test_enable_extension_empty_uuid() -> None:
    with pytest.raises(ValueError, match="cannot be empty"):
        gnome.enable_extension("  ")


def test_main_tools_delegation(monkeypatch) -> None:
    monkeypatch.setattr(gnome, "get_user_extensions_enabled", lambda: True)
    monkeypatch.setattr(gnome, "set_user_extensions_enabled", lambda enabled: "ok")
    monkeypatch.setattr(gnome, "list_extensions", lambda enabled_only=False: [])
    monkeypatch.setattr(
        gnome,
        "get_extension_info",
        lambda uuid: ExtensionInfo(
            uuid=uuid,
            name=None,
            description=None,
            enabled=False,
            state=None,
            path=None,
            url=None,
            version=None,
        ),
    )
    monkeypatch.setattr(gnome, "enable_extension", lambda uuid: "enabled")
    monkeypatch.setattr(gnome, "disable_extension", lambda uuid: "disabled")

    assert main.get_user_extensions_enabled() is True
    assert main.set_user_extensions_enabled(True) == "ok"
    assert main.list_extensions() == []
    assert main.get_extension_info("test@id").uuid == "test@id"
    assert main.enable_extension("test@id") == "enabled"
    assert main.disable_extension("test@id") == "disabled"
