"""Content extraction: HTML -> markdown/text using trafilatura with fallbacks."""
from __future__ import annotations

from typing import Optional


def extract(html: str, url: Optional[str] = None) -> dict:
    """Extract structured text from raw HTML.

    Returns a dict with: title, text, markdown, and a comment on the engine used.
    Trafilatura is preferred; BeautifulSoup is the fallback for poor extractions.
    """
    result: dict = {"title": None, "text": "", "markdown": "", "engine": "none"}

    # Primary: trafilatura (best main-text extraction, includes markdown output)
    try:
        import trafilatura  # type: ignore

        extracted = trafilatura.extract(
            html,
            url=url,
            output_format="markdown",
            include_comments=False,
            include_tables=True,
        )
        if extracted and len(extracted.strip()) > 80:
            title = trafilatura.extract(html, url=url, include_comments=False, with_metadata=True)
            md_title = ""
            if isinstance(title, dict):
                md_title = title.get("title") or ""
            result["markdown"] = extracted.strip()
            result["text"] = extracted.strip()
            result["title"] = md_title or None
            result["engine"] = "trafilatura"
            return result
    except Exception:
        pass

    # Fallback: BeautifulSoup plain text
    try:
        from bs4 import BeautifulSoup  # type: ignore

        soup = BeautifulSoup(html, "lxml")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        title_tag = soup.find("title")
        result["text"] = text
        result["markdown"] = text
        result["title"] = title_tag.get_text(strip=True) if title_tag else None
        result["engine"] = "beautifulsoup"
    except Exception:
        result["text"] = ""
        result["markdown"] = ""

    return result
