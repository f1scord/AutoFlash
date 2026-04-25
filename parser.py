import re
import pdfplumber
import docx
from exceptions import FileNotSupportedError

SUPPORTED = {".pdf", ".docx", ".txt"}


def parse_file(path: str) -> str:
    ext = _ext(path)
    if ext not in SUPPORTED:
        raise FileNotSupportedError(f"Unsupported file type: {ext}")
    return {
        ".pdf":  read_pdf,
        ".docx": read_docx,
        ".txt":  read_text,
    }[ext](path)


def read_pdf(path: str) -> str:
    parts = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            parts.append(text)
    return "\n\n".join(parts)


def read_docx(path: str) -> str:
    document = docx.Document(path)
    return "\n".join(p.text for p in document.paragraphs if p.text.strip())


def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def read_chunks(text: str, size: int = 4000):
    for i in range(0, len(text), size):
        yield text[i:i + size]


def _ext(path: str) -> str:
    m = re.search(r"\.[A-Za-z0-9]+$", path)
    if not m:
        raise FileNotSupportedError("File has no extension")
    return m.group(0).lower()
