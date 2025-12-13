# **GNOME & Fedora MCP Server**

# Tools 
- `analyze_metrics(metrics: SystemMetrics)`: returns health status/recommendation based on CPU/memory/process counts.
- `set_color_scheme(preference: "default"|"prefer-dark")`: switch GNOME light/dark color scheme.
- `set_wallpaper(image_path: str)`: set wallpaper URI for both light and dark keys.
- `set_night_light(enabled: bool)`: toggle Night Light on/off.
- `list_applications(limit: int = 50)`: list installed applications from .desktop files.
- `launch_application(desktop_id: str)`: launch app via gtk-launch by desktop id.
- `set_volume(volume_percent: int)`: set output volume 0–150% using pactl.
- `update_mute(action: "toggle"|"mute"|"unmute")`: change mute state on default sink.
- `control_media(action: "play-pause"|"next"|"previous"|"stop")`: send playerctl media command.
- `lock_screen()`: lock current GNOME session.
- `open_with_default(target: str)`: open file path or URL with GNOME default handler.

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
