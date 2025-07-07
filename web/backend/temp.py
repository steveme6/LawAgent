# ipv4 10.4.185.251
# uvicorn server:app --host 0.0.0.0 --port 8000 --reload

from typing import Union
from fastapi import FastAPI
from pydantic import BaseModel
from collections import defaultdict, deque
from datetime import datetime


class MultiConversationManager:
    def __init__(self, max_length_per_talk=100):
        # 使用 defaultdict 自动创建新对话
        self.talks = defaultdict(lambda: deque(maxlen=max_length_per_talk))

    def add_message(self, talk_id: str, role: str, content: str):
        """向指定对话添加消息"""
        message = {
            "role": role,
            "content": content,
            # "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        self.talks[talk_id].append(message)

    def add_talk(self):
        lens = len(self.talks)
        id = f"talk_{lens + 1:03d}"
        self.talks[id] = deque(maxlen=100)
        print(f"新对话已创建: {id}")
        return id

    def get_talk_history(self, talk_id: str):
        """获取指定对话的历史记录"""
        return list(self.talks.get(talk_id))

    def list_all_talks(self):
        """返回所有对话ID列表"""
        return list(self.talks.keys())

    def clear_talk(self, talk_id: str):
        """清空指定对话"""
        if talk_id in self.talks:
            self.talks[talk_id].clear()

    def clear_all(self):
        """清空所有对话"""
        self.talks.clear()


# 初始化管理器
manager = MultiConversationManager(max_length_per_talk=50)

# 添加消息到不同对话
manager.add_message("talk_001", "user", "你好！")
manager.add_message("talk_001", "ai", "你好！有什么可以帮您？")
manager.add_message("talk_002", "user", "Python怎么学？")
manager.add_message("talk_002", "ai", "可以从基础语法开始学习。")
# 添加新的对话
talk_id = manager.add_talk()

# 查询对话历史
print("对话001历史:", manager.get_talk_history("talk_001"))
print("对话001历史:", manager.get_talk_history("talk_002"))
print("所有对话ID:", manager.list_all_talks())

app = FastAPI()

class Item(BaseModel):
    name: str
    price: float
    is_offer: Union[bool, None] = None

class Message(BaseModel):
    role: str
    content: str

# root/chat/talks/sessions
@app.get("/")
def get_root():
    return {"Hello": "World"}

# 获取对话目录
@app.get("/chat/talks")
def read_talks():
    talks =  []
    for talk_id in manager.list_all_talks():
        talks.append({
            "id": talk_id,
            "history": manager.get_talk_history(talk_id)[0].get("content")
        })
    return talks

# curl -X POST http://localhost:8000/chat/talks
# 创建一个新对话
@app.post("/chat/talks")
def create_talk():
    return manager.add_talk()

# 添加一个新消息到指定对话
@app.post("/chat/{talk_id}")
def add_message_to_talk(talk_id: str, message: Message):
    print("add_message_to_talk", talk_id, message.role, message.content)
    manager.add_message(talk_id, message.role, message.content)
    return {"message": "Message added successfully", "talk_id": talk_id}

# 获取指定对话的历史记录
@app.get("/chat/{talks_id}")
def read_item(talks_id: str):
    print("read_item", talks_id)
    return manager.get_talk_history(talks_id)


@app.put("/items/{item_id}")
def update_item(item_id: int, item: Item):
    return {"item_name": item.name, "item_id": item_id}