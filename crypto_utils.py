import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class CryptoUtils:
    def __init__(self, password: str, salt: bytes = None):
        """
        Initialize with a password. 
        In production, salt should be stored/retrieved securely or generated once per user.
        """
        if salt is None:
            self.salt = os.urandom(16)
        else:
            self.salt = salt
            
        self.key = self._derive_key(password, self.salt)
        self.fernet = Fernet(self.key)

    def _derive_key(self, password: str, salt: bytes) -> bytes:
        """Derive a 32-byte key from the password using PBKDF2."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))

    def encrypt(self, plaintext: str) -> str:
        """Encrypts a string and returns a base64 encoded string."""
        return self.fernet.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str) -> str:
        """Decrypts a base64 encoded string."""
        return self.fernet.decrypt(ciphertext.encode()).decode()
