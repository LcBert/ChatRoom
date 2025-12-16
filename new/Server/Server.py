from ServerThread import IncomingMessages, ServerThread, Connection
from Database import Database


class Server:
    def __init__(self, ip: str, port: int):
        self.clients_list: list[Connection] = []
        self.ip, self.port = ip, port
        self.database = Database()
        self.serverThread: ServerThread
        self.incomingMessagesThread: IncomingMessages

        self.openServer()

    def openServer(self):
        self.serverThread = ServerThread(self.ip, self.port, self.clients_list, self.database)
        self.serverThread.start()

        self.incomingMessagesThread = IncomingMessages(self.clients_list, self.database)
        self.incomingMessagesThread.start()

    def closeServer(self):
        self.serverThread.stop()
        self.incomingMessagesThread.stop()


if __name__ == "__main__":
    server = Server("localhost", 5000)
