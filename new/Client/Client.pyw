from PyQt5.QtCore import QEvent, Qt
from PyQt5.QtGui import QMouseEvent, QFont
from PyQt5.QtWidgets import QMainWindow, QApplication, QLabel, QSpacerItem, QSizePolicy, QStackedWidget, QWidget, QVBoxLayout
import view.ChatPage as ChatPage
import view.AccessPage as AccessPage
import view.AddFriendPage as AddFriendPage

from threading import Thread
import socket
import sys
import json


class FriendLabel(QLabel):
    def __init__(self, app, text):
        super().__init__(text)
        self.app = app
        self.friend_username = text

    def mouseDoubleClickEvent(self, event):
        self.app.openChat(self.app.username, self.friend_username)

    def enterEvent(self, event):
        font = self.font()
        font.setBold(True)
        self.setFont(font)

    def leaveEvent(self, event):
        font = self.font()
        font.setBold(False)
        self.setFont(font)


class ChatPageApp(QMainWindow):
    def __init__(self, ip: str, port: int):
        super().__init__()
        self.username: str = ""
        self.ip, self.port = ip, port
        self.setWindowTitle("ChatRoom - Client")

        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        # Setup Chat Page
        self.chatPageWidget = QMainWindow()
        self.chatPage = ChatPage.Ui_ChatPage()
        self.chatPage.setupUi(self.chatPageWidget)
        self.stacked_widget.addWidget(self.chatPageWidget)

        # Setup Messages Layout
        self.messagesLayout = QVBoxLayout(self.chatPage.scrollAreaWidgetContents)
        self.messagesLayout.addStretch()

        # Setup Access Page
        self.accessPageWidget = QWidget()
        self.accessPage = AccessPage.Ui_AccessPage()
        self.accessPage.setupUi(self.accessPageWidget)
        self.stacked_widget.addWidget(self.accessPageWidget)

        # Setup AddFriend Page
        self.addFriendPage = QWidget()
        self.addFriendPageUI = AddFriendPage.Ui_AddFriendPage()
        self.addFriendPageUI.setupUi(self.addFriendPage)
        self.stacked_widget.addWidget(self.addFriendPage)

        # Open Access Page first
        self.openAccessPage()

        self.clientSend: ClientSend
        self.clientReceive: ClientReceive
        self.connect()

        # Chat Page Buttons Bindings
        self.chatPage.addFriendButton.clicked.connect(self.openAddFriendPage)
        self.chatPage.changeAccountAction.triggered.connect(self.openAccessPage)

        # Access Page Buttons Bindings
        self.accessPage.loginButton.clicked.connect(self.login)
        self.accessPage.registerButton.clicked.connect(self.register)

        # AddFriend Page Buttons Bindings
        self.addFriendPageUI.addFriendButton.clicked.connect(self.addFriend)

    def connect(self):
        self.socket = socket.socket()
        self.socket.connect((self.ip, self.port))

        self.clientSend = ClientSend(self.socket)
        self.clientReceive = ClientReceive(self.socket)

    def openChatPage(self):
        self.stacked_widget.setCurrentWidget(self.chatPageWidget)

    def openAccessPage(self):
        self.username = ""
        self.setWindowTitle("ChatRoom - Client")
        self.stacked_widget.setCurrentWidget(self.accessPageWidget)

    def openAddFriendPage(self):
        self.stacked_widget.setCurrentWidget(self.addFriendPage)

    def login(self):
        loginMessage: dict = {
            "type": "login",
            "username": self.accessPage.loginUsernameInput.text(),
            "password": self.accessPage.loginPasswordInput.text()
        }
        self.socket.send(json.dumps(loginMessage).encode())

        check: str = self.socket.recv(1024).decode()
        if (check == "success"):
            self.accessPage.loginStatusLabel.setText("Login successful!")
            self.stacked_widget.setCurrentWidget(self.chatPageWidget)
            self.username = self.accessPage.loginUsernameInput.text()
            self.setWindowTitle(f"ChatRoom - Client ({self.username})")

            self.accessPage.loginUsernameInput.setText("")
            self.accessPage.loginPasswordInput.setText("")
        elif (check == "failure"):
            self.accessPage.loginStatusLabel.setText("Invalid username or password!")

    def register(self):
        if (self.accessPage.registerPasswordInput.text() == self.accessPage.registerPasswordConfirmInput.text()):
            registerMessage: dict = {
                "type": "register",
                "username": self.accessPage.registerUsernameInput.text(),
                "password": self.accessPage.registerPasswordInput.text()
            }
            self.socket.send(json.dumps(registerMessage).encode())

            check: str = self.socket.recv(1024).decode()

            if (check == "success"):
                self.accessPage.registerStatusLabel.setText("Registration successful!")
                self.stacked_widget.setCurrentWidget(self.chatPageWidget)
                self.username = self.accessPage.registerUsernameInput.text()
                self.setWindowTitle(f"ChatRoom - Client ({self.username})")

                self.accessPage.registerUsernameInput.setText("")
                self.accessPage.registerPasswordInput.setText("")
                self.accessPage.registerPasswordConfirmInput.setText("")
            elif (check == "failure"):
                self.accessPage.registerStatusLabel.setText("Username already exists!")

    def addFriend(self):
        self.openChatPage()
        friend_username: str = self.addFriendPageUI.addFriendUsernameInput.text()
        self.addFriendPageUI.addFriendUsernameInput.setText("")

        if friend_username:
            layout = self.chatPage.friendsListLayout

            # Remove the spacer (last item)
            spacer_item = layout.takeAt(layout.count() - 1)

            # Add the new friend label
            friend_label = FriendLabel(self, friend_username)
            layout.addWidget(friend_label)

            # Add the spacer back
            layout.addItem(spacer_item)

    def openChat(self, user_username: str, friend_username: str):
        pass


class ClientSend(Thread):
    def __init__(self, socket: socket.socket):
        super(ClientSend, self).__init__()
        self.socket = socket


class ClientReceive(Thread):
    def __init__(self, socket: socket.socket):
        super(ClientReceive, self).__init__()
        self.socket = socket


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ChatPageApp("localhost", 5000)
    window.show()
    sys.exit(app.exec_())
