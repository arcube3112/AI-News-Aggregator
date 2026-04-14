"""
config.py — Centralised config. All secrets come from .env, never hardcoded.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── API Keys ────────────────────────────────────────────────────────────────
NEWSAPI_KEY   = os.getenv("NEWSAPI_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
FROM_EMAIL     = os.getenv("FROM_EMAIL", "digest@lumina-ai.com")

# ── News Categories → Search Keywords ───────────────────────────────────────
CATEGORIES = {
    "All AI News":        ["artificial intelligence", "AI research"],
    "Large Language Models": ["LLM", "GPT", "Claude AI", "Gemini", "large language model"],
    "Computer Vision":    ["computer vision", "image recognition", "DALL-E", "Stable Diffusion"],
    "Robotics":           ["AI robotics", "humanoid robot", "Boston Dynamics"],
    "Cybersecurity":      ["AI security", "cybersecurity AI", "adversarial AI"],
    "Healthcare AI":      ["AI healthcare", "medical AI", "AI diagnosis"],
    "AI Policy & Ethics": ["AI regulation", "AI ethics", "AI policy", "AI safety"],
    "Startups & Funding": ["AI startup", "AI funding", "AI investment"],
}

# ── Fetch Settings ───────────────────────────────────────────────────────────
MAX_ARTICLES_PER_CATEGORY = 20
ARTICLES_PER_PAGE         = 9        # 3×3 grid
CACHE_TTL_MINUTES         = 30
SIMILARITY_THRESHOLD      = 0.72     # for dedup (title similarity)

# ── Gemini Model ─────────────────────────────────────────────────────────────
GEMINI_MODEL = "gemini-1.5-flash"

# ── Database ─────────────────────────────────────────────────────────────────
DB_PATH = "lumina_ai.db"
