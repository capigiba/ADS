# pages/render_config.py

import yaml
import streamlit as st
from pathlib import Path

# Paths to the YAML files
CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"
BACKUP_PATH = Path(__file__).parent.parent / "config_backup.yaml"

# Load YAML configuration from a file
def load_config(path: Path) -> dict:
    with path.open('r', encoding='utf-8') as f:
        return yaml.safe_load(f)

# Persist configuration to a file
def save_config(path: Path, config: dict):
    with path.open('w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False)

# Streamlit page function
def render_config():
    st.header("Edit Configuration")

    # Load current settings
    config = load_config(CONFIG_PATH)

    # Weights
    st.subheader("Weights")
    config['user_skill_weight'] = st.slider(
        "User Skill Weight", 0.0, 1.0,
        value=config.get('user_skill_weight', 0.8), step=0.1
    )
    config['user_experience_weight'] = st.slider(
        "User Experience Weight", 0.0, 1.0,
        value=config.get('user_experience_weight', 0.2), step=0.1
    )

    # Validate that the two weights sum to exactly 1
    total_weights = config['user_skill_weight'] + config['user_experience_weight']
    if total_weights > 1:
        st.error("⚠️ The skill and experience weights sum to more than 1 (currently {:.2f}).".format(total_weights))
    elif total_weights < 1:
        st.warning("ℹ️ The skill and experience weights sum to less than 1 (currently {:.2f}).".format(total_weights))
    else:
        st.success("✅ Skill and experience weights sum to 1.")

    # Targets
    st.subheader("Targets")
    config['target_jd_similarity'] = st.slider(
        "Target JD Similarity", 0.0, 1.0,
        value=config.get('target_jd_similarity', 0.8), step=0.1
    )
    config['target_skills'] = st.number_input(
        "Target Skills", min_value=0, value=config.get('target_skills', 8), step=1
    )
    config['target_months_base'] = st.number_input(
        "Target Months Base", min_value=0, value=config.get('target_months_base', 60), step=1
    )
    config['target_word_count'] = st.number_input(
        "Target Word Count", min_value=0, value=config.get('target_word_count', 400), step=1
    )
    config['target_gpa'] = st.number_input(
        "Target GPA", min_value=0.0, max_value=4.0,
        value=config.get('target_gpa', 3.2), step=0.1
    )

    # Score Breakdown
    st.subheader("Score Breakdown")
    config['weight_jd'] = st.number_input(
        "Weight JD", min_value=0, value=config.get('weight_jd', 30), step=1
    )
    config['weight_skill'] = st.number_input(
        "Weight Skill", min_value=0, value=config.get('weight_skill', 50), step=1
    )
    config['weight_months'] = st.number_input(
        "Weight Months", min_value=0, value=config.get('weight_months', 50), step=1
    )
    config['weight_word'] = st.number_input(
        "Weight Word", min_value=0, value=config.get('weight_word', 10), step=1
    )
    config['weight_gpa'] = st.number_input(
        "Weight GPA", min_value=0, value=config.get('weight_gpa', 10), step=1
    )

    # Fuzzy Matching
    st.subheader("Fuzzy Matching")
    config['fuzzy_title_match_threshold'] = st.slider(
        "Fuzzy Title Match Threshold", 0, 100,
        value=config.get('fuzzy_title_match_threshold', 70)
    )
    config['fuzzy_skill_match_threshold'] = st.slider(
        "Fuzzy Skill Match Threshold", 0, 100,
        value=config.get('fuzzy_skill_match_threshold', 85)
    )

    # Action buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Save Configuration"):
            # Only save if weights sum to 1
            if total_weights == 1:
                save_config(CONFIG_PATH, config)
                st.success("Configuration saved to config.yaml")
            else:
                st.error("Cannot save: skill and experience weights must sum to 1.")
    with col2:
        if st.button("Reset to Default"):
            # Load defaults from backup YAML
            default = load_config(BACKUP_PATH)
            save_config(CONFIG_PATH, default)
            st.success("Configuration reset to default settings")
            st.rerun()  # reload page to reflect defaults

if __name__ == "__main__":
    render_config()