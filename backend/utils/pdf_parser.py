"""Low-level PDF text extraction utilities (PyMuPDF + pdfplumber)."""
import fitz  # PyMuPDF
import pdfplumber


def extract_text_pymupdf(file_path: str) -> str:
    """Extract raw text from every page using PyMuPDF."""
    doc = fitz.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text.strip()


def extract_tables_pdfplumber(file_path: str) -> str:
    """Extract tabular data (lab grids) from every page using pdfplumber."""
    table_text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    if row:
                        table_text += " | ".join([str(c or "") for c in row]) + "\n"
    return table_text


def combine_pdf_text(file_path: str) -> str:
    """Run both extractors and combine their output."""
    raw_text = extract_text_pymupdf(file_path)
    table_data = extract_tables_pdfplumber(file_path)
    return raw_text + "\n\n[TABLES]\n" + table_data
