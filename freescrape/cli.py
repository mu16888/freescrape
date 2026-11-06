"""FreeScrape CLI — a free, open-source web scraping command line.

Free, local-first alternative to commercial scraping CLIs. No paid account,
no proxy network, no telemetry. See README.md for capability boundaries.
"""
from __future__ import annotations

import json
import sys

import click
from rich.console import Console

from freescrape import __version__
from freescrape.config import get_key, load_config, save_config, set_key
from freescrape.utils import fatal, out

console = Console()


# --------------------------------------------------------------------------- #
# Root group
# --------------------------------------------------------------------------- #
@click.group()
@click.version_option(__version__, "-V", "--version", message="freescrape %(version)s")
@click.option("--json", "as_json", is_flag=True, help="Output raw JSON (compact).")
@click.option("--pretty", is_flag=True, help="Output pretty JSON.")
@click.option("-o", "--output", default=None, help="Write result to a file (json/md/csv/txt by extension).")
@click.pass_context
def cli(ctx, as_json, pretty, output):
    """FreeScrape — scrape, search, and extract web data from your terminal."""
    ctx.ensure_object(dict)
    ctx.obj["as_json"] = as_json
    ctx.obj["pretty"] = pretty
    ctx.obj["output"] = output


def _emit(ctx, data, humanizer=None):
    out(
        data,
        as_json=ctx.obj.get("as_json", False),
        pretty=ctx.obj.get("pretty", False),
        output_path=ctx.obj.get("output"),
        humanizer=humanizer,
    )


# --------------------------------------------------------------------------- #
# init / config
# --------------------------------------------------------------------------- #
@cli.command()
def init():
    """Interactive first-time setup (user-agent, proxy, optional LLM)."""
    cfg = load_config()
    ua = click.prompt("User-Agent", default=cfg.get("user_agent"))
    proxy = click.prompt("Proxy (empty for direct)", default=cfg.get("proxy") or "")
    llm = click.prompt("LLM API key (empty to skip AI features)", default=cfg.get("llm_api_key") or "", hide_input=True)
    base = click.prompt("LLM base URL", default=cfg.get("llm_base_url"))
    model = click.prompt("LLM model", default=cfg.get("llm_model"))
    cfg.update(
        user_agent=ua,
        proxy=proxy or None,
        llm_api_key=llm or None,
        llm_base_url=base,
        llm_model=model,
    )
    save_config(cfg)
    from freescrape.config import CONFIG_PATH

    console.print(f"[green]config saved[/green] -> {CONFIG_PATH}")


@cli.group()
def config():
    """View and edit local configuration (no remote account)."""


@config.command("list")
@click.pass_context
def config_list(ctx):
    """Show the current configuration."""
    cfg = load_config()
    # Mask secrets
    safe = dict(cfg)
    if safe.get("llm_api_key"):
        safe["llm_api_key"] = safe["llm_api_key"][:4] + "****"
    _emit(ctx, safe, lambda d: "\n".join(f"{k} = {v}" for k, v in d.items()))


@config.command("get")
@click.argument("key")
@click.pass_context
def config_get(ctx, key):
    """Get a single config value."""
    _emit(ctx, {key: get_key(key)}, lambda d: str(d.get(key)))


@config.command("set")
@click.argument("key")
@click.argument("value")
@click.pass_context
def config_set(ctx, key, value):
    """Set a config value (value is coerced: true/false->bool, digits->int)."""
    coerced = value
    if value.lower() in ("true", "false"):
        coerced = value.lower() == "true"
    elif value.isdigit():
        coerced = int(value)
    elif value.lower() in ("null", "none", ""):
        coerced = None
    set_key(key, coerced)
    console.print(f"[green]set[/green] {key} = {coerced!r}")


# --------------------------------------------------------------------------- #
# scrape
# --------------------------------------------------------------------------- #
@cli.command()
@click.argument("url")
@click.option("--browser", is_flag=True, help="Use Playwright for JS-rendered pages.")
@click.option("--proxy", default=None, help="Override proxy for this call.")
@click.option("--timeout", type=int, default=None, help="Request timeout (seconds).")
@click.option("--html", "with_html", is_flag=True, help="Include raw HTML in output.")
@click.pass_context
def scrape(ctx, url, browser, proxy, timeout, with_html):
    """Scrape URL and extract markdown/text."""
    from freescrape.engines.http_scraper import scrape as do_scrape

    try:
        res = do_scrape(url, use_browser=browser, proxy=proxy, timeout=timeout, with_html=with_html)
    except Exception as e:  # noqa: BLE001
        fatal(f"{type(e).__name__}: {e}")
    _emit(
        ctx,
        res,
        lambda d: (f"# {d.get('title') or '(no title)'}\n\n{d.get('markdown') or d.get('text') or '(empty)'}"
                   if not d.get("error") else f"ERROR: {d.get('error')}\n{d.get('hint','')}"),
    )


