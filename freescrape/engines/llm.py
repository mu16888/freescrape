"""Optional LLM helper (OpenAI-compatible). Used by `discover` and AI extraction.

No LLM is required for core scraping. Configure it via `freescrape config set`
(llm_api_key / llm_base_url / llm_model) or environment variables.
Works with OpenAI, OpenRouter, Azure, and local servers (Ollama, LM Studio, vLLM).
"""
from __future__ import annotations

import os
from typing import List, Optional

from freescrape.config import load_config


def is_configured() -> bool:
    cfg = load_config()
    return bool(cfg.get("llm_api_key") or os.environ.get("OPENAI_API_KEY"))


def _client():
    from openai import OpenAI  # type: ignore

    cfg = load_config()
    api_key = cfg.get("llm_api_key") or os.environ.get("OPENAI_API_KEY")
    base_url = cfg.get("llm_base_url") or os.environ.get("OPENAI_BASE_URL") or "https://api.openai.com/v1"
    return OpenAI(api_key=api_key, base_url=base_url)


def complete(prompt: str, system: str = "", *, temperature: float = 0.2) -> str:
    """Single chat completion. Raises RuntimeError if not configured."""
    if not is_configured():
        raise RuntimeError(
            "LLM not configured. Set it with:\n"
            "  freescrape config set llm_api_key sk-...\n"
            "  freescrape config set llm_base_url https://your-endpoint/v1\n"
            "  freescrape config set llm_model <model>\n"
            "Or export OPENAI_API_KEY / OPENAI_BASE_URL."
        )
    cfg = load_config()
    model = cfg.get("llm_model") or os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    resp = _client().chat.completions.create(model=model, messages=messages, temperature=temperature)
    return resp.choices[0].message.content or ""


def discover(query: str, candidates: List[dict], max: int = 5) -> dict:
    """Rank/filter search `candidates` against `query` and summarize via LLM."""
    if not is_configured():
        # Graceful degradation: return raw candidates with a note.
        return {
            "query": query,
            "llm": False,
            "note": "LLM not configured; returning raw search results. Configure LLM for AI ranking.",
            "results": candidates[:max],
        }
    listing = "\n".join(f"{i+1}. {c.get('title')} — {c.get('url')}\n   {c.get('snippet','')}" for i, c in enumerate(candidates))
    system = "You are a research assistant. Given a user intent and a list of search results, pick the most relevant ones and explain why in 2-3 bullet points. Respond in the user's language."
    prompt = f"Intent: {query}\n\nSearch results:\n{listing}\n\nReturn the top {max} most relevant result numbers and a short rationale."
    analysis = complete(prompt, system=system)
    return {"query": query, "llm": True, "analysis": analysis, "results": candidates[:max]}
