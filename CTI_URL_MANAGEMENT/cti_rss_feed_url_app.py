"""
cti_rss_feed_url_app.py
------------------------
Streamlit dashboard for CTI RSS Feed URL Scraper.

Workflow:
  1. Click "Run Daily Scrape"  → fetches RSS feeds, deduplicates in memory, previews new URLs
  2. Click "Push to DB"        → inserts the scraped new URLs into url_db with sequential url_ids

Run with:
    streamlit run cti_rss_feed_url_app.py
"""

import time
import email.utils
import feedparser
import requests
import streamlit as st
import pandas as pd

from cti_rss_feed_url_management import (
    test_connection,
    fetch_all_sources,
    fetch_existing_urls,
    insert_urls,
    build_url_record,
    generate_url_ids_for_batch,
    fetch_status_counts,
    fetch_source_counts,
    fetch_recent_urls,
)

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="CTI RSS Feed URL Scraper",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CyberNewsScraper/1.0)"}

# ─────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────
st.markdown(
    """
    <style>
    .metric-card {
        background: #1e1e2e;
        border: 1px solid #313244;
        border-radius: 12px;
        padding: 20px 24px;
        text-align: center;
    }
    .metric-card .label {
        font-size: 13px;
        color: #a6adc8;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        margin-bottom: 6px;
    }
    .metric-card .value { font-size: 36px; font-weight: 700; }
    .metric-card.total   .value { color: #89b4fa; }
    .metric-card.proc    .value { color: #a6e3a1; }
    .metric-card.unproc  .value { color: #fab387; }
    .metric-card.sources .value { color: #cba6f7; }
    .metric-card.new     .value { color: #f5c2e7; }

    .scrape-log {
        background: #11111b;
        border: 1px solid #313244;
        border-radius: 8px;
        padding: 12px 16px;
        font-family: monospace;
        font-size: 13px;
        color: #cdd6f4;
        max-height: 320px;
        overflow-y: auto;
    }
    .scrape-log .ok   { color: #a6e3a1; }
    .scrape-log .warn { color: #f9e2af; }
    .scrape-log .err  { color: #f38ba8; }
    .scrape-log .info { color: #89b4fa; }

    [data-testid="stDataFrame"] { border-radius: 8px; overflow: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────
# SESSION STATE INIT
# ─────────────────────────────────────────────
# scraped_records  : list of built dicts ready to insert (new URLs only, not yet in DB)
# scrape_summary   : dict with stats shown after scrape
# scrape_done      : True once a scrape has been run this session
if "scraped_records" not in st.session_state:
    st.session_state.scraped_records = []
if "scrape_summary" not in st.session_state:
    st.session_state.scrape_summary = None
if "scrape_done" not in st.session_state:
    st.session_state.scrape_done = False
if "push_done" not in st.session_state:
    st.session_state.push_done = False


# ─────────────────────────────────────────────
# CACHED DB WRAPPERS
# Only functions whose data changes rarely or
# tolerate slight staleness get cached.
#
# NOT cached (must always be fresh):
#   fetch_existing_urls()    — dedup before scrape
#   get_next_url_id_start()  — ID sequencing at push time
#   insert_urls()            — write operation
# ─────────────────────────────────────────────

@st.cache_data(ttl=60, show_spinner=False)
def cached_test_connection():
    """Cache DB ping for 60s — avoids hitting Azure on every rerender."""
    return test_connection()

@st.cache_data(ttl=300, show_spinner=False)
def cached_fetch_all_sources():
    """Cache source list for 5 min — sources change rarely."""
    return fetch_all_sources()

@st.cache_data(ttl=30, show_spinner=False)
def cached_fetch_status_counts():
    """Cache dashboard counts for 30s."""
    return fetch_status_counts()

@st.cache_data(ttl=30, show_spinner=False)
def cached_fetch_source_counts():
    """Cache per-source breakdown for 30s."""
    return fetch_source_counts()

@st.cache_data(ttl=30, show_spinner=False)
def cached_fetch_recent_urls(limit: int):
    """Cache recent URL table for 30s."""
    return fetch_recent_urls(limit)

def clear_dashboard_cache():
    """Call after a push to DB so next render gets fresh counts."""
    cached_fetch_status_counts.clear()
    cached_fetch_source_counts.clear()
    cached_fetch_recent_urls.clear()


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🛡️ CTI RSS Scraper")
    st.markdown("---")

    ok, msg = cached_test_connection()
    if ok:
        st.success("🟢 DB Connected")
    else:
        st.error(f"🔴 DB Error: {msg}")

    st.markdown("---")
    st.markdown("**Settings**")
    url_limit = st.slider("Recent URLs to display", 10, 200, 50, 10)
    st.markdown("---")
    st.markdown(
        "<small style='color:#585b70'>CTI Feed Scraper v1.0<br>by yadhavaprasanna</small>",
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────
# HELPER: metric card HTML
# ─────────────────────────────────────────────
def metric_card(label, value, kind="total"):
    return f"""
    <div class="metric-card {kind}">
        <div class="label">{label}</div>
        <div class="value">{value:,}</div>
    </div>
    """


# ─────────────────────────────────────────────
# CORE SCRAPE — returns new records (no DB write)
# ─────────────────────────────────────────────
def run_scrape(log_placeholder) -> dict:
    """
    Fetch all RSS sources, collect new URLs that are NOT already in url_db.
    Builds record dicts in memory but does NOT insert — returns them for review.
    url_ids are assigned just before insertion (in push_to_db) to avoid gaps.
    """
    logs = []

    def log(msg, kind="info"):
        logs.append(f'<span class="{kind}">{msg}</span>')
        log_placeholder.markdown(
            '<div class="scrape-log">' + "<br>".join(logs) + "</div>",
            unsafe_allow_html=True,
        )

    log("━━━ Daily Scrape Started ━━━")
    log(f"⏱  {time.strftime('%Y-%m-%d %H:%M:%S')} IST")

    # 1. Load sources from DB
    try:
        sources = cached_fetch_all_sources()
        log(f"📋 Loaded {len(sources)} sources from source_db", "ok")
    except Exception as e:
        log(f"FATAL: Cannot load sources — {e}", "err")
        return {"error": str(e)}

    # 2. Load existing URLs for dedup
    try:
        existing_urls = fetch_existing_urls()
        log(f"🗄  {len(existing_urls)} URLs already in url_db")
    except Exception as e:
        log(f"FATAL: Cannot load existing URLs — {e}", "err")
        return {"error": str(e)}

    total_found   = 0
    total_skipped = 0
    new_raw       = []   # list of (url, source_name, source_id, title, published)
    source_stats  = []

    # 3. Scrape each RSS feed
    for src in sources:
        source_name = src["source_name"]
        source_id   = src["source_id"]
        rss_url     = src["source_url"]

        log(f"")
        log(f"📡 [{source_name}]  {rss_url}")

        try:
            resp = requests.get(rss_url, headers=HEADERS, timeout=15, verify=False)
            resp.raise_for_status()
            feed    = feedparser.parse(resp.content)
            entries = feed.entries

            feed_new  = 0
            feed_skip = 0

            for entry in entries:
                url = entry.get("link", "").strip()
                if not url:
                    continue

                total_found += 1

                if url in existing_urls:
                    feed_skip    += 1
                    total_skipped += 1
                    continue

                title     = entry.get("title", None)
                published = entry.get("published", None)
                if not published and entry.get("published_parsed"):
                    published = email.utils.formatdate(
                        time.mktime(entry.published_parsed)
                    )

                existing_urls.add(url)   # prevent duplicates within same scrape run
                new_raw.append((url, source_name, source_id, title, published))
                feed_new += 1

            log(
                f"   ✅ {feed_new} new  |  ⏭ {feed_skip} skipped  "
                f"(feed total {len(entries)})",
                "ok",
            )
            source_stats.append({"Source": source_name, "New": feed_new, "Skipped": feed_skip})

        except Exception as e:
            log(f"   ❌ Error: {e}", "err")
            source_stats.append({"Source": source_name, "New": 0, "Skipped": 0, "Error": str(e)})

    log("")
    log(f"━━━ Scrape Complete ━━━")
    log(f"   Total found   : {total_found}")
    log(f"   Skipped (dup) : {total_skipped}")
    log(f"   New to insert : {len(new_raw)}", "ok")
    if len(new_raw) > 0:
        log(f"   ➡  Click 'Push to DB' to save these {len(new_raw)} URLs.", "warn")
    else:
        log("   ℹ️  Nothing new to push.", "warn")

    return {
        "total_found":  total_found,
        "skipped":      total_skipped,
        "new_count":    len(new_raw),
        "new_raw":      new_raw,       # raw tuples for building records at push time
        "source_stats": source_stats,
    }


# ─────────────────────────────────────────────
# PUSH TO DB
# ─────────────────────────────────────────────
def push_to_db(new_raw: list[tuple]) -> tuple[int, str]:
    """
    Assign sequential url_ids (continuing from DB max) and insert all new records.
    Returns (inserted_count, error_message_or_empty).
    """
    if not new_raw:
        return 0, ""

    try:
        url_ids = generate_url_ids_for_batch(len(new_raw))
    except Exception as e:
        return 0, f"Failed to generate url_ids: {e}"

    records = []
    for url_id, (url, source_name, source_id, title, published) in zip(url_ids, new_raw):
        records.append(
            build_url_record(
                url_id=url_id,
                url=url,
                source_name=source_name,
                source_id=source_id,
                title=title,
                published_str=published,
            )
        )

    try:
        inserted = insert_urls(records)
        return inserted, ""
    except Exception as e:
        return 0, str(e)


# ─────────────────────────────────────────────
# MAIN APP UI
# ─────────────────────────────────────────────
st.title("🛡️ CTI RSS Feed URL Scraper")
st.markdown(
    "Cyber Threat Intelligence — RSS feed aggregator with deduplication and Azure MySQL storage."
)
st.markdown("---")

# ── SECTION 1: Action Buttons ─────────────────
pending = len(st.session_state.scraped_records)

col1, col2, col3 = st.columns([1, 1, 4])

with col1:
    scrape_btn = st.button("🔍 Run Daily Scrape", type="primary", use_container_width=True)

with col2:
    push_label = f"📥 Push to DB ({pending} URLs)" if pending > 0 else "📥 Push to DB"
    push_btn = st.button(
        push_label,
        type="secondary",
        use_container_width=True,
        disabled=(pending == 0),
    )

# ── SCRAPE BUTTON HANDLER ─────────────────────
if scrape_btn:
    # Reset previous scrape state
    st.session_state.scraped_records = []
    st.session_state.scrape_summary  = None
    st.session_state.scrape_done     = False
    st.session_state.push_done       = False

    st.markdown("### 📝 Scrape Log")
    log_box = st.empty()

    with st.spinner("Scraping RSS feeds…"):
        result = run_scrape(log_box)

    if "error" in result:
        st.error(f"Scrape failed: {result['error']}")
    else:
        st.session_state.scraped_records = result["new_raw"]
        st.session_state.scrape_summary  = result
        st.session_state.scrape_done     = True

        if result["new_count"] > 0:
            st.success(
                f"✅ Scrape complete — **{result['new_count']} new URLs** found. "
                f"Click **Push to DB** to save them."
            )
        else:
            st.info("✅ Scrape complete — no new URLs found. Everything is already in DB.")

        if result.get("source_stats"):
            st.markdown("#### Per-Source Summary")
            st.dataframe(
                pd.DataFrame(result["source_stats"]),
                use_container_width=True,
                hide_index=True,
            )

        # Rerun so the Push to DB button re-renders with correct pending count and enabled state
        st.rerun()

# ── PUSH TO DB BUTTON HANDLER ─────────────────
if push_btn and st.session_state.scraped_records:
    with st.spinner(f"Inserting {len(st.session_state.scraped_records)} URLs into DB…"):
        inserted, err = push_to_db(st.session_state.scraped_records)

    if err:
        st.error(f"❌ Push failed: {err}")
    else:
        st.success(f"✅ Successfully pushed **{inserted} URLs** to url_db!")
        st.session_state.scraped_records = []   # clear pending after push
        st.session_state.push_done       = True
        clear_dashboard_cache()                  # invalidate stale cache so dashboard refreshes
        st.rerun()                               # refresh dashboard counts

# ── Pending badge (persists between reruns) ───
if st.session_state.scrape_done and not st.session_state.push_done:
    pending_now = len(st.session_state.scraped_records)
    if pending_now > 0:
        st.warning(
            f"⚠️  **{pending_now} URLs scraped but not yet pushed to DB.** "
            f"Click **Push to DB** above to save them."
        )

st.markdown("---")

# ── SECTION 2: Dashboard Stats ────────────────
st.markdown("### 📊 Dashboard")

try:
    counts     = cached_fetch_status_counts()
    src_counts = cached_fetch_source_counts()
    pending_n  = len(st.session_state.scraped_records)
    summary    = st.session_state.scrape_summary or {}
    last_new     = summary.get("new_count", 0)
    last_skipped = summary.get("skipped", 0)
    last_total   = summary.get("total_found", 0)

    # Row 1: DB counts
    st.markdown("##### 🗄️ Database")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(metric_card("Total URLs",  counts["total"],       "total"),   unsafe_allow_html=True)
    with c2:
        st.markdown(metric_card("Processed",   counts["processed"],   "proc"),    unsafe_allow_html=True)
    with c3:
        st.markdown(metric_card("Unprocessed", counts["unprocessed"], "unproc"),  unsafe_allow_html=True)
    with c4:
        st.markdown(metric_card("Sources",     len(src_counts),       "sources"), unsafe_allow_html=True)

    st.markdown("")

    # Row 2: Last scrape run counts
    st.markdown("##### 🔄 Last Scrape Run")
    c5, c6, c7, c8 = st.columns(4)
    with c5:
        st.markdown(metric_card("Total Scraped",  last_total,   "total"),   unsafe_allow_html=True)
    with c6:
        st.markdown(metric_card("New Found",      last_new,     "new"),     unsafe_allow_html=True)
    with c7:
        st.markdown(metric_card("Skipped (Dup)",  last_skipped, "unproc"),  unsafe_allow_html=True)
    with c8:
        st.markdown(metric_card("Pending Push",   pending_n,    "proc"),    unsafe_allow_html=True)

    st.markdown("")

    if src_counts:
        st.markdown("#### 📡 URLs by Source")
        df_sources = pd.DataFrame(src_counts)
        df_sources.columns = ["Source", "Total", "Processed", "Unprocessed"]
        df_sources = df_sources.fillna(0).astype(
            {"Total": int, "Processed": int, "Unprocessed": int}
        )
        st.dataframe(df_sources, use_container_width=True, hide_index=True)

except Exception as e:
    st.warning(f"Could not load dashboard stats: {e}")

st.markdown("---")

# ── SECTION 3: Scraped preview (before push) ──
if st.session_state.scraped_records and not st.session_state.push_done:
    st.markdown(f"### 🆕 Scraped URLs Preview ({len(st.session_state.scraped_records)} pending)")
    preview_data = [
        {
            "URL":     r[0],
            "Source":  r[1],
            "Title":   r[3] or "—",
            "Published": r[4] or "—",
        }
        for r in st.session_state.scraped_records[:100]   # show max 100 in preview
    ]
    st.dataframe(
        pd.DataFrame(preview_data),
        use_container_width=True,
        hide_index=True,
        column_config={
            "URL": st.column_config.LinkColumn("URL", display_text="Open ↗"),
            "Title": st.column_config.TextColumn("Title", width="large"),
        },
    )
    if len(st.session_state.scraped_records) > 100:
        st.caption(f"Showing first 100 of {len(st.session_state.scraped_records)} scraped URLs.")
    st.markdown("---")

# ── SECTION 4: Recent URLs from DB ────────────
st.markdown(f"### 🔗 Top {url_limit} Recently Added URLs")

try:
    recent = cached_fetch_recent_urls(limit=url_limit)

    if recent:
        df = pd.DataFrame(recent)
        df = df.rename(
            columns={
                "url_id":            "ID",
                "url":               "URL",
                "url_source":        "Source",
                "url_source_id":     "Source ID",
                "url_title":         "Title",
                "url_published_date":"Published (IST)",
                "url_created_type":  "Created Via",
                "url_created_at":    "Added At (IST)",
                "url_status":        "Status",
            }
        )

        def style_status(val):
            if val == "processed":
                return "background-color:#1e3a2a; color:#a6e3a1; border-radius:4px; padding:2px 8px;"
            elif val == "unprocessed":
                return "background-color:#3a2a1e; color:#fab387; border-radius:4px; padding:2px 8px;"
            return ""

        styled = df.style.applymap(style_status, subset=["Status"])

        st.dataframe(
            styled,
            use_container_width=True,
            hide_index=True,
            column_config={
                "URL":            st.column_config.LinkColumn("URL", display_text="Open ↗"),
                "Title":          st.column_config.TextColumn("Title", width="large"),
                "Added At (IST)": st.column_config.DatetimeColumn(
                    "Added At (IST)", format="YYYY-MM-DD HH:mm:ss"
                ),
                "Published (IST)": st.column_config.DatetimeColumn(
                    "Published (IST)", format="YYYY-MM-DD HH:mm:ss"
                ),
            },
        )
    else:
        st.info("No URLs in the database yet. Run a Daily Scrape then Push to DB.")

except Exception as e:
    st.warning(f"Could not load recent URLs: {e}")

# ── Footer ─────────────────────────────────────
st.markdown("---")
st.markdown(
    "<center><small style='color:#585b70'>CTI RSS Feed URL Scraper · by yadhavaprasanna</small></center>",
    unsafe_allow_html=True,
)
