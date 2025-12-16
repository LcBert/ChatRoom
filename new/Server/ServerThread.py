from typing import Mapping
from Database import Database

from threading import Thread
import socket
import json
import time


class IncomingMessages(Thread):
    def __init__(self, clients_list: list["Connection"], database: Database):
        super(IncomingMessages, self).__init__()
        self.clients_list = clients_list
        self.database = database
        self.running = True

    def run(self):
        while self.running:
            messages = self.database.getMessages()
            for message in messages:
                for client in self.clients_list:
                    if client.getUsername() == message["receiver_username"]:
                        try:
                            client.getSocket().send(json.dumps({
                                "type": "user_message",
                                "sender_username": message["sender_username"],
                                "receiver_username": message["receiver_username"],
                                "message": message["message"],
                                "timestamp": message["timestamp"]
                            }).encode())
                            self.database.removeMessage(message["id"])
                        except Exception as e:
                            print(f"Error sending message to {client.getUsername()}: {e}")
            time.sleep(15)

    def stop(self):
        self.running = False


class ServerThread(Thread):
    def __init__(self, ip: str, port: int, clients_list: list["Connection"], database: Database):
        super(ServerThread, self).__init__()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clients: list[Connection] = clients_list
        self.database = database
        self.ip, self.port = ip, port

    def run(self):
        self.socket.bind((self.ip, self.port))
        self.connected = True
        self.socket.listen(1)
        try:
            while True:
                self.client, self.addr = self.socket.accept()
                self.connection_thread = Connection(self.client, self.clients, self.database)
                self.clients.append(self.connection_thread)
                self.connection_thread.start()

        except Exception:
            self.connected = False

    def stop(self):
        try:
            self.socket.close()
            for client in self.clients:
                client.getSocket().close()
        except AttributeError:
            print("No Server opened - Closing")


class Connection(Thread):
    def __init__(self, conn: socket.socket, clients_list: list["Connection"], database: Database):
        super(Connection, self).__init__()
        self.socket: socket.socket = conn
        self.clients: list[Connection] = clients_list
        self.database = Database()
        self.connected = True
        self.username = ""

    def run(self):
        print("Client connected")
        while self.connected:
            try:
                text: str = self.socket.recv(1024).decode()
                message: dict = json.loads(text)
                match(message["type"]):
                    case "register":
                        self.registerUser(message)
                    case "login":
                        self.loginUser(message)
                    case "message":
                        self.database.addMessage(message["sender_username"], message["receiver_username"], message["message"])

            except WindowsError:
                print("Client disconnected")
                self.connected = False
            except json.JSONDecodeError:
                print("Client disconnected")
                self.connected = False
            except Exception as e:
                print(f"Server Error: {e}")

    def loginUser(self, message: dict):
        username: str = message["username"]
        password: str = message["password"]
        if (self.database.loginUser(username, password)):
            self.socket.send("success".encode())
            self.username = message["username"]
        else:
            self.socket.send("failure".encode())

    def registerUser(self, message: dict):
        username: str = message["username"]
        password: str = message["password"]
        if (self.database.registerUser(username, password)):
            self.socket.send("success".encode())
            self.username = message["username"]
        else:
            self.socket.send("failure".encode())

    def getUsername(self) -> str:
        return self.username

    def getSocket(self) -> socket.socket:
        return self.socket
