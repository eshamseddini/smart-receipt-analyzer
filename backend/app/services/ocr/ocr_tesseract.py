from pathlib import Path

import pytesseract
from pdf2image import convert_from_path
from PIL import Image

from app.services.ocr.base_ocr import BaseOCR


class TesseractOCR(BaseOCR):
    def extract_text(self, file_path: str) -> str:
        path = Path(file_path)
        extension = path.suffix.lower()

        if extension in [".png", ".jpg", ".jpeg"]:
            return self._extract_from_image(path)

        if extension == ".pdf":
            return self._extract_from_pdf(path)

        raise ValueError(f"Unsupported file extension for OCR: {extension}")

    def _extract_from_image(self, path: Path) -> str:
        with Image.open(path) as image:
            text = pytesseract.image_to_string(image)

        return text.strip()

    def _extract_from_pdf(self, path: Path) -> str:
        pages = convert_from_path(
            path,
            dpi=300,
            first_page=1,
            last_page=5,
        )

        extracted_pages: list[str] = []

        for page_number, page in enumerate(pages, start=1):
            text = pytesseract.image_to_string(page)

            if text.strip():
                extracted_pages.append(f"--- Page {page_number} ---\n{text.strip()}")

        return "\n\n".join(extracted_pages).strip()
