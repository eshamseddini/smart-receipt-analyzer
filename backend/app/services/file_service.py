import os
import uuid

from fastapi import UploadFile


def save_uploaded_file(file: UploadFile, contents: bytes) -> str:
    """
    Save already-read uploaded file content to the 'uploads' directory.

    Args:
        file (UploadFile): The uploaded file to be saved.
        contents (bytes): The raw content of the uploaded file.

    Returns:
        str: The path where the file was saved.
    """
    # Create the 'uploads' directory if it doesn't exist
    os.makedirs("uploads", exist_ok=True)
    safe_filename = file.filename.replace(" ", "_")
    unique_id = str(uuid.uuid4())[:8]

    # Define the destination path for the uploaded file
    dest_path = os.path.join("uploads", f"{unique_id}-{safe_filename}")

    # Save the uploaded file to the destination path
    with open(dest_path, "wb") as f:
        f.write(contents)

    return dest_path


def delete_local_file(file_path: str) -> bool:
    """
    Delete a local file.

    Args:
        file_path (str): The path of the file to be deleted.
    """
    if os.path.exists(file_path):
        os.remove(file_path)
        return True
    return False
