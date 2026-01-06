<script setup lang="ts">
import { ref } from 'vue'
import axios from 'axios'

// 1. 定义接口：告诉 TS 后端返回的数据长什么样
interface AnalysisResult {
  length: number
  is_question: boolean
  sentiment: string
  keywords: string[]
  ai_reply: string
}

// 2. 定义状态：明确指定 result 的类型
const inputText = ref<string>('')
const result = ref<AnalysisResult | null>(null) // 可能是结果，也可能是 null
const loading = ref<boolean>(false)

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
  }
}
</script>

<template>
  <div class="container">
    <h1>🤖 AI 全栈文本分析器 (TS版)</h1>

    <div class="card">
      <textarea v-model="inputText" placeholder="在这里输入你想分析的句子..." rows="4"></textarea>

      <button @click="analyzeText" :disabled="loading">
        {{ loading ? 'AI 正在思考中...' : '开始分析 ✨' }}
      </button>
      <button @click="">ceshi(改天练习调用 get返回 hello world)</button>
    </div>

    <div v-if="result" class="result-box">
      <h3>📊 分析报告</h3>
      <p><strong>字数统计：</strong> {{ result.length }} 个字符</p>
      <p><strong>情感倾向：</strong> {{ result.sentiment }}</p>
      <p><strong>是否提问：</strong> {{ result.is_question ? '是' : '否' }}</p>
      <div class="tags">
        <strong>关键词：</strong>
        <span v-for="tag in result.keywords" :key="tag" class="tag">{{ tag }}</span>
      </div>
      <div class="ai-reply">
        <strong>🤖 AI 回复：</strong>
        {{ result.ai_reply }}
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