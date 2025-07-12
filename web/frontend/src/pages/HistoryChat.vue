<template>
    <div>全部历史
        <li v-for="(talk, talkKey) in chatStore.data" :key="talkKey">
      <!-- record[0] 就是该会话的第一条消息 -->
        <RouterLink
        :to="{ name: 'xiang', params: { id: talkKey } }"
      >
        {{ talk.record[0]?.content }}
      </RouterLink>
    </li>
    </div>
</template>

<script setup lang="ts" name="history">
    import { useHistortChatStore } from '@/store/HistoryChat';
    import { RouterView, RouterLink } from 'vue-router';
    import { onMounted } from 'vue'
    import { useChatStore } from '@/store/Chat'
    const historychat=useHistortChatStore()
    const chatStore = useChatStore()
    onMounted(() => {chatStore.fetchMessages()})
</script>

<style scoped>
.chat{
    list-style-type: none;
}
</style>