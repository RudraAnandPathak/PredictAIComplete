"""Live news retrieval using public Google News RSS; no API key required."""
from __future__ import annotations
from urllib.parse import quote_plus
from xml.etree import ElementTree as ET
from datetime import datetime, timezone
import requests

USER_AGENT = "PredictAI/6.0 (news research; contact: local app)"


def search_news(query: str, limit: int = 8, language: str = "en", country: str = "IN") -> list[dict[str, str]]:
    query = (query or "").strip()
    if len(query) < 2:
        raise ValueError("Enter a specific topic or question to search for news.")
    limit = max(1, min(int(limit), 20))
    url = f"https://news.google.com/rss/search?q={quote_plus(query)}&hl={language}-{country}&gl={country}&ceid={country}:{language}"
    try:
        response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=(8, 20))
        response.raise_for_status()
        root = ET.fromstring(response.content)
    except requests.RequestException as exc:
        raise RuntimeError("Live news retrieval failed. Check your internet connection and try again.") from exc
    except ET.ParseError as exc:
        raise RuntimeError("The news provider returned an unreadable feed.") from exc
    results = []
    for item in root.findall("./channel/item")[:limit]:
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        published = (item.findtext("pubDate") or "").strip()
        source_el = item.find("source")
        source = (source_el.text or "Unknown source").strip() if source_el is not None else "Source shown in article title"
        description = (item.findtext("description") or "").strip()
        # RSS description may contain HTML; UI escapes it and does not treat it as trusted instructions.
        results.append({"title": title, "url": link, "published": published, "source": source, "snippet": description[:1200], "retrieved_at": datetime.now(timezone.utc).isoformat()})
    return results


def format_news_context(items: list[dict[str, str]], max_chars: int = 12000) -> str:
    chunks = []
    used = 0
    for i, item in enumerate(items, 1):
        part = f"[{i}] {item.get('title','')}\nSource: {item.get('source','')}\nPublished: {item.get('published','')}\nURL: {item.get('url','')}\nSnippet: {item.get('snippet','')}"
        if used + len(part) > max_chars:
            break
        chunks.append(part)
        used += len(part)
    return "\n\n".join(chunks)
