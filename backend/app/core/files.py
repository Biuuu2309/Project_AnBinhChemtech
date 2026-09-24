from pathlib import Path

from app.core.config import PROJECT_ROOT, settings


def _allowed_roots() -> list[Path]:
    roots = [(PROJECT_ROOT / "worker" / "output").resolve()]
    configured = (settings.quotation_output_dir or "").strip()
    if configured:
        roots.append(Path(configured).resolve())
    # dedupe
    unique: list[Path] = []
    for root in roots:
        if root not in unique:
            unique.append(root)
    return unique


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def resolve_allowed_output_path(raw_path: str, *, quotation_id: str) -> Path:
    """
    Prevent arbitrary filesystem access on download/complete.
    Path must resolve under allowed output dir and be named {quotation_id}.docx.
    """
    if not raw_path or not str(raw_path).strip():
        raise ValueError("output_path is required")

    path = Path(raw_path).resolve()
    if not any(_is_relative_to(path, root) for root in _allowed_roots()):
        raise ValueError("output_path is outside allowed output directory")

    expected = f"{quotation_id}.docx"
    if path.name != expected:
        raise ValueError(f"output filename must be {expected}")

    return path


def ensure_file_readable(path: Path) -> Path:
    if not path.is_file():
        raise FileNotFoundError(f"Quotation file missing: {path.name}")
    if path.stat().st_size <= 0:
        raise ValueError("Quotation file is empty")
    return path
