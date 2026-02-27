import streamlit as st
import webbrowser

st.set_page_config(
    page_title="IntelGenz CTI",
    page_icon="🛡️",
    layout="wide"
)

st.markdown("""
<style>

/* Clean dark professional background */
.stApp {
    background-color: #0f1117;
    color: #e2e8f0;
}

/* Header */
.header {
    padding: 32px 0 8px 0;
    border-bottom: 1px solid #1e2a3a;
    margin-bottom: 36px;
}

.header-title {
    font-size: 28px;
    font-weight: 700;
    color: #f1f5f9;
    letter-spacing: 0.5px;
}

.header-title span {
    color: #38bdf8;
}

.header-sub {
    font-size: 14px;
    color: #64748b;
    margin-top: 4px;
}

/* Status pill */
.status-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: #0f2a1f;
    border: 1px solid #166534;
    color: #4ade80;
    font-size: 12px;
    padding: 4px 12px;
    border-radius: 20px;
    float: right;
    margin-top: 6px;
}

.dot {
    width: 7px;
    height: 7px;
    background: #4ade80;
    border-radius: 50%;
    display: inline-block;
    animation: blink 2s infinite;
}

@keyframes blink {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.3; }
}

/* Section label */
.section-label {
    font-size: 11px;
    font-weight: 600;
    color: #475569;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 16px;
}

/* Cards */
.card {
    background: #161b27;
    border: 1px solid #1e2d40;
    border-radius: 10px;
    padding: 28px 24px;
    height: 160px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
    cursor: pointer;
    text-decoration: none;
}

.card:hover {
    border-color: #38bdf8;
    box-shadow: 0 0 0 1px #38bdf820, 0 4px 20px rgba(56,189,248,0.08);
}

.card-top {
    display: flex;
    align-items: center;
    gap: 14px;
}

.card-icon {
    font-size: 26px;
    width: 48px;
    height: 48px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}

.card-title {
    font-size: 15px;
    font-weight: 600;
    color: #e2e8f0;
    line-height: 1.3;
}

.card-desc {
    font-size: 12px;
    color: #475569;
    margin-top: 2px;
}

.card-badge {
    font-size: 11px;
    font-weight: 500;
    padding: 3px 10px;
    border-radius: 6px;
    display: inline-block;
    align-self: flex-start;
}

.badge-active {
    background: #0f2a1f;
    color: #4ade80;
    border: 1px solid #166534;
}

.badge-soon {
    background: #1a1f2e;
    color: #64748b;
    border: 1px solid #2d3748;
}

/* Divider */
.section-divider {
    border: none;
    border-top: 1px solid #1e2a3a;
    margin: 32px 0 24px 0;
}

/* Footer */
.footer {
    text-align: center;
    font-size: 12px;
    color: #334155;
    padding: 40px 0 20px 0;
    border-top: 1px solid #1e2a3a;
    margin-top: 48px;
}

#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 0 !important; max-width: 1100px; }

</style>
""", unsafe_allow_html=True)

# ── Header ──
st.markdown("""
<div class="header">
    <span class="status-pill"><span class="dot"></span> All Systems Operational</span>
    <div class="header-title">🛡️ Intel<span>Genz</span> CTI</div>
    <div class="header-sub">Cyber Threat Intelligence Platform — Command Dashboard</div>
</div>
""", unsafe_allow_html=True)

# ── Row 1 ──
st.markdown('<div class="section-label">Core Modules</div>', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <a class="card" href="https://cti-source-mangement.streamlit.app/" target="_blank">
        <div class="card-top">
            <div class="card-icon" style="background:#0c2a3a;">📂</div>
            <div>
                <div class="card-title">Source Management</div>
                <div class="card-desc">Manage and configure intelligence sources</div>
            </div>
        </div>
        <span class="card-badge badge-active">● Active</span>
    </a>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="card">
        <div class="card-top">
            <div class="card-icon" style="background:#1a1535;">🔗</div>
            <div>
                <div class="card-title">Source URL Pipeline</div>
                <div class="card-desc">Automated URL ingestion and processing</div>
            </div>
        </div>
        <span class="card-badge badge-soon">Coming Soon</span>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="card">
        <div class="card-top">
            <div class="card-icon" style="background:#0b2420;">📥</div>
            <div>
                <div class="card-title">Data Acquisition</div>
                <div class="card-desc">Collect and normalize raw threat data</div>
            </div>
        </div>
        <span class="card-badge badge-soon">Coming Soon</span>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Row 2 ──
st.markdown('<div class="section-label">Analysis & Intelligence</div>', unsafe_allow_html=True)

col4, col5, col6 = st.columns(3)

with col4:
    st.markdown("""
    <div class="card">
        <div class="card-top">
            <div class="card-icon" style="background:#1a1200;">🧠</div>
            <div>
                <div class="card-title">Cluster Management</div>
                <div class="card-desc">Group and analyze threat actor clusters</div>
            </div>
        </div>
        <span class="card-badge badge-soon">Coming Soon</span>
    </div>
    """, unsafe_allow_html=True)

with col5:
    st.markdown("""
    <div class="card">
        <div class="card-top">
            <div class="card-icon" style="background:#1a0d25;">🛑</div>
            <div>
                <div class="card-title">CVE ID Pipeline</div>
                <div class="card-desc">Track and correlate CVE vulnerabilities</div>
            </div>
        </div>
        <span class="card-badge badge-soon">Coming Soon</span>
    </div>
    """, unsafe_allow_html=True)

with col6:
    st.markdown("""
    <div class="card">
        <div class="card-top">
            <div class="card-icon" style="background:#0a1f2a;">📊</div>
            <div>
                <div class="card-title">Threat Analytics</div>
                <div class="card-desc">Visualize and report on threat intelligence</div>
            </div>
        </div>
        <span class="card-badge badge-soon">Coming Soon</span>
    </div>
    """, unsafe_allow_html=True)

# ── Footer ──
st.markdown("""
<div class="footer">© 2026 IntelGenz · Cyber Threat Intelligence Platform</div>
""", unsafe_allow_html=True)
