import sqlite3
import json
from contextlib import contextmanager


class Database:
    def __init__(self):
        self.db_path = "history_db/history.db"
        self.tables = ["message_store", "talks"]

    @contextmanager
    def get_connection(self):
        """上下文管理器，确保连接正确关闭"""
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()

    def fetch_message(self, talk_id=None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if not talk_id:
                cursor.execute("SELECT * FROM messages")
            else:
                cursor.execute(f"SELECT * FROM messages WHERE talk_id= ? ORDER BY id", (talk_id,))

            batch = []
            for row in cursor:
                record = {
                    "id" : row[0],
                    "talk_id" : row[1],
                    "session_id" : row[2],
                    "ques" : row[3],
                    "ans" : row[4],
                }
                batch.append(record)
        return batch

    def fetch_talks(self):
        with self.get_connection() as conn:

            cursor = conn.cursor()
            cursor.execute("SELECT * FROM messages GROUP BY talk_id")
            
            batch = []
            for row in cursor:
                record = {
                    "talk_id": row[1],
                    "ques": row[3]
                }
                print(row)
                batch.append(record)
            return batch

    def add_message(self, talk_id, session_id, ques, ans):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO messages (session_id, talk_id, ques, ans) VALUES (?, ?, ?, ?)",
                           (session_id, talk_id, ques, ans))
            conn.commit()

    def add_talk(self, talk_id, session_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO talks (talk_id, session_id) VALUES (?, ?)",
                           (talk_id, session_id))
            conn.commit()

    def create_talk_tables(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS talks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    talk_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES message_store(session_id)
                )
            """)
            conn.commit()

    def create_message_tables(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    talk_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    ques TEXT NOT NULL,
                    ans TEXT NOT NULL
                )
            """)
            conn.commit()
    
    def delete_talk(self, talk_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM talks WHERE talk_id = ?", (talk_id,))
            conn.commit()

    def delete_message(self, session_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM message_store WHERE session_id = ?", (session_id,))
            conn.commit()

    def delete_table(self, table_name):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
            conn.commit()

# # === 使用示例 ===
if __name__ == "__main__":
    database = Database()
    # database.fetch_message()
    # database.delete_table("talks")
    # database.create_tables()
    database.create_message_tables()
    # database.add_talk("talk_001", "aaaaaaaaa")
    # print(database.fetch_talks())
    # print(database.fetch_message())