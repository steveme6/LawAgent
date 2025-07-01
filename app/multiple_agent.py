import asyncio

from app import FinalAgent
from app import OriginAgent

class MultipleAgent():
    def __init__(self):
        self.origin_agent = OriginAgent()
        self.final_agent = None
    """多智能体接口"""
    async def run(self,query):
        async for word in self.origin_agent.ask_agent(query):
            yield word
        yield "\n总结agent:\n"
        self.final_agent = FinalAgent(self.origin_agent.result)
        async for chunk in self.final_agent.conclusion():
            yield chunk
async def main():
    """<UNK>"""
    agent = MultipleAgent()
    async for chunk in agent.run(query="你好，我叫小明，英语考了20分，我该怎么办"):
        print(chunk, end="", flush=True)
if __name__ == "__main__":
    asyncio.run(main())