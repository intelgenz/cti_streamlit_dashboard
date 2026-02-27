import streamlit as st
import webbrowser

# ---------------------------------------------------
# Page Configuration
# ---------------------------------------------------
st.set_page_config(
    page_title="IntelGenz CTI",
    page_icon="🛡️",
    layout="wide"
)

# ---------------------------------------------------
# Custom CSS - Premium Production Look
# ---------------------------------------------------
st.markdown("""
<style>

/* Background */
.stApp {
    background: linear-gradient(120deg, #141e30, #243b55);
    color: white;
}

/* Neon Visible Title */
.main-title {
    font-size: 60px;
    font-weight: 900;
    text-align: center;
    color: #00f5ff;
    text-shadow: 0px 0px 25px #00f5ff;
    margin-bottom: 10px;
}

/* Subtitle */
.subtitle {
    text-align: center;
    font-size: 20px;
    color: #e2e8f0;
    margin-bottom: 60px;
}

/* Big Rectangle Buttons */
.big-tile button {
    height: 200px;
    font-size: 24px;
    font-weight: 700;
    border-radius: 25px;
    border: none;
    transition: all 0.4s ease;
}

/* Tile Colors */
.source button {
    background: linear-gradient(135deg, #ff512f, #dd2476);
    color: white;
}

.pipeline button {
    background: linear-gradient(135deg, #24c6dc, #514a9d);
    color: white;
}

.data button {
    background: linear-gradient(135deg, #11998e, #38ef7d);
    color: white;
}

.cluster button {
    background: linear-gradient(135deg, #f7971e, #ffd200);
    color: black;
}

.cve button {
    background: linear-gradient(135deg, #8e2de2, #4a00e0);
    color: white;
}

/* Hover Effect */
.big-tile button:hover {
    transform: scale(1.04);
    box-shadow: 0px 15px 45px rgba(0,0,0,0.5);
}

/* Footer */
.footer {
    text-align: center;
    margin-top: 80px;
    font-size: 14px;
    color: #cbd5e1;
}

</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# Header Section
# ---------------------------------------------------
st.markdown('<div class="main-title">🛡️ IntelGenz CTI</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Next-Gen Cyber Threat Intelligence Platform</div>', unsafe_allow_html=True)

# ---------------------------------------------------
# Big Rectangle Tiles Layout
# ---------------------------------------------------

# Row 1
col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="big-tile source">', unsafe_allow_html=True)
    if st.button("📂  Source Management", use_container_width=True):
        webbrowser.open("https://www.cricbuzz.com/")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="big-tile pipeline">', unsafe_allow_html=True)
    if st.button("🔗  Source URL Pipeline\n\nWill be available soon", use_container_width=True):
        st.warning("Will be available soon 🚀")
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown(" ")

# Row 2
col3, col4 = st.columns(2)

with col3:
    st.markdown('<div class="big-tile data">', unsafe_allow_html=True)
    if st.button("📥  Data Acquisition Pipeline\n\nWill be available soon", use_container_width=True):
        st.warning("Will be available soon 🚀")
    st.markdown('</div>', unsafe_allow_html=True)

with col4:
    st.markdown('<div class="big-tile cluster">', unsafe_allow_html=True)
    if st.button("🧠  Cluster Management\n\nWill be available soon", use_container_width=True):
        st.warning("Will be available soon 🚀")
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown(" ")

# Row 3 - Full Width
st.markdown('<div class="big-tile cve">', unsafe_allow_html=True)
if st.button("🛑  CVE ID Pipeline  —  Will be available soon", use_container_width=True):
    st.warning("Will be available soon 🚀")
st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------
# Footer
# ---------------------------------------------------
st.markdown(
    '<div class="footer">© 2026 IntelGenz | Cyber Threat Intelligence Platform</div>',
    unsafe_allow_html=True
)
