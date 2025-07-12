import { createApp } from 'vue'
import App from './App.vue'
//第二步：引入pinia
import { createPinia } from 'pinia'
import router from './router'

const app=createApp(App)
//第二步：创建pinia
const pinia=createPinia()
//第三步：安装pinia
app.use(pinia)
app.use(router)
app.mount('#app')