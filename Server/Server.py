from PyQt5.QtGui import QCloseEvent
from PyQt5.QtWidgets import QMainWindow, QApplication, QTableWidgetItem
from PyQt5.QtCore import pyqtSignal, QObject
from ServerThread import *

import sys

import view.MainWindow as MainWindow


class WorkerSignals(QObject):
    clients_updated = pyqtSignal()
    disconnect_client = pyqtSignal(int)


def sendMessage(clients: list["Connection"], type: Literal["user_message", "refresh_list"], text: str = "", sender_name: str = "", sender_id: int = -1) -> None:
    if type == "refresh_list":
        text = ",".join(client.getName() for client in clients)

    message: dict = {
        "type": type,
        "text": text,
        "sender_name": sender_name,
        "sender_id": sender_id
    }

    for client in clients:
        client.getSocket().send(f"{json.dumps(message)}".encode())


class MainApp(QMainWindow):
    def __init__(self, ip: str = "localhost", port: int = 50000):
        super().__init__()
        self.ui = MainWindow.Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowTitle("ChatRoom - Server")
        self.connected: bool = False
        self.clients: list[Connection] = []
        self.ip, self.port = ip, port
        self.signals: WorkerSignals = WorkerSignals()

        self.ui.ip_lineEdit.setPlaceholderText(self.ip)
        self.ui.port_lineEdit.setPlaceholderText(str(self.port))

        self.ui.openServer_button.clicked.connect(self.openServer)
        self.ui.closeServer_button.clicked.connect(self.closeServer)
        self.ui.disconnectClient_button.clicked.connect(self.getSelectedClient)

        self.signals.clients_updated.connect(self.refreshClientsTable)
        self.signals.disconnect_client.connect(self.disconnectClient)

    def openServer(self) -> None:
        ip = self.ui.ip_lineEdit.text().strip()
        port = self.ui.port_lineEdit.text().strip()

        self.ip = ip if ip != "" else self.ip
        self.port = port if port != "" else self.port

        self.serverThread = ServerThread(self.clients, self.signals, self.ip, int(self.port))
        self.serverThread.start()

        self.ui.ip_lineEdit.setDisabled(True)
        self.ui.port_lineEdit.setDisabled(True)
        self.ui.openServer_button.setDisabled(True)
        self.ui.closeServer_button.setDisabled(False)
        self.ui.disconnectClient_button.setDisabled(False)

    def closeServer(self) -> None:
        self.serverThread.stop()
        for client in self.clients:
            client.getSocket().close()

        self.ui.ip_lineEdit.setDisabled(False)
        self.ui.port_lineEdit.setDisabled(False)
        self.ui.openServer_button.setDisabled(False)
        self.ui.closeServer_button.setDisabled(True)
        self.ui.disconnectClient_button.setDisabled(True)

    def getSelectedClient(self) -> None:
        table = self.ui.clientsTable
        ids_list: list[int] = []
        for item in table.selectedItems():
            if item.column() == 0:
                ids_list.append(int(item.text()))

        ids_list = list(ids_list)
        for id in ids_list:
            self.disconnectClient(id)

    def disconnectClient(self, id: int) -> None:
        client_to_disconnect: socket.socket = socket.socket()
        remaining_clients: list[Connection] = []

        for client in self.clients:
            if client.getId() == id:
                client_to_disconnect = client.getSocket()
            else:
                remaining_clients.append(client)

        client_to_disconnect.close()

        self.clients.clear()
        self.clients.extend(remaining_clients)
        self.signals.clients_updated.emit()

        sendMessage(self.clients, "refresh_list")

    def refreshClientsTable(self) -> None:
        table = self.ui.clientsTable
        table.setRowCount(len(self.clients))
        for index, client in enumerate(self.clients):
            table.setItem(index, 0, QTableWidgetItem(str(client.getId())))
            table.setItem(index, 1, QTableWidgetItem(client.getName()))

    def closeEvent(self, event: QCloseEvent | None) -> None:
        self.closeServer()
        return super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_app = MainApp()
    main_app.show()
    sys.exit(app.exec())
