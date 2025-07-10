import os

from app import AgentDB

agent_db = AgentDB(os.path.abspath(os.path.join(os.path.dirname(__file__), "./multiply.db")))
agent_db.delete_history("admin")
result = agent_db.select_query("admin")
print(result)