import os
import pandas as pd
import streamlit as st

CSV_PATH = "data/list_skills.csv"
COLUMNS = ["job_title", "skills_necessary", "status"]

def load_data():
    return pd.read_csv(CSV_PATH) if os.path.exists(CSV_PATH) else pd.DataFrame(columns=COLUMNS)

def save_data(df):
    df.to_csv(CSV_PATH, index=False)

def add_skill():
    st.session_state.skill_inputs.append("")

def remove_skill(idx):
    st.session_state.skill_inputs.pop(idx)

def edit_entry(idx):
    df = load_data()
    row = df.iloc[idx]
    # Populate inputs for editing
    st.session_state.job_title = row["job_title"]
    st.session_state.skill_inputs = [s.strip() for s in row["skills_necessary"].split(",") if s.strip()]
    st.session_state.edit_mode = True
    st.session_state.edit_index = idx

def delete_entry(idx):
    df = load_data()
    title = df.at[idx, "job_title"]
    df.at[idx, "status"] = "deleted"
    save_data(df)
    st.success(f"Marked **{title}** as deleted.")
    # Clear edit state if deleting current
    if st.session_state.get("edit_mode") and st.session_state.get("edit_index") == idx:
        cancel_edit_state()


def cancel_edit_state():
    # Reset form inputs and exit edit mode
    st.session_state.edit_mode = False
    if "edit_index" in st.session_state:
        del st.session_state["edit_index"]
    st.session_state.job_title = ""
    st.session_state.skill_inputs = [""]


def submit_skills():
    title = st.session_state.job_title.strip()
    skills = [s.strip() for s in st.session_state.skill_inputs if s.strip()]

    if not title:
        st.error("Please enter a job title.")
        return
    if not skills:
        st.error("Please enter at least one skill.")
        return

    df = load_data()
    if st.session_state.get("edit_mode", False):
        idx = st.session_state.edit_index
        df.at[idx, "job_title"] = title
        df.at[idx, "skills_necessary"] = ", ".join(skills)
        save_data(df)
        st.success(f"Updated skills for **{title}**!")
        cancel_edit_state()
    else:
        new_row = {
            "job_title": title,
            "skills_necessary": ", ".join(skills),
            "status": "active"
        }
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        save_data(df)
        st.success(f"Saved skills for **{title}**!")
        # clear inputs
        st.session_state.job_title = ""
        st.session_state.skill_inputs = [""]


def render_skills_page():
    st.title("📋 Skill List Manager")

    # Initialize state
    if "skill_inputs" not in st.session_state:
        st.session_state.skill_inputs = [""]
    if "edit_mode" not in st.session_state:
        st.session_state.edit_mode = False

    # --- Input Section ---
    st.text_input("Job Title", key="job_title")
    for idx in range(len(st.session_state.skill_inputs)):
        cols = st.columns([9, 2])
        val = cols[0].text_input(f"Skill #{idx+1}", value=st.session_state.skill_inputs[idx], key=f"skill_{idx}")
        cols[1].button("Remove", key=f"remove_{idx}", on_click=remove_skill, args=(idx,))
        st.session_state.skill_inputs[idx] = val

    # --- Form Actions ---
    if st.session_state.edit_mode:
        btn_cols = st.columns(3)
        btn_cols[0].button("✅ Update", on_click=submit_skills)
        btn_cols[1].button("❌ Cancel", on_click=cancel_edit_state)
        # delete current
        current_idx = st.session_state.edit_index
        btn_cols[2].button("🗑️ Delete", on_click=delete_entry, args=(current_idx,))
    else:
        action_cols = st.columns(2)
        action_cols[0].button("➕ Add Skill", on_click=add_skill)
        action_cols[1].button("✅ Submit", on_click=submit_skills)

    # --- Existing Entries ---
    st.markdown("---")
    st.subheader("Existing Entries")
    df = load_data()
    if df.empty:
        st.info("No entries yet.")
        return

    # Table header
    header_cols = st.columns([1, 3, 5, 3])
    for col, label in zip(header_cols, ["#", "Job Title", "Skills", "Actions"]):
        col.markdown(f"**{label}**")

    # Table rows
    for idx, row in df.iterrows():
        c_idx, c_title, c_skills, c_actions = st.columns([1, 3, 5, 3])
        c_idx.write(idx)
        c_title.write(row["job_title"])
        c_skills.write(row["skills_necessary"])
        if row["status"] == "active":
            c_actions.button("Edit", key=f"edit_{idx}", on_click=edit_entry, args=(idx,))
        else:
            c_actions.write("❌ deleted")

if __name__ == "__main__":
    render_skills_page()
