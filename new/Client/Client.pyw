from PyQt5.QtCore import QEvent, Qt, pyqtSignal, QObject
from PyQt5.QtGui import QMouseEvent, QFont
from PyQt5.QtWidgets import QMainWindow, QApplication, QLabel, QSpacerItem, QSizePolicy, QStackedWidget, QWidget, QVBoxLayout, QHBoxLayout

from threading import Thread
from typing import Literal
import socket
import sys
import json

import view.ChatPage as ChatPage
import view.AccessPage as AccessPage
import view.AddFriendPage as AddFriendPage

from Database import Database


class WorkingSignals(QObject):
    message_received = pyqtSignal()


class FriendLabel(QLabel):
    def __init__(self, app, text):
        super().__init__(text)
        self.app: ChatPageApp = app
        self.friend_username = text

    def mouseDoubleClickEvent(self, event):
        self.app.refreshChat(self.friend_username)

    def enterEvent(self, event):
        font = self.font()
        font.setBold(True)
        self.setFont(font)

    def leaveEvent(self, event):
        font = self.font()
        font.setBold(False)
        self.setFont(font)


class MessageWidget(QWidget):
    def __init__(self, app, type: Literal["sent", "received"], message: str):
        super().__init__()
        self.app = app
        self.message = message

        layout = QHBoxLayout()
        self.setLayout(layout)
        layout.setContentsMargins(0, 0, 0, 0)

        label = QLabel(message)

        if type == "sent":
            layout.addStretch()
            layout.addWidget(label)
        elif type == "received":
            layout.addWidget(label)
            layout.addStretch()


