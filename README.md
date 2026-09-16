# **GNOME & Linux Desktop MCP Server (v2 Stateless)**

Model Context Protocol (MCP v2) server for GNOME and Linux that lets AI clients automate desktop tasks. Built on the stateless MCP Python SDK v2 (`MCPServer`), it handles appearance tweaks, app launching, power management, networking, audio, notifications, clipboard, and file actions.

# Tools
- **Health**: `analyze_metrics(metrics: SystemMetrics)`.
- **Appearance**: `set_color_scheme`, `set_wallpaper`, `set_wallpaper_mode`, `set_gtk_theme`, `set_icon_theme`, `set_font`, `set_text_scaling`, `set_night_light`, `set_night_light_temperature`, `set_night_light_schedule_automatic`, `set_night_light_schedule`.
- **Apps & favorites**: `list_applications`, `launch_application`, `get_favorite_apps`, `set_favorite_apps`, `add_favorite_app`.
- **System controls**: `shutdown_system`, `reboot_system`, `get_system_details`, `set_wifi_enabled`, `set_bluetooth_enabled`, `set_networking_enabled`, `set_airplane_mode`, `set_power_profile`, `set_volume`, `update_mute`, `control_media`, `brightness_step_up`, `brightness_step_down`, `lock_screen`, `logout_session`.
- **Files & shell**: `open_with_default`, `move_to_trash`, `empty_trash`.
- **Notifications & clipboard**: `send_notification`, `copy_to_clipboard`, `paste_from_clipboard`.
- **Touchpad**: `set_tap_to_click`, `set_natural_scroll`, `set_touchpad_speed`.

# Resources
- `config://app/defaults`: Default monitoring thresholds and configuration.

# Requirements
- Python 3.12 or above
- [uv](https://docs.astral.sh/uv/) package manager

# Stack
- [**Python**](https://www.python.org/): Runtime environment.
- [**Model Context Protocol (python mcp v2)**](https://github.com/modelcontextprotocol/python-sdk): Stateless MCP SDK v2 (`MCPServer`) supporting `stdio` and `streamable-http` transports.
- [**Starlette / Uvicorn**](https://www.starlette.io/): ASGI support for stateless HTTP transport.

# Running the MCP Server

### 1. Install dependencies
```sh
uv sync
```

### 2. Run over standard I/O (Default, for VS Code & Claude Desktop)
```sh
uv run mcp-server
# or
uv run src/mcp_server/main.py
```

### 3. Run over Stateless Streamable HTTP
To run as an independent network service with stateless request handling:
```sh
uv run mcp-server --transport streamable-http --host 127.0.0.1 --port 8000
```
Or run directly via ASGI server:
```sh
uv run uvicorn mcp_server.main:app --host 127.0.0.1 --port 8000
```

### CLI Options & Environment Variables
| Option                           | Environment Variable | Default     | Description                                            |
| :------------------------------- | :------------------- | :---------- | :----------------------------------------------------- |
| `--transport`                    | `MCP_TRANSPORT`      | `stdio`     | Transport protocol (`stdio`, `streamable-http`, `sse`) |
| `--host`                         | `MCP_HOST`           | `127.0.0.1` | Host address for network transports                    |
| `--port`                         | `MCP_PORT`           | `8000`      | Port number for network transports                     |
| `--stateless` / `--no-stateless` | `MCP_STATELESS_HTTP` | `true`      | Enable stateless request handling for HTTP             |

# Running MCP Server in VS Code

1. Open the repository in VS Code.
2. Ensure the VS Code MCP extension reads `.vscode/mcp.json`.
3. The server runs via standard I/O (`stdio`), fully compatible with desktop AI agents:
```json
{
  "servers": {
    "linux-gnome-mcp": {
      "type": "stdio",
      "command": "/home/maruf/.local/bin/uv",
      "args": [
        "run",
        "--directory",
        "/home/maruf/Development/Personal/MCP/linux-gnome-mcp",
        "src/mcp_server/main.py"
      ],
      "env": {
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```
4. Reload the extension and start `linux-gnome-mcp` from the MCP panel.
