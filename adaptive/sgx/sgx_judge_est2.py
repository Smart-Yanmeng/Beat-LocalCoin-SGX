import base64
import random

from gevent import socket, monkey
import gevent

from cryptor import Cryptor

monkey.patch_all()

import pickle

HOST = '127.0.0.1'
PORT = 65432

cryptor = Cryptor()
aes_key = cryptor.load_aes_key_from_file(
    "/mnt/c/Users/yorky/Desktop/Project/Beat-LocalCoin-SGX/adaptive/sgx/aes.key"
)


def handle_client(conn):
    counter0 = 0
    counter1 = 0

    result = {
        "v": 0,
        "result": 0,
        "coin": 0
    }

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
        print("[SGX] 收到对象：", obj)

        # 模拟 SGX 处理逻辑
        voteObj3 = obj.get("voteObj3", dict())
        t = obj.get("t", 0)

        for key in voteObj3:
            vote = int.from_bytes(cryptor.decrypt_rsa(base64.b16decode(voteObj3[key])), byteorder="big")

            if vote == 0:
                result['v'] = vote
                counter0 += 1
            else:
                result['v'] = vote
                counter1 += 1

        if counter1 >= 2 * t + 1:
            result['result'] = 1
        elif counter0 >= 2 * t + 1:
            result['result'] = 2
        elif counter0 >= t + 1:
            result['result'] = 3
        elif counter1 >= t + 1:
            result['result'] = 4
        else:
            result['coin'] = random.choice([0, 1])  # 从 SGX 取得随机值

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
        print(f"[SGX] 连接来自 {addr}")
        # 使用 gevent 协程并发处理每个客户端连接
        gevent.spawn(handle_client, client_conn)


if __name__ == "__main__":
    start_server()
