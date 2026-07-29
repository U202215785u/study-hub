import base64
import sqlite3

import database
from services.secure_settings import (
    delete_secret,
    load_secret,
    save_secret,
    secret_status,
)


class ReversibleProtector:
    def protect(self, value: bytes) -> bytes:
        return b"protected:" + value[::-1]

    def unprotect(self, value: bytes) -> bytes:
        assert value.startswith(b"protected:")
        return value[len(b"protected:"):][::-1]


def test_secret_is_encrypted_and_status_never_returns_plaintext():
    protector = ReversibleProtector()
    conn = database.get_db()
    try:
        save_secret(conn, "douyin_cookie", "sessionid=top-secret", protector)
        row = conn.execute(
            "SELECT encrypted_value FROM secure_settings WHERE name = ?",
            ("douyin_cookie",),
        ).fetchone()

        assert "top-secret" not in row[0]
        assert base64.b64decode(row[0]).startswith(b"protected:")
        assert load_secret(conn, "douyin_cookie", protector) == "sessionid=top-secret"
        status = secret_status(conn, "douyin_cookie")
        assert status["configured"] is True
        assert status["updated_at"]
        assert "value" not in status
    finally:
        conn.close()


def test_secret_can_be_replaced_and_deleted():
    protector = ReversibleProtector()
    conn = database.get_db()
    try:
        save_secret(conn, "douyin_cookie", "first", protector)
        save_secret(conn, "douyin_cookie", "second", protector)
        assert load_secret(conn, "douyin_cookie", protector) == "second"

        assert delete_secret(conn, "douyin_cookie") is True
        assert load_secret(conn, "douyin_cookie", protector) is None
        assert secret_status(conn, "douyin_cookie") == {
            "configured": False,
            "updated_at": None,
        }
        assert delete_secret(conn, "douyin_cookie") is False
    finally:
        conn.close()


def test_secret_rejects_blank_and_oversized_values():
    protector = ReversibleProtector()
    conn = database.get_db()
    try:
        for value in ("", "   ", "x" * 20_001):
            try:
                save_secret(conn, "douyin_cookie", value, protector)
            except ValueError:
                pass
            else:
                raise AssertionError("invalid secret was accepted")
    finally:
        conn.close()


def test_real_windows_protector_round_trip():
    from services.secure_settings import WindowsDpapiProtector

    protector = WindowsDpapiProtector()
    encrypted = protector.protect(b"cookie-value")

    assert encrypted != b"cookie-value"
    assert protector.unprotect(encrypted) == b"cookie-value"

