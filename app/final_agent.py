import asyncio
from app.origin_agent import OriginAgent

class FinalAgent(OriginAgent):
    def __init__(self, last_result:str,prompt="你是一个总结智能体，你需要总结传递给你的内容\n\n{input}"):
        super().__init__(prompt)
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