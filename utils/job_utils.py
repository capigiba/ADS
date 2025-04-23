import os
import pandas as pd

def load_active_job_titles(jobs_csv_path: str = "data/jobs.csv") -> list[str]:
    """
    Read jobs.csv and return a list of job_title values
    where status != "deleted".
    """
    if not os.path.exists(jobs_csv_path):
        return []
    df = pd.read_csv(jobs_csv_path)
    # keep only non-deleted
    return df.loc[df["status"] != "deleted", "job_title"].tolist()
