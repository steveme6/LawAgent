# ipv4 10.4.185.251
# uvicorn server:app --host 0.0.0.0 --port 8000 --reload

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uuid
import asyncio
from collections import defaultdict


from main import MultipleAgent
from app.agent_db import AgentDB

app = FastAPI()

agent_db = AgentDB('./history_db/multiply.db/')

# 测试回答
markdown =  """
#### 以下是模板回答
</think>
你好
<think >

This is a **bold** text and this is *italic*.

##### Code block example:

```python
def hello():
    print("Hello, world!")
```

> This is a quote.

- List item 1
- List item 2
"""

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 用于存储新申请的talk_id
new_id = ''

# 根目录
@app.get("/")
async def get_root():
    return "Hello World"

# 获取所有对话信息
# records数据结构
# {
#     'talk_id' : id,
#     {
#         'ques' : ques, # 第一个问题
#         'record' : []
#     }
# }
@app.get("/chat/talks")
async def read_talks():
    rows = agent_db.select_all()
    # return rows
    records = dict()
    for r in rows:
        a_record = {'role': 'assistant', 'id': r[0], 'createAt': r[2], 'content': "\n\n#### 问答agent:\n\n"+r[5]+"\n\n#### 总结agent:\n\n"+r[6]}
        user_record = {'role': 'user', 'id': r[0], 'createAt': r[2], 'content': r[3]}
        if r[1] in records:
            records[r[1]]['record'].append(user_record)
            records[r[1]]['record'].append(a_record)
        else:
            records[r[1]] = {
                'ques': r[3],
                'record': [user_record]
            }
            records[r[1]]['record'].append(a_record)
    return records

# 获取所有对话
@app.get("/chat/talk_id")
async def read_talk_id():
    talks = agent_db.get_usernames()
    return talks

# 创建一个新的对话
@app.post("/chat/new_talks")
async def new_talk():
    # 对话id
    global new_id
    new_id = str(uuid.uuid4().hex)
    return new_id

# 用户提出一个问题, 返回一个回答并存入数据库
@app.post("/chat/{talk_id}")
async def add_message_to_talk(talk_id: str, request: Request):
    new_agent = MultipleAgent()
    print(talk_id)
    global new_id
    try:
        data = await request.json()
        content = data.get('content')
    except Exception as e:
        print(f"发生异常：{e}")
        return f"error: {e}"
    async def generate_with_save(talk_id : str, content):
        print(f"ques: {content}")
        try:
            talks = new_agent.agent_db.get_usernames()
            talks.append(new_id)
            # print(f"talk_id : {talk_id}")
            # print(f"new_id : {new_id}")
            print(talks)
            if talk_id  in talks:
                async for chunk in new_agent.run(query=content, username=str(talk_id)):
                    # for char in chunk:
                        # yield char
                    if chunk == '<think>':
                        chunk = '<!--'
                    elif chunk == '</think>':
                        chunk = '-->'
                    yield chunk
                    await asyncio.sleep(0.05)  # 控制输出速度（可选）
                new_agent.save_history()
            else:
                print('error: 不允许的talk_id')
                yield 'error: 不允许的talk_id'
        except Exception as e:
            print(f"发生异常：{e}")
            for char in markdown:
                yield char
                await asyncio.sleep(0.05)  # 控制输出速度（可选）
                # agent.agent_db.insert_history(talk_id, content, "test", "test", "test")
        print('done')
    return StreamingResponse(generate_with_save(talk_id, content), media_type="text/plain")

# 删除一个对话
@app.delete("/chat/{talk_id}")
async def delete_message_from_talk(talk_id: str):
    print(talk_id)
    agent_db.delete_history(talk_id)
    return True

# 获取指定对话的历史记录
@app.get("/chat/{talks_id}/records")
async def read_item(talks_id: str):
    # 返回对应对话的所有session
    return agent_db.select_query(talks_id)
