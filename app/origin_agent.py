import os
import uuid
import sqlite3
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableWithMessageHistory,RunnableConfig
from langchain_ollama import ChatOllama
import asyncio
from langchain_community.chat_message_histories import SQLChatMessageHistory
from app.config_parser import get_config
"""基本agent"""
class OriginAgent:
    def __init__(self,database_url:str,config_url:str,prompt="你是一个智能助手，使用用中文回答\n\n{input}"):
        """初始化聊天模型"""
        baseurl=get_config("ollama", "BASE_URL", config_url)
        model=get_config("ollama", "MODEL", config_url)
        self.chat_model = ChatOllama(
            base_url=baseurl,
            model=model,
            num_ctx=8192
        )
        self.result = ""
        self.prompt = ChatPromptTemplate.from_template(prompt)
        self.parser = StrOutputParser()

        """简单总结链"""
        self.chain = self.prompt | self.chat_model | self.parser
        """无解析器链"""
        self.no_parser_chain = self.prompt | self.chat_model
        """对话id"""
        self.config = RunnableConfig(configurable={"session_id": str(uuid.uuid4())})

        """sqlite3数据库"""
        self.database = database_url

        """历史链"""
        self.runnable_with_history = RunnableWithMessageHistory(
            self.chain,
            self.get_session_history
        )


    """可调用问答接口"""
    async def ask_agent(self, input_text: str):
        """流式响应生成器"""
        for chunk in self.runnable_with_history.stream({"input": input_text},config=self.config):
            self.result+=chunk
            yield chunk

    def get_session_history(self,session_id):
        """获取历史"""
        return SQLChatMessageHistory(session_id=session_id,connection=f'sqlite:///{self.database}')

    """给予final_agent的输入"""
    def get_session_history2(self,session_id):
        return self.result

    def delete_history(self,session_id):
        """删除历史"""
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM history WHERE session_id=?", (session_id,))
        conn.commit()
        conn.close()
    def return_chain(self):
        return self.chain
    def return_no_parser_chain(self):
        return self.no_parser_chain
"""测试main"""
async def main():
    config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../config/config.ini"))
    database_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../history_db/history.db"))
    client = OriginAgent(config_url=config_path,database_url=database_path)
    while True:
        print("\nQuery (type 'quit' to exit):")
        try:
            query = input("> ").strip()
            if query == "quit":
                break
            async for word in client.ask_agent(query):
                print(word, end="", flush=True)  # 逐词打印
        except Exception as e:
            print(e)


if __name__ == "__main__":
    asyncio.run(main())

