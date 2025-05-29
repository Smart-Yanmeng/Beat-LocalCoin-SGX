import base64

from gevent import socket, monkey
import gevent

from cryptor import Cryptor

monkey.patch_all()

import pickle

HOST = '127.0.0.1'
PORT = 65431

cryptor = Cryptor()
aes_key = cryptor.load_aes_key_from_file(
    "/mnt/c/Users/yorky/Desktop/Project/Beat-LocalCoin-SGX/adaptive/sgx/aes.key"
)


def handle_client(conn):
    result = 0
    try:
        # 接收全部数据，直到连接关闭
        data = bytearray()
        while True:
            chunk = conn.recv(4096)
            if not chunk:
                break
            data.extend(chunk)

        if not data:
            print("[SGX] 未收到任何数据")
            return

        # 反序列化对象
        obj = pickle.loads(data)
        print("[SGX SERVER] 收到对象")

        # 模拟 SGX 处理逻辑
        N = obj.get("n", 0)
        voteObj2 = obj.get("voteObj2", dict())
        count_0 = 0
        count_1 = 0

        for key in voteObj2:
            # print("voteObj2[key] ---->", voteObj2[key])
            vote = int.from_bytes(cryptor.decrypt_rsa(base64.b16decode(voteObj2[key])), byteorder="big")
            if vote == 0:
                count_0 += 1
            else:
                count_1 += 1

        if count_0 > N / 2:
            est = 0
        elif count_1 > N / 2:
            est = 1
        else:
            est = 2

        result = base64.b16encode(cryptor.encrypt_rsa(est.to_bytes(1, "big"))).decode("utf-8")

        # 序列化并发送结果
        response_bytes = pickle.dumps(result)
        conn.sendall(response_bytes)
        print("[SGX] 已发送响应：", result)

    finally:
        conn.close()


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
