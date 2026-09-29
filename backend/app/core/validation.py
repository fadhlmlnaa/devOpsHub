import os
import re
from fastapi import HTTPException, status

FORBIDDEN_CHAR_PATTERN = re.compile(r"[\x00\r\n;&|`$><]")
SAFE_IDENTIFIER_PATTERN = re.compile(r"^[a-zA-Z0-9_\.\-]+$")
FORBIDDEN_SYSTEM_PATHS = ["/etc/passwd", "/etc/shadow", "/etc/sudoers", "/root/.ssh", "/etc/ssl/private"]


def validate_safe_identifier(val: str, field_name: str = "identifier") -> str:
    """Validates that an identifier (like service name, container name) does not contain injection characters."""
    if not val or not isinstance(val, str):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"{field_name} tidak boleh kosong.",
        )

    if "\x00" in val:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"{field_name} mengandung null byte yang tidak valid.",
        )

    if not SAFE_IDENTIFIER_PATTERN.match(val):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"{field_name} mengandung karakter yang tidak diizinkan atau berbahaya.",
        )

    return val


def validate_safe_path(path_str: str, field_name: str = "path", base_dir: str = None) -> str:
    """Validates a file/directory path against path traversal and dangerous system files."""
    if not path_str or not isinstance(path_str, str):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"{field_name} tidak boleh kosong.",
        )

    if "\x00" in path_str:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"{field_name} mengandung null byte.",
        )

    # Check for path traversal attempts
    normalized = os.path.normpath(path_str)
    if "../" in path_str or "..\\" in path_str or path_str.startswith("../") or path_str == "..":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"{field_name} mengandung path traversal yang tidak sah.",
        )

    # Check forbidden system files
    for forbidden in FORBIDDEN_SYSTEM_PATHS:
        if normalized == forbidden or normalized.startswith(forbidden + "/"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Akses ke lokasi sistem sensitif ({forbidden}) dilarang.",
            )

    if base_dir:
        norm_base = os.path.normpath(base_dir)
        if not normalized.startswith(norm_base):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"{field_name} harus berada di dalam direktori {base_dir}.",
            )

    return normalized
