import sys
from pathlib import Path
from typing import Dict, List, Union, Optional, Set
from sentence_transformers import SentenceTransformer
import re
import spacy
from spacy.language import Language
from spacy.tokens import Doc
import argparse
from thefuzz import process, fuzz
import pymupdf
import csv
import io
from datetime import datetime
import torch
import dateparser
from collections import defaultdict
import yaml
from utils.skill_utils import load_skills
import streamlit as st

_config_path = Path(__file__).parent.parent / "config.yaml"
_cfg = yaml.safe_load(_config_path.read_text())

USER_SKILL_WEIGHT            = _cfg["user_skill_weight"]
USER_EXPERIENCE_WEIGHT       = _cfg["user_experience_weight"]

TARGET_JD_SIMILARITY         = _cfg["target_jd_similarity"]
TARGET_SKILLS                = _cfg["target_skills"]
TARGET_MONTHS_EXPERIENCE     = _cfg["target_months_base"] * USER_EXPERIENCE_WEIGHT
TARGET_WORD_COUNT            = _cfg["target_word_count"]
TARGET_GPA                   = _cfg["target_gpa"]

WEIGHT_JD                    = _cfg["weight_jd"]
WEIGHT_SKILL                 = _cfg["weight_skill"]
WEIGHT_MONTHS                = _cfg["weight_months"]
WEIGHT_WORD                  = _cfg["weight_word"]
WEIGHT_GPA                   = _cfg["weight_gpa"]

MAX_SCORE_WITH_GPA           = (
    WEIGHT_JD
    + WEIGHT_SKILL * USER_SKILL_WEIGHT
    + WEIGHT_MONTHS * USER_EXPERIENCE_WEIGHT
    + WEIGHT_WORD
    + WEIGHT_GPA
)
MAX_SCORE_WITHOUT_GPA = WEIGHT_JD + (WEIGHT_SKILL * USER_SKILL_WEIGHT) + (WEIGHT_MONTHS * USER_EXPERIENCE_WEIGHT) + WEIGHT_WORD

FUZZY_TITLE_MATCH_THRESHOLD  = _cfg["fuzzy_title_match_threshold"]
FUZZY_SKILL_MATCH_THRESHOLD  = _cfg["fuzzy_skill_match_threshold"]

def normalize_text(txt: str) -> str:
    return txt.strip().lower()

def load_requirement(req_file_path: Path) -> str:
    try:
        with open(req_file_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"Error: Requirement file not found at '{req_file_path}'", file=sys.stderr)
        raise
    except Exception as e:
        print(f"Error loading requirement file '{req_file_path}': {e}", file=sys.stderr)
        raise

def extract_job_title_from_requirement(req_text: str) -> Optional[str]:
    if not req_text:
        return None
    lines = [line.strip() for line in req_text.splitlines() if line.strip()]
    if not lines:
        return None

    prefixes = ["job title:", "position:", "role:", "title:", "job:", "opportunity:", "hiring:"]
    for line in lines[:7]:
        normalized_line = normalize_text(line)
        for prefix in prefixes:
            if normalized_line.startswith(prefix):
                title = line[len(prefix):].strip().rstrip('.,:;-*#')
                if title and 2 < len(title) < 100:
                    print(f"Info: Extracted title '{title}' using prefix '{prefix}'")
                    return normalize_text(title)

    first_line = lines[0].strip().rstrip('.,:;-*#')
    if 2 < len(first_line) < 70 and first_line.count(' ') < 10 and \
        not any(c in first_line for c in ['@', '<', '>', '=', '+']) and \
       'http' not in first_line.lower() and \
        not re.match(r'^\d+$', first_line):
           print(f"Info: Extracted title '{first_line}' using first line heuristic.")
           return normalize_text(first_line)

    print("Warning: Could not confidently extract job title from requirement.", file=sys.stderr)
    return None

