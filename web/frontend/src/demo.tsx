import { Chat, Radio, RadioGroup } from '@kousum/semi-ui-vue';
import { defineComponent, ref } from 'vue';
import { getNewTalkId } from '@/utils/newTalkId';
import { onMounted } from 'vue';

// import { useHistortChatStore } from './store/HistoryChat';
// const historychat = useHistortChatStore();
// const message = ref(historychat.defaultMessage);

const defaultMessage = [//初始聊天框内容
  {
    role: 'system',
    id: '1',
    createAt: 1715676751919,
    content: "欢迎来到法律法规知识问答系统！",
  }
];

const roleInfo = {
  user: {
    name: 'User',
    avatar: 'https://lf3-static.bytednsdoc.com/obj/eden-cn/ptlz_zlp/ljhwZthlaukjlkulzlp/docs-icon.png'
  },
  assistant: {
    name: 'Assistant',
    avatar: 'https://lf3-static.bytednsdoc.com/obj/eden-cn/ptlz_zlp/ljhwZthlaukjlkulzlp/other/logo.png'
  },
  system: {
    name: 'System',
    avatar: 'https://lf3-static.bytednsdoc.com/obj/eden-cn/ptlz_zlp/ljhwZthlaukjlkulzlp/other/logo.png'
  }
}

const commonOuterStyle = {
  // border: '1px solid var(--semi-color-border)',
  borderRadius: '16px',
  margin: '0px 0px',
  height: '75vh',
  // padding: '16px',
  width: '800px',
}

let id = 0;

function getId() {
  return `id-${id++}`
}

const uploadProps = { action: 'https://api.semi.design/upload' }
const uploadTipProps = { content: '自定义上传按钮提示信息' }

const DefaultChat = defineComponent(() => {

  const message = ref(defaultMessage);
  const mode = ref('bubble');
  const align = ref('leftRight');

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
  onMounted(() => {handleCreate()})
  const onMessageSend = async (content, attachment) => {
    try {
      const assistantMessageId = getId();
      const assistantMessage = {
        role: 'assistant',
        id: assistantMessageId,
        createAt: Date.now(),
        content: '',
      };
      message.value = [...message.value, assistantMessage];

      // 发起流式请求
      newId = newId.replace(/^"(.*)"$/, '$1');
      let web='http://47.94.240.154:8000/chat/'+newId
      console.log(web)
      // console.log(`http://47.94.240.154:8000/chat/${newId}`)
      const response = await fetch(`http://47.94.240.154:8000/chat/${newId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ content }),
      });

      if (!response.ok) {
        throw new Error('Network response was not ok');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');

      const read = () => {
        reader.read().then(({ done, value }) => {
          if (done) {
            console.log('流式数据接收完成');
            return;
          }
          const chunk = decoder.decode(value, { stream: true });
          console.log('接收到数据块:', chunk);

          // 更新助手消息内容
          const index = message.value.findIndex(m => m.id === assistantMessageId);
          if (index !== -1) {
            message.value[index].content += chunk;
          }

          read();
        });
      };

      read();
    } catch (error) {
      console.error('请求出错:', error);
    }
  };
  

  const onChatsChange = (chats) => {
    message.value = chats;
  };

  const onMessageReset = (e) => {
    setTimeout(() => {
      const lastMessage = message.value[message.value.length - 1];
      const newLastMessage = {
        ...lastMessage,
        status: 'complete',
        content: 'This is a mock reset message.',
      }
      message.value = [...message.value.slice(0, -1), newLastMessage]
    }, 200);
  }
  
  return () => (
    <>
      <Chat
        key={align.value + mode.value}
        align={align.value}
        mode={mode.value}
        uploadProps={uploadProps}
        style={commonOuterStyle}
        chats={message.value}
        roleConfig={roleInfo}
        onChatsChange={onChatsChange}
        onMessageSend={onMessageSend}
        onMessageReset={onMessageReset}
        uploadTipProps={uploadTipProps}
        placeholder="请输入内容"
        // autoFocus={true}
        // autoScrollToBottom={true}
      />
    </>
  )
})

export default DefaultChat