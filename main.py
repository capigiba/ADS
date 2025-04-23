import streamlit as st
from pages.upload_page import render_upload_section
from pages.manage_page import render_manage_section
from pages.jobs_page   import render_jobs_page

st.set_page_config(page_title="ADS", layout="wide")

# 1) Use one key for your sidebar…
page = st.sidebar.radio(
    "📑 Navigate to",
    ["Upload & Config", "Manage Records", "Jobs"],
    key="current_page",
    on_change=lambda: _clear_except("current_page")
)

def _clear_except(keep_key: str):
    """Remove every st.session_state key except the one named `keep_key`."""
    for k in list(st.session_state.keys()):
        if k != keep_key:
            del st.session_state[k]

# 2) Dispatch
if st.session_state.current_page == "Upload & Config":
    render_upload_section()
elif st.session_state.current_page == "Manage Records":
    render_manage_section()
else:
    render_jobs_page()