def extract_skills_fuzzy(nlp, text, skill_keywords, threshold=80):
    text_norm = normalize_text(text.lower())

    # 1) Collect single‐word lemmas as before
    doc = nlp(text_norm)
    lemmas = {tok.lemma_ for tok in doc if tok.is_alpha and not tok.is_stop}
    skills_exact = []
    for kw in skill_keywords:
        norm_kw = normalize_text(kw)
        if norm_kw in lemmas:
            skills_exact.append(norm_kw)

    # 2) Fuzzy‐match each remaining keyword
    skills_fuzzy = []
    for kw in skill_keywords:
        norm_kw = normalize_text(kw)
        if norm_kw in skills_exact:
            continue
        score = fuzz.partial_ratio(norm_kw, text_norm)
        if score >= threshold:
            skills_fuzzy.append(norm_kw)

    return sorted(set(skills_exact + skills_fuzzy))

def parse_date(date_str: str, is_end_date: bool = False):
    _current_time = datetime.now()
    date_str = date_str.lower().strip()
    if date_str in ['present', 'current', 'till date', 'now', 'ongoing']:
        return (_current_time.year, _current_time.month) if is_end_date else None

    try:
        month_name_local = r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z\.]{0,6}'
        year_local = r'\b(?:19[89]\d|20\d{2})\b'

        match = re.match(r'(' + month_name_local + r')\s+(' + year_local + r')', date_str, re.IGNORECASE)
        if match:
            month_str = match.group(1)[:3]
            month_map = {name[:3]: i+1 for i, name in enumerate(['jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec'])}
            return (int(match.group(2).strip()), month_map[month_str])

        match = re.match(r'(\d{1,2})\s?[/-]\s?(' + year_local + r')', date_str)
        if match:
            month = int(match.group(1))
            if 1 <= month <= 12:
                return (int(match.group(2).strip()), month)

        match = re.match(r'(' + year_local + r')', date_str)
        if match:
            year_val = int(match.group(1).strip())
            return (year_val, 12 if is_end_date else 1)

    except Exception:
        pass

    return None

def calculate_months_difference(start_date, end_date):
    if not start_date or not end_date: return 0

    start_year, start_month = start_date
    end_year, end_month = end_date

    if start_year > end_year or (start_year == end_year and start_month > end_month):
        return 0

    return (end_year - start_year) * 12 + (end_month - start_month) + 1


def extract_total_months_experience(text: str) -> int:
    month_name = r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z\.]{0,6}'
    year = r'\b(?:19[89]\d|20\d{2})\b'
    month_year = rf'(?:{month_name}\s+{year}|\b\d{{1,2}}\s?[/-]\s?{year}\b)'
    date_pattern = rf'(?:{month_year}|{year})'
    end_date_present = r'(?:Present|Current|Till\s+Date|Now|Ongoing)'
    end_date_pattern = rf'(?:{date_pattern}|{end_date_present})'
    date_range_separator = r'\s*[-\u2013\u2014to]+\s*'

    title_pattern = r'[A-Za-z][A-Za-z0-9\s\.,\-&\'\/]{3,90}'

    patterns = [
        rf"""
            (?:^|\n)\s*
            (?P<title>{title_pattern})
            (?:\s*(?:at|,)\s*[^\n(]+?)?
            \s*
            \(?\s*
            (?P<start_date>{date_pattern})
            {date_range_separator}
            (?P<end_date>{end_date_pattern})
            \s*\)?
        """,
        rf"""
            (?:^|\n)\s*
            (?P<title>{title_pattern})
            (?:\s*\n\s*[^\n(]{{2,80}})?
            (?:\s*\n\s*)?
            \(?\s*
            (?P<start_date>{date_pattern})
            {date_range_separator}
            (?P<end_date>{end_date_pattern})
            \s*\)?
        """,
        rf"""
            (?:^|\n)\s*
            (?P<start_date>{date_pattern})
            {date_range_separator}
            (?P<end_date>{end_date_pattern})
            \b
        """
    ]

    experiences = []
    found_spans = set()

    text_cleaned = re.sub(r'(\d)\s+(\d)', r'\1\2', text)

    for pattern_str in patterns:
        try:
            for match in re.finditer(pattern_str, text_cleaned, re.IGNORECASE | re.MULTILINE | re.VERBOSE):
                try:
                    start_str = match.group('start_date').strip()
                    end_str = match.group('end_date').strip()

                    date_span = (match.start('start_date'), match.end('end_date'))

                    if any(
                        (found[0] <= date_span[0] and found[1] >= date_span[1]) or
                        (date_span[0] <= found[0] and date_span[1] >= found[1]) or
                        (max(found[0], date_span[0]) < min(found[1], date_span[1]))
                        for found in found_spans
                    ):
                        continue

                    start_date = parse_date(start_str, is_end_date=False)
                    end_date = parse_date(end_str, is_end_date=True)

                    if not (start_date and end_date):
                        continue

                    months = calculate_months_difference(start_date, end_date)
                    if months > 0:
                        experiences.append({
                            'start': start_date,
                            'end': end_date,
                            'months': months,
                            'span': date_span
                        })
                        found_spans.add(date_span)

                except IndexError:
                    continue
                except Exception:
                    continue

        except re.error as e:
             continue

    if not experiences:
        return 0

    experiences.sort(key=lambda x: (x['start'], x['end']))

    merged = []
    if experiences:
        current_start, current_end = experiences[0]['start'], experiences[0]['end']

        for i in range(1, len(experiences)):
            next_start, next_end = experiences[i]['start'], experiences[i]['end']

            if next_start <= current_end:
                current_end = max(current_end, next_end)
            else:
                merged.append({'start': current_start, 'end': current_end})
                current_start, current_end = next_start, next_end

        merged.append({'start': current_start, 'end': current_end})

    total_merged_months = sum(calculate_months_difference(period['start'], period['end']) for period in merged)

    return total_merged_months


