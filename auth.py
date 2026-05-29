import hashlib
import hmac
import os
import re

# HMAC key used to sign every transaction record stored in the database.
# This lets us detect if someone tampers with a row directly in SQLite.
SIGNING_KEY = b"berliner_bank_mac_secret_2025"


def check_password_strength(password):
    """
    Returns True if the password meets the minimum security policy:
    at least 8 characters, one uppercase, one lowercase, one digit.
    """
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    return True


def hash_password(password, salt=None):
    """
    Hashes a password using PBKDF2-HMAC-SHA256 with a random salt.
    If salt is not given (new registration), a fresh random one is generated.
    Returns (hash_hex, salt_hex).
    """
    if salt is None:
        salt = os.urandom(16).hex()

    key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000)
    return key.hex(), salt


def get_mfa_code(seed):
    """
    Derives a static 6-digit MFA code from the user's personal seed string.
    The same seed always produces the same code - shown once at registration.
    """
    digest = hashlib.sha256(seed.encode()).hexdigest()
    code = str(int(digest, 16))[-6:]
    return code


def verify_mfa(seed, submitted_code):
    return get_mfa_code(seed) == submitted_code


def sign_transaction(sender, recipient, amount, timestamp):
    """
    Creates an HMAC-SHA256 signature over the core transaction fields.
    This signature is stored alongside the record so we can later verify
    no one has changed the amount, parties, or timestamp in the database.
    """
    message = f"{sender}|{recipient}|{amount:.2f}|{timestamp}".encode()
    sig = hmac.new(SIGNING_KEY, message, hashlib.sha256)
    return sig.hexdigest()


def verify_transaction(sender, recipient, amount, timestamp, stored_sig):
    """
    Re-computes the expected signature and compares it with the stored one
    using hmac.compare_digest to prevent timing attacks.
    """
    expected = sign_transaction(sender, recipient, amount, timestamp)
    return hmac.compare_digest(expected, stored_sig)