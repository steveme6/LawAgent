import sqlite3
from datetime import datetime


class AgentDB:
    def __init__(self, database_path):
        self.database_path = database_path
        with sqlite3.connect(self.database_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chat_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT,
                    timestamp TEXT NOT NULL,
                    user_query TEXT NOT NULL,
                    search_results TEXT,
                    origin_agent_response TEXT,
                    final_agent_response TEXT
                )
            ''')
            conn.commit()


    def select_query(self,user_name:str):
        with sqlite3.connect(self.database_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
            SELECT * FROM chat_history 
            WHERE username = ?
            ORDER BY timestamp DESC
            ''', (user_name,))
            row = cursor.fetchall()
            conn.commit()
            if row is None:
                return None
            else:
                return row
    def delete_history(self,user_name:str):
        with sqlite3.connect(self.database_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
            DELETE FROM chat_history
            WHERE username = ?
            ''', (user_name,))
            conn.commit()

    def insert_history(self,user_name, query, search_results, origin_response, final_response):
        with sqlite3.connect(self.database_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                           INSERT INTO chat_history (
                                     username,
                                     timestamp,
                                     user_query,
                                     search_results,
                                     origin_agent_response,
                                     final_agent_response)
                           VALUES (? ,?, ?, ?, ?, ?)
                           ''', (
                                user_name,
                               datetime.now().isoformat(),
                               query,
                               search_results,
                               origin_response,
                               final_response
                           ))
            conn.commit()
    
    # 获取所有记录
    def select_all(self):
        with sqlite3.connect(self.database_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''SELECT * FROM chat_history;''')
            conn.commit()
            row = cursor.fetchall()
            return row

    # 获取所有username
    def get_usernames(self):
        with sqlite3.connect(self.database_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''SELECT username FROM chat_history GROUP BY username;''')
            conn.commit()
            row = cursor.fetchall()
            usernames = [row[0] for row in row]
            return usernames