def extract_word_count(text: str) -> int:
    return len(text.split()) if text else 0

def extract_gpa(text: str) -> Optional[float]:
    patterns = [
        r'(?:GPA|Grade Point Average)\s*[:\-]?\s*(\d\.\d{1,2})\s*(?:/\s*4(?:\.0{1,2})?)?',
        r'(\d\.\d{1,2})\s*(?:/\s*4(?:\.0{1,2})?)?\s*(?:GPA|Grade Point Average)',
        r'GPA\s*of\s*(\d\.\d{1,2})',
        r'\b(\d\.\d{1,2})\s*(?:out\s+of\s+4(?:\.0{1,2})?)\b'
    ]
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            try:
                gpa_str = match.group(1)
                gpa = float(gpa_str)
                if 1.0 <= gpa <= 4.0:
                    return gpa
            except (ValueError, IndexError):
                continue
            except Exception as e:
                 print(f"Warning: Error parsing GPA match '{match.group(0)}': {e}", file=sys.stderr)

    return None

def calculate_jd_score(jd_similarity: float) -> float:
    if jd_similarity >= TARGET_JD_SIMILARITY:
        return WEIGHT_JD
    elif TARGET_JD_SIMILARITY > 0:
        return max(0.0, (jd_similarity / TARGET_JD_SIMILARITY) * WEIGHT_JD)
    return 0.0

def calculate_skill_score(skill_count: int) -> float:
    if skill_count >= TARGET_SKILLS:
        return WEIGHT_SKILL * USER_SKILL_WEIGHT
    elif TARGET_SKILLS > 0:
        return max(0.0, (skill_count / TARGET_SKILLS) * WEIGHT_SKILL * USER_SKILL_WEIGHT)
    return 0.0

def calculate_months_score(total_months: int, score_jd: float) -> float:
    factor = (score_jd / WEIGHT_JD)
    target = TARGET_MONTHS_EXPERIENCE
    if total_months >= target:
        return WEIGHT_MONTHS * USER_EXPERIENCE_WEIGHT * factor 
    elif target > 0:
        return max(0.0, (total_months / target) * WEIGHT_MONTHS * USER_EXPERIENCE_WEIGHT * factor)
    return 0.0

def calculate_word_score(word_count: int) -> float:
    if word_count >= TARGET_WORD_COUNT:
        return WEIGHT_WORD
    elif TARGET_WORD_COUNT > 0:
        return max(0.0, (word_count / TARGET_WORD_COUNT) * WEIGHT_WORD)
    return 0.0

def calculate_gpa_score(gpa: Optional[float]) -> float:
    if gpa is None:
        return 0.0
    if gpa >= TARGET_GPA:
        return WEIGHT_GPA
    elif TARGET_GPA > 0:
        return max(0.0, (gpa / TARGET_GPA) * WEIGHT_GPA)
    return 0.0

