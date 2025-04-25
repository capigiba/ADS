# Function extracted_with_Gemini
# Input: resume text, job description
# Output: current skills, key strengths, missing skills, areas for improvement

import requests
import os
import sys
import re
from pathlib import Path
from typing import Union, Tuple
import pymupdf
from dotenv import load_dotenv

# Trước khi in ra, thay đổi thiết lập mã hóa đầu ra của Python
sys.stdout.reconfigure(encoding='utf-8')

def extracted_with_Gemini(resume_text: str, job_description: str, api_key: str):
    prompt = f"""
        You are an expert resume analyst with deep knowledge of industry standards, job requirements, and hiring practices across various fields. Your task is to provide a comprehensive, detailed analysis of the resume provided.

        Please structure your response in the following format:

        ## Current Skills
        - **Current Skills**: [List ALL skills the candidate demonstrates in their resume, categorized by type (technical, soft, domain-specific, etc.). Be comprehensive.]

        ## Key Strengths
        [List 5-7 specific strengths of the resume with detailed explanations of why these are effective]

        Additionally, compare this resume to the following job description:

        Job Description:

        {job_description}

        ## Missing Skills
        [List specific requirements from the job description that are not addressed in the resume, with recommendations on how to address each gap]

        ## Areas for Improvement
        [List 5-7 specific areas where the resume could be improved with detailed, actionable recommendations]

        Resume:

        {resume_text}
        """
    
    url = (
        "https://generativelanguage.googleapis.com/"
        "v1beta/models/gemini-1.5-flash-latest:generateContent"
        f"?key={api_key}"
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ]
    }

    headers = {
        'Content-Type': 'application/json'
    }

    try:
        # Gửi yêu cầu POST
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()  # Raise an error for bad responses

        # Lấy nội dung kết quả từ API
        result = response.json()["candidates"][0]["content"]["parts"][0]["text"]
        
        sections = re.split(r'##\s+', result)
        sections = [s.strip() for s in sections if s.strip()]
        section_dict = {}

        for section in sections:
            lines = section.splitlines()
            title = lines[0].strip().lower().replace(" ", "_")  #"Current Skills" → "current_skills"
            content = "\n".join(lines[1:]).strip()
            section_dict[title] = content

        current_skills = section_dict.get("current_skills", "")
        key_strengths = section_dict.get("key_strengths", "")
        missing_skills = section_dict.get("missing_skills", "")
        areas_for_improvement = section_dict.get("areas_for_improvement", "")

        return current_skills, key_strengths, missing_skills, areas_for_improvement
        
    except requests.exceptions.RequestException as e:
        print(f"API call failed: {e}")

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

def analyze_resume(
    cv_text: str, job_description: str, api_key: str
) -> Tuple[str, str, str, str]:
    """
    High-level helper: read PDF, analyze with Gemini, and return structured results.

    Args:
      cv_text: Text of the resume PDF file.
      job_description: Text of the job description.

    Returns:
      Tuple containing:
        - current_skills
        - key_strengths
        - missing_skills
        - areas_for_improvement
    """
    return extracted_with_Gemini(cv_text, job_description, api_key)
# current_skills, key_strengths, missing_skills, areas_for_improvement