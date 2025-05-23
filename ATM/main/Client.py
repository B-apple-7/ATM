import tkinter as tk
from tkinter import messagebox
import socket
from threading import Thread

class ATMClient:
    def __init__(self, master):
        self.master = master
        self.master.title("ATM客户端")
        self.connection = None  
        
        self.user_id = tk.StringVar()
        self.password = tk.StringVar()
        self.balance = tk.StringVar()
        self.amount = tk.StringVar()
        self.server_ip = tk.StringVar(value="127.0.0.1")
        
        self.setup_ui()

    def setup_ui(self):
        # 登录界面
        self.login_frame = tk.Frame(self.master)
        tk.Label(self.login_frame, text="服务器IP:").grid(row=0, column=0, padx=5, pady=5)
        tk.Entry(self.login_frame, textvariable=self.server_ip).grid(row=0, column=1, padx=5, pady=5)
        tk.Label(self.login_frame, text="卡号:").grid(row=1, column=0, padx=5, pady=5)
        tk.Entry(self.login_frame, textvariable=self.user_id).grid(row=1, column=1, padx=5, pady=5)
        tk.Label(self.login_frame, text="密码:").grid(row=2, column=0, padx=5, pady=5)
        tk.Entry(self.login_frame, textvariable=self.password, show="*").grid(row=2, column=1, padx=5, pady=5)
        tk.Button(self.login_frame, text="登录", command=self._login).grid(row=3, columnspan=2, pady=10)
        self.login_frame.pack()

        # 操作界面
        self.operation_frame = tk.Frame(self.master)
        tk.Label(self.operation_frame, text="余额:").grid(row=0, column=0, padx=5, pady=5)
        tk.Label(self.operation_frame, textvariable=self.balance).grid(row=0, column=1, padx=5, pady=5)
        tk.Label(self.operation_frame, text="取款金额:").grid(row=1, column=0, padx=5, pady=5)
        tk.Entry(self.operation_frame, textvariable=self.amount).grid(row=1, column=1, padx=5, pady=5)
        tk.Button(self.operation_frame, text="查询余额", command=self._query_balance).grid(row=2, column=0, pady=10)
        tk.Button(self.operation_frame, text="确认取款", command=self._withdraw).grid(row=2, column=1, pady=10)
        tk.Button(self.operation_frame, text="退出", command=self._logout).grid(row=3, columnspan=2, pady=10)
        self.operation_frame.pack_forget()

    def _validate_input(self):
        if not self.user_id.get().isdigit():
            messagebox.showerror("错误", "卡号必须为数字")
            return False
        return True

    def _login(self):
        if not self._validate_input():
            return
        
        try:
            # 建立持久连接
            self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.connection.connect((self.server_ip.get(), 2525))
            
            # 协议处理
            self.connection.send(f"HELO {self.user_id.get()}\n".encode())
            response = self.connection.recv(1024).decode().strip()
            
            if response == "500 AUTH REQUIRED!":
                self.connection.send(f"PASS {self.password.get()}\n".encode())
                auth_response = self.connection.recv(1024).decode().strip()
                
                if auth_response == "525 OK!":
                    self.login_frame.pack_forget()
                    self.operation_frame.pack()
                    self._query_balance()
                else:
                    messagebox.showerror("错误", "密码错误")
            else:
                messagebox.showerror("错误", "用户不存在")
        except Exception as e:
            messagebox.showerror("连接错误", str(e))
            self._close_connection()

    # 查询余额
    def _query_balance(self):
        try:
            self.connection.send("BALA\n".encode())
            response = self.connection.recv(1024).decode().strip()
            if response.startswith("AMNT:"):
                self.balance.set(response.split(":")[1])
            else:
                messagebox.showerror("错误", "获取余额失败")
        except Exception as e:
            messagebox.showerror("通信错误", str(e))
            self._close_connection()

    # 取款操作
    def _withdraw(self):
        if not self.amount.get().isdigit():
            messagebox.showerror("错误", "请输入有效金额")
            return
        
        try:
            self.connection.send(f"WDRA {self.amount.get()}\n".encode())
            response = self.connection.recv(1024).decode().strip()
            
            if response == "525 OK":
                messagebox.showinfo("成功", "取款成功")
                self._query_balance()
            else:
                messagebox.showerror("错误", "取款失败，余额不足")
        except Exception as e:
            messagebox.showerror("通信错误", str(e))
            self._close_connection()

    # 退出系统
    def _logout(self):
        try:
            if self.connection:
                self.connection.send("BYE\n".encode())
                self.connection.recv(1024)  
        finally:
            self._close_connection()
            self.operation_frame.pack_forget()
            self.login_frame.pack()
            self.user_id.set("")
            self.password.set("")

    def _close_connection(self):
        if self.connection:
            self.connection.close()
            self.connection = None

if __name__ == "__main__":
    root = tk.Tk()
    app = ATMClient(root)
    root.mainloop()