import socket
from threading import Thread
from typing import Literal
import json

from Server import WorkerSignals, sendMessage


class ServerThread(Thread):
    def __init__(self, clients: list["Connection"],  signals: WorkerSignals,  ip: str, port: int):
        super(ServerThread, self).__init__()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ip = ip
        self.port = port
        self.connected = False
        self.clients: list[Connection] = clients
        self.signals: WorkerSignals = signals

    def run(self):
        self.client_id = 1
        self.socket.bind((self.ip, self.port))
        self.connected = True
        print(f"Server opened with IP: {self.ip} and Port: {self.port}")
        try:
            while self.connected:
                self.socket.listen(2)
                self.conn, self.addr = self.socket.accept()
                self.client_name = self.conn.recv(1024).decode()
                self.connection_thread = Connection(self.conn, self.client_id, self.client_name, self.clients, self.signals)
                self.clients.append(self.connection_thread)
                self.connection_thread.start()
                self.client_id += 1
        except Exception:
            self.connected = False

    def stop(self):
        self.socket.close()


class Connection(Thread):
    def __init__(self,  conn: socket.socket, client_id: int, client_name: str, clients: list["Connection"], signals: WorkerSignals):
        super(Connection, self).__init__()
        self.socket: socket.socket = conn
        self.client_id: int = client_id
        self.client_name: str = client_name
        self.connected: bool = False
        self.clients: list[Connection] = clients
        self.signals = signals

    def run(self):
        print(f"{self.client_name} connected")
        self.signals.clients_updated.emit()
        self.connected: bool = True
        self.socket.send(f"{self.client_id}".encode())

        sendMessage(self.clients, "refresh_list")

        while self.connected:
            try:
                text: str = self.socket.recv(1024).decode()
                sendMessage(self.clients, "user_message", text, self.client_name, self.client_id)
            except WindowsError:
                self.signals.disconnect_client.emit(self.client_id)
                print(f"{self.client_name} disconnected")
                self.connected = False
            except Exception:
                print("Server Error")

    def getId(self) -> int:
        return self.client_id

    def getName(self) -> str:
        return self.client_name

    def getSocket(self) -> socket.socket:
        return self.socket
