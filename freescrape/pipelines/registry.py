"""Built-in pipeline (scraper template) registry.

A pipeline is a small JSON descriptor: {name, description, url, fields:[{name, selector, attr}]}.
`run` fetches the page and extracts each field with BeautifulSoup. Users can add their
own templates under ~/.freescrape/pipelines/<name>.json.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from freescrape.config import CONFIG_DIR
from freescrape.engines.http_scraper import scrape

BUILTIN_DIR = Path(__file__).parent / "templates"
USER_DIR = CONFIG_DIR / "pipelines"


def _load_dir(d: Path) -> Dict[str, dict]:
    out: Dict[str, dict] = {}
    if not d.exists():
        return out
    for f in d.glob("*.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            out[data.get("name", f.stem)] = data
        except Exception:
            continue
    return out


def list_pipelines() -> List[dict]:
    """Return metadata for all available pipelines (built-in + user)."""
    all_p = {}
    all_p.update(_load_dir(BUILTIN_DIR))
    all_p.update(_load_dir(USER_DIR))
    return [
        {"name": k, "description": v.get("description", ""), "url": v.get("url", "")}
        for k, v in sorted(all_p.items())
    ]


def get_pipeline(name: str) -> dict:
    all_p = {}
    all_p.update(_load_dir(BUILTIN_DIR))
    all_p.update(_load_dir(USER_DIR))
    if name not in all_p:
        raise KeyError(f"pipeline not found: {name}. Use `freescrape pipelines search` to list.")
    return all_p[name]


def run_pipeline(name: str, max_items: int = 20) -> dict:
    """Execute a pipeline: fetch its URL and extract configured fields."""
    p = get_pipeline(name)
    url = p["url"]
    fields = p.get("fields", [])
    result = scrape(url, use_browser=False, with_html=True)

    from bs4 import BeautifulSoup  # type: ignore

    html = result.get("html", "")
    if not html:
        # Fallback raw fetch if html was not carried.
        from freescrape.engines.http_scraper import _fetch
        from freescrape.config import load_config

        cfg = load_config()
        html, _ = _fetch(url, cfg.get("proxy"), cfg.get("timeout", 30), cfg.get("user_agent"))
    soup = BeautifulSoup(html, "lxml")

    containers = soup.select(p.get("item_selector", "body"))
    items = []
    for node in containers[:max_items]:
        item = {}
        for fld in fields:
            sel = fld.get("selector")
            attr = fld.get("attr", "text")
            el = node.select_one(sel) if sel else node
            if el is None:
                item[fld["name"]] = ""
            elif attr == "text":
                item[fld["name"]] = el.get_text(strip=True)
            else:
                item[fld["name"]] = el.get(attr, "")
        items.append(item)

    return {
        "pipeline": name,
        "url": url,
        "count": len(items),
        "items": items,
        "source_status": result.get("status"),
    }
