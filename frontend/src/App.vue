<script setup lang="ts">
import { onMounted, ref } from 'vue'
import axios from 'axios'

// 1. 定义接口：告诉 TS 后端返回的数据长什么样
interface AnalysisResult {
  length: number
  is_question: boolean
  sentiment: string
  keywords: string[]
  ai_reply: string
}
interface HistoryRecord {
  id: number
  ai_reply: string
  sentiment: string
  text_content: string
  word_count: number
}

// 2. 定义状态：明确指定 result 的类型
const inputText = ref<string>('')
const result = ref<AnalysisResult | null>(null) // 可能是结果，也可能是 null
const streamMessage = ref('') // 专门存流式回复
const loading = ref<boolean>(false)
const historyList = ref<HistoryRecord[]>([])

// 发送请求
const analyzeText = async () => {
  if (!inputText.value) return

  loading.value = true
  result.value = null // 清空旧结果

  try {
    const response = await fetch('http://127.0.0.1:8000/analyze', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ text: inputText.value })
    })

    if (!response.ok) {
      throw new Error('网络请求失败')
    }

    // 这里 TS 知道 data 就是 AnalysisResult 类型
    const data: AnalysisResult = await response.json()
    result.value = data

  } catch (error) {
    console.error('出错了:', error)
    alert('连接后端失败，请检查后端终端是否开启！')
  } finally {
    loading.value = false
    await fetchHistory()
  }
}

// --- 新增：流式聊天函数 ---
const startChat = async () => {
  if (!inputText.value) return

  // 清空之前的状态
  streamMessage.value = ''
  result.value = null // 把之前的分析报告隐藏掉，避免干扰
  loading.value = true

  try {
    const response = await fetch('http://127.0.0.1:8000/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: inputText.value })
    })

    if (!response.ok) throw new Error('网络请求失败')

    // --- 关键黑魔法：读取流 ---
    if (!response.body) return
    const reader = response.body.getReader()
    const decoder = new TextDecoder() // 用来把二进制转成文字

    // 死循环读取，直到读完
    while (true) {
      const { done, value } = await reader.read()
      if (done) break // 读完了，跳出循环

      // 把读到的这一小块二进制解码成文字
      const chunk = decoder.decode(value)

      // 拼接到界面上 (这就是打字机效果的来源！)
      streamMessage.value += chunk
    }

  } catch (error) {
    console.error('聊天出错:', error)
    streamMessage.value = '哎呀，聊天断线了！'
  } finally {
    loading.value = false
    await fetchHistory()
  }
}

const fetchHistory = async () => {
  try {
    const res = await fetch('http://127.0.0.1:8000/history')
    console.log(res)
    if (!res.ok) return
    const data = await res.json()
    historyList.value = data
  } catch (error) {

  }
}

onMounted(() => {
  fetchHistory()
})
</script>

<template>
  <div class="container">
    <h1>🤖 AI 全栈文本分析器 (DB版)</h1>

    <div class="card input-section">
      <textarea v-model="inputText" placeholder="在这里输入你想分析的句子..." rows="4"></textarea>

      <button @click="analyzeText" :disabled="loading">
        {{ loading ? 'AI 正在思考中...' : '开始分析 ✨' }}
      </button>
      <button @click="startChat" :disabled="loading" style="background-color: #3498db; margin-top: 10px;">
        {{ loading ? 'AI 正在输出...' : '💬 随便聊聊 (流式)' }}
      </button>
    </div>

    <div v-if="streamMessage" class="card chat-box">
      <h3>💬 实时对话</h3>
      <p style="white-space: pre-wrap;">{{ streamMessage }}</p>
    </div>

    <div v-if="result" class="result-box">
      <h3>📊 本次分析报告</h3>
      <p><strong>字数统计：</strong> {{ result.length }}</p>
      <p><strong>情感倾向：</strong> {{ result.sentiment }}</p>
      <div class="ai-reply">
        <strong>🤖 AI 回复：</strong> {{ result.ai_reply }}
      </div>
    </div>

    <div class="history-section" v-if="historyList.length > 0">
      <h2>📜 最近的分析记录</h2>
      <div class="history-list">
        <div v-for="item in historyList" :key="item.id" class="history-item">
          <div class="item-header">
            <span class="tag-id">#{{ item.id }}</span>
            <span class="tag-sentiment">{{ item.sentiment }}</span>
            <span class="tag-count">{{ item.word_count }} 字</span>
          </div>
          <div class="item-content">
            <p class="user-text"><strong>我：</strong>{{ item.text_content }}</p>
            <p class="ai-text"><strong>AI：</strong>{{ item.ai_reply }}</p>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<style scoped>
.container {
  max-width: 600px;
  margin: 50px auto;
  font-family: Arial, sans-serif;
  text-align: center;
}

textarea {
  width: 100%;
  padding: 10px;
  border-radius: 8px;
  border: 1px solid #ddd;
  margin-bottom: 10px;
  font-size: 16px;
  /* 禁止拖拽大小 */
  resize: vertical;
}

button {
  background-color: #42b983;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 20px;
  font-size: 16px;
  cursor: pointer;
  transition: 0.3s;
}

button:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

button:hover:not(:disabled) {
  background-color: #3aa876;
}

.result-box {
  margin-top: 30px;
  padding: 20px;
  background-color: #f0f9f4;
  border-radius: 12px;
  text-align: left;
  border: 1px solid #42b983;
}

.tags {
  margin: 10px 0;
}

.tag {
  background-color: #e1f5fe;
  color: #0288d1;
  padding: 2px 8px;
  border-radius: 4px;
  margin-right: 5px;
  font-size: 0.9em;
}

.ai-reply {
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid #ddd;
  color: #555;
}
</style>
