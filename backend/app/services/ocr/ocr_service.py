from app.services.ocr.ocr_factory import OCRFactory


def extract_text_from_file(file_path: str) -> str:
    ocr_engine = OCRFactory.create(engine="tesseract")
    return ocr_engine.extract_text(file_path)
