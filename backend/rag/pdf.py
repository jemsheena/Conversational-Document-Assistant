import os
import re
from typing import Dict, List

import fitz  # PyMuPDF


def _normalize_hyphenation(text: str) -> str:
    """Fix hyphenation: join words split across lines."""
    # Remove hyphen-space-newline patterns
    text = re.sub(r"-\s+\n\s*", "", text)
    # Remove hyphen-newline patterns
    text = re.sub(r"-\n", "", text)
    return text


def _detect_header_footer(text: str, page_num: int, total_pages: int) -> tuple[str, str]:
    """
    Basic header/footer detection heuristic.
    Returns (header, footer) - typically first/last 2-3 lines.
    """
    lines = text.split("\n")
    if len(lines) < 6:
        return "", ""

    # First 2 lines often header
    header = "\n".join(lines[:2])
    # Last 2 lines often footer
    footer = "\n".join(lines[-2:])

    return header, footer


def _drop_repeating_headers_footers(pages: List[str], drop_headers: bool = True) -> List[str]:
    """
    Remove repeating headers/footers across pages.
    Simple heuristic: if first/last lines are identical across >50% pages, drop them.
    """
    if not drop_headers or len(pages) < 3:
        return pages

    # Count header/footer frequencies
    header_counts = {}
    footer_counts = {}

    for page in pages:
        lines = page.split("\n")
        if len(lines) >= 2:
            header = lines[0].strip()
            footer = lines[-1].strip()
            header_counts[header] = header_counts.get(header, 0) + 1
            footer_counts[footer] = footer_counts.get(footer, 0) + 1

    # Find common headers/footers (appear in >50% pages)
    threshold = len(pages) * 0.5
    common_headers = {h for h, c in header_counts.items() if c > threshold and len(h) > 0}
    common_footers = {f for f, c in footer_counts.items() if c > threshold and len(f) > 0}

    # Remove them
    cleaned = []
    for page in pages:
        lines = page.split("\n")
        if len(lines) >= 2:
            # Remove first line if it's a common header
            if lines[0].strip() in common_headers:
                lines = lines[1:]
            # Remove last line if it's a common footer
            if lines and lines[-1].strip() in common_footers:
                lines = lines[:-1]
        cleaned.append("\n".join(lines))

    return cleaned


def _extract_pages_from_doc(
    doc: fitz.Document,
    drop_headers: bool = True,
    normalize_hyphen: bool = True,
) -> List[str]:
    pages = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        if normalize_hyphen:
            text = _normalize_hyphenation(text)
        text = " ".join(text.split())
        pages.append(text)
    doc.close()
    if drop_headers:
        pages = _drop_repeating_headers_footers(pages, drop_headers=True)
    return pages


def extract_text_from_pdf_bytes(
    content: bytes, drop_headers: bool = True, normalize_hyphen: bool = True
) -> List[str]:
    """Extract text from PDF bytes, one string per page."""
    doc = fitz.open(stream=content, filetype="pdf")
    return _extract_pages_from_doc(
        doc, drop_headers=drop_headers, normalize_hyphen=normalize_hyphen
    )


def extract_text_from_pdf(
    pdf_path: str, drop_headers: bool = True, normalize_hyphen: bool = True
) -> List[str]:
    """
    Extract text from PDF, one string per page.
    Pipeline Stage 1: Parse & normalize.

    Args:
        pdf_path: Path to PDF file
        drop_headers: Remove repeating headers/footers
        normalize_hyphen: Fix hyphenation artifacts

    Returns:
        List of page texts with metadata
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    with open(pdf_path, "rb") as f:
        return extract_text_from_pdf_bytes(
            f.read(), drop_headers=drop_headers, normalize_hyphen=normalize_hyphen
        )


def extract_text_with_metadata(pdf_path: str) -> List[Dict]:
    """
    Extract text with bbox and page metadata.
    Returns list of dicts with 'text', 'page', 'bbox', 'font_size'.
    """
    doc = fitz.open(pdf_path)
    blocks = []

    for page_num in range(len(doc)):
        page = doc[page_num]

        # Get text blocks with bbox
        text_dict = page.get_text("dict")

        for block in text_dict["blocks"]:
            if "lines" in block:
                block_text = ""
                for line in block["lines"]:
                    for span in line["spans"]:
                        block_text += span["text"] + " "

                if block_text.strip():
                    blocks.append(
                        {
                            "text": block_text.strip(),
                            "page": page_num + 1,
                            "bbox": block["bbox"],
                            "font_size": block["lines"][0]["spans"][0]["size"]
                            if block["lines"]
                            else 12,
                        }
                    )

    doc.close()
    return blocks
