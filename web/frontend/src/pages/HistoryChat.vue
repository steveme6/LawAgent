<template>
  <div class="history-page">
    <h2>历史对话</h2>

    <!-- 滚动容器 -->
    <ul class="chat-list">
      <li
        v-for="(talk, talkKey) in chatStore.data"
        :key="talkKey"
        class="chat-card"
      >
        <RouterLink
          class="chat-content"
          :to="{ name: 'xiang', params: { id: talkKey } }"
        >
          <div class="question">
            <strong>问：</strong>{{ talk.record[0]?.content || '' }}
          </div>
          <div class="answer">
            <strong>答：</strong>
            {{
              talk.record[1]?.content
                ?.replace(/<think>.*?<\/think>/gs, '')   // 1. 去掉 <think> 段
                ?.trim()
                ?.slice(0, 100) || '暂无回答'
            }}…
          </div>
        </RouterLink>

        <button class="del-btn" @click="del(talkKey)">删除</button>
      </li>
    </ul>

    <!-- 空状态 -->
    <p v-if="!chatStore.data || !Object.keys(chatStore.data).length">
      暂无历史对话
    </p>
  </div>
</template>

<script setup lang="ts" name="History">
import { RouterLink } from 'vue-router';
import { useChatStore } from '@/store/Chat';

const chatStore = useChatStore();

/* 删除一条对话（原生 confirm，轻量） */
async function del(id: string) {
  if (!confirm('确认删除这条对话？')) return;

  try {
    // 1) 真正删除服务器数据
    await fetch(`http://localhost:8000/chat/${id}`, {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' }
    });

    // 2) 再删除本地 Pinia 数据，页面即时刷新
    delete chatStore.data[id];
  } catch (e) {
    alert('删除失败：' + e);
  }
}
</script>

<style scoped>
/* 整个历史页高度 = 左侧导航 82vh */
.history-page {
  height: 80vh;
  display: flex;
  flex-direction: column;
  padding: 16px;
  background: #ffffff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

h2 {
  margin: 0 0 12px;
  font-size: 18px;
  color: #303133;
}

/* 可滚动列表 */
.chat-list {
  flex: 1;
  overflow-y: auto;
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.chat-card {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 12px;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  background: #fafafa;
  transition: background 0.2s;
}

.chat-card:hover {
  background: #f2f6fc;
}

.chat-content {
  flex: 1;
  text-decoration: none;
  color: #303133;
  font-size: 14px;
  line-height: 1.4;
}

.question {
  font-weight: 600;
  margin-bottom: 4px;
}

.answer {
  color: #606266;
  word-break: break-all;
}

.del-btn {
  margin-left: 12px;
  padding: 4px 8px;
  font-size: 12px;
  border: none;
  border-radius: 4px;
  background: #f56c6c;
  color: #fff;
  cursor: pointer;
}

.del-btn:hover {
  background: #f78989;
}
</style>