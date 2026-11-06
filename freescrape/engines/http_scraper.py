"""HTTP scraping with httpx, plus optional Playwright fallback for JS-heavy pages."""
from __future__ import annotations

from typing import Any, Dict, Optional

from freescrape.config import load_config
from freescrape.engines.extractor import extract


def _fetch(url: str, proxy: Optional[str], timeout: int, user_agent: str) -> tuple[str, int]:
    import httpx  # type: ignore

    transport = None
    if proxy:
        transport = httpx.HTTPTransport(proxy=proxy)
    with httpx.Client(
        transport=transport,
        timeout=timeout,
        follow_redirects=True,
        headers={"User-Agent": user_agent, "Accept-Language": "en-US,en;q=0.9"},
    ) as client:
        resp = client.get(url)
        return resp.text, resp.status_code


def scrape(
    url: str,
    *,
    use_browser: bool = False,
    proxy: Optional[str] = None,
    timeout: Optional[int] = None,
    with_html: bool = False,
) -> Dict[str, Any]:
    """Scrape ``url`` and return extracted content.

    For JS-rendered pages pass ``use_browser=True`` to drive Playwright.
    """
    cfg = load_config()
    proxy = proxy if proxy is not None else cfg.get("proxy")
    timeout = timeout or cfg.get("timeout", 30)
    ua = cfg.get("user_agent")

    if use_browser:
        from freescrape.engines.browser_ctl import fetch_with_playwright

        html, status = fetch_with_playwright(url, proxy=proxy, timeout=timeout, ua=ua)
    else:
        try:
            html, status = _fetch(url, proxy, timeout, ua)
        except Exception as e:  # network/CAPTCHA/block -> offer browser fallback
            return {
                "url": url,
                "status": None,
                "ok": False,
                "error": f"{type(e).__name__}: {e}",
                "hint": "Site may block plain HTTP. Retry with --browser (needs playwright).",
                "title": None,
                "text": "",
                "markdown": "",
                "engine": "none",
            }

    parsed = extract(html, url=url)
    out: Dict[str, Any] = {
        "url": url,
        "status": status,
        "ok": 200 <= (status or 0) < 400,
        "title": parsed["title"],
        "text": parsed["text"],
        "markdown": parsed["markdown"],
        "engine": parsed["engine"],
    }
    if with_html:
        out["html"] = html
    return out
