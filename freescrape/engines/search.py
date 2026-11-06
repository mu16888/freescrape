"""Free search-engine result scraping (DuckDuckGo HTML / Bing). No API key needed."""
from __future__ import annotations

from typing import Dict, List, Optional

from freescrape.config import load_config

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}


def _http_get(url: str, proxy: Optional[str], timeout: int) -> str:
    import httpx  # type: ignore

    transport = httpx.HTTPTransport(proxy=proxy) if proxy else None
    with httpx.Client(transport=transport, timeout=timeout, follow_redirects=True, trust_env=False, headers=_HEADERS) as c:
        return c.get(url).text


def _parse_ddg(html: str) -> List[Dict[str, str]]:
    from bs4 import BeautifulSoup  # type: ignore

    soup = BeautifulSoup(html, "lxml")
    results: List[Dict[str, str]] = []
    for node in soup.select("a.result__a"):
        title = node.get_text(strip=True)
        href = node.get("href", "")
        # DDG wraps real URLs in a redirect; extract the uddg param if present.
        if "uddg=" in href:
            from urllib.parse import unquote, urlparse, parse_qs

            real = parse_qs(urlparse(href).query).get("uddg", [href])[0]
            href = unquote(real)
        snippet_node = node.find_parent("div", class_="result") or node.parent
        snippet = ""
        if snippet_node:
            sn = snippet_node.select_one(".result__snippet")
            snippet = sn.get_text(strip=True) if sn else ""
        if title:
            results.append({"title": title, "url": href, "snippet": snippet})
    return results


def _parse_bing(html: str) -> List[Dict[str, str]]:
    from bs4 import BeautifulSoup  # type: ignore

    soup = BeautifulSoup(html, "lxml")
    results: List[Dict[str, str]] = []
    for item in soup.select("li.b_algo"):
        title_node = item.select_one("h2 a")
        if not title_node:
            continue
        title = title_node.get_text(strip=True)
        href = title_node.get("href", "")
        snippet_node = item.select_one(".b_caption p, .b_lineclamp2, .b_lineclamp3, .b_lineclamp4")
        snippet = snippet_node.get_text(strip=True) if snippet_node else ""
        results.append({"title": title, "url": href, "snippet": snippet})
    return results


def search(
    query: str,
    *,
    engine: str = "ddg",
    max_results: int = 10,
    proxy: Optional[str] = None,
    timeout: Optional[int] = None,
) -> List[Dict[str, str]]:
    """Search the web for free. Returns a list of {title, url, snippet}."""
    cfg = load_config()
    proxy = proxy if proxy is not None else cfg.get("proxy")
    timeout = timeout or cfg.get("timeout", 30)
    from urllib.parse import quote_plus

    q = quote_plus(query)
    if engine == "ddg":
        html = _http_get(f"https://html.duckduckgo.com/html/?q={q}", proxy, timeout)
        results = _parse_ddg(html)
    elif engine == "bing":
        html = _http_get(f"https://www.bing.com/search?q={q}", proxy, timeout)
        results = _parse_bing(html)
    else:
        raise ValueError(f"unknown search engine: {engine}")
    return results[:max_results]
