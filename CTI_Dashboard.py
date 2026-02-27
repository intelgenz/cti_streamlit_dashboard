import streamlit as st

# -------------------- PAGE CONFIG --------------------
st.set_page_config(
    page_title="IntelGenz CTI",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# -------------------- CUSTOM CSS --------------------
# Injects styles to make buttons and the link tile look like sleek cards
st.markdown("""
<style>
    /* Style for all tile containers */
    div[data-testid="column"] {
        display: flex;
        justify-content: center;
        margin-bottom: 20px;
    }

    /* Style for Streamlit buttons (used for non‑link tiles) */
    .stButton > button {
        width: 280px;
        height: 160px;
        background: linear-gradient(145deg, #f0f2f6, #ffffff);
        border: 1px solid #e0e4e9;
        border-radius: 16px;
        box-shadow: 0 8px 16px rgba(0,0,0,0.05);
        font-size: 1.2rem;
        font-weight: 600;
        color: #1e293b;
        transition: all 0.2s ease-in-out;
        cursor: pointer;
        padding: 20px;
        display: flex;
        align-items: center;
        justify-content: center;
        text-align: center;
        line-height: 1.4;
    }

    .stButton > button:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 24px rgba(0,0,0,0.1);
        border-color: #a5b4cb;
        color: #0f172a;
    }

    /* Style for the custom link tile (Source Management) */
    .tile-link {
        width: 280px;
        height: 160px;
        background: linear-gradient(145deg, #f0f2f6, #ffffff);
        border: 1px solid #e0e4e9;
        border-radius: 16px;
        box-shadow: 0 8px 16px rgba(0,0,0,0.05);
        font-size: 1.2rem;
        font-weight: 600;
        color: #1e293b;
        transition: all 0.2s ease-in-out;
        display: flex;
        align-items: center;
        justify-content: center;
        text-align: center;
        line-height: 1.4;
        text-decoration: none;
        cursor: pointer;
    }

    .tile-link:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 24px rgba(0,0,0,0.1);
        border-color: #a5b4cb;
        background: #ffffff;
    }

    .tile-link a {
        text-decoration: none;
        color: inherit;
        width: 100%;
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    /* Adjust layout for small screens */
    @media (max-width: 768px) {
        .stButton > button, .tile-link {
            width: 240px;
            height: 140px;
            font-size: 1rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# -------------------- HEADER --------------------
st.title("🛡️ IntelGenz CTI Dashboard")
st.markdown("---")

# -------------------- TILE DEFINITIONS --------------------
# Each tile: (title, is_link, url_or_message)
# is_link = True only for Source Management
tiles = [
    {"title": "Source Management", "is_link": True, "url": "https://www.cricbuzz.com/"},
    {"title": "Source URL Pipeline", "is_link": False, "message": "Will be available soon"},
    {"title": "Data Acquisition Pipeline", "is_link": False, "message": "Will be available soon"},
    {"title": "Cluster Management", "is_link": False, "message": "Will be available soon"},
    {"title": "CVE ID Pipeline", "is_link": False, "message": "Will be available soon"},
]

# Arrange tiles in rows of 3, then 2 (total 5)
rows = [tiles[:3], tiles[3:]]

for row in rows:
    cols = st.columns(len(row))
    for col, tile in zip(cols, row):
        with col:
            if tile["is_link"]:
                # Render clickable tile that opens the URL in a new tab
                st.markdown(
                    f"""
                    <div class="tile-link">
                        <a href="{tile['url']}" target="_blank">{tile['title']}</a>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                # Render a button that shows an info message when clicked
                if st.button(tile["title"], key=tile["title"]):
                    st.info(tile["message"])

# -------------------- FOOTER (optional) --------------------
st.markdown("---")
st.caption("🔐 IntelGenz CTI – Threat Intelligence Dashboard")
