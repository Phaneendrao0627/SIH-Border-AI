# ============================================================
# AI-BASED FAKE IDENTITY & DOCUMENT SCREENING SYSTEM
# MODULE 1: SECURITY & FILE INTEGRITY VALIDATION
# ============================================================

import os
import hashlib

# Permitted MIME types and maximum allowable file upload size (25 MB)
MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff", ".tif"}

# Magic byte signatures for image formats
MAGIC_BYTES = {
    b"\xFF\xD8\xFF": "JPEG",
    b"\x89PNG\r\n\x1a\n": "PNG",
    b"BM": "BMP",
    b"RIFF": "WEBP",
    b"II*\x00": "TIFF_LE",
    b"MM\x00*": "TIFF_BE"
}


def compute_file_hash(file_path):
    """
    Computes SHA-256 cryptographic digest of the input file.
    """
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def validate_input_file(file_path):
    """
    Validates file existence, size, extension, and magic header bytes
    to prevent malicious upload attacks or corrupt payloads.
    
    Returns:
        tuple: (is_valid: bool, error_code: str, error_message: str, file_hash: str)
    """
    if not os.path.exists(file_path):
        return False, "ERR_FILE_NOT_FOUND", f"File does not exist: {file_path}", None

    file_size = os.path.getsize(file_path)
    if file_size == 0:
        return False, "ERR_EMPTY_FILE", "Uploaded file is 0 bytes (empty)", None

    if file_size > MAX_FILE_SIZE_BYTES:
        return False, "ERR_FILE_TOO_LARGE", f"File exceeds maximum allowed size of 25MB ({file_size} bytes)", None

    # Check extension
    _, ext = os.path.splitext(file_path.lower())
    if ext not in ALLOWED_EXTENSIONS:
        return False, "ERR_INVALID_EXTENSION", f"Unsupported file extension: {ext}", None

    # Verify Magic Bytes
    try:
        with open(file_path, "rb") as f:
            header = f.read(16)
    except Exception as e:
        return False, "ERR_FILE_READ", f"Could not read file header: {e}", None

    magic_match = False
    for magic, fmt in MAGIC_BYTES.items():
        if header.startswith(magic):
            magic_match = True
            break
        # WEBP check (RIFF....WEBP)
        if header.startswith(b"RIFF") and b"WEBP" in header[:16]:
            magic_match = True
            break

    if not magic_match:
        return False, "ERR_MALICIOUS_PAYLOAD", "File header does not match any allowed image format signature", None

    file_hash = compute_file_hash(file_path)
    return True, None, None, file_hash
