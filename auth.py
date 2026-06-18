import hashlib
import hmac
import os
import re


SIGNING_KEY = b"berliner_bank_mac_secret_2025"


def check_password_strength(password):
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
    if salt is None:
        salt = os.urandom(16).hex()

    key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000)
    return key.hex(), salt


def get_mfa_code(seed):
    digest = hashlib.sha256(seed.encode()).hexdigest()
    code = str(int(digest, 16))[-6:]
    return code


def verify_mfa(seed, submitted_code):
    return get_mfa_code(seed) == submitted_code


def sign_transaction(sender, recipient, amount, timestamp):
    message = f"{sender}|{recipient}|{amount:.2f}|{timestamp}".encode()
    sig = hmac.new(SIGNING_KEY, message, hashlib.sha256)
    return sig.hexdigest()


def verify_transaction(sender, recipient, amount, timestamp, stored_sig):
    expected = sign_transaction(sender, recipient, amount, timestamp)
    return hmac.compare_digest(expected, stored_sig)
