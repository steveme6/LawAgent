import asyncio
import re
import sys
from app import FinalAgent, AgentDB
from app import OriginAgent
from app import SearchAgent
import os
def extract_output(model_output):
    match = re.search(r'<think>\s*(.*?)$', model_output, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None
class MultipleAgent():
    def __init__(self):
        self.config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "./config/config.ini"))
        self.database_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "./history_db/history.db"))

        self.origin_agent = OriginAgent(config_url=self.config_path, database_url=self.database_path, prompt="你是一个智能助手，使用用中文回答，你需要提取和用户查询结果最接近的数据库查询结果，以此来回答用户输入,注意，请重点关注用户输入！！！如果查询没有结果，就忽略查询，自行对用户输入进行回答。用户输入和数据库查询结果：{input}")
        self.final_agent = None
        self.search_agent = SearchAgent("app/faiss_db","law_index", database_url=self.database_path, config_url=self.config_path)
        self.agent_db=AgentDB(os.path.abspath(os.path.join(os.path.dirname(__file__), "./history_db/multiply.db/")))
        self.username = ""
        self.query = ""
        self.search_results = ""
        self.origin_response = ""
        self.final_response = ""

    def save_history(self):
        """存储历史"""
        self.agent_db.insert_history(self.username, self.query, self.search_results, self.origin_response, self.final_response)
    def delete_history(self,username):
        """删除历史"""
        self.agent_db.delete_history(username)
    """多智能体接口"""
    async def run(self,query,username:str):
        new_query = await self.search_agent.search(query)
        self.query = query
        self.username = username
        self.search_results = ""
        self.origin_response = ""
        self.final_response = ""
        if new_query:
            if len(new_query[0]) > 3 and len(new_query[1]) > 3:
                new_query = new_query[0][:1]+new_query[1][:1]
            elif len(new_query[0]) > 3 > len(new_query[1]):
                new_query = new_query[0][:1]+new_query[1]
            elif len(new_query[1]) > 3 > len(new_query[0]):
                new_query = new_query[0]+new_query[1][:1]
            else:
                new_query = new_query[0]+new_query[1]
        self.search_results = str(new_query)

        # yield "查询agent查询结果:\n"
        # yield new_query

        yield "\n\n### 问答agent:\n\n"
        history_list = self.agent_db.select_query(username)
        if history_list:
            row = history_list[0]
            history = {
                "user_query": row[3],
                "final_agent_response": row[6]
            }
        else:
            history = {}
        async for word in self.origin_agent.ask_agent("上一对话历史记录："+str(history)+"\n数据库查询结果如下："+str(new_query)+"\n请注意用户的输入是："+query):
            if word == '<think>':
                word = '<!--'
            elif word == '</think>':
                word = '-->'
            self.origin_response+=word
            yield word
        new_results = extract_output(self.origin_agent.result)
        yield "\n\n### 总结agent:\n\n"

        self.final_agent = FinalAgent(database_url=self.database_path,config_url=self.config_path,last_result=str(new_results))
        async for chunk in self.final_agent.conclusion():
            if chunk == '<think>':
                chunk = '<!--'
            elif chunk == '</think>':
                chunk = '-->'
            self.final_response+=chunk
            yield chunk

async def main():
    """测试main"""
    agent = MultipleAgent()
    while True:
        print("\n请输入:\n> (type 'quit' to exit):")
        try:
            query = input().strip()
            if query.lower() == "quit":
                break
            async for chunk in agent.run(query=query,username="admin"):
                print(chunk, end="", flush=True)
            agent.save_history()
        except Exception as e:
            print(f"Error: {str(e)}")
if __name__ == "__main__":
    asyncio.run(main())
    """导入方式错误：multiple_agent.py中使用了from app import FinalAgent，这种绝对导入方式在作为主脚本运行时会出现问题。所以要在包外面"""