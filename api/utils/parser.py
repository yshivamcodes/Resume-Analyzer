"""
parser.py — PDF text extraction using pdfplumber.
Handles edge cases: empty pages, broken formatting, special characters.
"""
import io
import re
import pdfplumber


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extracts and cleans all text from a PDF file provided as bytes.
    Handles large PDFs, empty pages, and special character cleanup.
    """
    text_parts = []
    
    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                extracted = page.extract_text()
                if extracted:
                    text_parts.append(extracted)
    except Exception as e:
        print(f"Error parsing PDF: {e}")
        return ""
    
    raw_text = "\n".join(text_parts)
    
    # Clean up
    cleaned = _clean_text(raw_text)
    
    return cleaned


def _clean_text(text: str) -> str:
    """Cleans extracted PDF text for analysis."""
    if not text:
        return ""
    
    # Replace multiple whitespace/newlines with single space
    text = re.sub(r'\s+', ' ', text)
    
    # Remove unusual unicode characters but keep common symbols
    text = re.sub(r'[^\x00-\x7F\u2013\u2014\u2018\u2019\u201C\u201D\u2022\u2026]+', ' ', text)
    
    # Normalize dashes and bullets
    text = text.replace('\u2013', '-').replace('\u2014', '-')
    text = text.replace('\u2022', '•')
    text = text.replace('\u2018', "'").replace('\u2019', "'")
    text = text.replace('\u201C', '"').replace('\u201D', '"')
    
    # Collapse multiple spaces again after cleanup
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text
