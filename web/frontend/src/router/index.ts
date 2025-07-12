import { createRouter,createWebHistory } from "vue-router";

import CreateNewChat from "@/pages/CreateNewChat.vue";
import History from "@/pages/HistoryChat.vue";
import ChatDetail from "@/pages/ChatDetail.vue";

const router=createRouter({
    history:createWebHistory(),
    routes:[
        {
            name:'wenda',
            path:'/createNewChat',
            component:CreateNewChat
        },
        {
            name:'lishi',
            path:'/history',
            component:History
        },
        {
            name:'xiang',
            path:'/chatDetail/:id',
            component:ChatDetail,
        },
        {
            path: '/',
            redirect: '/createNewChat' // 将根路径重定向
        },
    ]
})

export default router