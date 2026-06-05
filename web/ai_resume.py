import json
import re
from pathlib import Path
from typing import Any, Dict

import pdfplumber

JSON_BLOCK_RE = re.compile(r"\{.*\}", re.DOTALL)


def extract_text_from_pdf(path: Path) -> str:
    with pdfplumber.open(str(path)) as pdf:
        return "\n".join(page.extract_text() or "" for page in pdf.pages)


def extract_json_payload(text: str) -> Dict[str, Any]:
    match = JSON_BLOCK_RE.search(text)
    if not match:
        raise ValueError("No JSON found in response")
    payload = match.group(0)
    return json.loads(payload)
