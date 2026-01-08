<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { ChatLineRound, DataAnalysis, Timer,  Delete, Monitor } from '@element-plus/icons-vue'

// --- 接口定义 ---
interface AnalysisResult {
  length: number
  is_question: boolean
  sentiment: string
  keywords: string[]
  ai_reply: string
}

interface HistoryRecord {
  id: number
  text_content: string
  ai_reply: string
  sentiment: string
  word_count: number
}

// --- 状态 ---
const inputText = ref('')
const result = ref<AnalysisResult | null>(null)
const loading = ref(false)
const streamMessage = ref('')
const historyList = ref<HistoryRecord[]>([])

// --- 颜色工具 ---
const getSentimentTagType = (sentiment: string) => {
  if (sentiment.includes('积极') || sentiment.includes('开心')) return 'success'
  if (sentiment.includes('消极') || sentiment.includes('愤怒')) return 'danger'
  if (sentiment.includes('疑问')) return 'warning'
  return 'info'
}

// --- API 方法 ---
const fetchHistory = async () => {
  try {
    const res = await fetch('http://127.0.0.1:8000/history')
    if (res.ok) historyList.value = await res.json()
  } catch (error) { console.error(error) }
}

const analyzeText = async () => {
  if (!inputText.value) return ElMessage.warning('内容不能为空')
  loading.value = true
  result.value = null
  streamMessage.value = ''
  try {
    const response = await fetch('http://127.0.0.1:8000/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: inputText.value })
    })
    if (!response.ok) throw new Error('API Error')
    result.value = await response.json()
    await fetchHistory() 
  } catch (error) { ElMessage.error('请求失败') } 
  finally { loading.value = false }
}

const startChat = async () => {
  if (!inputText.value) return ElMessage.warning('内容不能为空')
  streamMessage.value = ''
  result.value = null
  loading.value = true
  try {
    const response = await fetch('http://127.0.0.1:8000/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: inputText.value })
    })
    if (!response.body) return
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      streamMessage.value += decoder.decode(value)
    }
    await fetchHistory()
  } catch (error) { ElMessage.error('聊天中断') } 
  finally { loading.value = false }
}

onMounted(fetchHistory)
</script>

<template>
  <div class="app-layout">
    
    <header class="navbar">
      <div class="logo">
        <el-icon :size="20"><Monitor /></el-icon>
        <span>DeepSeek Console</span>
      </div>
      <div class="status-badge">Online</div>
    </header>

    <div class="main-grid">
      
      <main class="workspace">
        
        <div class="panel input-panel">
          <div class="panel-header">工作台</div>
          <el-input
            v-model="inputText"
            :rows="6"
            type="textarea"
            placeholder="在此输入文本..."
            resize="none"
            class="clean-input"
          />
          <div class="action-row">
            <el-button type="primary" :icon="DataAnalysis" @click="analyzeText" :loading="loading" color="#2563eb">立即分析</el-button>
            <el-button type="info" :icon="ChatLineRound" @click="startChat" :loading="loading" plain>流式对话</el-button>
          </div>
        </div>

        <div class="output-area">
          
          <div v-if="result" class="panel result-panel">
            <div class="panel-header">
              <span>分析报告</span>
              <el-tag :type="getSentimentTagType(result.sentiment)" size="small" effect="dark">{{ result.sentiment }}</el-tag>
            </div>
            
            <div class="stats-row">
              <div class="stat-item">
                <span class="label">字数统计</span>
                <span class="val">{{ result.length }}</span>
              </div>
              <div class="stat-item">
                <span class="label">是否提问</span>
                <span class="val">{{ result.is_question ? '是' : '否' }}</span>
              </div>
            </div>

            <div class="keyword-row">
              <span class="label">关键词：</span>
              <el-tag v-for="w in result.keywords" :key="w" size="small" class="kw-tag">{{ w }}</el-tag>
            </div>

            <div class="ai-box">
              <div class="ai-title">AI 回复</div>
              <p>{{ result.ai_reply }}</p>
            </div>
          </div>

          <div v-if="streamMessage" class="panel chat-panel">
            <div class="panel-header">实时输出</div>
            <div class="stream-content">
              {{ streamMessage }}<span class="cursor">_</span>
            </div>
          </div>

          <div v-if="!result && !streamMessage" class="empty-state">
            结果将显示在这里...
          </div>

        </div>
      </main>

      <aside class="sidebar">
        <div class="sidebar-header">
          <el-icon><Timer /></el-icon> 历史记录
        </div>
        
        <div class="history-scroll">
          <div v-for="item in historyList" :key="item.id" class="history-card">
            <div class="h-header">
              <span class="h-id">#{{ item.id }}</span>
              <el-tag size="small" :type="getSentimentTagType(item.sentiment)" effect="plain">{{ item.sentiment }}</el-tag>
            </div>
            <div class="h-text">{{ item.text_content }}</div>
            <div class="h-reply">AI: {{ item.ai_reply }}</div>
          </div>
          
          <div v-if="historyList.length === 0" class="no-history">暂无记录</div>
        </div>
      </aside>

    </div>
  </div>
