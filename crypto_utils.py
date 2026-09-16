"""
رمزگذاری AES-256-GCM + PBKDF2-SHA256
رفع باگ: ALPHABET[len(combined)] وقتی len >= 42 بود IndexError می‌داد
راه‌حل: طول با ۲ کاراکتر فارسی کدگذاری می‌شه (ظرفیت ۱۷۶۳)
"""

import os
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

ALPHABET = "۰۱۲۳۴۵۶۷۸۹ابپتثجچحخدذرزژسشصضطظعغفقکگلمنوهی"
BASE = len(ALPHABET)  # 42

FIXED_SALT = bytes([
    0x4f, 0x3a, 0x9c, 0x1e, 0x77, 0xb2, 0x5d, 0x08,
    0xe1, 0x6a, 0xc4, 0x93, 0x2f, 0x81, 0x0d, 0x5b
])


def _derive_key(password: str) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=FIXED_SALT,
        iterations=100000,
    )
    return kdf.derive(password.encode("utf-8"))


def _encode_fa(data: bytes) -> str:
    num = int.from_bytes(data, "big")
    if num == 0:
        return ALPHABET[0]
    out = ""
    while num > 0:
        rem = num % BASE
        out = ALPHABET[rem] + out
        num //= BASE
    return out


def _encode_len(length: int) -> str:
    """طول را با ۲ کاراکتر فارسی کد می‌کند (حداکثر ۴۲²-۱ = ۱۷۶۳)"""
    high = (length // BASE) % BASE
    low  = length % BASE
    return ALPHABET[high] + ALPHABET[low]


def encrypt(plain_text: str, password: str) -> str:
    """
    رمزگذاری و خروجی فارسی.
    فرمت: [۲ نماد طول][داده رمزشده]
    """
    iv = os.urandom(12)
    key = _derive_key(password)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(iv, plain_text.encode("utf-8"), None)
    combined = iv + ciphertext
    return _encode_len(len(combined)) + _encode_fa(combined)
