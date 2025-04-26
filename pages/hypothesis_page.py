import streamlit as st
import pandas as pd
import os
import base64
from streamlit.components.v1 import html as st_html

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

    # 2) Show the raw table
    st.markdown("## All Records")
    st.dataframe(df)

    st.markdown("## Detailed Records")
    for idx, row in df.iterrows():
        title = f"#{idx}"
        if "ID" in row:
            title += f": {row['ID']}"
        with st.expander(title):
            # 1) Render Resume_str
            if "Resume_str" in row:
                st.markdown("**Plain Text Extract:**")
                st.write(row["Resume_str"])

            # 2) Render Resume_html as actual HTML
            if "Resume_html" in row and pd.notna(row["Resume_html"]):
                st.markdown("**Rendered HTML Extract:**")
                # adjust height to fit your content
                st_html(row["Resume_html"], height=400, scrolling=True)

            # 3) Other metadata
            if "Category" in row:
                st.markdown(f"**Category:** {row['Category']}")

if __name__ == "__main__":
    render_hypothesis()
