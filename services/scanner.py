import pandas as pd
from pathlib import Path
from typing import Union, List, Dict, Tuple, Optional
from datetime import datetime
from internal.cv_scanner import run_cv_scanner

def scan_record_score(
    filename: str,
    job_title: str,
    job_description: str,
    score_all: bool,
    pdf_folder: Union[str, Path] = "folder_pdf",
    records_csv_path: Union[str, Path] = "data/records.csv",
    skills_file_path: Union[str, Path] = "data/skills.csv",
    user_skill_weight: Optional[float] = None,
    user_experience_weight: Optional[float] = None,
) -> Tuple[float, str]:
    """
    1) Reads `records_csv_path` (CSV with columns:
       id,name pdf,job_title,job_description,weight1,weight2,created_at,updated_at,status)
    2) Filters rows where `job_title` matches the passed-in job_title
    3) Builds a list of `name pdf` values
    4) Calls run_cv_scanner(...) over that list
    5) Saves the full results dict into a CSV under `scan_results/`
    6) Returns a tuple (score_for_‘filename’, result_csv_filename)
    """
    # -- load and filter records.csv --
    df = pd.read_csv(records_csv_path)
    df_filtered = df[df["job_title"] == job_title]
    if df_filtered.empty:
        raise ValueError(f"No records found for job_title '{job_title}' in '{records_csv_path}'")

    # -- choose pdf list based on score_all flag --
    if score_all:
        pdf_list: List[str] = df_filtered["name pdf"].dropna().tolist()
    else:
        # only scan the single target file
        all_names = df_filtered["name pdf"].dropna().tolist()
        if filename not in all_names:
            raise FileNotFoundError(
                f"Filename '{filename}' not found among records for job_title '{job_title}'"
            )
        pdf_list = [filename]

    # -- run the CV scanner on only those PDFs --
    if user_skill_weight is not None and user_experience_weight is not None:
        results: Dict[str, Dict] = run_cv_scanner(
            skills_file_path=skills_file_path,
            job_description=job_description,
            pdf_folder=pdf_folder,
            pdf_list=pdf_list,
            user_skill_weight=user_skill_weight,
            user_experience_weight=user_experience_weight,
            job_title=job_title
        )
    else:
        results: Dict[str, Dict] = run_cv_scanner(
            skills_file_path=skills_file_path,
            job_description=job_description,
            pdf_folder=pdf_folder,
            pdf_list=pdf_list,
            job_title=job_title
        )

    # -- prepare scan_results folder and filename --
    scan_dir = Path("scan_results")
    scan_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    safe_title = job_title.replace(" ", "_")
    result_filename = f"[{safe_title}]_{timestamp}_{len(pdf_list)}.csv"
    result_path = scan_dir / result_filename

    # -- save full results dict to CSV --
    # convert { pdf_path: { ...details... } } into a DataFrame
    df_results = pd.DataFrame.from_dict(results, orient="index").reset_index()
    df_results.rename(columns={"index": "pdf_path"}, inplace=True)
    df_results.to_csv(result_path, index=False)

    # -- extract and return the score for our target filename --
    for path_str, detail in results.items():
        if Path(path_str).name == filename:
            score = detail.get("score", 0.0)
            return score, result_filename

    raise FileNotFoundError(
        f"Filename '{filename}' not found among scanned PDFs: {pdf_list}"
    )
