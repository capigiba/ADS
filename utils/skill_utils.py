from pathlib import Path
import csv
from typing import Dict, List, Tuple
import sys

skills_file_path: Path = Path("data/list_skills.csv")

def normalize_text(txt: str) -> str:
    """
    Lowercases, trims, and collapses whitespace in a string.
    """
    return " ".join(txt.strip().lower().split())


def load_job_titles() -> List[Tuple[int, str]]:
    if not skills_file_path.exists():
        raise FileNotFoundError(f"Skills file not found: {skills_file_path}")

    titles: List[Tuple[int, str]] = []
    with skills_file_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)  
        for idx, row in enumerate(reader):
            status = row.get('status', '').strip().lower()
            if status != 'active':
                continue
            title = row.get('job_title', '').strip()
            if title:
                titles.append((idx, title))
    return titles


def load_skills() -> Dict[str, List[str]]:
    if not skills_file_path.exists():
        raise FileNotFoundError(f"Skills file not found: {skills_file_path}")

    job_skills: Dict[str, List[str]] = {}
    with skills_file_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            status = row.get('status', '').strip().lower()
            if status != 'active':
                continue

            raw_title = row.get('job_title', '').strip()
            if not raw_title:
                continue
            title = normalize_text(raw_title)

            raw_skills = row.get('skills_necessary', '').strip()
            if not raw_skills:
                job_skills[title] = []
                continue

            # split on commas (inside quotes they’ll be preserved)
            skills = [normalize_text(s) for s in raw_skills.split(',') if s.strip()]
            job_skills[title] = sorted(set(skills))

    if not job_skills:
        print(f"Warning: no active skills loaded from '{skills_file_path}'", file=sys.stderr)

    return job_skills
