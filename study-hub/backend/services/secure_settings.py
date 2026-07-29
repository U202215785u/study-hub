import base64
import ctypes
import os
from ctypes import wintypes
from typing import Protocol


MAX_SECRET_LENGTH = 20_000


class SecretProtector(Protocol):
    def protect(self, value: bytes) -> bytes: ...
    def unprotect(self, value: bytes) -> bytes: ...


class _DataBlob(ctypes.Structure):
    _fields_ = [
        ("cbData", wintypes.DWORD),
        ("pbData", ctypes.POINTER(ctypes.c_byte)),
    ]


def _blob(value: bytes):
    buffer = ctypes.create_string_buffer(value)
    return _DataBlob(
        len(value), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_byte))
    ), buffer


class WindowsDpapiProtector:
    """Encrypt values for the currently logged-in Windows user."""

    _UI_FORBIDDEN = 0x1

    def __init__(self):
        if os.name != "nt":
            raise RuntimeError("DPAPI is only available on Windows")
        self._crypt32 = ctypes.windll.crypt32
        self._kernel32 = ctypes.windll.kernel32

    def protect(self, value: bytes) -> bytes:
        source, source_buffer = _blob(value)
        target = _DataBlob()
        if not self._crypt32.CryptProtectData(
            ctypes.byref(source),
            "Study Hub Douyin Cookie",
            None,
            None,
            None,
            self._UI_FORBIDDEN,
            ctypes.byref(target),
        ):
            raise ctypes.WinError()
        try:
            return ctypes.string_at(target.pbData, target.cbData)
        finally:
            self._kernel32.LocalFree(target.pbData)

    def unprotect(self, value: bytes) -> bytes:
        source, source_buffer = _blob(value)
        target = _DataBlob()
        if not self._crypt32.CryptUnprotectData(
            ctypes.byref(source),
            None,
            None,
            None,
            None,
            self._UI_FORBIDDEN,
            ctypes.byref(target),
        ):
            raise ctypes.WinError()
        try:
            return ctypes.string_at(target.pbData, target.cbData)
        finally:
            self._kernel32.LocalFree(target.pbData)


def _protector(protector: SecretProtector | None) -> SecretProtector:
    return protector or WindowsDpapiProtector()


def save_secret(conn, name: str, value: str, protector: SecretProtector | None = None):
    clean_value = value.strip()
    if not clean_value or len(clean_value) > MAX_SECRET_LENGTH:
        raise ValueError("secret must contain 1 to 20000 characters")
    encrypted = _protector(protector).protect(clean_value.encode("utf-8"))
    encoded = base64.b64encode(encrypted).decode("ascii")
    conn.execute(
        """
        INSERT INTO secure_settings (name, encrypted_value)
        VALUES (?, ?)
        ON CONFLICT(name) DO UPDATE SET
            encrypted_value = excluded.encrypted_value,
            updated_at = CURRENT_TIMESTAMP
        """,
        (name, encoded),
    )
    conn.commit()


def load_secret(conn, name: str, protector: SecretProtector | None = None):
    row = conn.execute(
        "SELECT encrypted_value FROM secure_settings WHERE name = ?", (name,)
    ).fetchone()
    if not row:
        return None
    encrypted = base64.b64decode(row[0], validate=True)
    return _protector(protector).unprotect(encrypted).decode("utf-8")


def secret_status(conn, name: str):
    row = conn.execute(
        "SELECT updated_at FROM secure_settings WHERE name = ?", (name,)
    ).fetchone()
    return {
        "configured": bool(row),
        "updated_at": row[0] if row else None,
    }


def delete_secret(conn, name: str):
    cursor = conn.execute("DELETE FROM secure_settings WHERE name = ?", (name,))
    conn.commit()
    return cursor.rowcount > 0
