// src/store/chat.ts
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useChatStore = defineStore('chat', () => {
  /* 1. 定义状态：data 用来存放接口返回的 {"talk_001":{...}, "talk_002":{...}} */
  const data = ref<Record<string, {
    ques: string
    record: { role:string, content:string }[]
  }>>({})

  /* 2. 定义 action：去后端拉一次数据 */
  const fetchMessages = async () => {
    try {
      const res   = await fetch('http://47.94.240.154:8000/chat/talks')
      data.value  = await res.json()
    //   console.log('store 里的 data 已更新：', data.value)
    } catch (e) {
      console.error(e)
    }
  }

  /* 3. 把状态和方法都导出去，任何地方都能用 */
  return { data, fetchMessages }
})