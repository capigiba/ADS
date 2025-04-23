import os
import ast
import streamlit as st
import pandas as pd
from utils.pdf_utils import show_pdf

# Directory containing scan result CSVs
RESULTS_DIR = "scan_results"


def _safe_eval(val, default):
    """Safely evaluate a literal or return default on failure."""
    if pd.isna(val) or not isinstance(val, str):
        return default
    try:
        return ast.literal_eval(val)
    except Exception:
        return default


def render_scan_results_page():
    st.title("📂 CV Scanner Results")

    # List available result files
    if not os.path.isdir(RESULTS_DIR):
        st.error(f"Directory '{RESULTS_DIR}' not found.")
        return

    files = [f for f in os.listdir(RESULTS_DIR) if f.lower().endswith('.csv')]
    if not files:
        st.info("No result CSV files found in the scan_results directory.")
        return

    selected = st.selectbox("Select a result file:", files)
    file_path = os.path.join(RESULTS_DIR, selected)

    # Read CSV
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        st.error(f"Failed to read '{selected}': {e}")
        return

    # Parse list and dict columns
    for col in ["matched_skills_list", "target_skills_list"]:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: _safe_eval(x, []))
    if "scores" in df.columns:
        df["scores"] = df["scores"].apply(lambda x: _safe_eval(x, {}))

    # Summary table
    st.markdown("### Summary Table")
    summary_cols = [c for c in ["file_path", "score", "jd_similarity", "matched_skills_count"] if c in df.columns]
    st.dataframe(df[summary_cols])

    # Details per record
    st.markdown("### Detailed Records")
    for idx, row in df.iterrows():
        title = f"#{idx}: {os.path.basename(str(row.get('file_path', '')))}"
        if 'score' in row and pd.notna(row['score']):
            title += f" (Score: {row['score']:.2f})"
        with st.expander(title):
            st.markdown(f"**PDF Path:** `{row.get('pdf_path', '')}`")
            if 'file_path' in row and os.path.exists(row['file_path']):
                show_pdf(row['file_path'])
            else:
                st.warning("PDF file not found or path missing.")

            # Display parsed lists
            if "matched_skills_list" in row:
                st.markdown("**Matched Skills:**")
                st.write(row["matched_skills_list"])
            if "target_skills_list" in row:
                st.markdown("**Target Skills List:**")
                st.write(row["target_skills_list"])

            # Other numeric fields
            for field in ["jd_similarity", "total_months_experience", "word_count", "gpa"]:
                if field in row:
                    st.markdown(f"**{field.replace('_', ' ').title()}:** {row[field]}")

            # Scores breakdown
            if "scores" in row:
                st.markdown("**Scores Breakdown:**")
                st.json(row["scores"])
