// src/utils/newTalkId.ts
export async function getNewTalkId(): Promise<string> {
  const res = await fetch('http://localhost:8000/chat/new_talks', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({})
  })
  const id = await res.text()   // ← 用 text() 而不是 json()
  if (!id) throw new Error('接口未返回 id')
  return id
}