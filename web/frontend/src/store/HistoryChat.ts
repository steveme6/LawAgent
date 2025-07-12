import { defineStore } from "pinia";

export const useHistortChatStore=defineStore('historyChat',{
    actions:{
        
    },
    state() {
        return {
            Hchat:[
                    {
                        id:'talk_001',
                        defaultMessage:[
                        {
                            role: 'system',
                            id: '1',
                            createAt: 1715676751919,
                            content: "欢迎来到法律法规知识问答系统！",
                        },
                        {
                            role: 'user',
                            id: '1',
                            createAt: 1715676751919,
                            content: "哈哈哈",
                        },
                    ],
                },
                {
                        id:'talk_002',
                        defaultMessage:[
                        {
                            role: 'system',
                            id: '1',
                            createAt: 1715676751919,
                            content: "欢迎来到法律法规知识问答系统！",
                        },
                        {
                            role: 'user',
                            id: '1',
                            createAt: 1715676751919,
                            content: "你是笨蛋",
                        },
                    ],
                },
            ]
        }
    }
})