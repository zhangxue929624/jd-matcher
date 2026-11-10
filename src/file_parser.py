"""文件解析：从上传文件（PDF/DOCX/TXT/MD）提取纯文本。"""
from pathlib import Path

SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf", ".docx"}


class FileParseError(Exception):
    """文件解析失败，message面向用户可读。"""


def _parse_pdf(path: Path) -> str:
    import fitz  # PyMuPDF

    with fitz.open(path) as doc:
        return "\n".join(page.get_text() for page in doc)


def _parse_docx(path: Path) -> str:
    import docx  # python-docx

    doc = docx.Document(path)
    return "\n".join(p.text for p in doc.paragraphs)


def parse_file(path: str | Path) -> str:
    """按扩展名解析文件为纯文本；空内容或不支持的格式抛FileParseError。"""
    path = Path(path)
    ext = path.suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise FileParseError(f"不支持的文件格式 {ext}，请使用：{', '.join(sorted(SUPPORTED_EXTENSIONS))}")
    try:
        if ext in (".txt", ".md"):
            text = path.read_text(encoding="utf-8", errors="ignore")
        elif ext == ".pdf":
            text = _parse_pdf(path)
        else:
            text = _parse_docx(path)
    except FileParseError:
        raise
    except Exception as e:
        raise FileParseError(f"文件解析失败：{e}") from e
    if not text.strip():
        raise FileParseError("未能从文件中提取到文字内容（可能是扫描件图片）")
    return text.strip()
