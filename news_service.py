import hashlib
import logging
import requests
import streamlit as st
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from typing import Optional

from config import (
    CATEGORIES,
    MAX_ARTICLES_PER_CATEGORY,
    SIMILARITY_THRESHOLD,
)
from database import cache_articles, get_cached_articles

# 1. AUTHENTICATION: Get GNews Key from Secrets
NEWSAPI_KEY = st.secrets.get("NEWSAPI_KEY")

logger = logging.getLogger(__name__)

# 2. ENDPOINT: Use GNews instead of NewsAPI to avoid Cloud blocks
NEWSAPI_BASE = "https://gnews.io/api/v4/search"

# ── Helpers ──────────────────────────────────────────────────────────────────

def _title_similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def _cache_key(category: str) -> str:
    return hashlib.md5(category.encode()).hexdigest()

def _normalise(raw: dict) -> Optional[dict]:
    """Convert raw GNews article to internal schema."""
    title = (raw.get("title") or "").strip()
    url = (raw.get("url") or "").strip()

    if not title or not url:
        return None

    return {
        "title": title,
        "url": url,
        "source": raw.get("source", {}).get("name", "Unknown"),
        "published_at": raw.get("publishedAt", ""),
        "description": (raw.get("description") or raw.get("content") or "")[:800],
        "image_url": raw.get("image") or "", # GNews uses 'image' not 'urlToImage'
        "summary": [],
    }

# ── Deduplication ─────────────────────────────────────────────────────────────

def deduplicate(articles: list[dict]) -> list[dict]:
    seen_urls = set()
    unique = []
    for article in articles:
        url = article["url"]
        if url in seen_urls: continue
        
        is_dup = False
        for kept in unique:
            if _title_similarity(article["title"], kept["title"]) >= SIMILARITY_THRESHOLD:
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
    if not NEWSAPI_KEY:
        logger.warning("API Key not set.")
        return []

    all_articles = []

    for keyword in keywords:
        try:
            # UPDATED: Using GNews parameter names
            resp = requests.get(
                NEWSAPI_BASE,
                params={
                    "q": keyword,
                    "lang": "en",
                    "token": NEWSAPI_KEY, 
                    "max": MAX_ARTICLES_PER_CATEGORY,
                },
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()

            for raw in data.get("articles", []):
                normalised = _normalise(raw)
                if normalised:
                    all_articles.append(normalised)

        except requests.RequestException as exc:
            logger.error("Request failed for '%s': %s", keyword, exc)

    return all_articles

# ── Public API ────────────────────────────────────────────────────────────────

def get_articles(category: str, force_refresh: bool = False) -> list[dict]:
    key = _cache_key(category)
    if not force_refresh:
        cached = get_cached_articles(key)
        if cached is not None: return cached

    keywords = CATEGORIES.get(category, CATEGORIES["All AI News"])
    raw_articles = _fetch_from_api(keywords)
    unique = deduplicate(raw_articles)
    unique.sort(key=lambda a: a.get("published_at", ""), reverse=True)
    cache_articles(key, unique)
    return unique

def search_articles(query: str) -> list[dict]:
    raw = _fetch_from_api([query], days_back=7)
    return deduplicate(raw)
