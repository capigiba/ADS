import os, uuid, datetime, csv
import pandas as pd, streamlit as st
from utils.file_utils import make_filename
from utils.skill_utils import load_job_titles
from services.scanner import scan_record_score
from utils.gauge_utils import render_ats_gauge
from pathlib import Path
import yaml
from typing import Dict, List, Tuple

_config_path = Path(__file__).parent.parent / "config.yaml"
_cfg = yaml.safe_load(_config_path.read_text())

USER_SKILL_WEIGHT            = _cfg["user_skill_weight"]
USER_EXPERIENCE_WEIGHT       = _cfg["user_experience_weight"]

def render_upload_section():
    if "submitted" not in st.session_state:
        st.session_state.submitted = False
        st.session_state.filename = ""
        st.session_state.job_title = ""
        st.session_state.job_description = ""
        st.session_state.score_all = False
        st.session_state.weight1 = USER_SKILL_WEIGHT
        st.session_state.weight2 = USER_EXPERIENCE_WEIGHT
        st.session_state.custom_weights = False

    left, right = st.columns(2)
    with left:
        st.subheader("Upload PDF")
        pdf_file = st.file_uploader("Choose a PDF file", type=["pdf"])
        st.subheader("Configuration")

        job_tuples: List[Tuple[int, str]] = load_job_titles()

        if not job_tuples:
            st.warning("No active jobs available. Please create one on the Jobs page first.")
            return

        # 2) Build a dict:  display_label -> actual_title
        label_to_title = {
            f"{title} #{id}": title
            for id, title in job_tuples
        }

        # 3) Use the labels as the selectbox options
        selected_label = st.selectbox(
            "Job Title",
            options=list(label_to_title.keys())
        )

        # 4) Grab your pure title
        job_title = label_to_title[selected_label]
        job_description = st.text_area(
            "Job Description",
            placeholder="Enter a detailed job description here…",
            height=120,
        )
        custom_weights = st.checkbox("Enable custom weights", value=False)
        if custom_weights:
            weight1 = st.number_input(
                "Skill weight",
                min_value=0.0, max_value=1.0, step=0.1,
                value=USER_SKILL_WEIGHT
            )
            weight2 = st.number_input(
                "Experience weight",
                min_value=0.0, max_value=1.0, step=0.1,
                value=USER_EXPERIENCE_WEIGHT
            )
        else:
            weight1 = USER_SKILL_WEIGHT
            weight2 = USER_EXPERIENCE_WEIGHT
            st.write(f"Using default weights → Skill: **{weight1}**, Experience: **{weight2}**")
        # weight1 = st.number_input("Skill", min_value=0.0, max_value=1.0, step=0.1, value=0.5)
        # weight2 = st.number_input("Experience", min_value=0.0, max_value=1.0, step=0.1, value=0.5)

        # check the sum
        total = weight1 + weight2
        if total > 1:
            st.error("⚠️ The weights sum to more than 1.")
        elif total < 1:
            st.warning("ℹ️ The weights sum to less than 1 (must equal 1).")
        else:
            st.success("✅ Weights sum to 1")

        scan_mode = st.radio(
            "Scan mode",
            ("Only this PDF", "All PDFs for this job title")
        )
        score_all = (scan_mode == "All PDFs for this job title")

        submit = st.button("Submit")
        if submit:
            if pdf_file is None:
                st.error("Please upload a PDF before submitting.")
            elif abs(total - 1.0) > 1e-6:
                st.error("Cannot submit: please adjust weights so they sum to exactly 1.")
            else:
                # 1) Save PDF with sanitized name
                os.makedirs("folder_pdf", exist_ok=True)
                record_id = str(uuid.uuid4())
                filename = make_filename(job_title, pdf_file.name)
                save_path = os.path.join("folder_pdf", filename)
                with open(save_path, "wb") as f:
                    f.write(pdf_file.read())

                # 2) Append record to CSV
                csv_path = "data/records.csv"
                header = [
                    "id",
                    "name pdf",
                    "job_title",
                    "job_description",
                    "weight1",
                    "weight2",
                    "created_at",
                    "updated_at",
                    "status",
                ]
                now = datetime.datetime.now().isoformat()
                row = [
                    record_id,
                    filename,
                    job_title,
                    job_description,
                    weight1,
                    weight2,
                    now,
                    now,
                    "active",
                ]

                write_header = not os.path.exists(csv_path)
                with open(csv_path, "a", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    if write_header:
                        writer.writerow(header)
                    writer.writerow(row)

                st.session_state.submitted = True
                st.session_state.filename = filename
                st.session_state.job_title = job_title
                st.session_state.job_description = job_description
                st.session_state.score_all = score_all
                st.session_state.custom_weights = custom_weights
                st.session_state.weight1 = weight1
                st.session_state.weight2 = weight2

                st.success("✅ PDF uploaded and record saved.")

    with right:
        if st.session_state.submitted:
            st.subheader("ATS Score")
            with st.spinner("🔄 Scanning CV, please wait…"):
                if st.session_state.custom_weights:
                    score, result_file = scan_record_score(
                        filename=st.session_state.filename,
                        job_title=st.session_state.job_title,
                        job_description=st.session_state.job_description,
                        score_all=st.session_state.score_all,
                        user_skill_weight=st.session_state.weight1,
                        user_experience_weight=st.session_state.weight2,
                    )
                else:
                    score, result_file = scan_record_score(
                        filename=st.session_state.filename,
                        job_title=st.session_state.job_title,
                        job_description=st.session_state.job_description,
                        score_all=st.session_state.score_all
                    )
            st.success("✅ Scan complete!")
            render_ats_gauge(score)

            # download button for full results CSV
            result_path = Path("scan_results") / result_file
            if result_path.exists():
                with open(result_path, "rb") as f:
                    st.download_button(
                        label="Download full scan results",
                        data=f,
                        file_name=result_file,
                        mime="text/csv"
                    )
            else:
                st.warning(f"Result file not found: {result_path}")

