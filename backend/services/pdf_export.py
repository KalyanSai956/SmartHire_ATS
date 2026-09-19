import io
import logging

from playwright.sync_api import sync_playwright
from pypdf import PdfReader, PdfWriter

logger = logging.getLogger("ats_resume_scorer")


def generate_combined_pdf(html_docs: dict[str, str]) -> bytes:
    """
    Generate a combined PDF from multiple HTML documents.

    Playwright runs synchronously because FastAPI will execute
    this function in a worker thread.
    """

    if not html_docs:
        raise ValueError("No HTML documents provided.")

    pdf_chunks: list[bytes] = []

    with sync_playwright() as p:
        browser = p.chromium.launch()

        try:
            for name, html_str in html_docs.items():

                if not isinstance(html_str, str):
                    raise TypeError(
                        f"HTML document '{name}' must be a string, "
                        f"got {type(html_str).__name__}"
                    )

                logger.info(
                    "Generating PDF for %s (%d characters)",
                    name,
                    len(html_str)
                )

                page = browser.new_page()

                try:
                    page.set_content(
                        html_str,
                        wait_until="networkidle"
                    )

                    pdf_bytes = page.pdf(
                        format="A4",
                        print_background=True,
                        margin={
                            "top": "15mm",
                            "right": "15mm",
                            "bottom": "15mm",
                            "left": "15mm",
                        },
                    )

                    pdf_chunks.append(pdf_bytes)

                finally:
                    page.close()

        finally:
            browser.close()

    return merge_pdfs(pdf_chunks)


def merge_pdfs(pdf_chunks: list[bytes]) -> bytes:
    """Merge multiple PDF byte streams into one PDF."""

    writer = PdfWriter()

    for pdf_bytes in pdf_chunks:
        reader = PdfReader(io.BytesIO(pdf_bytes))

        for page in reader.pages:
            writer.add_page(page)

    output = io.BytesIO()
    writer.write(output)

    return output.getvalue()