def calculate_final_score(jd_similarity: float, skill_count: int, total_months: int,
                         word_count: int, gpa: Optional[float], details: Dict) -> float:
    score_jd = calculate_jd_score(jd_similarity)
    score_skill = calculate_skill_score(skill_count)
    score_months = calculate_months_score(total_months, score_jd)
    score_word = calculate_word_score(word_count)
    score_gpa = calculate_gpa_score(gpa)

    raw_score = score_jd + score_skill + score_months + score_word + score_gpa

    max_score = MAX_SCORE_WITH_GPA if gpa is not None else MAX_SCORE_WITHOUT_GPA

    final_score = (raw_score / max_score) * 100.0 if max_score > 0 else 0.0

    details['scores'] = {
        'jd': score_jd, 'skill': score_skill, 'months': score_months,
        'word': score_word, 'gpa': score_gpa,
        'raw': raw_score, 'max': max_score
    }

    # st.info(details)

    return max(0.0, min(100.0, final_score))

class CVScanner:
    def __init__(self, model_id: str = "BAAI/bge-large-en-v1.5", batch_size: int = 128, spacy_package: str = "en_core_web_sm"):
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print(f"Info: Using device: {self.device}")
        try:
            models_cache_dir = Path("./models")
            models_cache_dir.mkdir(parents=True, exist_ok=True)
            print(f"Info: Loading Sentence Transformer model '{model_id}'...")
            self.model = SentenceTransformer(model_id, device=self.device, cache_folder=str(models_cache_dir))
            print(f"Info: Sentence Transformer model loaded.")
        except Exception as e:
            print(f"Error: Failed to load Sentence Transformer model '{model_id}': {e}", file=sys.stderr)
            print("Ensure the model name is correct and dependencies are installed.", file=sys.stderr)
            raise

        try:
            if not spacy.util.is_package(spacy_package):
                 print(f"Info: SpaCy model '{spacy_package}' not found. Downloading...")
                 spacy.cli.download(spacy_package)
            print(f"Info: Loading SpaCy model '{spacy_package}'...")
            self.nlp = spacy.load(spacy_package, disable=['parser', 'ner', 'textcat'])
            print(f"Info: SpaCy model loaded.")
        except Exception as e:
            print(f"Error: Failed to load SpaCy model '{spacy_package}': {e}", file=sys.stderr)
            print("Ensure the package name is correct and installed.", file=sys.stderr)
            raise

        self.batch_size = batch_size

    def extract_text_from_pdf(self, pdf_path: Union[str, Path]) -> str:
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

    def normalize_cv_text(self, text: str) -> str:
        return re.sub(r'\s+', ' ', text).strip().lower()

    def calculate_similarity(self, text1: str, text2: str) -> float:
        if not text1 or not text2:
            return 0.0
        try:
            embeddings = self.model.encode(
                [text1, text2],
                normalize_embeddings=True,
                device=self.device,
                batch_size=self.batch_size
            )
            similarity = float(embeddings[0] @ embeddings[1].T)
            return max(0.0, min(1.0, similarity))
        except Exception as e:
            print(f"Error calculating sentence similarity: {e}", file=sys.stderr)
            return 0.0

    def scan(self, req_text: str, pdf_dir: Path, job_skills_map: Dict[str, List[str]], target_job_title: Optional[str] = None, pdf_list: Optional[List[str]] = None) -> Dict[str, Dict]:
        pdf_dir = Path(pdf_dir)
        if not pdf_dir.is_dir():
            print(f"Error: PDF directory not found: '{pdf_dir}'", file=sys.stderr)
            return {}

        if pdf_list:
            file_paths = [pdf_dir / fname for fname in pdf_list]
        else:
            file_paths = sorted(pdf_dir.glob("*.pdf"))

        if not file_paths:
            print(f"Warning: No PDF files found in '{pdf_dir}' (pdf_list={pdf_list})", file=sys.stderr)
            return {}

        print(f"Info: Found {len(file_paths)} PDF files to scan.")

        final_title_to_match = None
        if target_job_title:
             final_title_to_match = normalize_text(target_job_title)
             print(f"Info: Using provided target job title: '{final_title_to_match}'")
        else:
            print("Info: Attempting to extract job title from requirement text...")
            extracted_title = extract_job_title_from_requirement(req_text)
            if extracted_title:
                final_title_to_match = extracted_title
                print(f"Info: Using extracted job title: '{final_title_to_match}'")
            else:
                print("Warning: Could not determine job title. Skill matching will be skipped.", file=sys.stderr)
                final_title_to_match = None

        relevant_skills: List[str] = []
        matched_skills_map_title: Optional[str] = None
        if final_title_to_match and job_skills_map:
            print(f"Info: Finding relevant skills for title '{final_title_to_match}'...")
            match_result = process.extractOne(
                final_title_to_match,
                job_skills_map.keys(),
                scorer=fuzz.token_sort_ratio
            )
            if match_result and match_result[1] >= FUZZY_TITLE_MATCH_THRESHOLD:
                matched_skills_map_title = match_result[0]
                relevant_skills = job_skills_map[matched_skills_map_title]
                print(f"Info: Matched title '{final_title_to_match}' to skills map title '{matched_skills_map_title}' (Score: {match_result[1]}). Using {len(relevant_skills)} skills.")
            else:
                score_info = f"(Score: {match_result[1]})" if match_result else "(No match)"
                print(f"Warning: Could not find a good match for title '{final_title_to_match}' in the skills map {score_info}. Skill matching may be inaccurate or skipped.", file=sys.stderr)
        elif not final_title_to_match:
             print("Info: No job title determined, skipping skill extraction based on title.")
        elif not job_skills_map:
             print("Info: Job skills map is empty, skipping skill extraction.")

        judgements: Dict[str, Dict] = {}
        normalized_req_text = self.normalize_cv_text(req_text)

        for i, file_path in enumerate(file_paths):
            # st.info(f"\n--- Processing CV {i+1}/{len(file_paths)}: {file_path.name} ---")
            cv_text_raw = self.extract_text_from_pdf(file_path)

            details = {
                'file_path': str(file_path),
                'matched_skills_map_title': matched_skills_map_title,
                'target_skills_list': relevant_skills,
                'cv_text_raw_len': len(cv_text_raw),
                'error': None
            }

            if not cv_text_raw:
                # st.info("Warning: Could not extract text from PDF. Assigning score 0.", file=sys.stderr)
                details['error'] = "PDF text extraction failed"
                judgements[str(file_path)] = {'score': 0.0, **details}
                continue

            normalized_cv_text = self.normalize_cv_text(cv_text_raw)
            if not normalized_cv_text:
                # st.info("Warning: Normalized CV text is empty. Assigning score 0.", file=sys.stderr)
                details['error'] = "CV text empty after normalization"
                judgements[str(file_path)] = {'score': 0.0, **details}
                continue

            # st.info("Calculating JD similarity...")
            jd_similarity = self.calculate_similarity(normalized_req_text, normalized_cv_text)
            details['jd_similarity'] = jd_similarity
            # st.info(f"JD Similarity: {jd_similarity:.3f}")

            # st.info(f"Extracting skills (using {len(relevant_skills)} target skills)...")
            # st.info(f"[cv_text_raw]: {cv_text_raw}")
            # st.info(f"[relevant_skills]:  {relevant_skills}")
            matched_skills = extract_skills_fuzzy(self.nlp, cv_text_raw, relevant_skills)
            details['matched_skills_list'] = matched_skills
            details['matched_skills_count'] = len(matched_skills)
            # st.info(f"Matched Skills ({len(matched_skills)}): {', '.join(matched_skills) if matched_skills else 'None'}")

            # st.info("Calculating total months experience...")
            total_months = extract_total_months_experience(cv_text_raw)
            details['total_months_experience'] = total_months
            # st.info(f"Total Experience: {total_months} months")

            word_count = extract_word_count(normalized_cv_text)
            details['word_count'] = word_count
            # st.info(f"Word Count: {word_count}")

            # st.info("Extracting GPA...")
            gpa = extract_gpa(cv_text_raw)
            details['gpa'] = gpa
            # st.info(f"GPA: {gpa if gpa is not None else 'Not Found'}")

            # st.info("Calculating final score...")
            final_score = calculate_final_score(jd_similarity, len(matched_skills), total_months, word_count, gpa, details)
            details['score'] = final_score
            # st.info(f"--- Final Score for {file_path.name}: {final_score:.2f} ---")

            judgements[str(file_path)] = details

        return dict(sorted(judgements.items(), key=lambda item: item[1]['score'], reverse=True))

