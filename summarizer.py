"""
summarizer.py — Gemini 1.5 Flash summarization.

Generates exactly 3 bullet-point sentences for each article.
Uses a tight prompt to keep output consistent and parseable.
Caches summaries in-memory per session to avoid re-calling Gemini
for already-seen articles.
"""
import logging
from functools import lru_cache

import google.generativeai as genai

from config import GEMINI_API_KEY, GEMINI_MODEL

logger = logging.getLogger(__name__)

# Configure Gemini client once at import time
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    _model = genai.GenerativeModel(GEMINI_MODEL)
else:
    _model = None
    logger.warning("GEMINI_API_KEY not set — summaries will be unavailable.")


PROMPT_TEMPLATE = """
You are a professional AI news analyst. Read the article excerpt below and produce
EXACTLY 3 concise bullet points summarising the key information.

Rules:
- Each bullet must be a single sentence, max 20 words.
- Focus on: what happened, who is involved, why it matters.
- Use plain language. No jargon. No opinions.
- Return ONLY the 3 bullets, each starting with "• ".

Article Title: {title}
Article Excerpt: {description}
"""

FALLBACK_BULLETS = [
    "• Summary unavailable — click Read More for the full article.",
    "• The article has not been summarised due to a configuration issue.",
    "• Add your GEMINI_API_KEY to .env to enable AI summaries.",
]


@lru_cache(maxsize=256)
def _summarise_cached(title: str, description: str) -> list[str]:
    """LRU-cached so the same article is never summarised twice per session."""
    if not _model:
        return FALLBACK_BULLETS

    if not description or len(description) < 30:
        return [
            "• This article has minimal preview text available.",
            "• Click Read More to read the full content.",
            "• Summary could not be generated from the available excerpt.",
        ]

    prompt = PROMPT_TEMPLATE.format(title=title, description=description[:600])

    try:
        response = _model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.3,     # low temp = consistent, factual output
                max_output_tokens=150,
            ),
        )
        text = response.text.strip()
        bullets = [line.strip() for line in text.split("\n") if line.strip().startswith("•")]

        # Ensure exactly 3 bullets
        if len(bullets) < 3:
            bullets += FALLBACK_BULLETS[len(bullets):]
        return bullets[:3]

    except Exception as exc:
        logger.error("Gemini summarisation failed for '%s': %s", title[:60], exc)
        return FALLBACK_BULLETS


def summarise(article: dict) -> list[str]:
    """
    Public function. Pass in an article dict, get back a list of 3 bullet strings.
    Updates the article dict in-place and also returns the bullets.
    """
    bullets = _summarise_cached(
        title=article.get("title", ""),
        description=article.get("description", ""),
    )
    article["summary"] = bullets
    return bullets


def summarise_batch(articles: list[dict]) -> list[dict]:
    """Summarise a list of articles. Each article is mutated in-place."""
    for article in articles:
        if not article.get("summary"):
            summarise(article)
    return articles
