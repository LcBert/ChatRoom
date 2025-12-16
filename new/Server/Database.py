import sqlite3
from datetime import datetime


class Database():
    def __init__(self):
        self.conn = sqlite3.connect("chatroom.db", check_same_thread=False)
        self.cursor = self.conn.cursor()

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password TEXT NOT NULL
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS  incoming_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                timestamp DATETIME NOT NULL,
                sender_username TEXT NOT NULL,
                receiver_username TEXT NOT NULL,
                message TEXT NOT NULL
            )
        ''')

        self.commit()

    def loginUser(self, username: str, password: str) -> bool:
        self.cursor.execute("SELECT username FROM users WHERE username = ? AND password = ?", (username, password))
        if self.cursor.fetchone():
            return True
        return False

    def registerUser(self, username: str, password: str) -> bool:
        self.cursor.execute("SELECT username FROM users WHERE username = ?", (username,))
        if self.cursor.fetchone():
            return False

        self.cursor.execute('''
            INSERT INTO users(username, password) VALUES (?, ?)
        ''', (username, password))

        self.commit()
        return True

    def addMessage(self, sender_username: str, receiver_username: str, message: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute('''
            INSERT INTO incoming_messages(timestamp, sender_username, receiver_username, message)
            VALUES (?, ?, ?, ?)
        ''', (timestamp, sender_username, receiver_username, message))
        self.commit()

    def getMessages(self) -> list[dict]:
        self.cursor.execute("SELECT id, timestamp, sender_username, receiver_username, message FROM incoming_messages")
        rows = self.cursor.fetchall()
        messages = []
        for row in rows:
            messages.append({
                "id": row[0],
                "timestamp": row[1],
                "sender_username": row[2],
                "receiver_username": row[3],
                "message": row[4]
            })
        return messages

    def removeMessage(self, message_id: int):
        self.cursor.execute("DELETE FROM incoming_messages WHERE id = ?", (message_id,))
        self.commit()

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()