class ChatPageApp(QMainWindow):
    def __init__(self, ip: str, port: int):
        super().__init__()
        self.username: str = ""
        self.open_chat_username: str = ""
        self.database: Database
        self.signals = WorkingSignals()
        self.ip, self.port = ip, port
        self.setWindowTitle("ChatRoom - Client")

        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        # Signals Connections
        self.signals.message_received.connect(lambda: self.refreshChat(self.open_chat_username))

        # Setup Chat Page
        self.chatPageWidget = QMainWindow()
        self.chatPage = ChatPage.Ui_ChatPage()
        self.chatPage.setupUi(self.chatPageWidget)
        self.stacked_widget.addWidget(self.chatPageWidget)

        # Setup Access Page
        self.accessPageWidget = QWidget()
        self.accessPage = AccessPage.Ui_AccessPage()
        self.accessPage.setupUi(self.accessPageWidget)
        self.stacked_widget.addWidget(self.accessPageWidget)

        # Setup AddFriend Page
        self.addFriendPageWidget = QWidget()
        self.addFriendPage = AddFriendPage.Ui_AddFriendPage()
        self.addFriendPage.setupUi(self.addFriendPageWidget)
        self.stacked_widget.addWidget(self.addFriendPageWidget)

        # Open Access Page first
        self.openAccessPage()

        self.clientReceive: ClientReceive

        # Chat Page Buttons Bindings
        self.chatPage.addFriendButton.clicked.connect(self.openAddFriendPage)
        self.chatPage.sendMessageButton.clicked.connect(lambda: self.sendMessage(self.chatPage.messageLineEdit.text()))
        self.chatPage.changeAccountAction.triggered.connect(self.openAccessPage)

        # Access Page Buttons Bindings
        self.accessPage.loginButton.clicked.connect(self.login)
        self.accessPage.registerButton.clicked.connect(self.register)

        # AddFriend Page Buttons Bindings
        self.addFriendPage.addFriendButton.clicked.connect(self.addFriend)

    def connect(self):
        self.socket = socket.socket()
        self.socket.connect((self.ip, self.port))

        self.clientReceive = ClientReceive(self, self.socket, self.database, self.signals)

    def openChatPage(self):
        self.stacked_widget.setCurrentWidget(self.chatPageWidget)

    def openAccessPage(self):
        self.username = ""
        self.setWindowTitle("ChatRoom - Client")
        self.stacked_widget.setCurrentWidget(self.accessPageWidget)

    def openAddFriendPage(self):
        self.stacked_widget.setCurrentWidget(self.addFriendPageWidget)

    def login(self):
        self.username = self.accessPage.loginUsernameInput.text()
        password = self.accessPage.loginPasswordInput.text()
        self.database = Database(self.username)
        self.connect()

        loginMessage: dict = {
            "type": "login",
            "username": self.username,
            "password": password
        }
        self.socket.send(json.dumps(loginMessage).encode())

        check: str = self.socket.recv(1024).decode()
        if (check == "success"):
            self.accessPage.loginStatusLabel.setText("Login successful!")
            self.stacked_widget.setCurrentWidget(self.chatPageWidget)
            self.username = self.accessPage.loginUsernameInput.text()
            self.setWindowTitle(f"ChatRoom - Client ({self.username})")

            try:
                self.clientReceive.start()
            except Exception as e:
                pass

            self.accessPage.loginUsernameInput.setText("")
            self.accessPage.loginPasswordInput.setText("")
        elif (check == "failure"):
            self.accessPage.loginStatusLabel.setText("Invalid username or password!")

    def register(self):
        self.username = self.accessPage.registerUsernameInput.text()
        password = self.accessPage.registerPasswordInput.text()
        confirm_password = self.accessPage.registerPasswordConfirmInput.text()
        self.database = Database(self.username)
        self.connect()

        if (password == confirm_password):
            registerMessage: dict = {
                "type": "register",
                "username": self.username,
                "password": password
            }
            self.socket.send(json.dumps(registerMessage).encode())

            check: str = self.socket.recv(1024).decode()

            if (check == "success"):
                self.accessPage.registerStatusLabel.setText("Registration successful!")
                self.stacked_widget.setCurrentWidget(self.chatPageWidget)
                self.username = self.accessPage.registerUsernameInput.text()
                self.setWindowTitle(f"ChatRoom - Client ({self.username})")

                try:
                    self.clientReceive.start()
                except Exception as e:
                    pass

                self.accessPage.registerUsernameInput.setText("")
                self.accessPage.registerPasswordInput.setText("")
                self.accessPage.registerPasswordConfirmInput.setText("")

            elif (check == "failure"):
                self.accessPage.registerStatusLabel.setText("Username already exists!")

    def addFriend(self):
        self.openChatPage()
        friend_username: str = self.addFriendPage.addFriendUsernameInput.text()
        self.addFriendPage.addFriendUsernameInput.setText("")

        if friend_username:
            layout = self.chatPage.friendsListLayout

            # Remove the spacer (last item)
            spacer_item = layout.takeAt(layout.count() - 1)

            # Add the new friend label
            friend_label = FriendLabel(self, friend_username)
            layout.addWidget(friend_label)

            # Add the spacer back
            layout.addItem(spacer_item)

    def refreshChat(self, friend_username: str):
        self.open_chat_username = friend_username
        messages: list[dict] = self.database.getMessages(self.username, friend_username)

        layout = self.chatPage.messagesContainerLayout

        spacer_item = layout.takeAt(layout.count() - 1)
        self.clearLayour(layout)

        for mex in messages:
            if (mex["sender_username"] == self.username):
                message_widget = MessageWidget(self, "sent", mex["message"])
            else:
                message_widget = MessageWidget(self, "received", mex["message"])
            layout.addWidget(message_widget)
        layout.addItem(spacer_item)

    def clearLayour(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def sendMessage(self, message: str):
        message_dict: dict = {
            "type": "message",
            "sender_username": self.username,
            "receiver_username": self.open_chat_username,
            "message": message
        }
        self.socket.send(json.dumps(message_dict).encode())
        self.database.addMessage(self.username, self.open_chat_username, message)
        self.refreshChat(self.open_chat_username)


class ClientReceive(Thread):
    def __init__(self, app: ChatPageApp, socket: socket.socket, database: Database, signals: WorkingSignals):
        super(ClientReceive, self).__init__()
        self.app = app
        self.socket = socket
        self.database = database
        self.signals = signals
        self.running = True

    def run(self):
        while self.running:
            try:
                text: str = self.socket.recv(1024).decode()
                messages: dict = json.loads(text)

                if (messages["type"] == "user_message"):
                    self.database.addMessage(messages["sender_username"], messages["receiver_username"], messages["message"])
                    if (self.app.open_chat_username == messages["sender_username"]):
                        self.signals.message_received.emit()
            except Exception as e:
                print(f"Client Receive Error: {e}")
                break


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ChatPageApp("localhost", 5000)
    window.show()
    sys.exit(app.exec_())
