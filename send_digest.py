"""
send_digest.py — Standalone script for the daily digest cron job.
Called by GitHub Actions every morning.

Usage: python send_digest.py [--category "All AI News"]
"""
import argparse
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Send Lumina AI daily digest")
    parser.add_argument(
        "--category", default="All AI News",
        help="Category to send (must match config.CATEGORIES key)"
    )
    args = parser.parse_args()

    # Lazy imports — ensures .env is loaded before config runs
    from database import init_db
    from news_service import get_articles
    from summarizer import summarise_batch
    from email_service import send_daily_digest

    init_db()

    logger.info("Fetching articles for category: %s", args.category)
    articles = get_articles(args.category, force_refresh=True)

    if not articles:
        logger.warning("No articles found. Aborting digest.")
        sys.exit(0)

    logger.info("Summarising top 5 articles...")
    summarise_batch(articles[:5])

    logger.info("Sending digest to all subscribers...")
    result = send_daily_digest(articles, category=args.category)

    logger.info(
        "Digest complete — sent: %d, failed: %d",
        result["sent"], result["failed"]
    )

    if result["errors"]:
        for err in result["errors"]:
            logger.warning("Send error: %s", err)

    sys.exit(0 if result["failed"] == 0 else 1)


if __name__ == "__main__":
    main()
