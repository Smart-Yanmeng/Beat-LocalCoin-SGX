"""Pure Python ECDSA wrapper using the 'ecdsa' package, compatible with OpenSSL 3.x."""
import hashlib
import sys
import importlib

# Temporarily remove adaptive paths to import the pip ecdsa package
_original_path = sys.path[:]
sys.path = [p for p in sys.path if '/adaptive' not in p]
try:
    # Force reimport of ecdsa from the pip package
    if 'ecdsa' in sys.modules:
        del sys.modules['ecdsa']
    import ecdsa as _ecdsa
finally:
    sys.path = _original_path


class KEY:
    SECP256K1 = _ecdsa.SECP256k1

    def __init__(self):
        self._sk = None
        self._vk = None
        self._compressed = False
        self.prikey = None

    def __del__(self):
        pass

    def generate(self, secret=None):
        if secret:
            if isinstance(secret, str):
                secret = bytes.fromhex(secret)
            self.prikey = secret
            self._sk = _ecdsa.SigningKey.from_string(secret, curve=_ecdsa.SECP256k1)
            self._vk = self._sk.get_verifying_key()
            return self
        else:
            self._sk = _ecdsa.SigningKey.generate(curve=_ecdsa.SECP256k1)
            self._vk = self._sk.get_verifying_key()
            self.prikey = self._sk.to_string()
            return self

    def set_compressed(self, compressed):
        self._compressed = bool(compressed)

    def get_pubkey(self):
        if self._compressed:
            return self._vk.to_string("compressed")
        else:
            return self._vk.to_string("uncompressed")

    def get_privkey(self):
        return self._sk.to_string()

    def get_secret(self):
        return self._sk.to_string()

    def sign(self, hash_data):
        return self._sk.sign_digest(hash_data, sigencode=_ecdsa.util.sigencode_der)

    def verify(self, hash_data, sig):
        try:
            return self._vk.verify_digest(sig, hash_data, sigdecode=_ecdsa.util.sigdecode_der)
        except _ecdsa.BadSignatureError:
            return False
