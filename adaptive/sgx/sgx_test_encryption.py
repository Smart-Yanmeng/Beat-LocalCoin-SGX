import secrets
import time

from adaptive.sgx.cryptor import Cryptor


def main():
    cryptor = Cryptor()

    data = secrets.token_bytes(100)

    key = cryptor.load_aes_key_from_file("scripts/aes.key")
    e_data = cryptor.encrypt_aes(data, key)
    e_key = cryptor.encrypt_rsa(key)

    start_time = time.time()
    dec_key = cryptor.decrypt_rsa(e_key)

    dec_key_time = time.time()

    dec_data = cryptor.decrypt_aes(e_data, dec_key)

    dec_data_time = time.time()

    print("Decrypt Key Time:", dec_key_time - start_time)
    print("Decrypt Data Time:", dec_data_time - dec_key_time)

    print("key ---> ", key)
    print("data ---> ", data)
    print("dec key ---> ", dec_key)
    print("dec data ---> ", dec_data)


if __name__ == '__main__':
    main()
