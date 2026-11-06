"""Minimal MCP (Model Context Protocol) server over stdio.

Implements just enough of the JSON-RPC protocol to expose FreeScrape's
`scrape` and `search` tools to MCP clients (Claude Code, Cursor, etc.).

Run with:  freescrape mcp --stdio
"""
from __future__ import annotations

import json
import sys
from typing import Any, Dict

from freescrape.engines.http_scraper import scrape
from freescrape.engines.search import search


def _tools() -> list:
    return [
        {
            "name": "scrape",
            "description": "Fetch a URL and return cleaned markdown/text. Set browser=true for JS-heavy pages.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Target URL"},
                    "browser": {"type": "boolean", "description": "Use Playwright for JS rendering", "default": False},
                },
                "required": ["url"],
            },
        },
        {
            "name": "search",
            "description": "Free web search returning a list of {title, url, snippet}.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "engine": {"type": "string", "enum": ["ddg", "bing"], "default": "ddg"},
                    "max_results": {"type": "integer", "default": 10},
                },
                "required": ["query"],
            },
        },
    ]


def _call_tool(name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    if name == "scrape":
        res = scrape(args["url"], use_browser=args.get("browser", False))
        return {"content": [{"type": "text", "text": res.get("markdown") or res.get("text") or json.dumps(res, ensure_ascii=False)}]}
    if name == "search":
        res = search(args["query"], engine=args.get("engine", "ddg"), max_results=args.get("max_results", 10))
        return {"content": [{"type": "text", "text": json.dumps(res, ensure_ascii=False, indent=2)}]}
    raise ValueError(f"unknown tool: {name}")


def _handle(msg: Dict[str, Any]) -> Dict[str, Any]:
    method = msg.get("method")
    mid = msg.get("id")
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": mid,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "freescrape", "version": "0.1.0"},
            },
        }
    if method == "notifications/initialized":
        return {}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": mid, "result": {"tools": _tools()}}
    if method == "tools/call":
        try:
            result = _call_tool(msg["params"]["name"], msg["params"].get("arguments", {}))
        except Exception as e:  # noqa: BLE001
            result = {"content": [{"type": "text", "text": f"error: {e}"}], "isError": True}
        return {"jsonrpc": "2.0", "id": mid, "result": result}
    return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": f"method not found: {method}"}}


def serve() -> None:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        resp = _handle(msg)
        if resp:  # skip empty notifications
            sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    serve()
