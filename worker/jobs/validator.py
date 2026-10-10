from pathlib import Path
from zipfile import ZipFile


def validate_quotation_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Output file missing: {path}")
    if path.stat().st_size <= 0:
        raise ValueError(f"Output file is empty: {path}")

    suffix = path.suffix.lower()
    if suffix == ".pptx":
        try:
            with ZipFile(path) as zf:
                names = set(zf.namelist())
                if "[Content_Types].xml" not in names:
                    raise ValueError("PPTX missing [Content_Types].xml")
                if not any(n.startswith("ppt/slides/") for n in names):
                    raise ValueError("PPTX missing ppt/slides/")
        except ValueError:
            raise
        except Exception as exc:
            raise ValueError(f"Output is not a valid PPTX: {path}") from exc
        return

    if suffix == ".docx":
        from docx import Document

        try:
            Document(path)
        except Exception as exc:
            raise ValueError(f"Output is not a valid DOCX: {path}") from exc
        return

    raise ValueError(f"Unsupported quotation output type: {path.suffix}")
