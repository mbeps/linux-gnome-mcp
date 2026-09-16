import json
from collections.abc import AsyncIterator
from unittest.mock import patch

import pytest
from mcp import Client
from starlette.applications import Starlette

from mcp_server.main import app, mcp, parse_args
from mcp_server.models import AnalysisResult

EXPECTED_TOOLS: set[str] = {
    "analyze_metrics",
    "set_color_scheme",
    "set_wallpaper",
    "set_night_light",
    "set_wallpaper_mode",
    "set_gtk_theme",
    "set_icon_theme",
    "set_font",
    "set_text_scaling",
    "set_night_light_temperature",
    "set_night_light_schedule_automatic",
    "set_night_light_schedule",
    "list_applications",
    "launch_application",
    "get_favorite_apps",
    "set_favorite_apps",
    "add_favorite_app",
    "shutdown_system",
    "reboot_system",
    "get_system_details",
    "set_wifi_enabled",
    "set_bluetooth_enabled",
    "set_networking_enabled",
    "set_airplane_mode",
    "set_power_profile",
    "lock_screen",
    "logout_session",
    "open_with_default",
    "brightness_step_up",
    "brightness_step_down",
    "move_to_trash",
    "empty_trash",
    "send_notification",
    "copy_to_clipboard",
    "paste_from_clipboard",
    "set_tap_to_click",
    "set_natural_scroll",
    "set_touchpad_speed",
    "get_user_extensions_enabled",
    "set_user_extensions_enabled",
    "list_extensions",
    "get_extension_info",
    "enable_extension",
    "disable_extension",
    "set_volume",
    "update_mute",
    "control_media",
}


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
async def mcp_client() -> AsyncIterator[Client]:
    async with Client(mcp, raise_exceptions=True) as client:
        yield client


def test_server_metadata() -> None:
    assert mcp.name == "Linux-GNOME-Automations"
    assert mcp.version == "0.1.0"
    assert mcp.description is not None
    assert "GNOME" in mcp.description


@pytest.mark.anyio
async def test_tools_registered(mcp_client: Client) -> None:
    result = await mcp_client.list_tools()
    registered_names = {t.name for t in result.tools}

    assert registered_names == EXPECTED_TOOLS
    assert len(result.tools) == 47

    for tool in result.tools:
        assert tool.description, f"Tool {tool.name} has empty description"
        assert tool.input_schema is not None
        assert tool.input_schema.get("type") == "object"


@pytest.mark.anyio
async def test_call_analyze_metrics_healthy(mcp_client: Client) -> None:
    res = await mcp_client.call_tool(
        "analyze_metrics",
        {"metrics": {"cpu_percent": 25.0, "memory_gb": 4.0, "process_count": 80}},
    )
    assert not res.is_error
    assert res.structured_content is not None
    data = AnalysisResult.model_validate(res.structured_content)
    assert data.status == "healthy"
    assert data.recommendation is None


@pytest.mark.anyio
async def test_call_analyze_metrics_critical(mcp_client: Client) -> None:
    res = await mcp_client.call_tool(
        "analyze_metrics",
        {"metrics": {"cpu_percent": 95.0, "memory_gb": 16.0, "process_count": 200}},
    )
    assert not res.is_error
    assert res.structured_content is not None
    data = AnalysisResult.model_validate(res.structured_content)
    assert data.status == "critical"
    assert data.recommendation is not None


@pytest.mark.anyio
async def test_call_aliased_tools(mcp_client: Client) -> None:
    with patch("mcp_server.tools.gnome.run_command") as mock_run:
        from mcp_server.models import CommandResult

        mock_run.return_value = CommandResult(
            success=True, command="pactl", stdout="", stderr="", returncode=0
        )
        res = await mcp_client.call_tool("set_volume", {"volume_percent": 60})
        assert not res.is_error
        assert "Volume set to 60%" in res.content[0].text  # type: ignore[union-attr]

        mock_run.return_value = CommandResult(
            success=True, command="playerctl", stdout="", stderr="", returncode=0
        )
        res = await mcp_client.call_tool("control_media", {"action": "play-pause"})
        assert not res.is_error
        assert "Executed media action" in res.content[0].text  # type: ignore[union-attr]


@pytest.mark.anyio
async def test_resources(mcp_client: Client) -> None:
    res_list = await mcp_client.list_resources()
    uris = [r.uri for r in res_list.resources]
    assert "config://app/defaults" in uris

    content = await mcp_client.read_resource("config://app/defaults")
    text_content = content.contents[0].text  # type: ignore[union-attr]
    data = json.loads(text_content)
    assert data["poll_interval_seconds"] == 60
    assert data["cpu_threshold_warning"] == 70.0
    assert data["cpu_threshold_critical"] == 90.0


def test_stateless_http_app() -> None:
    assert isinstance(app, Starlette)
    new_app = mcp.streamable_http_app(stateless_http=True)
    assert isinstance(new_app, Starlette)


def test_parse_args_defaults() -> None:
    args = parse_args([])
    assert args.transport == "stdio"
    assert args.host == "127.0.0.1"
    assert args.port == 8000
    assert args.stateless is True


def test_parse_args_custom() -> None:
    args = parse_args(
        ["--transport", "streamable-http", "--host", "0.0.0.0", "--port", "9090", "--no-stateless"]
    )
    assert args.transport == "streamable-http"
    assert args.host == "0.0.0.0"
    assert args.port == 9090
    assert args.stateless is False


def test_parse_args_env_vars() -> None:
    with patch.dict(
        "os.environ",
        {
            "MCP_TRANSPORT": "streamable-http",
            "MCP_HOST": "10.0.0.1",
            "MCP_PORT": "8080",
            "MCP_STATELESS_HTTP": "false",
        },
    ):
        args = parse_args([])
        assert args.transport == "streamable-http"
        assert args.host == "10.0.0.1"
        assert args.port == 8080
        assert args.stateless is False