# --------------------------------------------------------------------------- #
# search
# --------------------------------------------------------------------------- #
@cli.command()
@click.argument("query")
@click.option("--engine", type=click.Choice(["ddg", "bing"]), default="ddg")
@click.option("--max", "max_results", type=int, default=10)
@click.option("--proxy", default=None)
@click.pass_context
def search(ctx, query, engine, max_results, proxy):
    """Search the web for free (DuckDuckGo/Bing). Returns {title,url,snippet}."""
    from freescrape.engines.search import search as do_search

    try:
        res = do_search(query, engine=engine, max_results=max_results, proxy=proxy)
    except Exception as e:  # noqa: BLE001
        fatal(f"{type(e).__name__}: {e}")
    _emit(ctx, res, lambda d: "\n\n".join(f"{i+1}. {r['title']}\n   {r['url']}\n   {r.get('snippet','')}" for i, r in enumerate(d)))


# --------------------------------------------------------------------------- #
# discover (AI-ranked search)
# --------------------------------------------------------------------------- #
@cli.command()
@click.argument("query")
@click.option("--engine", type=click.Choice(["ddg", "bing"]), default="ddg")
@click.option("--max", "max_results", type=int, default=10)
@click.pass_context
def discover(ctx, query, engine, max_results):
    """AI-assisted discovery: search then rank/summarize via optional LLM."""
    from freescrape.engines.llm import discover as ai_discover
    from freescrape.engines.search import search as do_search

    candidates = do_search(query, engine=engine, max_results=max_results)
    res = ai_discover(query, candidates, max=max_results)
    _emit(ctx, res, lambda d: d.get("analysis") or "\n".join(f"{r['title']} — {r['url']}" for r in d.get("results", [])))


# --------------------------------------------------------------------------- #
# browser
# --------------------------------------------------------------------------- #
@cli.group()
def browser():
    """Real-browser automation via Playwright (optional dependency)."""


@browser.command("open")
@click.argument("url")
@click.option("--no-headless", is_flag=True, help="Show the browser window.")
@click.option("--keep-open", is_flag=True, help="Keep the headed browser open until closed by user.")
@click.option("--proxy", default=None)
@click.option("--session", default=None, help="Named persistent profile (cookies survive).")
@click.option("--wait", type=int, default=2, help="Seconds to wait after load.")
@click.pass_context
def browser_open(ctx, url, no_headless, keep_open, proxy, session, wait):
    """Open URL in a real browser and return a snapshot."""
    from freescrape.engines.browser_ctl import open_page

    try:
        snap = open_page(url, headless=not no_headless, proxy=proxy, user_data_dir=session, wait=wait, keep_open=keep_open and not no_headless)
    except Exception as e:  # noqa: BLE001
        fatal(str(e))
    _emit(ctx, snap, lambda d: f"title: {d['title']}\nurl: {d['url']}\nlinks: {d['num_links']}  text_len: {d['text_length']}")


@browser.command("snapshot")
@click.argument("url")
@click.option("--proxy", default=None)
@click.option("--session", default=None)
@click.pass_context
def browser_snapshot(ctx, url, proxy, session):
    """Return a snapshot (title, url, link count) of URL."""
    from freescrape.engines.browser_ctl import snapshot as do_snapshot

    try:
        snap = do_snapshot(url, proxy=proxy, user_data_dir=session)
    except Exception as e:  # noqa: BLE001
        fatal(str(e))
    _emit(ctx, snap, lambda d: f"title: {d['title']}\nurl: {d['url']}\nlinks: {d['num_links']}")


@browser.command("screenshot")
@click.argument("url")
@click.argument("path")
@click.option("--proxy", default=None)
@click.option("--session", default=None)
@click.pass_context
def browser_screenshot(ctx, url, path, proxy, session):
    """Save a screenshot of URL to PATH."""
    from freescrape.engines.browser_ctl import screenshot as do_shot

    try:
        res = do_shot(url, path, proxy=proxy, user_data_dir=session)
    except Exception as e:  # noqa: BLE001
        fatal(str(e))
    _emit(ctx, res, lambda d: f"screenshot -> {d['screenshot']}")


@browser.command("click")
@click.argument("url")
@click.option("--selector", required=True, help="CSS selector to click.")
@click.option("--proxy", default=None)
@click.option("--session", default=None)
@click.pass_context
def browser_click(ctx, url, selector, proxy, session):
    """Load URL, click SELECTOR, return resulting snapshot."""
    from freescrape.engines.browser_ctl import click as do_click

    try:
        snap = do_click(url, selector, proxy=proxy, user_data_dir=session)
    except Exception as e:  # noqa: BLE001
        fatal(str(e))
    _emit(ctx, snap, lambda d: f"after click -> {d['url']}\nlinks: {d['num_links']}")


@browser.command("type")
@click.argument("url")
@click.option("--selector", required=True)
@click.option("--text", required=True)
@click.option("--proxy", default=None)
@click.option("--session", default=None)
@click.pass_context
def browser_type(ctx, url, selector, text, proxy, session):
    """Load URL, fill SELECTOR with TEXT, return snapshot."""
    from freescrape.engines.browser_ctl import type_text as do_type

    try:
        snap = do_type(url, selector, text, proxy=proxy, user_data_dir=session)
    except Exception as e:  # noqa: BLE001
        fatal(str(e))
    _emit(ctx, snap, lambda d: f"after type -> {d['url']}")


