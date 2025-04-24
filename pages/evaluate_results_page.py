import os
import pandas as pd
import streamlit as st
from utils.pdf_utils import show_pdf  # assumes you have this utility

# Directory containing your evaluation result CSVs
RESULTS_DIR = "evaluate_results"


def render_evaluate_results_page():
    st.title("📂 Evaluation Results")

    # ensure the folder exists
    if not os.path.isdir(RESULTS_DIR):
        st.error(f"Directory '{RESULTS_DIR}' not found.")
        return

    # list CSV files
    files = sorted(f for f in os.listdir(RESULTS_DIR) if f.lower().endswith(".csv"))
    if not files:
        st.info(f"No CSV files found in '{RESULTS_DIR}'.")
        return

    # select one
    selected = st.selectbox("Select a result file:", files)
    file_path = os.path.join(RESULTS_DIR, selected)

    # read it
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        st.error(f"Failed to read '{selected}': {e}")
        return

    # summary table
    st.markdown("### Summary")
    summary_cols = [c for c in ["pdf_path", "created_at"] if c in df.columns]
    st.dataframe(df[summary_cols])

    # detailed view
    st.markdown("### Details")
    for idx, row in df.iterrows():
        display_name = os.path.basename(row.get("pdf_path", "")) or f"Record {idx}"
        with st.expander(f"#{idx} – {display_name}"):
            # show PDF if available
            pdf_path = row.get("pdf_path", "")
            if pdf_path and os.path.exists(pdf_path):
                st.markdown(f"**PDF Path:** `{pdf_path}`")
                show_pdf(pdf_path)
            else:
                st.warning("PDF not found or path invalid.")

            # render each markdown field
            for field, label in [
                ("current_skills", "Current Skills"),
                ("key_strengths", "Key Strengths"),
                ("missing_skills", "Missing Skills"),
                ("areas_for_improvement", "Areas for Improvement"),
            ]:
                if field in row and pd.notna(row[field]):
                    st.markdown(f"**{label}:**")
                    st.markdown(row[field])

            # created_at
            if "created_at" in row:
                st.markdown(f"**Created At:** {row['created_at']}")


if __name__ == "__main__":
    render_evaluate_results_page()
