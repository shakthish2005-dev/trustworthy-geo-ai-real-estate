from __future__ import annotations

import hashlib
import io
import re
from typing import Any


SURVEY_PATTERNS = [
    r"(?:survey|sy\.?\s*no|s\.?\s*no)\s*[:#-]?\s*([A-Z0-9/-]{2,30})",
    r"(?:plot|site)\s*(?:no)?\s*[:#-]?\s*([A-Z0-9/-]{1,30})",
]
RERA_PATTERN = r"\b(?:RERA|PRM|P\d{4})[-/A-Z0-9]{5,35}\b"


def _pdf_text(data: bytes) -> str:
    try:
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(data))
        return "\n".join((page.extract_text() or "") for page in reader.pages)
    except Exception:
        return ""


def inspect_upload(name: str, data: bytes, mime_type: str = "") -> dict[str, Any]:
    digest = hashlib.sha256(data).hexdigest()
    text = _pdf_text(data) if name.lower().endswith(".pdf") else ""
    normalized = " ".join(text.split())
    survey_numbers = []
    for pattern in SURVEY_PATTERNS:
        survey_numbers.extend(re.findall(pattern, normalized, flags=re.IGNORECASE))
    rera_ids = re.findall(RERA_PATTERN, normalized, flags=re.IGNORECASE)
    warnings = []
    if not data:
        warnings.append("Empty file")
    if name.lower().endswith(".pdf") and not text:
        warnings.append("No extractable PDF text; this may be a scanned document requiring OCR/manual review")
    return {
        "file_name": name,
        "mime_type": mime_type,
        "size_bytes": len(data),
        "sha256": digest,
        "text_characters": len(text),
        "survey_numbers": sorted(set(survey_numbers))[:10],
        "rera_ids": sorted(set(rera_ids))[:10],
        "warnings": warnings,
        "notice": "Hash and text extraction do not establish authenticity. Verify certified originals with the issuing authority.",
    }
