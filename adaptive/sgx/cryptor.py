from cryptography.hazmat.primitives import serialization, hashes, padding
from cryptography.hazmat.primitives.asymmetric import rsa, padding as rsa_padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

import os
import base64


class Cryptor:
    def __init__(self):
        self.public_key = self._load_public_key("/mnt/c/Users/yorky/Desktop/Project/Beat-LocalCoin-SGX/adaptive/sgx/pub.pem")
        self.private_key = self._load_private_key("/mnt/c/Users/yorky/Desktop/Project/Beat-LocalCoin-SGX/adaptive/sgx/sec.pem")

    def _load_public_key(self, path: str):
        with open(path, "rb") as key_file:
            return serialization.load_pem_public_key(
                key_file.read(),
                backend=default_backend()
            )

    def _load_private_key(self, path: str):
        with open(path, "rb") as key_file:
            return serialization.load_pem_private_key(
                key_file.read(),
                password=None,
                backend=default_backend()
            )

    def load_aes_key_from_file(self, path: str) -> bytes:
        with open(path, "rb") as f:
            return base64.b64decode(f.read())

    # RSA加密
    def encrypt_rsa(self, plaintext: bytes) -> bytes:
        if not self.public_key:
            raise ValueError("Public key not loaded.")
        return self.public_key.encrypt(
            plaintext,
            rsa_padding.OAEP(
                mgf=rsa_padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

    # RSA 解密
    def decrypt_rsa(self, ciphertext: bytes) -> bytes:
        if not self.private_key:
            raise ValueError("Private key not loaded.")
        return self.private_key.decrypt(
            ciphertext,
            rsa_padding.OAEP(
                mgf=rsa_padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

    # AES加密（对称）
    def encrypt_aes(self, plaintext: bytes, key: bytes, iv: bytes = None) -> bytes:
        if iv is None:
            iv = os.urandom(16)

        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(plaintext) + padder.finalize()

        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()

        return iv + ciphertext  # 将 IV 拼接在前面，方便解密

    # AES解密
    def decrypt_aes(self, ciphertext: bytes, key: bytes) -> bytes:
        iv = ciphertext[:16]
        real_ciphertext = ciphertext[16:]

        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        padded_data = decryptor.update(real_ciphertext) + decryptor.finalize()

        unpadder = padding.PKCS7(128).unpadder()
        return unpadder.update(padded_data) + unpadder.finalize()

    def encrypt_aes_b64(self, plaintext: str, key: bytes) -> str:
        raw = self.encrypt_aes(plaintext.encode('utf-8'), key)
        return base64.b64encode(raw).decode('utf-8')

    def decrypt_aes_b64(self, ciphertext_b64: str, key: bytes) -> str:
        raw = base64.b64decode(ciphertext_b64)
        return self.decrypt_aes(raw, key).decode('utf-8')