</template>

<style scoped>
/* 整体布局 - 铺满全屏 */
.app-layout {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: #f1f5f9; /* 浅灰底色，干净 */
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  color: #334155;
}

/* 顶部导航 */
.navbar {
  height: 50px;
  background: #fff;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  flex-shrink: 0;
}
.logo {
  font-weight: 600;
  font-size: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  color: #0f172a;
}
.status-badge {
  font-size: 12px;
  background: #dcfce7;
  color: #166534;
  padding: 2px 8px;
  border-radius: 12px;
  font-weight: 500;
}

/* 主要网格布局 - 关键改变 */
.main-grid {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 320px; /* 左边自适应，右边固定320px */
  gap: 20px;
  padding: 20px;
  overflow: hidden; /* 防止整个页面滚动 */
  max-width: 1600px; /* 超大屏限制一下，一般屏铺满 */
  margin: 0 auto;
  width: 100%;
  box-sizing: border-box;
}

/* --- 左侧工作区 --- */
.workspace {
  display: flex;
  flex-direction: column;
  gap: 20px;
  overflow-y: auto; /* 允许内部滚动 */
  padding-right: 5px;
}

.panel {
  background: #fff;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  padding: 20px;
  box-shadow: 0 1px 2px rgba(0,0,0,0.05);
}

.panel-header {
  font-size: 14px;
  font-weight: 600;
  color: #64748b;
  margin-bottom: 15px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

/* 输入框样式 */
:deep(.clean-input .el-textarea__inner) {
  box-shadow: none !important;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  padding: 15px;
  font-size: 15px;
  border-radius: 6px;
}
:deep(.clean-input .el-textarea__inner:focus) {
  border-color: #2563eb;
  background: #fff;
}

.action-row {
  margin-top: 15px;
  display: flex;
  gap: 10px;
}

/* 结果区域 */
.output-area {
  flex: 1;
  min-height: 200px;
}

.empty-state {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #94a3b8;
  border: 2px dashed #e2e8f0;
  border-radius: 8px;
  background: rgba(255,255,255,0.5);
}

/* 统计行 */
.stats-row {
  display: flex;
  gap: 30px;
  margin-bottom: 15px;
  padding-bottom: 15px;
  border-bottom: 1px solid #f1f5f9;
}
.stat-item { display: flex; flex-direction: column; gap: 4px; }
.stat-item .label { font-size: 12px; color: #94a3b8; }
.stat-item .val { font-size: 20px; font-weight: bold; color: #334155; }

.keyword-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 20px;
  font-size: 13px;
  color: #64748b;
}
.kw-tag { border: none; background: #f1f5f9; color: #475569; }

.ai-box {
  background: #f8fafc;
  padding: 15px;
  border-radius: 6px;
  border-left: 4px solid #2563eb;
}
.ai-title { font-size: 12px; font-weight: bold; color: #2563eb; margin-bottom: 5px; }
.ai-box p { margin: 0; line-height: 1.6; font-size: 15px; color: #1e293b; }

/* 流式对话 */
.stream-content {
  font-family: monospace;
  font-size: 15px;
  line-height: 1.8;
  white-space: pre-wrap;
}
.cursor {
  display: inline-block;
  width: 6px;
  height: 16px;
  background: #2563eb;
  margin-left: 4px;
  animation: blink 1s infinite;
  vertical-align: middle;
}
@keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }

/* --- 右侧侧边栏 --- */
.sidebar {
  background: #fff;
  border-left: 1px solid #e2e8f0;
  border-radius: 8px; /* 也做成卡片风格 */
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid #e2e8f0;
}

.sidebar-header {
  padding: 15px;
  font-weight: 600;
  border-bottom: 1px solid #f1f5f9;
  display: flex;
  align-items: center;
  gap: 8px;
  background: #fff;
  color: #475569;
}

.history-scroll {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
  background: #f8fafc;
}

.history-card {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  padding: 12px;
  margin-bottom: 10px;
  cursor: pointer;
  transition: all 0.2s;
}
.history-card:hover {
  border-color: #cbd5e1;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.h-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 6px;
}
.h-id { font-size: 12px; color: #94a3b8; }
.h-text {
  font-size: 13px;
  color: #334155;
  font-weight: 500;
  margin-bottom: 6px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.h-reply {
  font-size: 12px;
  color: #64748b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  padding-top: 6px;
  border-top: 1px dashed #f1f5f9;
}
.no-history {
  text-align: center;
  color: #cbd5e1;
  margin-top: 40px;
  font-size: 13px;
}
</style>