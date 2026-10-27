"""Read-only GitHub MCP handshake diagnostics with actionable Windows errors."""
import asyncio
import os
import shutil
import subprocess
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

IMAGE = "ghcr.io/github/github-mcp-server"


def _docker_preflight(token: str) -> str:
    """Validate Docker is available and the official image can be started."""
    docker = shutil.which("docker")
    if not docker:
        raise RuntimeError(
            "Docker CLI was not found. Install Docker Desktop for Windows, start it, "
            "then close and reopen PowerShell and Streamlit. Alternatively, use the "
            "GitHub MCP server configuration in a supported MCP host."
        )
    try:
        info = subprocess.run([docker, "info"], capture_output=True, text=True, timeout=15)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("Docker did not respond to 'docker info' within 15 seconds. Start Docker Desktop and retry.") from exc
    if info.returncode != 0:
        detail = (info.stderr or info.stdout or "Docker daemon is unavailable.").strip()[-1200:]
        raise RuntimeError(f"Docker Desktop is not ready. Start Docker Desktop, wait until it says running, then retry. Details: {detail}")

    # Pull separately so image/network errors are shown clearly instead of being hidden
    # inside an asyncio TaskGroup exception from stdio_client startup.
    pull = subprocess.run([docker, "pull", IMAGE], capture_output=True, text=True, timeout=180)
    if pull.returncode != 0:
        detail = (pull.stderr or pull.stdout or "Docker image pull failed.").strip()[-1600:]
        raise RuntimeError(f"Could not download the GitHub MCP server image. Check internet access and Docker registry access. Details: {detail}")
    return docker


async def _initialize_and_list_tools(docker: str, token: str) -> dict[str, Any]:
    params = StdioServerParameters(
        command=docker,
        args=[
            "run", "-i", "--rm",
            "-e", "GITHUB_PERSONAL_ACCESS_TOKEN",
            "-e", "GITHUB_READ_ONLY=1",
            IMAGE,
        ],
        env={**os.environ, "GITHUB_PERSONAL_ACCESS_TOKEN": token, "GITHUB_READ_ONLY": "1"},
    )
    async with stdio_client(params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            initialized = await asyncio.wait_for(session.initialize(), timeout=45)
            listed = await asyncio.wait_for(session.list_tools(), timeout=45)
            server_info = getattr(initialized, "serverInfo", None)
            capabilities = getattr(initialized, "capabilities", None)
            return {
                "status": "initialized",
                "protocol_version": getattr(initialized, "protocolVersion", "unknown"),
                "server_name": getattr(server_info, "name", "GitHub MCP server"),
                "server_version": getattr(server_info, "version", "unknown"),
                "tools": [{"name": tool.name, "description": (tool.description or "").strip()} for tool in listed.tools],
                "tools_count": len(listed.tools),
                "tools_capability": bool(getattr(capabilities, "tools", None)),
                "read_only": True,
                "note": "Handshake succeeded. Session closes after tool discovery; no write tool was called.",
            }


def _root_error(exc: BaseException) -> str:
    """Flatten Python 3.11+ ExceptionGroup/TaskGroup errors to the useful cause."""
    messages = []
    stack = [exc]
    while stack:
        current = stack.pop(0)
        nested = getattr(current, "exceptions", None)
        if nested:
            stack[0:0] = list(nested)
        else:
            message = str(current).strip()
            if message and message not in messages:
                messages.append(message)
    return " | ".join(messages) or repr(exc)


def initialize_github_mcp() -> dict[str, Any]:
    """Synchronous wrapper for Streamlit with clear diagnostics."""
    token = os.getenv("GITHUB_TOKEN", "").strip()
    if not token or token.startswith("replace_with_"):
        raise RuntimeError("Set a real GITHUB_TOKEN in .env before initializing GitHub MCP, then restart Streamlit.")
    docker = _docker_preflight(token)
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        try:
            return asyncio.run(_initialize_and_list_tools(docker, token))
        except BaseException as exc:
            raise RuntimeError(f"GitHub MCP handshake failed: {_root_error(exc)}") from exc
    raise RuntimeError("An asyncio event loop is already running; run the MCP client in a separate thread or call the async function directly.")
