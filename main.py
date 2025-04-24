import streamlit as st

from pages.upload_page import render_upload_section
from pages.manage_page import render_manage_section
from pages.scan_results_page import render_scan_results_page
from pages.evaluate_results_page import render_evaluate_results_page
from pages.skills_page import render_skills_page
from pages.config_page import render_config

st.set_page_config(page_title="ADS Dashboard", layout="wide")

# initialize or read current page
if "current_page" not in st.session_state:
    st.session_state.current_page = "Introduction"

# helper to switch pages
def _go_to(page_name: str):
    st.session_state.current_page = page_name
    st.rerun()

# --- INTRODUCTION SCREEN ---
if st.session_state.current_page == "Introduction":
    # Beautiful header
    st.markdown(
        """
        <div style="text-align:center; padding:30px; background: linear-gradient(90deg, #e3ffe7 0%, #d9e7ff 100%); border-radius: 8px;">
            <h1 style="font-size:3rem; margin:0; color:#2c3e50;">
                👋 Welcome to <span style="color:#27ae60;">ADS</span> Dashboard
            </h1>
            <p style="font-size:1.2rem; color:#34495e; margin-top:10px; max-width:800px; margin-left:auto; margin-right:auto;">
                Your all-in-one platform to upload, evaluate, and manage resumes with ease.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write("---")

    # Feature buttons in a grid
    cols = st.columns(3)
    pages = [
        ("🚀", "Upload & Config",       "Upload a resume PDF and get ATS score + detailed evaluation."),
        ("🗃️", "Manage Records",        "View & delete uploaded PDFs along with job title & description."),
        ("📊", "Scan Results",          "Browse all your past ATS scan scores anytime."),
        ("📝", "Evaluation Results",    "Access and review all your in-depth analyses."),
        ("🛠", "Skills",               "Edit required skills for each job title in the library."),
        ("⚙️", "Configuration",        "Advanced: tweak skill vs. experience weights carefully."),
    ]
    for idx, (icon, title, desc) in enumerate(pages):
        with cols[idx % 3]:
            st.markdown(f"**{icon} {title}**")
            st.write(desc)
            if st.button(f"Go → {title}", key=title):
                _go_to(title)

# --- UPLOAD & CONFIG ---
elif st.session_state.current_page == "Upload & Config":
    if st.button("← Back to Home"):
        _go_to("Introduction")
    render_upload_section()

# --- MANAGE RECORDS ---
elif st.session_state.current_page == "Manage Records":
    if st.button("← Back to Home"):
        _go_to("Introduction")
    render_manage_section()

# --- SCAN RESULTS ---
elif st.session_state.current_page == "Scan Results":
    if st.button("← Back to Home"):
        _go_to("Introduction")
    render_scan_results_page()

# --- EVALUATION RESULTS ---
elif st.session_state.current_page == "Evaluation Results":
    if st.button("← Back to Home"):
        _go_to("Introduction")
    render_evaluate_results_page()

# --- SKILLS LIBRARY ---
elif st.session_state.current_page == "Skills":
    if st.button("← Back to Home"):
        _go_to("Introduction")
    render_skills_page()

# --- CONFIGURATION ---
elif st.session_state.current_page == "Configuration":
    if st.button("← Back to Home"):
        _go_to("Introduction")
    render_config()
