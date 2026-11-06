import pypdf
import io


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    Extract plain text from a PDF file.
    Args:
        pdf_bytes: Raw bytes of the PDF file
    Returns:
        Extracted text as a string
    """
    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))

    text_parts = []
    for page_num, page in enumerate(reader.pages):
        text = page.extract_text()
        if text and text.strip():
            text_parts.append(text.strip())

    full_text = "\n\n".join(text_parts)

    if not full_text.strip():
        raise ValueError(
            "Could not extract text from PDF. "
            "The file may be scanned or image-based."
        )

    return full_text