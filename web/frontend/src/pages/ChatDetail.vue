<template>
  <div class="main-content">
    <div class="center-contain">
      <Demo :key="chatId" :chatId="chatId"/>
    </div>
  </div>
</template>

<script setup lang="ts" name="chatDetail">
import Demo from '@/demo(1).tsx'
import { useRoute } from 'vue-router';
import { computed } from 'vue'

const route = useRoute()
const chatId = computed(() => route.params.id as string);
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