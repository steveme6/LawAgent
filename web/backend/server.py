# ipv4 10.4.185.251
# uvicorn server:app --host 0.0.0.0 --port 8000 --reload

from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uuid
import asyncio


from web.backend.database import Database
from main import MultipleAgent

database = Database()

app = FastAPI()

origins = [
    "http://localhost:5173/",
]

# Allow these methods to be used
methods = ["GET", "POST", "PUT", "DELETE"]

# Only these headers are allowed
headers = ["Content-Type", "Authorization"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=methods,
    allow_headers=headers,
)

# root/chat/talks/sessions
@app.get("/")
async def get_root():
    return "Hello"

# 获取对话目录, 返回所有对话列表和其第一个问题
@app.get("/chat/talks")
async def read_talks():
    talks = database.fetch_talks()
    return talks

# 用户提出一个问题, 返回一个回答并存入数据库
@app.post("/chat/{talk_id}")
async def add_message_to_talk(talk_id: str, content: str):
    agent = MultipleAgent()
    message_id = uuid.uuid4().hex
    async def generate_with_save(talk_id, content):
        ans = ""
        try:
            async for chunk in agent.run(query=content):
                ans+=chunk  # 保存数据
                yield chunk  # 发送数据到客户端
        except:
            for i in range(5):
                ans+=f"Chunk {i} "
                yield f"Chunk {i} "
                await asyncio.sleep(1)
        database.add_message(talk_id, message_id, content, ans)
    return StreamingResponse(generate_with_save(talk_id, content), media_type="text/plain")

# 获取指定对话的历史记录
@app.get("/chat/{talks_id}/records")
async def read_item(talks_id: str):
    # 返回对应对话的所有session
    return database.fetch_message(talks_id)
