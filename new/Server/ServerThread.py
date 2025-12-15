from Database import Database

from threading import Thread
import socket
import json


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
                    case "get_chat_history":
                        self.getChatHistory(message)

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
        else:
            self.socket.send("failure".encode())

    def registerUser(self, message: dict):
        username: str = message["username"]
        password: str = message["password"]
        else:
            self.socket.send("failure".encode())

    def getChatHistory(self, message: dict):
        sender = message["sender"]
        receiver = message["receiver"]
        messages = self.database.getMessages(sender, receiver)
        # messages is a list of tuples: (timestamp, sender, receiver, message)
        # Convert to list of dicts for JSON serialization
        history = []
        for msg in messages:
            history.append({
                "timestamp": msg[0],
                "sender": msg[1],
                "receiver": msg[2],
                "message": msg[3]
            })
        self.socket.send(json.dumps({"type": "chat_history", "data": history}).encode())
        if (self.database.registerUser(username, password)):
            self.socket.send("success".encode())
        else:
            self.socket.send("failure".encode())

    def getSocket(self) -> socket.socket:
        return self.socket
