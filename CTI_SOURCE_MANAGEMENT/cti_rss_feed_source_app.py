import streamlit as st
import pandas as pd
import time
from cti_rss_feed_source_management import (
    add_source, update_source, delete_source, get_all_sources
)

st.set_page_config(
    page_title="IntelGenz CTI RSS Feed Source Management",
    page_icon="📡",
    layout="wide"
)

# Custom CSS for better appearance
st.markdown("""
<style>
    .main-header { font-size: 2.5rem; color: #0a2351; text-align: center; margin-bottom: 1rem; }
    .sub-header { font-size: 1.5rem; color: #1e3a5f; margin-top: 2rem; margin-bottom: 1rem; }
    .stButton>button { background-color: #0a2351; color: white; border-radius: 5px; }
    .stButton>button:hover { background-color: #1e3a5f; }
    .delete-btn>button { background-color: #b22222; }
    .delete-btn>button:hover { background-color: #8b0000; }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-header">📡 IntelGenz CTI RSS Feed Source Management</h1>', unsafe_allow_html=True)

# -------------------- Sidebar: Add / Edit Form --------------------
creators = ["Manesh", "John", "Anish", "Yadhavaprasanna"]

with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/rss.png", width=80)
    st.markdown("## Source Management")

    # Initialize session state
    if 'edit_mode' not in st.session_state:
        st.session_state.edit_mode = False
        st.session_state.edit_source = None
    if 'delete_id' not in st.session_state:
        st.session_state.delete_id = None

    if st.session_state.edit_mode and st.session_state.edit_source:
        st.markdown(f"### ✏️ Edit Source: {st.session_state.edit_source['source_id']}")
        default_name = st.session_state.edit_source['source_name']
        default_url = st.session_state.edit_source['source_url']
        form_key = "edit_form"
        submit_label = "Update Source"
    else:
        st.markdown("### ➕ Add New Source")
        default_name = ""
        default_url = ""
        form_key = "add_form"
        submit_label = "Add Source"

    with st.form(key=form_key):
        name = st.text_input("Source Name *", value=default_name, placeholder="e.g., BleepingComputer")
        url = st.text_input("Source URL *", value=default_url, placeholder="https://example.com/feed.xml")
        person = st.selectbox(
            "Created By *" if not st.session_state.edit_mode else "Updated By *",
            options=creators,
            index=0
        )
        submitted = st.form_submit_button(submit_label)

        if submitted:
            if not name or not url or not person:
                st.error("All fields are required!")
            elif st.session_state.edit_mode:
                success, msg = update_source(
                    st.session_state.edit_source['source_id'],
                    name, url, person
                )
                if success:
                    st.success(msg)
                    st.session_state.edit_mode = False
                    st.session_state.edit_source = None
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(msg)
            else:
                success, msg, new_id = add_source(name, url, person)
                if success:
                    st.success(f"{msg} (ID: {new_id})")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(msg)

    # Cancel edit button (only visible in edit mode)
    if st.session_state.edit_mode:
        if st.button("Cancel Edit"):
            st.session_state.edit_mode = False
            st.session_state.edit_source = None
            st.rerun()

    st.markdown("---")
    st.markdown("**Creators:** Manesh, John, Anish, Yadhavaprasanna")
    st.markdown("**Source Type:** RSS only")
    st.markdown("Developed for IntelGenz")

# -------------------- Main Area: Source List --------------------
st.markdown('<h2 class="sub-header">📋 Current RSS Sources</h2>', unsafe_allow_html=True)

# Fetch and prepare data
sources = get_all_sources()
df = pd.DataFrame(sources)
if not df.empty and 'created_at' in df.columns:
    df['created_at'] = pd.to_datetime(df['created_at']).dt.strftime('%Y-%m-%d %H:%M:%S')
    df['updated_at'] = pd.to_datetime(df['updated_at']).dt.strftime('%Y-%m-%d %H:%M:%S')

if df.empty:
    st.info("No sources found. Add a new source using the sidebar.")
else:
    # Display as a table with action buttons (edit and delete)
    col_spec = [2, 3, 3, 1, 1, 1, 1]
    cols = st.columns(col_spec)
    cols[0].markdown("**ID**")
    cols[1].markdown("**Name**")
    cols[2].markdown("**URL**")
    cols[3].markdown("**Created By**")
    cols[4].markdown("**Updated By**")
    cols[5].markdown("**Created At**")
    cols[6].markdown("**Actions**")

    for _, row in df.iterrows():
        c1, c2, c3, c4, c5, c6, c7 = st.columns(col_spec)
        c1.write(row['source_id'])
        c2.write(row['source_name'])
        c3.write(row['source_url'])
        c4.write(row['created_by'])
        c5.write(row['updated_by'])
        c6.write(row['created_at'])

        with c7:
            # Edit button
            if st.button("✏️", key=f"edit_{row['source_id']}", help="Edit"):
                st.session_state.edit_mode = True
                st.session_state.edit_source = row.to_dict()
                st.rerun()
            # Delete button (triggers confirmation)
            if st.button("🗑️", key=f"del_{row['source_id']}", help="Delete"):
                st.session_state.delete_id = row['source_id']
                st.rerun()

# -------------------- Delete Confirmation (below the table) --------------------
if 'delete_id' in st.session_state and st.session_state.delete_id:
    sid = st.session_state.delete_id
    st.warning(f"Are you sure you want to delete source **{sid}**? This action cannot be undone.")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Yes, delete", key="confirm_del"):
            success, msg = delete_source(sid)
            if success:
                st.success(msg)
            else:
                st.error(msg)
            st.session_state.delete_id = None
            time.sleep(1)
            st.rerun()
    with col2:
        if st.button("Cancel", key="cancel_del"):
            st.session_state.delete_id = None
            st.rerun()

st.markdown("---")
st.markdown("© 2025 IntelGenz. All rights reserved.")
