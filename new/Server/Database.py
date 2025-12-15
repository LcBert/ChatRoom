import sqlite3


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
            CREATE TABLE IF NOT EXISTS messages (
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

    def getMessages(self, sender_username:str, receiver_username:str):
        self.cursor.execute('''
            SELECT timestamp, sender_username, receiver_username, message
            FROM messages
            WHERE (sender_username = ? AND receiver_username = ?)
               OR (sender_username = ? AND receiver_username = ?)
            ORDER BY timestamp ASC
        ''', (sender_username, receiver_username, receiver_username, sender_username))
        return self.cursor.fetchall()

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()