@browser.command("scroll")
@click.argument("url")
@click.option("--amount", type=int, default=1000)
@click.option("--proxy", default=None)
@click.option("--session", default=None)
@click.pass_context
def browser_scroll(ctx, url, amount, proxy, session):
    """Load URL and scroll by AMOUNT pixels."""
    from freescrape.engines.browser_ctl import scroll as do_scroll

    try:
        snap = do_scroll(url, amount, proxy=proxy, user_data_dir=session)
    except Exception as e:  # noqa: BLE001
        fatal(str(e))
    _emit(ctx, snap, lambda d: f"after scroll -> {d['url']}  text_len: {d['text_length']}")


# --------------------------------------------------------------------------- #
# pipelines
# --------------------------------------------------------------------------- #
@cli.group()
def pipelines():
    """Run built-in / user scraper templates (community pipelines)."""


@pipelines.command("search")
@click.argument("term", required=False)
@click.pass_context
def pipelines_search(ctx, term):
    """List available pipelines, optionally filtered by TERM."""
    from freescrape.pipelines.registry import list_pipelines

    items = list_pipelines()
    if term:
        items = [i for i in items if term.lower() in i["name"].lower() or term.lower() in i["description"].lower()]
    _emit(ctx, items, lambda d: "\n".join(f"{i['name']:18} {i['description']}" for i in d) or "(none)")


@pipelines.command("info")
@click.argument("name")
@click.pass_context
def pipelines_info(ctx, name):
    """Show a pipeline descriptor."""
    from freescrape.pipelines.registry import get_pipeline

    try:
        _emit(ctx, get_pipeline(name))
    except KeyError as e:
        fatal(str(e))


@pipelines.command("run")
@click.argument("name")
@click.option("--max", "max_items", type=int, default=20)
@click.pass_context
def pipelines_run(ctx, name, max_items):
    """Execute a pipeline and extract structured items."""
    from freescrape.pipelines.registry import run_pipeline

    try:
        res = run_pipeline(name, max_items=max_items)
    except KeyError as e:
        fatal(str(e))
    except Exception as e:  # noqa: BLE001
        fatal(f"{type(e).__name__}: {e}")
    _emit(
        ctx,
        res,
        lambda d: f"pipeline: {d['pipeline']}  count: {d['count']}\n" + "\n".join(json.dumps(i, ensure_ascii=False) for i in d["items"]),
    )


# --------------------------------------------------------------------------- #
# budget (free status)
# --------------------------------------------------------------------------- #
@cli.command()
@click.pass_context
def budget(ctx):
    """Show usage status. FreeScrape is 100% free — no credits, no billing."""
    _emit(
        ctx,
        {
            "plan": "free / open-source",
            "credits_used": 0,
            "credits_limit": "unlimited (your own machine + network)",
            "cost": "$0.00",
            "note": "No proxy network or anti-bot unlock included. Bring your own proxy for blocked sites.",
        },
        lambda d: "plan: free / open-source\ncost: $0.00\nlimits: unlimited (runs on your machine)\n"
                  "note: no paid proxy/anti-bot unlock; bring your own proxy for hard targets.",
    )


# --------------------------------------------------------------------------- #
# add mcp (write client config snippet)
# --------------------------------------------------------------------------- #
@cli.command("add")
@click.argument("target", type=click.Choice(["mcp"]))
@click.option("--client", type=click.Choice(["claude-code", "cursor", "generic"]), default="generic")
@click.pass_context
def add(ctx, target, client):
    """Install FreeScrape into an AI coding agent as an MCP server."""
    if target != "mcp":
        fatal("only 'mcp' is supported")
    import shutil
    import sys

    exe = shutil.which("freescrape") or f"{sys.executable} -m freescrape"
    snippet = {
        "mcpServers": {
            "freescrape": {"command": exe.split()[0], "args": (exe.split()[1:] if len(exe.split()) > 1 else []) + ["mcp", "--stdio"]}
        }
    }
    if client == "generic":
        console.print("[bold]Add this to your MCP client config:[/bold]")
        console.print_json(json.dumps(snippet, indent=2, ensure_ascii=False))
        console.print("\nOr run directly: ")
        console.print(f"  {exe} mcp --stdio")
    else:
        console.print(f"[green]For {client}:[/green] merge the following into its MCP config file, then restart the client.")
        console.print_json(json.dumps(snippet, indent=2, ensure_ascii=False))


# --------------------------------------------------------------------------- #
# mcp server entrypoint
# --------------------------------------------------------------------------- #
@cli.command()
@click.option("--stdio", is_flag=True, help="Run the MCP JSON-RPC server on stdin/stdout.")
def mcp(stdio):
    """Run FreeScrape as an MCP server (for AI agents)."""
    if not stdio:
        console.print("Use: freescrape mcp --stdio")
        return
    from freescrape.mcp_server import serve

    serve()


# --------------------------------------------------------------------------- #
# Alias entry: `fs`
# --------------------------------------------------------------------------- #
def fs_main():
    cli()


if __name__ == "__main__":
    cli()
