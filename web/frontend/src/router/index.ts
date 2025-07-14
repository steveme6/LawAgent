import { createRouter,createWebHistory } from "vue-router";

import CreateNewChat from "@/pages/CreateNewChat.vue";
import History from "@/pages/HistoryChat.vue";
import ChatDetail from "@/pages/ChatDetail.vue";
import Empty from "@/pages/Empty.vue";

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
            name:'kong',
            path: '/empty',
            component: Empty // 空组件即可
        },
        {
            path: '/',
            redirect: '/createNewChat' // 将根路径重定向
        },
    ]
})

export default router