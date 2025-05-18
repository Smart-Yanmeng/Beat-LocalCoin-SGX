import random

from gevent import socket, monkey
import gevent

monkey.patch_all()

import pickle

HOST = '127.0.0.1'
PORT = 65431


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
        print("[SGX] 收到对象：", obj)

        # 模拟 SGX 处理逻辑
        N = obj.get("n", 0)
        voteObj2 = obj.get("voteObj2", dict())
        count_0 = 0
        count_1 = 0

        for key in voteObj2:
            print("voteObj2[key] ---->", voteObj2[key])
            if voteObj2[key] == 0:
                count_0 += 1
            else:
                count_1 += 1

        if count_0 > N / 2:
            result = 0
        elif count_1 > N / 2:
            result = 1
        else:
            result = 2

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
