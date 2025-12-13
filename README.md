# **GNOME & Fedora MCP Server**

# Tools
- Health: `analyze_metrics(metrics: SystemMetrics)`.
- Appearance: `set_color_scheme`, `set_wallpaper`, `set_wallpaper_mode`, `set_gtk_theme`, `set_icon_theme`, `set_font`, `set_text_scaling`, `set_night_light`, `set_night_light_temperature`, `set_night_light_schedule_automatic`, `set_night_light_schedule`.
- Apps & favorites: `list_applications`, `launch_application`, `get_favorite_apps`, `set_favorite_apps`, `add_favorite_app`.
- System controls: `shutdown_system`, `reboot_system`, `get_system_details`, `set_wifi_enabled`, `set_bluetooth_enabled`, `set_networking_enabled`, `set_airplane_mode`, `set_power_profile`, `set_volume`, `update_mute`, `control_media`, `brightness_step_up`, `brightness_step_down`, `lock_screen`, `logout_session`.
- Files & shell: `open_with_default`, `move_to_trash`, `empty_trash`.
- Notifications & clipboard: `send_notification`, `copy_to_clipboard`, `paste_from_clipboard`.
- Touchpad: `set_tap_to_click`, `set_natural_scroll`, `set_touchpad_speed`.

# Requirements
These are the requirements for running this project:
- Python 3.12 or above
- UV package manager

# Stack
These are the main technologies used in this project:

## **Runtime & Tooling**
- [**Python**](https://www.python.org/): runtime for the MCP server.
- [**Model Context Protocol (python mcp)**](https://github.com/modelcontextprotocol/python-sdk): FastMCP server over stdio with CLI helpers.

# Running MCP Server in VS Code
These steps start the MCP server from the VS Code MCP extension.

## 1. **Clone the project locally**
```sh
git clone https://github.com/mbeps/linux-gnome-mcp.git
cd linux-gnome-mcp
```

## 2. **Install dependencies**
```sh
uv sync
```

## 3. **Configure the VS Code MCP extension**
1. Open the repo in VS Code.
2. Ensure the extension reads `.vscode/mcp.json`.
3. The file registers `linux-gnome-automations` with `type` set to `stdio`.
4. It runs `/home/maruf/.local/bin/uv run --directory /home/maruf/Development/Personal/MCP/linux-gnome-automations src/mcp_server/main.py`.
5. It sets `PYTHONUNBUFFERED=1` for stderr flushing.
6. Update the `command` field if your `uv` path is different.

## 4. **Start the server**
Reload the extension and start `linux-gnome-automations` from the MCP panel.
