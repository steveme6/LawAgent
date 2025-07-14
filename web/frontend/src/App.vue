<template>
  <div class="app">
    <Header/>
    <div class="content">
      <!-- 导航区 -->
      <div class="navigate">
        <RouterLink 
        :to="{path:'/createNewChat'}"
        @click="forceCreateNewChat"
        >创建会话</RouterLink>
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
        <RouterView :key="routeKey"></RouterView>
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
  import { useRouter,useRoute } from 'vue-router' 
  import { nextTick } from 'vue';
  import { ref, watch } from 'vue';

  const chatStore = useChatStore()
  const router    = useRouter() 
  const route = useRoute();
  const routeKey = ref(route.fullPath);
  onMounted(() => {chatStore.fetchMessages()})

function forceCreateNewChat() {
  if (route.path === '/createNewChat') {
    // 1）先把 key 换成带时间戳的新值，强制销毁组件
    routeKey.value = `/createNewChat?_t=${Date.now()}`;
    // console.log('CreateNewChat 组件 mounted', Date.now()); 
    // 2）用 replace 跳中转（不留历史记录）
    router.replace('/empty');
    // 3）下一帧再 replace 回来，此时组件会重新挂载
    nextTick(() => {
      router.replace(routeKey.value);
    });
  } else {
    // 不在当前页就正常 push
    router.push('/createNewChat');
  }
}

watch(
  () => route.fullPath,
  (newPath) => {
    if (newPath === '/createNewChat') {
      routeKey.value = `/createNewChat?_${Date.now()}`;
    } else {
      routeKey.value = newPath;
    }
  }
);
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

.main-content {
  width: 80%; 
  background-color: #e0e0e0; 
  border-radius: 5px;
  border: 1px solid #000; 
  padding: 10px;
  height: 85vh;
}

/* ========= 导航区整体 ========= */
.navigate {
  border-radius: 5px;
  border: 1px solid #000; /* 边框 */
  width: 240px;               /* 固定宽度，比 20% 更稳 */
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,.08);
  padding: 20px;
  height: 82vh;
  display: flex;
  flex-direction: column;
  gap: 16px;                  /* 三个区块之间留空 */
}

/* 通用按钮样式：创建会话 / 查看全部 */
.navigate > a {
  display: block;
  padding: 10px 16px;
  background: #409eff;
  color: #fff;
  border-radius: 6px;
  text-align: center;
  font-size: 14px;
  text-decoration: none;
  transition: background .2s;
}
.navigate > a:hover {
  background: #66b1ff;
}

/* ========= 历史记录区块 ========= */
.history {
  flex: 1;                    /* 占满剩余高度 */
  display: flex;
  flex-direction: column;
  overflow: hidden;           /* 让 ul 滚动而不是整个区域 */
}

.history-title {
  font-weight: 600;
  font-size: 15px;
  color: #ffffff;
  margin-bottom: 8px;
}

.history ul {
  flex: 1;
  overflow-y: auto;           /* 超出时滚动 */
  list-style: none;
  margin: 0;
  padding: 0;
  font-size: 13px;
}

.history li a {
  display: block;
  padding: 6px 8px;
  color: #606266;
  border-radius: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  text-decoration: none;
  transition: background .15s;
}
.history li a:hover {
  background: #f2f6fc;
  color: #409eff;
}
</style>