from PyQt5.QtWidgets import QMainWindow, QApplication, QTableWidgetItem
from PyQt5.QtCore import pyqtSignal, QObject
from ServerThread import *

import sys

import view.MainWindow as MainWindow


class WorkerSignals(QObject):
    clients_updated = pyqtSignal()
    disconnect_client = pyqtSignal(int)


class MainApp(QMainWindow):
    def __init__(self, ip: str = "localhost", port: int = 50000):
        super().__init__()
        self.ui = MainWindow.Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowTitle("ChatRoom - Server")
        self.connected: bool = False
        self.clients: list[dict] = []
        self.ip, self.port = ip, port
        self.signals: WorkerSignals = WorkerSignals()

        self.ui.ip_lineEdit.setPlaceholderText(self.ip)
        self.ui.port_lineEdit.setPlaceholderText(str(self.port))

        self.ui.openServer_button.clicked.connect(self.openServer)
        self.ui.closeServer_button.clicked.connect(self.closeServer)
        self.ui.disconnectClient_button.clicked.connect(self.getSelectedClient)

        self.signals.clients_updated.connect(self.refreshClientsTable)
        self.signals.disconnect_client.connect(self.disconnectClient)

    def openServer(self):
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

    def closeServer(self):
        self.serverThread.stop()
        for client in self.clients:
            client["conn"].close()

        self.ui.ip_lineEdit.setDisabled(False)
        self.ui.port_lineEdit.setDisabled(False)
        self.ui.openServer_button.setDisabled(False)
        self.ui.closeServer_button.setDisabled(True)
        self.ui.disconnectClient_button.setDisabled(True)

    def getSelectedClient(self):
        table = self.ui.clientsTable
        ids_list: list[int] = []
        for item in table.selectedItems():
            if item.column() == 0:
                ids_list.append(int(item.text()))

        ids_list = list(ids_list)
        self.disconnectClient(ids_list)

    def disconnectClient(self, ids_list: list[int]):
        remaining_clients = []

        if isinstance(ids_list, int):
            ids_list = [ids_list]
        else:
            ids_list = ids_list

        for client in self.clients:
            client_id = client["id"]

            if client_id in ids_list:
                try:
                    client["conn"].close()
                except AttributeError:
                    pass
            else:
                remaining_clients.append(client)

        self.clients.clear()
        self.clients.extend(remaining_clients)
        self.signals.clients_updated.emit()

    def refreshClientsTable(self):
        table = self.ui.clientsTable
        table.setRowCount(len(self.clients))
        for index, client in enumerate(self.clients):
            table.setItem(index, 0, QTableWidgetItem(str(client["id"])))
            table.setItem(index, 1, QTableWidgetItem(client["name"]))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_app = MainApp()
    main_app.show()
    sys.exit(app.exec())
