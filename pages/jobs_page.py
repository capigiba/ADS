import os, datetime, uuid
import pandas as pd
import streamlit as st

CSV_PATH   = "jobs.csv"
FIELDNAMES = ["id", "job_title", "created_at", "updated_at", "status"]

def delete_record(rec_id: str, df: pd.DataFrame, csv_path: str):
    df.loc[df["id"] == rec_id, ["status", "updated_at"]] = [
        "deleted",
        datetime.datetime.now().isoformat()
    ]
    df.to_csv(csv_path, index=False)

    st.success("Record marked as deleted.")
    # reset to list view
    st.session_state.selected_record = None

def add_job():
    # 1) Load or init
    if not os.path.exists(CSV_PATH):
        df = pd.DataFrame(columns=FIELDNAMES)
    else:
        df = pd.read_csv(CSV_PATH)

    # 2) Append new row with default status "active"
    now = datetime.datetime.now().isoformat()
    new = {
        "id": str(uuid.uuid4()),
        "job_title": st.session_state.new_job.strip(),
        "created_at": now,
        "updated_at": now,
        "status": "active"
    }
    df = pd.concat([df, pd.DataFrame([new])], ignore_index=True)

    # 3) Save back
    df.to_csv(CSV_PATH, index=False)
    st.success(f"Created job “{new['job_title']}”")
    st.session_state.new_job = ""

def render_jobs_page():
    st.title("🏷️ Jobs")
    csv_path = CSV_PATH

    # — ensure list vs. detail toggle key —
    if "selected_job" not in st.session_state:
        st.session_state.selected_job = None

    # —— LIST + CREATE ——  
    if st.session_state.selected_job is None:
        # 1) Load or init DataFrame
        if not os.path.exists(csv_path):
            df = pd.DataFrame(columns=FIELDNAMES)
        else:
            df = pd.read_csv(csv_path)

        # 2) List
        if df.empty:
            st.info("No jobs found yet.")
        else:
            # include Status column
            cols = st.columns([2, 3, 2, 2, 2])
            for c, lbl in zip(cols, ["ID", "Job Title", "Created At", "Updated At", "Action"]):
                c.markdown(f"**{lbl}**")

            for _, row in df.iterrows():
                id_c, title_c, ca_c, ua_c, act_c = st.columns([2, 3, 2, 2, 2])
                id_c.write(row["id"])
                title_c.write(row["job_title"])
                ca_c.write(row["created_at"])
                ua_c.write(row["updated_at"])
                if row["status"] == "deleted":
                    act_c.markdown("❌ deleted")
                else:
                    act_c.button(
                        "Edit",
                        key=f"edit_{row['id']}",
                        on_click=lambda rec=row["id"]: st.session_state.__setitem__("selected_job", rec)
                    )

        st.markdown("---")
        st.subheader("Create New Job")
        st.text_input("Job Title", key="new_job")
        st.button("Create Job", on_click=add_job)

    # —— EDIT VIEW ——  
    else:
        # 1) Load DataFrame
        df = pd.read_csv(csv_path)
        job_id  = st.session_state.selected_job
        job_row = df.loc[df["id"] == job_id].iloc[0]

        st.button(
            "← Back to list",
            on_click=lambda: st.session_state.__setitem__("selected_job", None)
        )
        st.markdown("---")
        st.subheader(f"Edit Job “{job_row['job_title']}”")

        # editable title
        st.text_input("Job Title", value=job_row["job_title"], key="edit_title")

        # Save / Cancel / Delete buttons
        col1, col2, col3 = st.columns(3)
        with col1:
            st.button(
                "Save",
                on_click=lambda: (
                    df.loc[df["id"] == job_id, ["job_title","updated_at"]]\
                      .__setitem__(slice(None),
                                  [st.session_state.edit_title.strip(),
                                   datetime.datetime.now().isoformat()]),
                    df.to_csv(csv_path, index=False),
                    st.success(f"Saved changes to “{st.session_state.edit_title}”"),
                    st.session_state.__setitem__("selected_job", None)
                )
            )
        with col2:
            st.button(
                "Cancel",
                on_click=lambda: st.session_state.__setitem__("selected_job", None)
            )
        with col3:
            st.button(
                "Delete",
                key=f"del_{job_id}",
                    on_click=lambda rec=job_id: delete_record(rec, df, csv_path)
            )

# To actually run:
if __name__ == "__main__":
    render_jobs_page()
