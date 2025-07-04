import sqlite3

conn = sqlite3.connect('./history.db')
c = conn.cursor()
c.execute('SELECT * FROM message_store')
result = c.fetchone()
print(result)