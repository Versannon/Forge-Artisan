"""ForgeArtisan Model Context Protocol (MCP) Server.

Exposes ForgeArtisan 3D artist tools over standard JSON-RPC (MCP) protocol,
allowing external agents (Muse Code, Claude Desktop, Antigravity) to command
game engines and generate beveled, detailed 3D models.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from agent_kit import client as client_module
from agent_kit import tools


def handle_rpc_message(msg: dict) -> dict | None:
    method = msg.get("method")
    msg_id = msg.get("id")

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "forge-artisan-mcp",
                    "version": "1.0.0"
                }
            }
        }

    elif method == "tools/list":
        tool_defs = tools.definitions()
        mcp_tools = []
        for t in tool_defs:
            mcp_tools.append({
                "name": t["name"],
                "description": t["description"],
                "inputSchema": t["parameters"]
            })
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "tools": mcp_tools
            }
        }

    elif method == "tools/call":
        params = msg.get("params", {})
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        class MockCall:
            def __init__(self, name: str, args: dict):
                self.function = self
                self.name = name
                self.arguments = json.dumps(args)

        c = client_module.make_client()
        result = tools.run(c, Path(__file__).parent.parent, "mcp_session", MockCall(tool_name, arguments))

        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result, indent=2)
                    }
                ]
            }
        }

    return {
        "jsonrpc": "2.0",
        "id": msg_id,
        "error": {
            "code": -32601,
            "message": f"Method '{method}' not found."
        }
    }


def run_stdio():
    """Reads JSON-RPC from stdin line-by-line and writes response to stdout."""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            res = handle_rpc_message(req)
            if res:
                sys.stdout.write(json.dumps(res) + "\n")
                sys.stdout.flush()
        except Exception as ex:
            err_res = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": str(ex)}
            }
            sys.stdout.write(json.dumps(err_res) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    run_stdio()
