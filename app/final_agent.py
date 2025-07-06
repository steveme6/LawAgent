import asyncio
from app.origin_agent import OriginAgent

class FinalAgent(OriginAgent):
    def __init__(self,database_url:str,config_url:str, last_result:str,prompt="上一输入{input}\n\n你是一个总结智能体，你需要总结传递给你的内容,记住你只需要总结关键部分，不需要在重复上次输入"):
        super().__init__(config_url=config_url,database_url=database_url,prompt=prompt)
        self.last_result = last_result
    """总结接口"""
    async def conclusion(self):
        async for chunk in self.chain.astream({"input": self.last_result}):
            yield chunk
"""测试"""
async def main():
    """总结"""
    agent = FinalAgent(last_result="我叫小李，喜欢英语")
    async for chunk in agent.conclusion():
        print(chunk, end="", flush=True)
if __name__ == "__main__":
    asyncio.run(main())