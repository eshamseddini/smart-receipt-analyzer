from pathlib import Path

import pytesseract
from pdf2image import convert_from_path
from PIL import Image

from app.services.ocr.base_ocr import BaseOCR

# Above this, downscale before running OCR. Deliberately generous: testing
# showed Tesseract's accuracy is sensitive to resolution (a receipt shrunk
# to 2400px flipped "Carrefour" into "Garrefour"), and now that processing
# runs in the background (see receipt_processing_service.py), raw runtime
# matters far less than getting the merchant name right. This is a safety
# net for genuinely oversized images (6000px+ raw camera photos), not a
# routine downscale for typical phone photos.
MAX_OCR_DIMENSION = 4000


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
            resized = self._resize_if_needed(image)
            text = pytesseract.image_to_string(resized)

        return text.strip()

    def _resize_if_needed(self, image: Image.Image) -> Image.Image:
        if max(image.size) <= MAX_OCR_DIMENSION:
            return image

        resized = image.copy()
        resized.thumbnail((MAX_OCR_DIMENSION, MAX_OCR_DIMENSION), Image.LANCZOS)

        return resized

    def _extract_from_pdf(self, path: Path) -> str:
        pages = convert_from_path(
            path,
            dpi=300,
            first_page=1,
            last_page=5,
        )

        extracted_pages: list[str] = []

        for page_number, page in enumerate(pages, start=1):
            resized_page = self._resize_if_needed(page)
            text = pytesseract.image_to_string(resized_page)

            if text.strip():
                extracted_pages.append(f"--- Page {page_number} ---\n{text.strip()}")

        return "\n\n".join(extracted_pages).strip()
