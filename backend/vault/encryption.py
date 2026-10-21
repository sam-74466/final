from cryptography.fernet import Fernet
from django.conf import settings


def _fernet():
    return Fernet(settings.VAULT_ENCRYPTION_KEY.encode())


def encrypt_text(value):
    return _fernet().encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_text(value):
    return _fernet().decrypt(value.encode("utf-8")).decode("utf-8")
