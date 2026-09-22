from pathlib import Path

from docx import Document


def validate_quotation_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Output file missing: {path}")
    if path.stat().st_size <= 0:
        raise ValueError(f"Output file is empty: {path}")
    try:
        Document(path)
    except Exception as exc:
        raise ValueError(f"Output is not a valid DOCX: {path}") from exc
