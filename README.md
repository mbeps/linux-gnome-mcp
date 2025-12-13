# MCP server starter (uv)

This repository is a minimal, typed MCP server scaffold that follows the guidance in `AGENTS.md` and uses `uv` for dependency and Python management.

## Quick start
- Install [uv](https://github.com/astral-sh/uv) if you do not already have it on your PATH.
- Sync the environment (installs dependencies and the local package in editable mode): `uv sync`
- Run the server over stdio: `uv run --directory . mcp-server`
- Type-check the code: `uv run --directory . mypy src`
- Explore with the MCP Inspector: `npx @modelcontextprotocol/inspector uv run --directory . mcp-server`

## Project layout
- `pyproject.toml`, `uv.lock` – project metadata and locked dependencies managed by uv
- `src/mcp_server/main.py` – FastMCP entrypoint with a sample tool and resource
- `src/mcp_server/tools/system.py` – pure logic for system health analysis
- `src/mcp_server/models.py` – Pydantic models for tool inputs/outputs
- `src/mcp_server/utils/logger.py` – stderr-only logging configuration to keep MCP stdout clean
