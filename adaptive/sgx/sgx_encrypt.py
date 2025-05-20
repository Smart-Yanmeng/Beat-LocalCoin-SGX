import base64

from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend

from gevent import socket, monkey
import gevent

monkey.patch_all()

import pickle

HOST = '127.0.0.1'
PORT = 65436


# BS = 16
# pad = lambda s: s + (BS - len(s) % BS) * chr(BS - len(s) % BS)

# group = ECGroup(prime256v1)
# g = group.random(G)
# g1 = group.random(G)


# def xor(x, y):
#     # assert len(x) == len(y) == 32
#     return ''.join(chr(ord(x_) ^ ord(y_)) for x_, y_ in zip(x, y))
#
#
# def serialize(g):
#     return decodestring(group.serialize(g)[2:])
#
#
# def hashH(x, L, u, w, u1, w1):  # H_2
#     # assert len(x) == 32
#     return group.hash(
#         x + L + serialize(u).decode("ISO-8859-1") + serialize(w).decode("ISO-8859-1") + serialize(u1).decode(
#             "ISO-8859-1") + serialize(w1).decode("ISO-8859-1"))
#
#
# def hashG(g):  # H_1
#     return SHA256.new(serialize(g)).digest()
#
#
# def encrypt(self, m, L):
#     r = group.random()
#     s = group.random()
#     c = xor(m.decode("ISO-8859-1"), hashG(self.VK ** r).decode("ISO-8859-1"))  # bytes to string
#     u = g ** r
#     w = g ** s
#     u1 = g1 ** r
#     w1 = g1 ** s
#     e = hashH(c, L, u, w, u1, w1)
#     f = s + r * e
#     C = (c, L, u, u1, e, f)
#     print("---> C >>>>>>>", C)
#     return C


def handle_client(conn):
    try:
        # 接收全部数据，直到连接关闭
        data = bytearray()
        while True:
            chunk = conn.recv(4096)
            if not chunk:
                break
            data.extend(chunk)

        if not data:
            print("未收到任何数据")
            return

        # 反序列化对象
        obj = pickle.loads(data)
        print("收到对象：", obj)

        # 模拟 SGX 处理逻辑
        selected_B = base64.b16encode(obj.get("selected_B", "")).decode("utf-8")

        public_key = load_public_key_from_pem("./pub.pem")
        encrypted_B = encrypt_with_rsa(public_key, selected_B)

        # 序列化并发送结果
        response_bytes = pickle.dumps(encrypted_B)
        conn.sendall(response_bytes)
        print("已发送响应：", encrypted_B)

    finally:
        conn.close()


def load_public_key_from_pem(pem_path: str):
    with open(pem_path, "rb") as key_file:
        public_key = serialization.load_pem_public_key(
            key_file.read(),
            backend=default_backend()
        )
    return public_key


def encrypt_with_rsa(public_key, plaintext: str) -> bytes:
    ciphertext = public_key.encrypt(
        plaintext.encode("utf-8"),
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return ciphertext


# def encrypt(key, raw):
# assert len(key) == 32
# raw = pad(raw.decode("ISO-8859-1"))  # bytes to string
#
# iv = Random.new().read(AES.block_size)
# cipher = AES.new(key, AES.MODE_CBC, iv)
# return (iv + cipher.encrypt(raw.encode("ISO-8859-1")))  # string to bytes


def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen()

    print(f"[SGX Server] Listening on {HOST}:{PORT}...")

    while True:
        client_conn, addr = server_socket.accept()
        print(f"连接来自 {addr}")
        # 使用 gevent 协程并发处理每个客户端连接
        gevent.spawn(handle_client, client_conn)


if __name__ == "__main__":
    start_server()
