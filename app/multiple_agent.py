import asyncio
import sys

from app import FinalAgent
from app import OriginAgent
from app import SearchAgent
import os

class MultipleAgent():
    def __init__(self):
        self.config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../config/config.ini"))
        self.database_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../history_db/history.db"))

        self.origin_agent = OriginAgent(config_url=self.config_path, database_url=self.database_path, prompt="你是一个智能助手，使用用中文回答，你需要提取和用户查询结果最接近的数据库查询结果，以此来回答用户输入,注意，请重点关注用户输入！！！如果查询没有结果，就忽略查询，自行对用户输入进行回答。用户输入和数据库查询结果：{input}")
        self.final_agent = None
        self.search_agent = SearchAgent("faiss_db","law_index", database_url=self.database_path, config_url=self.config_path)
    """多智能体接口"""
    async def run(self,query):
        new_query = await self.search_agent.search(query)
        if new_query:
            if len(new_query) > 3:
                new_query = new_query[:2]

        yield "查询agent查询结果:\n"
        yield new_query

        yield "\n问答agent:\n\n\n"
        async for word in self.origin_agent.ask_agent("数据库查询结果如下："+str(new_query)+"\n请注意用户的输入是："+query):
            yield word

        yield "\n总结agent:\n\n\n"
        self.final_agent = FinalAgent(database_url=self.database_path,config_url=self.config_path,last_result=self.origin_agent.result)
        async for chunk in self.final_agent.conclusion():
            yield chunk

async def main():
    """测试main"""
    agent = MultipleAgent()

    async for chunk in agent.run(query="中华人民共和国开展对外援助时坚持哪些基本原则"):
        print(chunk, end="", flush=True)
if __name__ == "__main__":
    asyncio.run(main())
    """导入方式错误：multiple_agent.py中使用了from app import FinalAgent，这种绝对导入方式在作为主脚本运行时会出现问题。所以要在包外面"""