<template>
  <div class="main-content">
    <div class="center-containe">
      <Demo/>
    </div>
  </div>
</template>

<script setup lang="ts" name="createNewChat">
  import Demo from '@/demo.tsx'
  import { getNewTalkId } from '@/utils/newTalkId';
  import { onMounted } from 'vue';
  let newId=' '

  const handleCreate = async () => {
  try {
    newId = await getNewTalkId()
    console.log('新会话 id：', newId)
    // 此处你可以把 id 存 Pinia、发事件、或自己跳转
  } catch (e) {
    console.error(e)
  }
}
  // onMounted(() => {handleCreate()})
</script>

<style scoped>
.main-content {
  width: 80%; /* 展示区宽度 */
  background-color: #eeeeee;
  border-radius: 5px;
  border: 1px solid #000;
  padding: 10px;
  box-sizing: border-box; /* 确保内边距和边框包含在宽度内 */
}

.center-containe {
  width: 100%; /* 占满整个展示区 */
  display: flex; /* 使用 Flexbox 布局 */
  justify-content: center; /* 水平居中 */
  align-items: center; /* 垂直居中 */
  box-sizing: border-box; /* 确保内边距和边框包含在宽度内 */
}
</style>