import { defineStore } from "pinia";

export const useCreateNewChatStore=defineStore('createNewChat',{
    actions:{
        
    },
    state() {
        return {
            qanswer:[
                {id:0,ques:'',ans:''},
            ]
        }
    }
})