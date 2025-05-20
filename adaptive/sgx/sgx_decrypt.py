import pickle
import gevent

from gevent import socket, monkey
from cryptor import Cryptor

monkey.patch_all()

HOST = '127.0.0.1'
PORT = 65437
TR_SIZE = 250

cryptor = Cryptor()


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
            print("[SGX Server] 未收到任何数据")
            return

        # 反序列化对象
        obj = pickle.loads(data)
        print("[SGX Server] 收到对象：", obj)

        # 模拟 SGX 处理逻辑
        proposal = obj.get("proposal", "")

        aesKeyFromEncrypted = cryptor.decrypt_rsa(proposal[:256])
        encodedTxSet = cryptor.decrypt_aes(proposal[256:].rstrip(b'\x01'), aesKeyFromEncrypted)

        assert len(encodedTxSet) % TR_SIZE == 0

        recoveredSyncedTx = [encodedTxSet[i:i + TR_SIZE] for i in range(0, len(encodedTxSet), TR_SIZE)]

        # 序列化并发送结果
        response_bytes = pickle.dumps(recoveredSyncedTx)
        conn.sendall(response_bytes)
        print("[SGX Server] 已发送响应：", recoveredSyncedTx)

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
