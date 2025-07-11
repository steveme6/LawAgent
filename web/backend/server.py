# ipv4 10.4.185.251
# uvicorn server:app --host 0.0.0.0 --port 8000 --reload

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uuid
import asyncio


from main import MultipleAgent

app = FastAPI()

agent = MultipleAgent()

# 测试回答
markdown =  """
#### 以下是模板回答

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
    rows = agent.agent_db.select_all()
    records = dict()
    for r in rows:
        a_record = {'role': 'assistant', 'id': r[0], 'createAt': r[2], 'content': r[3]}
        user_record = {'role': 'user', 'id': r[0], 'createAt': r[2], 'content': 'null'}
        if r[1] in records:
            records[r[1]]['record'].append(a_record)
            records[r[1]]['record'].append(user_record)
        else:
            records[r[1]] = {
                'ques': r[3],
                'record': [a_record]
            }
            records[r[1]]['record'].append(user_record)
    return records

# 获取所有对话
@app.get("/chat/talk_id")
async def read_talk_id():
    talks = agent.agent_db.get_usernames()
    return talks

# 创建一个新的对话
@app.post("/chat/new_talks")
async def new_talk():
    # 对话id
    new_id = str(uuid.uuid4().hex)
    return new_id

# 用户提出一个问题, 返回一个回答并存入数据库
@app.post("/chat/{talk_id}")
async def add_message_to_talk(talk_id: str, request: Request):
    try:
        data = await request.json()
        content = data.get('content')
    except Exception as e:
        print(f"发生异常：{e}")
        return f"error: {e}"
    async def generate_with_save(talk_id, content):
        print(f"ques: {content}")
        try:
            talks = agent.agent_db.get_usernames()
            talks.append(new_id)
            if talk_id  in talks:
                async for chunk in agent.run(query=content, username=str(talk_id)):
                    for char in chunk:
                        yield char
                        # print(char)
                        await asyncio.sleep(0.05)  # 控制输出速度（可选）
                agent.save_history()
            else:
                print('error: 不允许的talk_id')
                yield 'error: 不允许的talk_id'
        except Exception as e:
            print(f"发生异常：{e}")
            for char in markdown:
                yield char
                await asyncio.sleep(0.05)  # 控制输出速度（可选）
        print('done')
    return StreamingResponse(generate_with_save(talk_id, content), media_type="text/plain")

# 获取指定对话的历史记录
@app.get("/chat/{talks_id}/records")
async def read_item(talks_id: str):
    # 返回对应对话的所有session
    return agent.agent_db.select_query(talks_id)
