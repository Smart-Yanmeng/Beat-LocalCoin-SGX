import sys
import os

_SYS_ECDSA_PARENT = '/usr/local/lib/python3.10/dist-packages'
if _SYS_ECDSA_PARENT not in sys.path:
    sys.path.insert(0, _SYS_ECDSA_PARENT)

_local_ecdsa = sys.modules.pop('adaptive.ecdsa', None)
_local_ecdsa_init = sys.modules.pop('adaptive.ecdsa.__init__', None)
if 'ecdsa' in sys.modules:
    del sys.modules['ecdsa']
for k in list(sys.modules.keys()):
    if k.startswith('ecdsa.'):
        del sys.modules[k]

import importlib
_ecdsa = importlib.import_module('ecdsa')
SigningKey = _ecdsa.SigningKey
SECP256k1 = _ecdsa.SECP256k1
BadSignatureError = _ecdsa.BadSignatureError

if _local_ecdsa is not None:
    sys.modules['adaptive.ecdsa'] = _local_ecdsa
if _local_ecdsa_init is not None:
    sys.modules['adaptive.ecdsa.__init__'] = _local_ecdsa_init
sys.path.remove(_SYS_ECDSA_PARENT)


class KEY:
    def __init__(self):
        self.POINT_CONVERSION_COMPRESSED = 2
        self.POINT_CONVERSION_UNCOMPRESSED = 4
        self._compressed = False
        self._sk = None
        self._vk = None
        self.prikey = None

    def __del__(self):
        pass

    def generate(self, secret=None):
        if secret:
            self.prikey = secret
            self._sk = SigningKey.from_string(secret, curve=SECP256k1)
            self._vk = self._sk.get_verifying_key()
            return self
        else:
            self._sk = SigningKey.generate(curve=SECP256k1)
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
        except BadSignatureError:
            return False
