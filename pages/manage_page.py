import os, datetime
import pandas as pd
import streamlit as st
from utils.pdf_utils import show_pdf

def delete_record(rec_id: str, df: pd.DataFrame, csv_path: str):
    # 1) remove PDF file
    pdf_path = os.path.join("folder_pdf", df.loc[df["id"] == rec_id, "name pdf"].iloc[0])
    try:
        os.remove(pdf_path)
    except OSError:
        pass

    # 2) mark deleted in CSV
    df.loc[df["id"] == rec_id, ["status", "updated_at"]] = [
        "deleted",
        datetime.datetime.now().isoformat()
    ]
    df.to_csv(csv_path, index=False)

    st.success("Record marked as deleted.")
    # reset to list view
    st.session_state.selected_record = None

def render_manage_section():
    st.title("📋 Manage Records")
    csv_path = "data/records.csv"

    # --- 1) Ensure we have a session_state key to tell list vs detail ---
    if "selected_record" not in st.session_state:
        st.session_state.selected_record = None

    # --- 2) Load or bail ---
    if not os.path.exists(csv_path):
        st.info("No records found yet.")
        return

    df = pd.read_csv(csv_path)

    # --- 3) LIST VIEW ---
    if st.session_state.selected_record is None:
        cols = st.columns([2, 3, 2, 2, 2])
        for c, label in zip(cols, ["ID", "PDF Name", "Created At", "Updated At", "Status"]):
            c.markdown(f"**{label}**")

        for _, row in df.iterrows():
            id_col, pdf_col, ca_col, ua_col, act_col = st.columns([2, 3, 2, 2, 2])
            id_col.write(row["id"])
            pdf_col.write(row["name pdf"])
            ca_col.write(row["created_at"])
            ua_col.write(row["updated_at"])

            if row["status"] == "deleted":
                act_col.markdown("❌ deleted")
            else:
                # on_click sets the record and automatically reruns
                act_col.button(
                    "View",
                    key=f"view_{row['id']}",
                    on_click=lambda rec=row["id"]: st.session_state.__setitem__("selected_record", rec)
                )

    # --- 4) DETAIL VIEW ---
    else:
        rec_id = st.session_state.selected_record
        row = df.loc[df["id"] == rec_id].iloc[0]

        # Back button
        st.button(
            "← Back to list",
            on_click=lambda: st.session_state.__setitem__("selected_record", None)
        )

        left, right = st.columns([3, 2])
        pdf_path = os.path.join("folder_pdf", row["name pdf"])

        with left:
            show_pdf(pdf_path)
            # debug path
            left.write(f"Looking for PDF at: `{pdf_path}`")

        with right:
            st.markdown(f"**ID:** {row['id']}")
            st.markdown(f"**Job Title:** {row['job_title']}")
            st.markdown("**Description:**\n\n" + row["job_description"])
            st.markdown(f"**PDF Name:** {row['name pdf']}")
            st.markdown(f"**Skill:** {row['skill']} **Experience:** {row['experience']}")
            st.markdown(f"**Created:** {row['created_at']}")
            st.markdown(f"**Updated:** {row['updated_at']}")
            st.markdown(f"**Status:** {row['status']}")

            if row["status"] != "deleted":
                st.button(
                    "Delete",
                    key=f"del_{rec_id}",
                    on_click=lambda rec=rec_id: delete_record(rec, df, csv_path)
                )

if __name__ == "__main__":
    render_manage_section()
