import sqlite3
from datetime import datetime


class Database():
    def __init__(self, username: str):
        self.conn = sqlite3.connect(f"chatroom-{username}.db", check_same_thread=False)
        self.cursor = self.conn.cursor()

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                timestamp DATETIME NOT NULL,
                sender_username TEXT NOT NULL,
                receiver_username TEXT NOT NULL,
                message TEXT NOT NULL
            )
        ''')

        self.commit()

    def addMessage(self, sender_username: str, receiver_username: str, message: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute('''
            INSERT INTO messages(timestamp, sender_username, receiver_username, message)
            VALUES (?, ?, ?, ?)
        ''', (timestamp, sender_username, receiver_username, message))
        self.commit()

    def getMessages(self, sender_username: str, receiver_username: str) -> list[dict]:
        self.cursor.execute('''
            SELECT timestamp, sender_username, receiver_username, message
            FROM messages
            WHERE (sender_username = ? AND receiver_username = ?)
               OR (sender_username = ? AND receiver_username = ?)
            ORDER BY timestamp ASC
        ''', (sender_username, receiver_username, receiver_username, sender_username))

        rows = self.cursor.fetchall()
        messages = []
        for row in rows:
            messages.append({
                "timestamp": row[0],
                "sender_username": row[1],
                "receiver_username": row[2],
                "message": row[3]
            })

        return messages

    def commit(self):
        self.conn.commit()
