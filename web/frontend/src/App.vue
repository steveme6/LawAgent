<template>
  <div class="app">
    <Header/>
    <div class="content">
      <!-- 导航区 -->
      <div class="navigate">
        <RouterLink :to="{path:'/createNewChat'}">创建会话</RouterLink>
        <div class="history">
          <div class="history-title">历史记录</div>
          <ul>
            <li v-for="(talk, talkKey) in chatStore.data" :key="talkKey">
            <!-- record[0] 就是该会话的第一条消息 -->
            <RouterLink
              :to="{ name: 'xiang', params: { id: talkKey } }"
              >{{ talk.record[0]?.content }}
            </RouterLink>
            </li>
          </ul>
        </div>
        <RouterLink :to="{path:'/history'}">查看全部</RouterLink>
      </div>
      <!-- 展示区 -->
      <div class="main-content">
        <RouterView></RouterView>
         <!-- <Demo/> -->
      </div>
    </div>
  </div>
</template>

<script setup lang="ts" name="App">
  import { RouterView, RouterLink } from 'vue-router';
  import Header from './components/Header.vue';
  import { onMounted } from 'vue';
  import { useChatStore } from '@/store/Chat'
  import { useRouter } from 'vue-router' 
  const chatStore = useChatStore()
  const router    = useRouter() 
  onMounted(() => {chatStore.fetchMessages()})
</script>

<style scoped>
.app {
  display: flex;
  flex-direction: column;
  height:90%; 
  
}

.content {
  display: flex;
  flex: 1; /* 让内容区域占据剩余空间 */
}

.navigate {
  width: 20%; 
  background-color: #f0f0f0; 
  border-radius: 5px;
  border: 1px solid #000; /* 边框 */
  padding: 10px;
  height: 85vh;
  margin-bottom: 10px;
}

.main-content {
  width: 80%; 
  background-color: #e0e0e0; 
  border-radius: 5px;
  border: 1px solid #000; 
  padding: 10px;
  height: 85vh;
}

.history {
  border-top: 1px solid #000; /* 顶部边框 */
  padding-top: 10px;
  position: relative;
}

.history-title {
  font-weight: bold;
  margin-bottom: 5px;
}

ul {
  list-style-type: none; /* 去除小黑点 */
  padding: 0;
  margin: 0;
}

li {
  margin-bottom: 5px;
}
</style>