from ServerThread import ServerThread, Connection
from Database import Database


class Server:
    def __init__(self, ip: str, port: int):
        self.clients: list[Connection] = []
        self.ip, self.port = ip, port
        self.database = Database()

        self.openServer()

    def openServer(self):
        self.serverThread = ServerThread(self.ip, self.port, self.clients, self.database)
        self.serverThread.start()

    def closeServer(self):
        self.serverThread.stop()


if __name__ == "__main__":
    server = Server("localhost", 5000)
