import unittest
import os
from crypto_utils import CryptoUtils

class TestCryptoUtils(unittest.TestCase):
    def setUp(self):
        self.key = "dummy_key_value_for_test"
        self.salt = os.urandom(16)
        self.crypto = CryptoUtils(self.key, self.salt)
        
    def test_enc_dec(self):
        """Test that data can be encrypted and decrypted back to original."""
        data = "dummy_data_content_verified"
        enc = self.crypto.encrypt(data)
        
        self.assertNotEqual(data, enc)
        
        dec = self.crypto.decrypt(enc)
        self.assertEqual(data, dec)

if __name__ == '__main__':
    unittest.main()
