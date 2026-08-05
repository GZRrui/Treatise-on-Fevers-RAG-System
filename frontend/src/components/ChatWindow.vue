<template>
  <div class="chat-window">
    <div class="messages">
      <div
        v-for="(message, index) in messages"
        :key="index"
        :class="['message', message.role]"
      >
        <div class="message-avatar">
          {{ message.role === 'user' ? '👤' : '📜' }}
        </div>
        <div class="message-content">
          <div class="message-text" v-html="formatMessage(message.content)"></div>
          <div v-if="message.sources && message.sources.length > 0" class="sources">
            <div class="sources-title">📚 引用条文:</div>
            <div
              v-for="(source, i) in message.sources"
              :key="i"
              class="source-item"
            >
              <span class="source-badge">{{ source.chapter }} 第{{ source.standard_id }}条</span>
              <span class="source-text">{{ source.text.substring(0, 80) }}...</span>
            </div>
          </div>
          <div class="message-time">{{ message.time }}</div>
        </div>
      </div>

      <div v-if="isLoading" class="message assistant loading">
        <div class="message-avatar">📜</div>
        <div class="message-content">
          <div class="loading-dots">
            <span></span><span></span><span></span>
          </div>
        </div>
      </div>
    </div>

    <div class="input-area">
      <input
        v-model="inputText"
        type="text"
        placeholder="请输入您的问题..."
        :disabled="isLoading"
        @keyup.enter="sendMessage"
      />
      <button @click="sendMessage" :disabled="isLoading || !inputText.trim()">
        {{ isLoading ? '思考中...' : '发送' }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { qaApi, type ArticleSource } from '../api/qa'

interface Message {
  role: 'user' | 'assistant'
  content: string
  sources?: ArticleSource[]
  time: string
}

const inputText = ref('')
const isLoading = ref(false)
const messages = reactive<Message[]>([])

const sendMessage = async () => {
  const text = inputText.value.trim()
  if (!text || isLoading.value) return

  // 添加用户消息
  messages.push({
    role: 'user',
    content: text,
    time: new Date().toLocaleTimeString(),
  })

  inputText.value = ''
  isLoading.value = true

  try {
    const response = await qaApi.ask({ query: text, top_k: 5 })

    if (response.code === 200) {
      messages.push({
        role: 'assistant',
        content: response.data.answer,
        sources: response.data.sources,
        time: new Date().toLocaleTimeString(),
      })
    } else {
      messages.push({
        role: 'assistant',
        content: `抱歉发生了错误: ${response.message}`,
        time: new Date().toLocaleTimeString(),
      })
    }
  } catch (error: any) {
    console.error('QA Error:', error)
    let errorMessage = '未知错误'
    if (error) {
      if (typeof error === 'string') {
        errorMessage = error
      } else if (error.message) {
        errorMessage = error.message
      } else if (error.response?.data?.message) {
        errorMessage = error.response.data.message
      } else if (error.statusText) {
        errorMessage = error.statusText
      } else {
        errorMessage = JSON.stringify(error)
      }
    }
    messages.push({
      role: 'assistant',
      content: `抱歉发生了错误: ${errorMessage}`,
      time: new Date().toLocaleTimeString(),
    })
  } finally {
    isLoading.value = false
  }
}

const formatMessage = (content: string) => {
  // 简单的 Markdown 转换
  return content
    .replace(/\n/g, '<br>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
}
</script>

<style scoped>
.chat-window {
  width: 100%;
  max-width: 800px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
  display: flex;
  flex-direction: column;
  height: calc(100vh - 200px);
  max-height: 700px;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.message {
  display: flex;
  gap: 1rem;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.message.user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
  flex-shrink: 0;
}

.message.assistant .message-avatar {
  background: #e8f5e9;
}

.message.user .message-avatar {
  background: #e3f2fd;
}

.message-content {
  flex: 1;
  max-width: 80%;
}

.message-text {
  padding: 0.8rem 1rem;
  border-radius: 12px;
  line-height: 1.6;
  font-size: 0.95rem;
}

.message.assistant .message-text {
  background: #f5f5f5;
  border-top-left-radius: 4px;
}

.message.user .message-text {
  background: #667eea;
  color: white;
  border-top-right-radius: 4px;
}

.sources {
  margin-top: 0.5rem;
  padding: 0.8rem;
  background: #f8f9fa;
  border-radius: 8px;
  font-size: 0.85rem;
}

.sources-title {
  font-weight: 600;
  margin-bottom: 0.5rem;
  color: #666;
}

.source-item {
  padding: 0.3rem 0;
  border-bottom: 1px solid #eee;
}

.source-item:last-child {
  border-bottom: none;
}

.source-badge {
  display: inline-block;
  background: #e8f5e9;
  color: #2e7d32;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  font-size: 0.8rem;
  margin-right: 0.5rem;
}

.source-text {
  color: #666;
}

.message-time {
  font-size: 0.75rem;
  color: #999;
  margin-top: 0.3rem;
}

.loading-dots {
  display: flex;
  gap: 4px;
  padding: 0.8rem 1rem;
}

.loading-dots span {
  width: 8px;
  height: 8px;
  background: #999;
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out both;
}

.loading-dots span:nth-child(1) { animation-delay: -0.32s; }
.loading-dots span:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

.input-area {
  display: flex;
  gap: 0.5rem;
  padding: 1rem;
  border-top: 1px solid #eee;
  background: #fafafa;
  border-radius: 0 0 12px 12px;
}

.input-area input {
  flex: 1;
  padding: 0.8rem 1rem;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 1rem;
  outline: none;
  transition: border-color 0.2s;
}

.input-area input:focus {
  border-color: #667eea;
}

.input-area button {
  padding: 0.8rem 1.5rem;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  cursor: pointer;
  transition: background 0.2s;
}

.input-area button:hover:not(:disabled) {
  background: #5a6fd6;
}

.input-area button:disabled {
  background: #ccc;
  cursor: not-allowed;
}
</style>