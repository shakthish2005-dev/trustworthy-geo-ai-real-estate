from __future__ import annotations

import hashlib
import hmac
import secrets

PBKDF2_ITERATIONS = 600_000


def hash_password(password: str, pepper: str = "") -> str:
    """Create a versioned PBKDF2-SHA256 password record."""
    if len(password) < 12:
        raise ValueError("Password must contain at least 12 characters.")
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", (password + pepper).encode("utf-8"), salt, PBKDF2_ITERATIONS
    )
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str, pepper: str = "") -> bool:
    try:
        algorithm, iterations, salt_hex, digest_hex = stored.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            (password + pepper).encode("utf-8"),
            bytes.fromhex(salt_hex),
            int(iterations),
        )
        return hmac.compare_digest(digest.hex(), digest_hex)
    except (TypeError, ValueError):
        return False


def validate_password_strength(password: str) -> tuple[bool, str]:
    checks = [
        (len(password) >= 12, "Use at least 12 characters."),
        (any(c.isupper() for c in password), "Add an uppercase letter."),
        (any(c.islower() for c in password), "Add a lowercase letter."),
        (any(c.isdigit() for c in password), "Add a number."),
    ]
    for passed, message in checks:
        if not passed:
            return False, message
    return True, ""
