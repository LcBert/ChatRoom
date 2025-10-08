import socket
from threading import Thread
from typing import Literal
import json

from Server import WorkerSignals


class ServerThread(Thread):
    def __init__(self, clients: list,  signals: WorkerSignals,  ip: str, port: int):
        super(ServerThread, self).__init__()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ip = ip
        self.port = port
        self.connected = False
        self.clients: list = clients
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
                self.clients.append({"id": self.client_id, "name": self.client_name, "conn": self.conn})
                self.serverThread = Connection(self.conn, self.client_id, self.client_name, self.clients, self.signals)
                self.serverThread.start()
                self.client_id += 1
        except Exception:
            self.connected = False

    def stop(self):
        self.socket.close()


class Connection(Thread):
    def __init__(self,  conn: socket.socket, client_id: int, client_name: str, clients: list[dict], signals: WorkerSignals):
        super(Connection, self).__init__()
        self.conn: socket.socket = conn
        self.client_id: int = client_id
        self.client_name: str = client_name
        self.connected: bool = False
        self.clients: list[dict] = clients
        self.signals = signals

    def run(self):
        print(f"{self.client_name} connected")
        self.signals.clients_updated.emit()
        self.connected: bool = True
        self.conn.send(f"{self.client_id}".encode())

        clients_list = ",".join(client["name"] for client in self.clients)
        # clients_list: str = ""
        # for client in self.clients:
        #     clients_list += f"{client["name"]},"
        self.sendMessage("refresh_list", clients_list, self.client_name, self.client_id)

        while self.connected:
            try:
                text: str = self.conn.recv(1024).decode()
                self.sendMessage("user_message", text, self.client_name, self.client_id)
            except WindowsError:
                self.signals.disconnect_client.emit(self.client_id)
                print(f"{self.client_name} disconnected")
                self.connected = False
            except Exception:
                print("Server Error")

    def sendMessage(self, type: Literal["user_message", "refresh_list"], text, sender_name: str, sender_id: int):
        message: dict = {
            "type": type,
            "text": text,
            "sender_name": sender_name,
            "sender_id": sender_id
        }

        for client in self.clients:
            client["conn"].send(f"{json.dumps(message)}".encode())
