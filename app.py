"""
app.py — Lumina AI | Main Streamlit application.

Runs with: streamlit run app.py
"""
import time
import streamlit as st

from config import CATEGORIES, ARTICLES_PER_PAGE
from database import init_db, add_subscriber, add_bookmark, get_bookmarks, remove_bookmark
from news_service import get_articles, search_articles
from summarizer import summarise_batch
from email_service import send_article

# ── Page config (must be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="Lumina AI",
    page_icon="🔦",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_db()


# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* ── Import Fonts ── */
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Serif+Display&display=swap');

    /* ── Global Reset ── */
    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
        background-color: #F9FAFB !important;
        color: #1F2937;
    }

    /* ── Hide Streamlit Chrome ── */
    #MainMenu, footer, header { visibility: hidden; }
    .block-container { padding: 2rem 2.5rem 4rem !important; }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background: #FFFFFF !important;
        border-right: 1px solid #E5E7EB;
        padding-top: 1.5rem;
    }
    [data-testid="stSidebar"] .stRadio label {
        font-size: 0.88rem;
        font-weight: 500;
        color: #374151;
        padding: 6px 0;
        cursor: pointer;
    }
    [data-testid="stSidebar"] .stRadio [data-checked="true"] label {
        color: #1F2937;
        font-weight: 600;
    }

    /* ── Page title ── */
    .lumina-header {
        display: flex;
        align-items: baseline;
        gap: 6px;
        margin-bottom: 4px;
    }
    .lumina-logo {
        font-family: 'DM Serif Display', serif;
        font-size: 2rem;
        font-weight: 400;
        color: #1F2937;
        letter-spacing: -0.5px;
    }
    .lumina-logo-accent { color: #9CA3AF; }
    .lumina-tagline {
        font-size: 0.82rem;
        color: #9CA3AF;
        font-weight: 400;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        margin-bottom: 1.8rem;
    }

    /* ── Search bar ── */
    .stTextInput input {
        border: 1px solid #E5E7EB !important;
        border-radius: 10px !important;
        background: #FFFFFF !important;
        font-family: 'DM Sans', sans-serif !important;
        font-size: 0.9rem !important;
        padding: 12px 16px !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04) !important;
        color: #1F2937 !important;
    }
    .stTextInput input:focus {
        border-color: #9CA3AF !important;
        box-shadow: 0 0 0 3px rgba(156,163,175,0.15) !important;
    }

    /* ── News Card ── */
    .news-card {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 14px;
        padding: 22px 22px 18px;
        margin-bottom: 0;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.04), 0 2px 4px -1px rgba(0,0,0,0.02);
        transition: box-shadow 0.2s ease, transform 0.2s ease;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .news-card:hover {
        box-shadow: 0 8px 16px -2px rgba(0,0,0,0.08);
        transform: translateY(-2px);
    }
    .card-source-badge {
        display: inline-block;
        background: #F3F4F6;
        color: #6B7280;
        font-size: 0.73rem;
        font-weight: 600;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        padding: 3px 10px;
        border-radius: 20px;
        margin-bottom: 10px;
    }
    .card-title {
        font-family: 'DM Serif Display', serif;
        font-size: 1.05rem;
        font-weight: 400;
        color: #111827;
        line-height: 1.45;
        margin: 0 0 14px;
    }
    .card-date {
        font-size: 0.75rem;
        color: #9CA3AF;
        margin-bottom: 12px;
    }
    .card-summary {
        list-style: none;
        padding: 0;
        margin: 0 0 16px;
    }
    .card-summary li {
        font-size: 0.84rem;
        color: #4B5563;
        line-height: 1.65;
        padding: 3px 0 3px 16px;
        position: relative;
    }
    .card-summary li::before {
        content: "–";
        position: absolute;
        left: 0;
        color: #9CA3AF;
    }
    .card-image {
        width: 100%;
        height: 160px;
        object-fit: cover;
        border-radius: 8px;
        margin-bottom: 14px;
    }

    /* ── Buttons ── */
    .stButton > button {
        font-family: 'DM Sans', sans-serif !important;
        font-size: 0.82rem !important;
        font-weight: 500 !important;
        border-radius: 8px !important;
        padding: 7px 16px !important;
        border: 1px solid #E5E7EB !important;
        background: #FFFFFF !important;
        color: #374151 !important;
        transition: all 0.15s ease !important;
    }
    .stButton > button:hover {
        background: #F9FAFB !important;
        border-color: #9CA3AF !important;
        color: #1F2937 !important;
    }
    .primary-btn > button {
        background: #1F2937 !important;
        color: #FFFFFF !important;
        border-color: #1F2937 !important;
    }
    .primary-btn > button:hover {
        background: #374151 !important;
        border-color: #374151 !important;
    }

    /* ── Divider ── */
    hr { border: none; border-top: 1px solid #E5E7EB; margin: 2rem 0; }

    /* ── Digest footer ── */
    .digest-banner {
        background: #1F2937;
        border-radius: 16px;
        padding: 32px 36px;
        margin-top: 3rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 24px;
    }
    .digest-banner h3 {
        font-family: 'DM Serif Display', serif;
        font-size: 1.4rem;
        color: #F9FAFB;
        margin: 0 0 6px;
        font-weight: 400;
    }
    .digest-banner p {
        font-size: 0.85rem;
        color: #9CA3AF;
        margin: 0;
    }

    /* ── Status/info messages ── */
    .stSuccess, .stInfo, .stWarning, .stError {
        border-radius: 10px !important;
        font-size: 0.85rem !important;
    }

    /* ── Spinner ── */
    .stSpinner > div { border-color: #1F2937 transparent transparent !important; }

    /* ── Pagination ── */
    .page-indicator {
        text-align: center;
        font-size: 0.8rem;
        color: #9CA3AF;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


# ── Session state defaults ────────────────────────────────────────────────────
if "page" not in st.session_state:
    st.session_state.page = 0
if "active_category" not in st.session_state:
    st.session_state.active_category = "All AI News"
if "search_query" not in st.session_state:
    st.session_state.search_query = ""
if "view" not in st.session_state:
    st.session_state.view = "feed"  # "feed" | "bookmarks"


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
        <div style="padding:0 0 20px;">
            <span style="font-family:'DM Serif Display',serif;font-size:1.4rem;color:#1F2937;">
                Lumina <span style="color:#9CA3AF;">AI</span>
            </span><br>
            <span style="font-size:0.72rem;color:#9CA3AF;text-transform:uppercase;
                         letter-spacing:0.07em;">Intelligence Feed</span>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("**Categories**")
    category_list = list(CATEGORIES.keys())

    selected = st.radio(
        label="",
        options=category_list,
        index=category_list.index(st.session_state.active_category),
        label_visibility="collapsed",
    )

    if selected != st.session_state.active_category:
        st.session_state.active_category = selected
        st.session_state.page = 0
        st.session_state.search_query = ""
        st.rerun()

    st.markdown("<hr>", unsafe_allow_html=True)

    # View toggle
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("📰 Feed", use_container_width=True):
            st.session_state.view = "feed"
            st.rerun()
    with col_b:
        if st.button("🔖 Saved", use_container_width=True):
            st.session_state.view = "bookmarks"
            st.rerun()

    st.markdown("<hr>", unsafe_allow_html=True)

    # Refresh
    if st.button("↻  Refresh Feed", use_container_width=True):
        from database import clear_cache
        clear_cache()
        st.session_state.page = 0
        st.cache_data.clear()
        st.rerun()


# ── Main content ──────────────────────────────────────────────────────────────

# Header
st.markdown(f"""
    <div class="lumina-header">
        <span class="lumina-logo">Lumina <span class="lumina-logo-accent">AI</span></span>
    </div>
    <div class="lumina-tagline">Your intelligent AI news briefing</div>
""", unsafe_allow_html=True)

# ── BOOKMARKS VIEW ────────────────────────────────────────────────────────────
if st.session_state.view == "bookmarks":
    st.markdown("### 🔖 Saved Articles")
    bookmarks = get_bookmarks()

    if not bookmarks:
        st.info("No bookmarks yet. Save articles from the feed using the bookmark button.")
    else:
        for i, bm in enumerate(bookmarks):
            with st.container():
                st.markdown(f"""
                    <div class="news-card">
                        <div>
                            <span class="card-source-badge">{bm['source']}</span>
                            <p class="card-title">{bm['title']}</p>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

                col1, col2 = st.columns([1, 1])
                with col1:
                    st.link_button("Read More →", bm["url"], use_container_width=True)
                with col2:
                    if st.button("🗑 Remove", key=f"rm_bm_{i}", use_container_width=True):
                        remove_bookmark(bm["url"])
                        st.rerun()

    st.stop()


# ── FEED VIEW ─────────────────────────────────────────────────────────────────

# Search bar
search_input = st.text_input(
    label="",
    placeholder="🔍  Search AI news...",
    value=st.session_state.search_query,
    label_visibility="collapsed",
)

if search_input != st.session_state.search_query:
    st.session_state.search_query = search_input
    st.session_state.page = 0

# Fetch articles
with st.spinner("Fetching latest articles..."):
    if st.session_state.search_query.strip():
        articles = search_articles(st.session_state.search_query.strip())
        feed_label = f'Results for "{st.session_state.search_query}"'
    else:
        articles = get_articles(st.session_state.active_category)
        feed_label = st.session_state.active_category

if not articles:
    st.warning("No articles found. Try a different category or search term.")
    st.stop()

# Summarise visible page only (saves Gemini quota)
total = len(articles)
page  = st.session_state.page
start = page * ARTICLES_PER_PAGE
end   = min(start + ARTICLES_PER_PAGE, total)
page_articles = articles[start:end]

with st.spinner("Generating AI summaries..."):
    summarise_batch(page_articles)

# Feed label + count
st.markdown(f"""
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:1.2rem;">
        <span style="font-size:0.95rem;font-weight:600;color:#1F2937;">{feed_label}</span>
        <span style="font-size:0.78rem;color:#9CA3AF;">{total} articles</span>
    </div>
""", unsafe_allow_html=True)

# ── News Cards Grid (3 columns) ───────────────────────────────────────────────
cols = st.columns(3, gap="medium")

for idx, article in enumerate(page_articles):
    col = cols[idx % 3]
    with col:
        # Format date
        pub_raw = article.get("published_at", "")
        pub_display = pub_raw[:10] if pub_raw else ""

        # Summary bullets
        bullets = article.get("summary", [])
        bullets_html = "".join(
            f'<li>{b.lstrip("• ").strip()}</li>' for b in bullets
        )

        # Card HTML
        image_html = ""
        if article.get("image_url"):
            image_html = f'<img class="card-image" src="{article["image_url"]}" alt="" onerror="this.style.display=\'none\'">'

        st.markdown(f"""
            <div class="news-card">
                {image_html}
                <div>
                    <span class="card-source-badge">{article.get('source','Unknown')}</span>
                    <p class="card-title">{article.get('title','')}</p>
                    <p class="card-date">{pub_display}</p>
                    <ul class="card-summary">{bullets_html}</ul>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Action buttons
        b1, b2, b3 = st.columns(3)

        with b1:
            st.link_button("Read →", article["url"], use_container_width=True)

        with b2:
            bm_key = f"bm_{start + idx}"
            if st.button("🔖", key=bm_key, use_container_width=True, help="Save for later"):
                ok, msg = add_bookmark(
                    url=article["url"],
                    title=article["title"],
                    source=article.get("source", ""),
                    summary="\n".join(article.get("summary", [])),
                )
                st.toast(msg)

        with b3:
            email_key = f"email_btn_{start + idx}"
            if st.button("✉", key=email_key, use_container_width=True, help="Send to email"):
                st.session_state[f"show_email_{start + idx}"] = True

        # Inline email input (shown only when button clicked)
        email_input_key = f"show_email_{start + idx}"
        if st.session_state.get(email_input_key):
            with st.form(key=f"email_form_{start + idx}"):
                to_email = st.text_input("Enter email", placeholder="you@example.com",
                                          label_visibility="collapsed")
                send_col, cancel_col = st.columns(2)
                with send_col:
                    submitted = st.form_submit_button("Send", use_container_width=True)
                with cancel_col:
                    if st.form_submit_button("Cancel", use_container_width=True):
                        st.session_state[email_input_key] = False
                        st.rerun()

                if submitted and to_email:
                    with st.spinner("Sending..."):
                        ok, msg = send_article(to_email, article)
                    if ok:
                        st.success(msg)
                        st.session_state[email_input_key] = False
                    else:
                        st.error(msg)

        # Spacer between cards
        st.markdown("<div style='margin-bottom:1.2rem;'></div>", unsafe_allow_html=True)


# ── Pagination ────────────────────────────────────────────────────────────────
st.markdown("<hr>", unsafe_allow_html=True)
total_pages = (total + ARTICLES_PER_PAGE - 1) // ARTICLES_PER_PAGE

p_col1, p_col2, p_col3 = st.columns([1, 2, 1])

with p_col1:
    if page > 0:
        if st.button("← Previous", use_container_width=True):
            st.session_state.page -= 1
            st.rerun()

with p_col2:
    st.markdown(
        f'<p class="page-indicator">Page {page + 1} of {total_pages}</p>',
        unsafe_allow_html=True,
    )

with p_col3:
    if end < total:
        if st.button("Next →", use_container_width=True):
            st.session_state.page += 1
            st.rerun()


# ── Daily Digest Subscribe Banner ─────────────────────────────────────────────
st.markdown("<div style='margin-top:3rem;'></div>", unsafe_allow_html=True)

st.markdown("""
    <div class="digest-banner">
        <div>
            <h3>Get your daily AI briefing</h3>
            <p>Top stories delivered to your inbox every morning at 8:00 AM.</p>
        </div>
    </div>
""", unsafe_allow_html=True)

st.markdown("<div style='margin-top:1rem;'></div>", unsafe_allow_html=True)

with st.form("subscribe_form"):
    sub_col1, sub_col2 = st.columns([3, 1])
    with sub_col1:
        sub_email = st.text_input(
            label="",
            placeholder="your@email.com",
            label_visibility="collapsed",
        )
    with sub_col2:
        subscribed = st.form_submit_button("Subscribe →", use_container_width=True)

    if subscribed:
        if sub_email and "@" in sub_email:
            ok, msg = add_subscriber(sub_email)
            if ok:
                st.success(f"✓ {msg} You'll receive your first digest tomorrow.")
            else:
                st.info(msg)
        else:
            st.warning("Please enter a valid email address.")

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
    <div style="text-align:center;padding:3rem 0 1rem;font-size:0.75rem;color:#9CA3AF;">
        Lumina AI · Powered by NewsAPI, Gemini 1.5 Flash & Resend
    </div>
""", unsafe_allow_html=True)
