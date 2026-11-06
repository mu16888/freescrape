"""Playwright-based real-browser control.

Playwright is an OPTIONAL dependency (``pip install playwright && playwright install``).
Every function lazily imports it so the rest of FreeScrape works without a browser.
"""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from freescrape.config import load_config


def _require_playwright():
    if shutil.which("playwright") is None and _import_playwright() is None:
        raise RuntimeError(
            "Playwright not installed. Run:\n"
            "  pip install playwright\n"
            "  playwright install chromium\n"
            "Then retry with --browser."
        )
    return _import_playwright()


def _import_playwright():
    try:
        from playwright.sync_api import sync_playwright  # type: ignore

        return sync_playwright
    except Exception:
        return None


def _launch_kwargs(cfg, headless: bool, proxy: Optional[str], user_data_dir: Optional[str]):
    kwargs: Dict[str, Any] = {"headless": headless}
    if proxy:
        kwargs["proxy"] = {"server": proxy}
    if user_data_dir:
        kwargs["user_data_dir"] = user_data_dir
    return kwargs


def fetch_with_playwright(url: str, *, proxy: Optional[str] = None, timeout: int = 30, ua: Optional[str] = None):
    """Return (html, status) using a headless browser. Used by ``scrape --browser``."""
    sync_playwright = _require_playwright()
    cfg = load_config()
    proxy = proxy or cfg.get("proxy")
    from playwright.sync_api import TimeoutError as PWTimeout  # type: ignore

    with sync_playwright() as p:
        browser = p.chromium.launch(**_launch_kwargs(cfg, True, proxy, None))
        page = browser.new_page()
        if ua:
            page.set_extra_http_headers({"User-Agent": ua})
        try:
            resp = page.goto(url, timeout=timeout * 1000, wait_until="networkidle")
            html = page.content()
            status = resp.status if resp else 0
        except PWTimeout:
            html = page.content()
            status = 0
        finally:
            browser.close()
    return html, status


def _snapshot_dict(page) -> Dict[str, Any]:
    title = page.title()
    url = page.url
    content = page.content()
    text = page.inner_text("body") if page.query_selector("body") else ""
    links = page.eval_on_selector_all("a", "els => els.map(e => e.href)") if page.query_selector("a") else []
    return {
        "title": title,
        "url": url,
        "html_length": len(content),
        "text_length": len(text),
        "num_links": len(links),
        "text_sample": (text or "")[:500],
    }


def with_page(
    url: Optional[str],
    action: Callable,
    *,
    headless: bool = True,
    proxy: Optional[str] = None,
    user_data_dir: Optional[str] = None,
    wait: int = 0,
) -> Any:
    """Launch a browser, optionally navigate to ``url``, run ``action(page)``, close."""
    sync_playwright = _require_playwright()
    cfg = load_config()
    proxy = proxy or cfg.get("proxy")
    with sync_playwright() as p:
        browser = p.chromium.launch(**_launch_kwargs(cfg, headless, proxy, user_data_dir))
        page = browser.new_page()
        if url:
            page.goto(url, wait_until="domcontentloaded")
            if wait:
                page.wait_for_timeout(wait * 1000)
        try:
            result = action(page)
        finally:
            browser.close()
    return result


def open_page(url: str, *, headless: bool = True, proxy=None, user_data_dir=None, wait=2, keep_open=False):
    """Open ``url`` and return a snapshot. If keep_open (headed), block until closed."""
    sync_playwright = _require_playwright()
    cfg = load_config()
    proxy = proxy or cfg.get("proxy")
    with sync_playwright() as p:
        browser = p.chromium.launch(**_launch_kwargs(cfg, headless, proxy, user_data_dir))
        page = browser.new_page()
        page.goto(url, wait_until="networkidle" if headless else "load")
        page.wait_for_timeout(wait * 1000)
        snap = _snapshot_dict(page)
        if keep_open and not headless:
            # Headed + keep-open: let the user interact, exit when they close the window.
            try:
                while not browser.is_connected() or len(browser.contexts) > 0 and page.is_closed() is False:
                    page.wait_for_timeout(1000)
            except Exception:
                pass
        browser.close()
    return snap


def click(url: str, selector: str, *, headless=True, proxy=None, user_data_dir=None, wait=1) -> Dict[str, Any]:
    def act(page):
        page.click(selector, timeout=10000)
        page.wait_for_timeout(wait * 1000)
        return _snapshot_dict(page)
    return with_page(url, act, headless=headless, proxy=proxy, user_data_dir=user_data_dir)


def type_text(url: str, selector: str, text: str, *, headless=True, proxy=None, user_data_dir=None, wait=1) -> Dict[str, Any]:
    def act(page):
        page.fill(selector, text)
        page.wait_for_timeout(wait * 1000)
        return _snapshot_dict(page)
    return with_page(url, act, headless=headless, proxy=proxy, user_data_dir=user_data_dir)


def screenshot(url: str, path: str, *, headless=True, proxy=None, user_data_dir=None, wait=2) -> Dict[str, Any]:
    def act(page):
        page.screenshot(path=path, full_page=False)
        return {"url": page.url, "screenshot": str(Path(path).resolve())}
    return with_page(url, act, headless=headless, proxy=proxy, user_data_dir=user_data_dir, wait=wait)


def scroll(url: str, amount: int = 1000, *, headless=True, proxy=None, user_data_dir=None) -> Dict[str, Any]:
    def act(page):
        page.mouse.wheel(0, amount)
        page.wait_for_timeout(500)
        return _snapshot_dict(page)
    return with_page(url, act, headless=headless, proxy=proxy, user_data_dir=user_data_dir)


def snapshot(url: str, *, headless=True, proxy=None, user_data_dir=None, wait=1) -> Dict[str, Any]:
    def act(page):
        page.wait_for_timeout(wait * 1000)
        return _snapshot_dict(page)
    return with_page(url, act, headless=headless, proxy=proxy, user_data_dir=user_data_dir)
