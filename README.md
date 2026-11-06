# FreeScrape 🕸️

**A free, open-source web scraping CLI.** Scrape, search, and extract structured web
data directly from your terminal — no paid account, no proxy network, no telemetry.

> ⚠️ **Independent project.** FreeScrape is *not* affiliated with, endorsed by, or
> sponsored by Bright Data or any commercial scraping vendor. It is a community-built
> free alternative that mirrors the *command surface* of commercial scraping CLIs using
> only open-source engines.

---

## Why this exists

Commercial scraping CLIs are powerful, but their magic — residential proxy networks and
anti-bot unlock (CAPTCHA / Cloudflare solving) — is **paid infrastructure** you cannot
replicate for free. FreeScrape gives you the **software layer** for $0:

| Capability | FreeScrape | Commercial CLI (paid) |
|---|---|---|
| CLI commands & output formats | ✅ | ✅ |
| Local config (no login) | ✅ | ✅ |
| Web → Markdown / JSON extraction | ✅ (httpx + trafilatura) | ✅ |
| Free web search (DDG / Bing) | ✅ | ✅ (SERP API) |
| Real-browser automation (Playwright) | ✅ | ✅ (Scraping Browser) |
| AI discovery / extraction (bring your own LLM) | ✅ | ✅ |
| MCP server for AI agents | ✅ | ✅ |
| Prebuilt scraper templates (pipelines) | ✅ (extensible) | ✅ (thousands) |
| **Residential proxy network** | ❌ (bring your own proxy) | ✅ paid |
| **Anti-bot unlock / CAPTCHA solving** | ❌ (best-effort only) | ✅ paid |

**Bottom line:** FreeScrape covers the majority of ordinary scraping needs for free.
For sites protected by serious anti-bot systems, you will need to supply your own proxy
or accept that it may be blocked. This is a deliberate, honest trade-off.

---

## Install

Requires **Python ≥ 3.10**.

```bash
# Core (HTTP scraping + search + extraction)
pip install freescrape

# Optional: real-browser automation (`browser` commands)
pip install "freescrape[browser]" && playwright install chromium

# Optional: AI features (`discover`) — any OpenAI-compatible endpoint
pip install "freescrape[llm]"
```

Or run without installing:

```bash
python -m freescrape <command>
```

---

## Quick start

```bash
# 1. Interactive first-time setup (user-agent, proxy, optional LLM)
freescrape init

# 2. Scrape a page to Markdown
freescrape scrape https://example.com

# 3. Search the web (free, no API key)
freescrape search "web scraping best practices"

# 4. Run a built-in pipeline (structured extraction)
freescrape pipelines search
freescrape pipelines run hackernews

# 5. Use a real browser for JS-heavy pages
freescrape scrape https://spa.example.com --browser

# 6. Expose FreeScrape to an AI agent (MCP)
freescrape add mcp
```

All commands support `--json`, `--pretty`, and `-o file.json|file.md|file.csv` for
pipe-friendly automation.

---

## Command reference

### `scrape <url>`
Fetch a URL and extract Markdown / text.
- `--browser` — use Playwright for JS-rendered SPAs
- `--proxy <url>` — override proxy for this call
- `--timeout <sec>`, `--html` (include raw HTML)

### `search <query>`
Free search returning `{title, url, snippet}`.
- `--engine ddg|bing` (default `ddg`), `--max N`

### `discover <query>`
Search then AI-rank/summarize. If no LLM is configured, degrades to raw results.

### `browser` (group)
Real-browser automation via Playwright (optional dependency):
`open`, `snapshot`, `screenshot <url> <path>`, `click --selector`, `type --selector --text`, `scroll --amount`.

### `pipelines` (group)
Run built-in / user scraper templates: `search`, `info <name>`, `run <name>`.
Add your own: drop a JSON descriptor in `~/.freescrape/pipelines/<name>.json`.

### `config` (group)
`list`, `get <key>`, `set <key> <value>` — all local, no remote account.

### `budget`
Shows the (free) status. Always $0.00.

### `add mcp` / `mcp --stdio`
Expose `scrape` and `search` as MCP tools to Claude Code, Cursor, etc.

---

## Configuration

Stored in `~/.freescrape/config.json`. Key fields:

| key | meaning |
|---|---|
| `user_agent` | Default UA header |
| `proxy` | `http://host:port` or `null` for direct |
| `timeout` | Request timeout (seconds) |
| `browser_headless` | Playwright headless default |
| `llm_api_key` / `llm_base_url` / `llm_model` | OpenAI-compatible credentials (optional) |

Environment variables `OPENAI_API_KEY` / `OPENAI_BASE_URL` / `OPENAI_MODEL` are also honored.

---

## License

[MIT](LICENSE). Do whatever you want; contributions welcome.

---

## Disclaimer

Web scraping may be subject to a site's Terms of Service and applicable law. You are
responsible for how you use FreeScrape. Respect `robots.txt`, rate-limit your requests,
and do not use it to violate any site's terms.
