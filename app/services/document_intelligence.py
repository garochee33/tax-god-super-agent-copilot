"""
Advanced PDF extraction and document intelligence (Trinity GEM port).

- Full text and table extraction from PDFs for vault ingest and RAG.
- Optional entity hints for tax docs (W-2, 1099 style).
"""

from __future__ import annotations

import io
import re
from dataclasses import dataclass, field
from typing import Any

logger = None  # set on first use to avoid import-time logging config


def _log():
    import logging
    global logger
    if logger is None:
        logger = logging.getLogger(__name__)
    return logger


@dataclass
class ExtractedTable:
    """One table extracted from text (ragflow-style pipe tables)."""
    headers: list[str]
    rows: list[list[str]]
    raw_text: str


@dataclass
class PdfExtractionResult:
    """Result of PDF extraction (Trinity advanced-pdf style)."""
    text: str
    num_pages: int
    tables: list[ExtractedTable]
    metadata: dict[str, Any] = field(default_factory=dict)


def extract_tables_from_text(text: str) -> list[ExtractedTable]:
    """
    Extract markdown-style pipe tables from text (Trinity ragflow port).
    Lines that look like | col1 | col2 | are grouped into tables.
    """
    tables: list[ExtractedTable] = []
    lines = text.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        if "|" in line and line.strip().startswith("|"):
            table_lines: list[str] = []
            while i < len(lines) and "|" in lines[i]:
                table_lines.append(lines[i])
                i += 1
            if len(table_lines) >= 2:
                def parse_cells(l: str) -> list[str]:
                    return [c.strip() for c in l.split("|") if c.strip() and not re.match(r"^[\s\-:]+$", c.strip())]
                header_line = table_lines[0]
                # skip separator line like |---|-----|
                data_lines = [l for l in table_lines[1:] if not re.match(r"^\s*\|[\s\-:|]+\|\s*$", l)]
                headers = parse_cells(header_line)
                rows = [parse_cells(l) for l in data_lines]
                tables.append(ExtractedTable(headers=headers, rows=rows, raw_text="\n".join(table_lines)))
            continue
        i += 1
    return tables


def extract_text_from_pdf(buffer: bytes) -> PdfExtractionResult:
    """
    Extract full text and tables from a PDF buffer (Trinity advanced-pdf port).
    Uses pypdf for text; tables are detected from pipe-style blocks in extracted text.
    """
    try:
        from pypdf import PdfReader  # type: ignore[import-untyped]
    except ImportError:
        _log().warning("pypdf not installed; run pip install pypdf")
        return PdfExtractionResult(
            text="",
            num_pages=0,
            tables=[],
            metadata={"error": "pypdf not installed"},
        )
    text_parts: list[str] = []
    num_pages = 0
    metadata: dict[str, Any] = {}
    try:
        reader = PdfReader(io.BytesIO(buffer))
        num_pages = len(reader.pages)
        for page in reader.pages:
            t = page.extract_text()
            if t:
                text_parts.append(t)
        if reader.metadata:
            metadata["pdf_metadata"] = {
                k: getattr(reader.metadata, k, None)
                for k in ("title", "author", "subject", "creator", "producer")
                if getattr(reader.metadata, k, None)
            }
    except Exception as e:
        _log().exception("PDF extraction failed")
        return PdfExtractionResult(
            text="",
            num_pages=0,
            tables=[],
            metadata={"error": str(e)},
        )
    text = "\n".join(text_parts) or ""
    tables = extract_tables_from_text(text)
    return PdfExtractionResult(
        text=text,
        num_pages=num_pages,
        tables=[ExtractedTable(headers=t.headers, rows=t.rows, raw_text=t.raw_text) for t in tables],
        metadata=metadata,
    )


def extract_pdf_text_only(buffer: bytes) -> str:
    """Plain text only from PDF (for pipelines that only need content)."""
    result = extract_text_from_pdf(buffer)
    return result.text


def extract_entities_tax_doc(text: str) -> list[dict[str, str]]:
    """
    Simple entity hints for tax documents (W-2, 1099 style).
    Looks for SSN/EIN-like patterns and common labels; no PII stored.
    Returns list of { "type": "ssn"|"ein"|"amount"|"year", "label": str, "value": str }.
    """
    entities: list[dict[str, str]] = []
    # SSN pattern (XXX-XX-XXXX)
    for m in re.finditer(r"\b(\d{3}-\d{2}-\d{4})\b", text):
        entities.append({"type": "ssn", "label": "SSN", "value": m.group(1)})
    # EIN (XX-XXXXXXX)
    for m in re.finditer(r"\b(\d{2}-\d{7})\b", text):
        entities.append({"type": "ein", "label": "EIN", "value": m.group(1)})
    # Tax year
    for m in re.finditer(r"\b(20\d{2})\s+(?:tax\s+)?year\b", text, re.I):
        entities.append({"type": "year", "label": "Tax year", "value": m.group(1)})
    return entities
