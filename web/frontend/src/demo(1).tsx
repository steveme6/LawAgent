import { Chat, Radio, RadioGroup } from '@kousum/semi-ui-vue';
import { defineComponent, ref,onMounted,type PropType  } from 'vue';//

const defaultMessage = [
  {
    role: 'system',
    id: '1',
    createAt: 1715676751919,
    content: "欢迎来到法律法规知识问答系统！",
  },
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
  borderRadius: '16px',
  margin: '0px 0px',
  height: '75vh',
  width: '800px',
}

let id = 0;

function getId() {
  return `id-${id++}`
}

const uploadProps = { action: 'https://api.semi.design/upload' }
const uploadTipProps = { content: '自定义上传按钮提示信息' }

const DefaultChat = defineComponent({
  props: {
    chatId: {
      type: String as PropType<string>,
      required: true,
    }
  },
  
  setup(props) {
    console.log(props.chatId)
    const message = ref(defaultMessage);
    const mode = ref('bubble');
    const align = ref('leftRight');

    const fetchMessages = async () => {//网页取数据
    try {
    const response = await fetch('http://localhost:8000/chat/talks');
    const data = await response.json();
    const records = data[props.chatId].record; // 假设你想要获取talk_001的记录
    message.value = records;
  } catch (error) {
    console.error('Error fetching messages:', error);
  }
};

onMounted(() => {
  fetchMessages();
});

const onMessageSend = async (content, attachment) => {
    try {
      // 添加用户消息
      // const userMessage = {
      //   role: 'user',
      //   id: getId(),
      //   createAt: Date.now(),
      //   content,
      // };
      // message.value = [...message.value, userMessage];

      // 添加一个空的助手消息，用于流式更新
      //console.log(message)
      const assistantMessageId = getId();
      const assistantMessage = {
        role: 'assistant',
        id: assistantMessageId,
        createAt: Date.now(),
        content: '',
      };
      message.value = [...message.value, assistantMessage];

      // 发起流式请求
      const response = await fetch('http://47.94.240.154:8000/chat/talk_001', {
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
        />
      </>
    )
  }
})

export default DefaultChat