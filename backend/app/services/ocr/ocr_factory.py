from app.services.ocr.base_ocr import BaseOCR
from app.services.ocr.ocr_tesseract import TesseractOCR


class OCRFactory:
    @staticmethod
    def create(engine: str = "tesseract") -> BaseOCR:
        if engine == "tesseract":
            return TesseractOCR()

        raise ValueError(f"Unsupported OCR engine: {engine}")
