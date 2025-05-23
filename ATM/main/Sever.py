import socket
import threading
import json
import logging
from datetime import datetime

# 配置日志记录
logging.basicConfig(
    filename='server.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)

class ATMServer:
    def __init__(self, port=2525):
        self.port = port
        self.users = self.load_users()  # 加载用户数据
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(('0.0.0.0', self.port))  
        self.server_socket.listen(5)
        logging.info(f"服务器启动，监听端口 {self.port}")

    def load_users(self):
        try:
            with open('users.json', 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
                # 转换所有键为字符串类型
                return {str(k): v for k, v in raw_data.items()}
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save_users(self):
        with open('users.json', 'w', encoding='utf-8') as f:
            json.dump(self.users, f, indent=4, ensure_ascii=False)

    def handle_client(self, client_socket, addr):
        logging.info(f"新连接: {addr}")
        user_id = None
        try:
            while True:
                data = client_socket.recv(1024).decode().strip()
                if not data:
                    break

                # 处理HELO消息
                if data.startswith("HELO"):
                    parts = data.split()
                    if len(parts) != 2 or not parts[1].isdigit():
                        client_socket.sendall("401 ERROR!\n".encode())
                        continue
                    user_id = parts[1]
                    if user_id in self.users:
                        client_socket.sendall("500 AUTH REQUIRED!\n".encode())  # 添加感叹号
                    else:
                        client_socket.sendall("401 ERROR!\n".encode())

                # 处理PASS消息
                elif data.startswith("PASS"):
                    if user_id is None:
                        client_socket.sendall("401 ERROR!\n".encode())
                        continue
                    parts = data.split()
                    if len(parts) != 2 or not parts[1].isdigit() or len(parts[1]) != 6:
                        client_socket.sendall("401 ERROR!\n".encode())
                        continue
                    password = parts[1]
                    if self.users.get(user_id, {}).get('password') == password:
                        client_socket.sendall("525 OK!\n".encode())
                    else:
                        client_socket.sendall("401 ERROR!\n".encode())

                # 处理BALA消息
                elif data == "BALA":
                    if user_id not in self.users:
                        client_socket.sendall("401 ERROR!\n".encode())
                        continue
                    balance = self.users[user_id]['balance']
                    client_socket.sendall(f"AMNT:{balance}\n".encode())
                    logging.info(f"{user_id} 查询余额: {balance}")

                # 处理WDRA消息
                elif data.startswith("WDRA"):
                    if user_id not in self.users:
                        client_socket.sendall("401 ERROR!\n".encode())
                        continue
                    try:
                        amount = int(data.split()[1])
                        if self.users[user_id]['balance'] >= amount:
                            self.users[user_id]['balance'] -= amount
                            self.save_users()
                            client_socket.sendall("525 OK\n".encode())
                            logging.info(f"{user_id} 取款: {amount}, 余额: {self.users[user_id]['balance']}")
                        else:
                            client_socket.sendall("401 ERROR!\n".encode())
                    except (IndexError, ValueError):
                        client_socket.sendall("401 ERROR!\n".encode())

                # 处理BYE消息
                elif data == "BYE":
                    client_socket.sendall("BYE\n".encode())
                    logging.info(f"{user_id} 退出系统")
                    break

        except Exception as e:
            logging.error(f"客户端处理错误: {str(e)}")
        finally:
            client_socket.close()
            logging.info(f"连接关闭: {addr}")

    def run(self):
        while True:
            client_socket, addr = self.server_socket.accept()
            threading.Thread(target=self.handle_client, args=(client_socket, addr)).start()

if __name__ == "__main__":
    server = ATMServer()
    server.run()