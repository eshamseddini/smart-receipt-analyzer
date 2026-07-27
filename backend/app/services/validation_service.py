from fastapi import HTTPException, UploadFile

from app.core.config import settings

ALLOWED_EXTENSIONS = ["pdf", "png", "jpg", "jpeg"]

ALLOWED_MIME_TYPES_BY_EXTENSION = {
    "pdf": {"application/pdf"},
    "png": {"image/png"},
    "jpg": {"image/jpeg"},
    "jpeg": {"image/jpeg"},
}


def validate_uploaded_file(file: UploadFile) -> str:
    """
    Validate the uploaded file's name, extension and declared MIME type.

    Args:
        file (UploadFile): The uploaded file to be validated.

    Raises:
        HTTPException: If the file is not uploaded or has an invalid type.
    """
    if file is None or file.filename == "":
        raise HTTPException(status_code=400, detail="No file uploaded. Please upload a PDF, PNG, JPG, or JPEG file.")

    extension = file.filename.split(".")[-1].lower()
    if extension == "":
        raise HTTPException(status_code=400, detail="File has no extension. Please upload a PDF, PNG, JPG, or JPEG file.")

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a PDF, PNG, JPG, or JPEG file.")

    expected_mime_types = ALLOWED_MIME_TYPES_BY_EXTENSION[extension]
    if file.content_type not in expected_mime_types:
        raise HTTPException(
            status_code=400,
            detail=f"File content type '{file.content_type}' does not match its '.{extension}' extension.",
        )

    return extension


def validate_file_size(contents: bytes) -> None:
    """
    Validate that the uploaded file does not exceed the configured size limit.

    Args:
        contents (bytes): The raw uploaded file content.

    Raises:
        HTTPException: If the file exceeds the maximum allowed size.
    """
    max_size_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(contents) > max_size_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File is too large. Maximum allowed size is {settings.MAX_UPLOAD_SIZE_MB}MB.",
        )