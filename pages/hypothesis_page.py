import streamlit as st
import pandas as pd
import os
import base64
from streamlit.components.v1 import html as st_html
import math

#— helper to embed a PDF in the page
def show_pdf(file_path: str):
    with open(file_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    pdf_display = (
        f'<iframe src="data:application/pdf;base64,{b64}" '
        'width="700" height="900" type="application/pdf"></iframe>'
    )
    st.markdown(pdf_display, unsafe_allow_html=True)

def render_hypothesis():
    st.title("CSV Records Viewer")

    df = pd.read_csv("hypothesis/Resume.csv")  # your fallback

    # # 2) Show the raw table
    # st.markdown("## All Records")
    # st.dataframe(df)

    total = len(df)

    # --- pagination controls in the sidebar ---
    page_size = st.sidebar.number_input(
        "Rows per page", min_value=1, max_value=100, value=10
    )
    total_pages = math.ceil(total / page_size)

    page = st.sidebar.number_input(
        "Page number", min_value=1, max_value=total_pages, value=1
    )

    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    df_page = df.iloc[start_idx:end_idx]

    st.markdown(f"## Showing rows {start_idx + 1}–{min(end_idx, total)} of {total}")
    st.dataframe(df_page)

    st.markdown("## Detailed Records")
    for idx, row in df_page.iterrows():
        title = f"#{idx}"
        if "ID" in row:
            title += f": {row['ID']}"
        with st.expander(title):
            # Plain text
            if "Resume_str" in row and pd.notna(row["Resume_str"]):
                st.markdown("**Plain Text Extract:**")
                st.write(row["Resume_str"])

            # HTML render
            if "Resume_html" in row and pd.notna(row["Resume_html"]):
                st.markdown("**Rendered HTML Extract:**")
                st_html(row["Resume_html"], height=300, scrolling=True)

            # Category
            if "Category" in row:
                st.markdown(f"**Category:** {row['Category']}")

if __name__ == "__main__":
    render_hypothesis()
