import pytest
from fastapi import HTTPException

from app.services.validation_service import validate_file_size, validate_uploaded_file


class FakeUploadFile:
    def __init__(self, filename: str, content_type: str | None = None):
        self.filename = filename
        self.content_type = content_type


def test_valid_png_file():
    file = FakeUploadFile("ticket.png", content_type="image/png")
    result = validate_uploaded_file(file)
    assert result == "png"


def test_valid_pdf_file():
    file = FakeUploadFile("document.pdf", content_type="application/pdf")
    result = validate_uploaded_file(file)
    assert result == "pdf"


def test_invalid_txt_file():
    file = FakeUploadFile("bad.txt", content_type="text/plain")

    with pytest.raises(HTTPException):
        validate_uploaded_file(file)


def test_empty_filename():
    file = FakeUploadFile("")

    with pytest.raises(HTTPException):
        validate_uploaded_file(file)


def test_mismatched_content_type_is_rejected():
    file = FakeUploadFile("ticket.png", content_type="application/pdf")

    with pytest.raises(HTTPException):
        validate_uploaded_file(file)


def test_file_within_size_limit_is_accepted():
    validate_file_size(b"small content")


def test_file_exceeding_size_limit_is_rejected(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "MAX_UPLOAD_SIZE_MB", 1)

    oversized_content = b"0" * (2 * 1024 * 1024)

    with pytest.raises(HTTPException):
        validate_file_size(oversized_content)
