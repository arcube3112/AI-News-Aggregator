"""
news_service.py — Fetch articles from NewsAPI.org, deduplicate, normalise.

Deduplication strategy:
  1. Exact URL match (trivial).
  2. Title similarity via SequenceMatcher — titles above SIMILARITY_THRESHOLD
     are considered the same story; we keep the one with the longer description.
"""
import hashlib
import logging
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from typing import Optional

import requests

from config import (
    NEWSAPI_KEY,
    CATEGORIES,
    MAX_ARTICLES_PER_CATEGORY,
    SIMILARITY_THRESHOLD,
)
from database import cache_articles, get_cached_articles

logger = logging.getLogger(__name__)

NEWSAPI_BASE = "https://newsapi.org/v2/everything"


# ── Helpers ──────────────────────────────────────────────────────────────────

def _title_similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def _cache_key(category: str) -> str:
    return hashlib.md5(category.encode()).hexdigest()


def _normalise(raw: dict) -> Optional[dict]:
    """Convert raw NewsAPI article to our internal schema. Returns None if unusable."""
    title = (raw.get("title") or "").strip()
    url   = (raw.get("url") or "").strip()

    if not title or not url or title == "[Removed]":
        return None

    return {
        "title":       title,
        "url":         url,
        "source":      raw.get("source", {}).get("name", "Unknown"),
        "published_at": raw.get("publishedAt", ""),
        "description": (raw.get("description") or raw.get("content") or "")[:800],
        "image_url":   raw.get("urlToImage") or "",
        "summary":     [],   # filled later by summarizer.py
    }


# ── Deduplication ─────────────────────────────────────────────────────────────

def deduplicate(articles: list[dict]) -> list[dict]:
    """
    Remove near-duplicate articles. O(n²) but n is small (≤200 articles max).
    Keeps the article with the longer description.
    """
    seen_urls: set[str] = set()
    unique: list[dict] = []

    for article in articles:
        url = article["url"]
        if url in seen_urls:
            continue

        # Check title similarity against already-kept articles
        is_dup = False
        for kept in unique:
            if _title_similarity(article["title"], kept["title"]) >= SIMILARITY_THRESHOLD:
                # Keep the one with more content
                if len(article["description"]) > len(kept["description"]):
                    unique.remove(kept)
                    unique.append(article)
                    seen_urls.add(url)
                is_dup = True
                break

        if not is_dup:
            unique.append(article)
            seen_urls.add(url)

    return unique


# ── Fetching ──────────────────────────────────────────────────────────────────

def _fetch_from_api(keywords: list[str], days_back: int = 3) -> list[dict]:
    """
    Hits NewsAPI /everything for each keyword and merges results.
    Uses a 3-day window to keep content fresh without burning quota.
    """
    if not NEWSAPI_KEY:
        logger.warning("NEWSAPI_KEY not set — returning empty list.")
        return []

    from_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    all_articles: list[dict] = []

    for keyword in keywords:
        try:
            resp = requests.get(
                NEWSAPI_BASE,
                params={
                    "q":        keyword,
                    "language": "en",
                    "sortBy":   "publishedAt",
                    "from":     from_date,
                    "pageSize": MAX_ARTICLES_PER_CATEGORY,
                    "apiKey":   NEWSAPI_KEY,
                },
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()

            if data.get("status") != "ok":
                logger.error("NewsAPI error for '%s': %s", keyword, data.get("message"))
                continue

            for raw in data.get("articles", []):
                normalised = _normalise(raw)
                if normalised:
                    all_articles.append(normalised)

        except requests.RequestException as exc:
            logger.error("Request failed for keyword '%s': %s", keyword, exc)

    return all_articles


# ── Public API ────────────────────────────────────────────────────────────────

def get_articles(category: str, force_refresh: bool = False) -> list[dict]:
    """
    Returns deduplicated, normalised articles for the given category.
    Uses cache unless force_refresh=True or cache is stale.
    """
    key = _cache_key(category)

    if not force_refresh:
        cached = get_cached_articles(key)
        if cached is not None:
            return cached

    keywords = CATEGORIES.get(category, CATEGORIES["All AI News"])
    raw_articles = _fetch_from_api(keywords)
    unique = deduplicate(raw_articles)

    # Sort by date descending
    unique.sort(key=lambda a: a.get("published_at", ""), reverse=True)

    cache_articles(key, unique)
    return unique


def search_articles(query: str) -> list[dict]:
    """Ad-hoc search — not cached."""
    raw = _fetch_from_api([query], days_back=7)
    return deduplicate(raw)
