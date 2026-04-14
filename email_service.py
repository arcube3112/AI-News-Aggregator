"""
email_service.py — Email delivery via Resend API.

Two modes:
1. send_article(email, article)  — single article card email
2. send_daily_digest(category)   — fetch top articles, email all subscribers
"""
import logging
from datetime import date

import resend

from config import RESEND_API_KEY, FROM_EMAIL
from database import get_all_subscribers

logger = logging.getLogger(__name__)

if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY
else:
    logger.warning("RESEND_API_KEY not set — emails will not be sent.")


# ── HTML Templates ────────────────────────────────────────────────────────────

def _article_card_html(article: dict) -> str:
    bullets = article.get("summary", [])
    bullet_html = "".join(f"<li>{b.lstrip('• ')}</li>" for b in bullets)
    return f"""
    <div style="border:1px solid #E5E7EB;border-radius:12px;padding:24px;margin-bottom:20px;
                font-family:'Helvetica Neue',sans-serif;background:#ffffff;">
        <p style="font-size:11px;color:#9CA3AF;margin:0 0 8px;">
            {article.get('source','Unknown')} &nbsp;·&nbsp;
            {article.get('published_at','')[:10]}
        </p>
        <h2 style="font-size:18px;color:#1F2937;margin:0 0 12px;line-height:1.4;">
            {article.get('title','')}
        </h2>
        <ul style="color:#374151;font-size:14px;line-height:1.7;padding-left:18px;margin:0 0 16px;">
            {bullet_html}
        </ul>
        <a href="{article.get('url','#')}"
           style="display:inline-block;background:#1F2937;color:#ffffff;
                  text-decoration:none;padding:10px 20px;border-radius:8px;font-size:13px;">
            Read Full Article →
        </a>
    </div>
    """


def _email_wrapper(title: str, body_html: str) -> str:
    return f"""
    <!DOCTYPE html>
    <html>
    <body style="margin:0;padding:0;background:#F9FAFB;font-family:'Helvetica Neue',sans-serif;">
        <div style="max-width:640px;margin:40px auto;padding:0 16px;">
            <!-- Header -->
            <div style="text-align:center;padding:32px 0 24px;">
                <span style="font-size:22px;font-weight:700;color:#1F2937;
                             letter-spacing:-0.5px;">Lumina <span style="color:#9CA3AF;">AI</span></span>
                <p style="font-size:13px;color:#9CA3AF;margin:6px 0 0;">{title}</p>
            </div>

            <!-- Body -->
            {body_html}

            <!-- Footer -->
            <div style="text-align:center;padding:32px 0;border-top:1px solid #E5E7EB;margin-top:32px;">
                <p style="font-size:12px;color:#9CA3AF;margin:0;">
                    You're receiving this from Lumina AI.<br>
                    <a href="#" style="color:#9CA3AF;">Unsubscribe</a>
                </p>
            </div>
        </div>
    </body>
    </html>
    """


# ── Public Functions ──────────────────────────────────────────────────────────

def send_article(to_email: str, article: dict) -> tuple[bool, str]:
    """Send a single article card to one email address."""
    if not RESEND_API_KEY:
        return False, "RESEND_API_KEY is not configured."

    try:
        body = _email_wrapper(
            title=f"Article from {article.get('source', 'Lumina AI')}",
            body_html=_article_card_html(article),
        )
        resend.Emails.send({
            "from":    FROM_EMAIL,
            "to":      [to_email],
            "subject": f"📰 {article.get('title', 'AI News from Lumina')[:80]}",
            "html":    body,
        })
        return True, f"Article sent to {to_email}."
    except Exception as exc:
        logger.error("send_article failed: %s", exc)
        return False, f"Failed to send email: {exc}"


def send_daily_digest(articles: list[dict], category: str = "All AI News") -> dict:
    """
    Send the top articles to ALL active subscribers.
    Returns a results dict: {sent: int, failed: int, errors: list}
    """
    if not RESEND_API_KEY:
        return {"sent": 0, "failed": 0, "errors": ["RESEND_API_KEY not configured."]}

    subscribers = get_all_subscribers()
    if not subscribers:
        return {"sent": 0, "failed": 0, "errors": ["No active subscribers."]}

    # Build the digest body — top 5 articles
    top_articles = articles[:5]
    cards_html = "".join(_article_card_html(a) for a in top_articles)
    body = _email_wrapper(
        title=f"Your daily AI digest · {date.today().strftime('%B %d, %Y')} · {category}",
        body_html=cards_html,
    )
    subject = f"🔦 Lumina AI Digest — {date.today().strftime('%b %d')} · {category}"

    sent, failed, errors = 0, 0, []

    for email in subscribers:
        try:
            resend.Emails.send({
                "from":    FROM_EMAIL,
                "to":      [email],
                "subject": subject,
                "html":    body,
            })
            sent += 1
        except Exception as exc:
            logger.error("Digest send failed for %s: %s", email, exc)
            failed += 1
            errors.append(f"{email}: {exc}")

    return {"sent": sent, "failed": failed, "errors": errors}
