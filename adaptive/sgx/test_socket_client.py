import socket
import pickle
import secrets
import time

HOST = '127.0.0.1'
PORT = 6666

def main():
    # 要发送的随机字节长度（例如 1MB）
    data_length = 250

    # 生成指定长度的随机字节
    msg = secrets.token_bytes(data_length)

    # 构造要发送的对象
    payload = {
        "length": data_length,
        "msg": msg,
    }

    # 序列化对象
    data = pickle.dumps(payload)

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((HOST, PORT))

    try:
        start_time = time.time()

        # 发送数据
        client_socket.sendall(data)
        client_socket.shutdown(socket.SHUT_WR)  # 通知服务端数据已发完

        response_data = bytearray()
        while True:
            chunk = client_socket.recv(4096)
            if not chunk:
                break
            response_data.extend(chunk)

        end_time = time.time()

        # 反序列化响应数据
        obj = pickle.loads(response_data)
        print(f"收到响应对象，长度: {obj.get('length')}")
        print(f"总耗时: {end_time - start_time:.6f} 秒")

    finally:
        client_socket.close()

if __name__ == "__main__":
    main()