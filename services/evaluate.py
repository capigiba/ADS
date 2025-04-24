import requests
import os
import sys
import re
from pathlib import Path
from typing import Union, Tuple
import pymupdf
from internal.cv_evaluate import analyze_resume
import pandas as pd
from datetime import datetime

def extract_text_from_pdf(pdf_path: Union[str, Path]) -> str:
    try:
        doc = pymupdf.open(pdf_path)
        text_content = []
        for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                blocks = page.get_text("blocks", sort=True)
                page_text = " ".join([b[4].replace('\n', ' ').strip() for b in blocks if len(b[4].strip()) > 10])
                text_content.append(page_text)
        doc.close()
        full_text = "\n".join(text_content)
        full_text = re.sub(r'\s*\n\s*', '\n', full_text)
        full_text = re.sub(r'-\n(\w)', r'\1', full_text)
        full_text = re.sub(r'\s+', ' ', full_text)
        return full_text.strip()
    except Exception as e:
        print(f"Error reading PDF '{pdf_path}': {e}")
        return ""
    


def evaluate_resume(
    pdf_path: Union[str, Path], 
    job_description: str
) -> Tuple[str, str, str, str]:
    cv_text = extract_text_from_pdf(pdf_path)

    current_skills, key_strengths, missing_skills, areas_for_improvement = analyze_resume(cv_text, job_description)

    out_dir = Path("evaluate_results")
    out_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    safe_name = Path(pdf_path).stem.replace(" ", "_")
    result_filename = f"{safe_name}_{timestamp}_1.csv"
    result_path = out_dir / result_filename

    df = pd.DataFrame([{
        "pdf_path": str(pdf_path),
        "current_skills": current_skills,
        "key_strengths": key_strengths,
        "missing_skills": missing_skills,
        "areas_for_improvement": areas_for_improvement,
        "created_at": datetime.now().isoformat(),
    }])
    df.to_csv(result_path, index=False)

    return current_skills, key_strengths, missing_skills, areas_for_improvement
