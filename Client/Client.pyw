from PyQt5.QtWidgets import QMainWindow, QApplication, QLabel, QSpacerItem, QSizePolicy
from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtGui import QCloseEvent
from threading import Thread
from FileManager import File
from typing import Literal

import sys
import socket
import json

import view.MainWindow as MainWindow


class WorkerSignals(QObject):
    message_received = pyqtSignal(str)
    refresh_clients_list = pyqtSignal(str)
    disconnect_client = pyqtSignal()


class ThreadReceive(Thread):
    def __init__(self, signals: WorkerSignals, socket: socket.socket, client_name: str):
        super(ThreadReceive, self).__init__()
        self.socket = socket
        self.signals = signals
        self.client_id: int
        self.client_name: str = client_name

    def run(self):
        self.client_id = int(self.socket.recv(1024).decode())
        self.connected = True
        while self.connected:
            try:
                message = json.loads(self.socket.recv(1024).decode())
                type: str = message["type"]
                text: str = message["text"]
                sender_name: str = message["sender_name"]
                sender_id: int = int(message["sender_id"])

                match (type):
                    case "user_message":
                        if (sender_id == self.client_id):
                            self.signals.message_received.emit(f"You: {text}")
                        else:
                            self.signals.message_received.emit(f"{sender_name}: {text}")
                    case "refresh_list":
                        self.signals.refresh_clients_list.emit(text)
            except WindowsError:
                self.connected = False
                self.signals.disconnect_client.emit()
            except Exception:
                print("Receive Error")


class MainApp(QMainWindow):
    def __init__(self, ip: str = "localhost", port: int = 50000):
        super().__init__()
        self.ui = MainWindow.Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowTitle("ChatRoom - Client")
        self.ip, self.port = ip, port
        self.id: int
        self.signals = WorkerSignals()
        self.netSettFile = File("NetworkSettings.json")

        self.ui.ip_lineEdit.setPlaceholderText(self.ip)
        self.ui.port_lineEdit.setPlaceholderText(str(self.port))

        # Button click connections
        self.ui.saveNetworkSettings_button.clicked.connect(self.saveNetworkSettings)
        self.ui.clearNetworkSettings_button.clicked.connect(self.clearNetworkSettings)
        self.ui.connect_button.clicked.connect(self.connectSocket)
        self.ui.disconnect_button.clicked.connect(self.disconnectSocket)
        self.ui.send_button.clicked.connect(self.sendMessage)

        # Signals connections
        self.signals.message_received.connect(self.update_gui_with_message)
        self.signals.refresh_clients_list.connect(self.refreshClientsList)
        self.signals.disconnect_client.connect(self.disconnectSocket)

        if (self.netSettFile.exists() and not self.netSettFile.is_empty()):
            sett_dict = json.loads(self.netSettFile.read())
            self.ui.ip_lineEdit.setText(sett_dict["ip"])
            self.ui.port_lineEdit.setText(sett_dict["port"])
            self.ui.name_lineEdit.setText(sett_dict["name"])

    def saveNetworkSettings(self):
        sett_dict = {}
        sett_dict["ip"] = self.ui.ip_lineEdit.text().strip()
        sett_dict["port"] = self.ui.port_lineEdit.text().strip()
        sett_dict["name"] = self.ui.name_lineEdit.text().strip()

        print(sett_dict["ip"] == "")
        print(sett_dict["port"] == "")
        print(sett_dict["name"] == "")

        if not (sett_dict["ip"] == "" and sett_dict["port"] == "" and sett_dict["name"] == ""):
            if not self.netSettFile.exists():
                self.netSettFile.create()
            self.netSettFile.write(json.dumps(sett_dict))

    def clearNetworkSettings(self):
        if (self.netSettFile.exists()):
            self.netSettFile.delete()

        self.ui.ip_lineEdit.clear()
        self.ui.port_lineEdit.clear()
        self.ui.name_lineEdit.clear()

    def refreshClientsList(self, list: str):
        self.clearLayout(self.ui.clients_container)
        for client in list.split(","):
            label = QLabel()
            label.setText(client)

            self.ui.clients_container.addWidget(label)
        self.ui.clients_container.addItem(QSpacerItem(27, 207, QSizePolicy.Expanding, QSizePolicy.Minimum))

    def clearLayout(self, layout):
        if layout is not None:
            while layout.count():
                child = layout.takeAt(0)
                if not isinstance(child, QSpacerItem):
                    if child.widget() is not None:
                        child.widget().deleteLater()
                    elif child.layout() is not None:
                        self.clearLayout(child.layout())

    def connectSocket(self):
        try:
            ip = self.ui.ip_lineEdit.text().strip()
            port = self.ui.port_lineEdit.text().strip()
            name = self.ui.name_lineEdit.text().strip()

            ip = ip if ip != "" else self.ip
            port = port if port != "" else self.port

            if (name == ""):
                self.setStatus("Insert a name", "warning")
                return

            self.socket = socket.socket()
            self.socket.connect((ip, int(port)))
            self.thread_receive = ThreadReceive(self.signals, self.socket, name)
            self.thread_receive.start()
            self.socket.send(name.encode())

            self.setStatus("Connected to server", "info")

            self.ui.networkSettings_groupBox.setDisabled(True)
            self.ui.connect_button.setDisabled(True)
            self.ui.disconnect_button.setDisabled(False)
            self.ui.message_lineEdit.setDisabled(False)
            self.ui.send_button.setDisabled(False)
        except WindowsError:
            self.setStatus("The server is not online", "warning")
        except ValueError:
            self.setStatus("Invalid port", "error")
        except Exception:
            print("Connection Error")

    def disconnectSocket(self):
        try:
            self.socket.close()
            self.setStatus("Disconnected from server", "info")
            self.ui.networkSettings_groupBox.setDisabled(False)
            self.ui.connect_button.setDisabled(False)
            self.ui.disconnect_button.setDisabled(True)
            self.ui.message_lineEdit.setDisabled(True)
            self.ui.send_button.setDisabled(True)
        except Exception:
            print("Disconnection Error")

    def update_gui_with_message(self, text):
        label = QLabel()
        label.setText(text)
        self.ui.message_container.addWidget(label)

    def sendMessage(self):
        try:
            text = self.ui.message_lineEdit.text()
            if (text != ""):
                self.socket.send(text.encode())

            self.ui.message_lineEdit.clear()
            self.ui.message_lineEdit.setFocus()
        except WindowsError:
            self.setStatus("Error: Disconnected from server", "info")
            self.ui.networkSettings_groupBox.setDisabled(False)
            self.ui.connect_button.setDisabled(False)
        except Exception:
            print("Send Error")

    def closeEvent(self, event: QCloseEvent | None) -> None:
        self.disconnectSocket()
        return super().closeEvent(event)

    def setStatus(self, status: str, type: Literal["info", "warning", "error"] = "info"):
        print(status)
        self.ui.connectionStatut_label.setText(status)
        if (type == "info"):
            self.ui.connectionStatut_label.setStyleSheet("color:green;")
        elif (type == "warning"):
            self.ui.connectionStatut_label.setStyleSheet("color:orange;")
        elif (type == "error"):
            self.ui.connectionStatut_label.setStyleSheet("color:red;")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_app = MainApp()
    main_app.show()
    sys.exit(app.exec())
