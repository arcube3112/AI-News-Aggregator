# Lumina AI — News Aggregator

## Stack
- **Frontend/Backend**: Streamlit (Python)
- **News**: NewsAPI.org
- **Summarization**: Google Gemini 1.5 Flash
- **Email**: Resend API
- **Database**: SQLite (local) / swap to Supabase for production

## Directory Structure
```
lumina-ai/
├── app.py                  # Main Streamlit app (UI + routing)
├── news_service.py         # NewsAPI fetching + deduplication
├── summarizer.py           # Gemini summarization logic
├── email_service.py        # Resend email + digest builder
├── database.py             # SQLite: emails, bookmarks, cache
├── config.py               # API keys, constants (load from .env)
├── requirements.txt
└── .env.example
```

## Setup
```bash
pip install -r requirements.txt
cp .env.example .env
# Fill in your API keys in .env
streamlit run app.py
```

## Environment Variables
```
NEWSAPI_KEY=your_newsapi_org_key
GEMINI_API_KEY=your_gemini_api_key
RESEND_API_KEY=your_resend_api_key
FROM_EMAIL=digest@yourdomain.com
```

## GitHub Actions (Daily Digest)
See `.github/workflows/daily_digest.yml` — runs at 08:00 UTC daily.
