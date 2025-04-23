import os, datetime

def make_filename(job_title: str, original_name: str) -> str:
    """Sanitize job title and original filename, append timestamp."""
    name, ext = os.path.splitext(original_name)
    safe_title = job_title.replace(" ", "_")
    safe_name = name.replace(" ", "_")
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    return f"[{safe_title}]_{safe_name}_{timestamp}{ext}"
