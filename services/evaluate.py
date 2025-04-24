import requests
import os
import sys
import re
from pathlib import Path
from typing import Union, Tuple
import pymupdf
from internal.gemini_api import analyze_resume

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

    return analyze_resume(cv_text, job_description)
# current_skills, key_strengths, missing_skills, areas_for_improvement

