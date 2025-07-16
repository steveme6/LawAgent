import os

from app import AgentDB

agent_db = AgentDB(os.path.abspath(os.path.join(os.path.dirname(__file__), "./multiply.db")))
result = agent_db.select_query("")
print(result)