from PIL import Image

from app.services.ocr.ocr_tesseract import MAX_OCR_DIMENSION, TesseractOCR


def test_small_image_is_left_untouched():
    ocr = TesseractOCR()
    image = Image.new("RGB", (800, 1200))

    result = ocr._resize_if_needed(image)

    assert result.size == (800, 1200)
    assert result is image


def test_oversized_image_is_downscaled_preserving_aspect_ratio():
    ocr = TesseractOCR()
    image = Image.new("RGB", (3000, 6000))

    result = ocr._resize_if_needed(image)

    assert max(result.size) == MAX_OCR_DIMENSION
    assert result.size[0] / result.size[1] == 3000 / 6000


def test_image_exactly_at_the_threshold_is_left_untouched():
    ocr = TesseractOCR()
    image = Image.new("RGB", (MAX_OCR_DIMENSION, 1000))

    result = ocr._resize_if_needed(image)

    assert result is image