def run_cv_scanner(
    skills_file_path: Union[str, Path],
    job_description: str,
    pdf_folder: Union[str, Path],
    user_skill_weight: Optional[float] = None,
    user_experience_weight: Optional[float] = None,
    pdf_list: Optional[List[str]] = None,
    job_title: Optional[str] = None,
    model_id: str = "BAAI/bge-large-en-v1.5",
    spacy_model: str = "en_core_web_sm",
) -> Dict[str, Dict]:
    """
    1) Loads skills map from a pipe-delimited CSV.
    2) Uses the provided job_description text.
    3) Instantiates CVScanner with the given model & spaCy package.
    4) Scans only the PDFs you care about (either all in pdf_folder or just those in pdf_list).
    Returns: { pdf_path_str: details_dict } sorted by details['score'] desc.
    """
    # override the globals with what was passed in global USER_SKILL_WEIGHT, USER_EXPERIENCE_WEIGHT
    global USER_SKILL_WEIGHT, USER_EXPERIENCE_WEIGHT
    global TARGET_MONTHS_EXPERIENCE
    global MAX_SCORE_WITH_GPA, MAX_SCORE_WITHOUT_GPA

    global USER_SKILL_WEIGHT, USER_EXPERIENCE_WEIGHT
    global TARGET_MONTHS_EXPERIENCE, MAX_SCORE_WITH_GPA, MAX_SCORE_WITHOUT_GPA

    # 1) override
    if user_skill_weight is not None:
        USER_SKILL_WEIGHT = user_skill_weight
    if user_experience_weight is not None:
        USER_EXPERIENCE_WEIGHT = user_experience_weight

    # 2) recompute everything that depends on those two
    TARGET_MONTHS_EXPERIENCE = _cfg["target_months_base"] * USER_EXPERIENCE_WEIGHT

    MAX_SCORE_WITH_GPA = (
        WEIGHT_JD
        + WEIGHT_SKILL * USER_SKILL_WEIGHT
        + WEIGHT_MONTHS * USER_EXPERIENCE_WEIGHT
        + WEIGHT_WORD
        + WEIGHT_GPA
    )
    MAX_SCORE_WITHOUT_GPA = (
        WEIGHT_JD
        + WEIGHT_SKILL * USER_SKILL_WEIGHT
        + WEIGHT_MONTHS * USER_EXPERIENCE_WEIGHT
        + WEIGHT_WORD
    )
    # 1) load skills
    skills_map = load_skills()
    # st.info("🛠️ Configuration after overrides:")
    # st.info(f"   • user_skill_weight  (param): {user_skill_weight!r}")
    # st.info(f"   • USER_SKILL_WEIGHT (global): {USER_SKILL_WEIGHT!r}")
    # st.info(f"   • user_experience_weight  (param): {user_experience_weight!r}")
    # st.info(f"   • USER_EXPERIENCE_WEIGHT (global): {USER_EXPERIENCE_WEIGHT!r}")
    # st.info(f"   • TARGET_MONTHS_EXPERIENCE    : {TARGET_MONTHS_EXPERIENCE!r}")
    # st.info(f"   • MAX_SCORE_WITH_GPA          : {MAX_SCORE_WITH_GPA!r}")
    # st.info(f"   • MAX_SCORE_WITHOUT_GPA       : {MAX_SCORE_WITHOUT_GPA!r}")
    # st.info("──────────────────────────────────\n")

    # 2) validate job_description
    if not job_description or not job_description.strip():
        raise ValueError("`job_description` must be a non-empty string")

    # 3) build scanner
    scanner = CVScanner(
        model_id=model_id,
        spacy_package=spacy_model
    )

    # 4) run scan
    return scanner.scan(
        req_text=job_description,
        pdf_dir=Path(pdf_folder),
        job_skills_map=skills_map,
        target_job_title=job_title,
        pdf_list=pdf_list
    )