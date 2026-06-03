<template>
  <div class="ai-analysis-page">
    <!-- 页面标题 -->
    <el-page-header @back="$router.push('/main')" title="返回工作台" />
    <div class="page-header">
      <h2>
        <el-icon :size="28"><MagicStick /></el-icon>
        智能分析
        <el-tag
          type="warning"
          effect="dark"
          size="small"
          style="vertical-align: middle; margin-left: 8px"
          >试运行</el-tag
        >
      </h2>
      <p class="page-desc">基于 DeepSeek 大模型，对案件信息进行智能分析，生成结构化分析报告</p>
    </div>

    <!-- ==================== 隐私风险警告 ==================== -->
    <el-alert
      title="⚠️ 隐私与数据安全提醒"
      type="warning"
      :closable="false"
      show-icon
      class="privacy-alert"
    >
      <template #default>
        <div class="privacy-warning-content">
          <p><strong>该操作会将以下数据发送至 DeepSeek API（第三方大模型服务）：</strong></p>
          <ul>
            <li>案件基本信息（案号、案由、法院、标的金额等）</li>
            <li>当事人姓名/名称（<strong>已自动过滤身份证号、电话、地址</strong>）</li>
            <li>卷宗 OCR 文本内容</li>
            <li>您额外上传的分析材料</li>
          </ul>
          <p class="privacy-note">
            请确保已获得客户授权或脱敏处理。分析完成后，数据不会被持久化保存。
          </p>
          <el-checkbox v-model="privacyConfirmed" class="privacy-checkbox">
            我已了解上述风险，确认继续
          </el-checkbox>
        </div>
      </template>
    </el-alert>

    <!-- ==================== 分析步骤进度条 ==================== -->
    <el-steps
      v-if="currentStep > 0 && currentStep < 4"
      :active="currentStep"
      :direction="isMobile ? 'vertical' : 'horizontal'"
      align-center
      finish-status="success"
      process-status="process"
      style="margin-bottom: 20px"
    >
      <el-step title="数据聚合" description="加载案件信息与卷宗" />
      <el-step title="OCR 识别" description="提取文件文本内容" />
      <el-step title="AI 分析" description="DeepSeek 生成报告" />
      <el-step title="完成" />
    </el-steps>

    <!-- ==================== 配置区域 ==================== -->
    <div class="config-section" v-loading="generating" :element-loading-text="loadingText">
      <el-card shadow="never">
        <template #header>
          <span><strong>① 选择案件</strong></span>
        </template>

        <el-row :gutter="20">
          <el-col :span="16">
            <el-select
              v-model="selectedCaseId"
              filterable
              remote
              reserve-keyword
              clearable
              placeholder="搜索案件编号、案由或当事人"
              :remote-method="searchCases"
              :loading="searchingCases"
              style="width: 100%"
              @change="onCaseSelected"
            >
              <el-option
                v-for="item in caseOptions"
                :key="item.case_id"
                :label="`${item.case_number} - ${item.cause || '无案由'} (${item.case_category})`"
                :value="item.case_id"
              >
                <div class="case-option-item">
                  <div class="case-option-main">
                    <span class="case-number">{{ item.case_number }}</span>
                    <el-tag size="small" type="info">{{ item.case_category }}</el-tag>
                  </div>
                  <div class="case-option-sub">
                    <span>{{ item.cause || '无案由' }}</span>
                    <span v-if="item.main_lawyer" class="lawyer-name"
                      >主办: {{ item.main_lawyer }}</span
                    >
                  </div>
                </div>
              </el-option>
            </el-select>
          </el-col>

          <el-col :span="8">
            <div class="selected-case-preview" v-if="selectedCase">
              <el-descriptions :column="1" size="small" border>
                <el-descriptions-item label="案号">{{
                  selectedCase.case_number
                }}</el-descriptions-item>
                <el-descriptions-item label="案件类别">{{
                  selectedCase.case_category
                }}</el-descriptions-item>
                <el-descriptions-item label="案由">{{
                  selectedCase.cause || '未记录'
                }}</el-descriptions-item>
              </el-descriptions>
            </div>
          </el-col>
        </el-row>
      </el-card>

      <el-card shadow="never" style="margin-top: 16px">
        <template #header>
          <span><strong>② 补充材料（可选）</strong></span>
        </template>

        <el-upload
          ref="uploadRef"
          :auto-upload="false"
          :file-list="extraFiles"
          :on-change="onFileChange"
          :on-remove="onFileRemove"
          multiple
          drag
          class="upload-area"
        >
          <el-icon class="el-icon--upload" :size="40"><UploadFilled /></el-icon>
          <div class="el-upload__text">拖拽文件到此处，或 <em>点击上传</em></div>
          <template #tip>
            <div class="el-upload__tip">
              支持格式：PDF、Word (.docx/.doc)、图片 (JPG/PNG/BMP/TIF)，系统将自动进行 OCR 文字提取
            </div>
          </template>
        </el-upload>
      </el-card>

      <!-- ==================== 生成按钮 ==================== -->
      <div class="action-bar">
        <el-button
          type="primary"
          size="large"
          :disabled="!canGenerate"
          :loading="generating"
          @click="generateReport"
        >
          <el-icon><MagicStick /></el-icon>
          {{ generating ? '正在生成分析报告…' : '开始智能分析' }}
        </el-button>

        <el-button
          v-if="reportMarkdown && !isMobile"
          type="success"
          size="large"
          @click="downloadPdf"
          plain
        >
          <el-icon><Download /></el-icon>
          下载 PDF
        </el-button>

        <el-button
          v-if="reportMarkdown"
          size="large"
          @click="downloadDocx"
          :loading="exportingDocx"
          plain
        >
          <el-icon><Document /></el-icon>
          导出 Word
        </el-button>

        <el-button v-if="reportMarkdown" size="large" @click="copyReport" plain>
          <el-icon><CopyDocument /></el-icon>
          {{ copied ? '已复制' : '复制内容' }}
        </el-button>
      </div>
    </div>

    <!-- ==================== 报告展示 ==================== -->
    <div v-if="reportMarkdown" class="report-section">
      <el-card shadow="never" class="report-card">
        <template #header>
          <div class="report-header">
            <span><strong>📄 智能分析报告</strong></span>
            <span class="report-meta">
              案号：{{ selectedCase?.case_number }} | 生成时间：{{ generatedAt }}
            </span>
          </div>
        </template>

        <div class="markdown-body" v-html="renderedHtml"></div>

        <el-divider />

        <div class="report-disclaimer">
          <el-alert title="免责声明" type="info" :closable="false" show-icon>
            <template #default>
              <p>
                本报告由 AI
                自动生成，仅供律师参考，不构成法律意见。报告中涉及的法条引用、策略建议等，请结合专业判断和实际情况审慎使用。最终决策由承办律师自行负责。
              </p>
            </template>
          </el-alert>
        </div>
      </el-card>
    </div>

    <!-- ==================== 相关法条面板（RAG 知识库检索结果） ==================== -->
    <div v-if="relevantProvisions.length > 0" class="provisions-section">
      <el-card shadow="never" class="provisions-card">
        <template #header>
          <div class="provisions-header">
            <span class="provisions-title">
              <el-icon :size="18"><Collection /></el-icon>
              相关法律条文（来自知识库）
            </span>
            <el-button size="small" type="primary" @click="window.open('/main/legal-search', '_blank')" plain>
              打开法律知识库
            </el-button>
          </div>
        </template>

        <div class="provisions-list">
          <div
            v-for="(p, idx) in relevantProvisions"
            :key="idx"
            class="provision-item"
          >
            <div class="provision-tags">
              <el-tag type="success" effect="plain" size="small">{{ p.law_name }}</el-tag>
              <el-tag effect="plain" size="small" type="primary">{{ p.article_number }}</el-tag>
              <span class="provision-chapter" v-if="p.chapter">{{ p.chapter }}</span>
            </div>
            <div class="provision-content" v-html="renderedProvisionContent(p.content)"></div>
            <el-divider v-if="idx < relevantProvisions.length - 1" />
          </div>
        </div>
      </el-card>
    </div>

    <!-- ==================== 追问对话区域 ==================== -->
    <div v-if="reportMarkdown" class="chat-section">
      <el-card shadow="never" class="chat-card">
        <template #header>
          <div class="chat-header">
            <span class="chat-title">
              <el-icon :size="20"><ChatDotRound /></el-icon>
              追问分析
            </span>
            <el-button
              v-if="chatMessages.length > 0"
              type="danger"
              size="small"
              plain
              @click="clearChat"
            >
              清空对话
            </el-button>
          </div>
        </template>

        <!-- 消息列表 -->
        <div class="chat-messages" ref="chatMessagesRef">
          <!-- 空状态引导 -->
          <div v-if="chatMessages.length === 0" class="chat-empty">
            <el-icon :size="48" color="#c0c4cc"><ChatLineSquare /></el-icon>
            <p class="chat-empty-title">基于报告内容继续追问</p>
            <p class="chat-empty-desc">您可以追问法律适用细节、诉讼策略优化、证据链完善等问题</p>
            <div class="chat-suggestions">
              <el-tag
                v-for="q in suggestedQuestions"
                :key="q"
                class="suggestion-tag"
                @click="sendSuggestion(q)"
              >
                {{ q }}
              </el-tag>
            </div>
          </div>

          <!-- 消息气泡 -->
          <div
            v-for="(msg, idx) in chatMessages"
            :key="idx"
            class="chat-message"
            :class="msg.role === 'user' ? 'chat-message--user' : 'chat-message--ai'"
          >
            <div class="chat-avatar">
              <el-avatar
                :size="36"
                :style="{
                  backgroundColor: msg.role === 'user' ? '#165DFF' : '#00B42A',
                }"
              >
                {{ msg.role === 'user' ? '您' : 'AI' }}
              </el-avatar>
            </div>
            <div class="chat-bubble-wrapper">
              <div class="chat-bubble" :class="msg.role === 'user' ? 'bubble-user' : 'bubble-ai'">
                <div class="bubble-content" v-html="renderChatMarkdown(msg.content)"></div>
              </div>
              <div class="chat-time">{{ formatChatTime(msg._time) }}</div>
            </div>
          </div>

          <!-- 加载动画 -->
          <div v-if="chatLoading" class="chat-message chat-message--ai">
            <div class="chat-avatar">
              <el-avatar :size="36" style="background-color: #00b42a">AI</el-avatar>
            </div>
            <div class="chat-bubble-wrapper">
              <div class="chat-bubble bubble-ai bubble-loading">
                <span class="loading-dot">●</span>
                <span class="loading-dot">●</span>
                <span class="loading-dot">●</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 输入区域 -->
        <div class="chat-input-area">
          <el-input
            v-model="chatInput"
            type="textarea"
            :rows="2"
            placeholder="输入追问内容，例如：诉讼时效是否已过？有哪些有利证据可以补充？"
            :disabled="chatLoading"
            resize="none"
            @keydown.enter.exact.prevent="sendMessage"
          />
          <div class="chat-input-actions">
            <span class="chat-input-hint">Enter 发送，Shift+Enter 换行</span>
            <el-button
              type="primary"
              :disabled="!chatInput.trim() || chatLoading"
              :loading="chatLoading"
              @click="sendMessage"
            >
              <el-icon><Promotion /></el-icon>
              发送
            </el-button>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import {
  MagicStick,
  UploadFilled,
  Download,
  CopyDocument,
  Document,
  ChatDotRound,
  ChatLineSquare,
  Promotion,
  Collection,
} from '@element-plus/icons-vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'

import request from '@/utils/request'

// ========== Markdown 渲染器配置：链接在新标签页打开 ==========
const renderer = new marked.Renderer()
// 备份原始的 link 渲染方法
const originalLink = renderer.link.bind(renderer)

// 重写 link 方法，兼容不同版本的 marked（无论是传 token 对象还是传分开的参数）
renderer.link = function (...args) {
  // 先调用原始方法生成原生的 <a> 标签 HTML
  let html = originalLink(...args)
  // 在 <a> 标签开头注入 target="_blank" 以及安全属性 rel
  return html.replace(/^<a /, '<a target="_blank" rel="noopener noreferrer" ')
}
marked.setOptions({ renderer })

// ========== 响应式状态 ==========
const privacyConfirmed = ref(false)
const selectedCaseId = ref(null)
const selectedCase = ref(null)
const caseOptions = ref([])
const searchingCases = ref(false)
const extraFiles = ref([])
const generating = ref(false)
const loadingText = ref('正在分析…')
const reportMarkdown = ref('')
const generatedAt = ref('')
const copied = ref(false)
const exportingDocx = ref(false)
const uploadRef = ref(null)
const relevantProvisions = ref([])  // RAG 检索到的相关法条

// ========== 步骤进度状态 ==========
const currentStep = ref(0) // 0-3
const useStreaming = ref(true) // 默认启用流式

// ========== 移动端检测 ==========
const isMobile = ref(false)

function checkDeviceType() {
  isMobile.value = window.innerWidth < 768
}

onMounted(() => {
  checkDeviceType()
  window.addEventListener('resize', checkDeviceType)
})

onUnmounted(() => {
  window.removeEventListener('resize', checkDeviceType)
})

// ========== 追问对话状态 ==========
const chatMessages = ref([])
const chatInput = ref('')
const chatLoading = ref(false)
const chatMessagesRef = ref(null)

// 建议追问列表（根据报告内容动态显示）
const suggestedQuestions = ref([
  '本案的诉讼时效是否已过？',
  '有哪些有利证据可以补充完善？',
  '本案可能面临哪些法律风险？',
  '请详细分析适用的法律条文原文',
  '被告可能提出哪些抗辩理由？',
  '建议下一步采取什么具体行动？',
])

// ========== 计算属性 ==========
const canGenerate = computed(() => {
  return (
    privacyConfirmed.value &&
    selectedCaseId.value !== null &&
    selectedCaseId.value !== '' &&
    !generating.value
  )
})

const renderedHtml = computed(() => {
  if (!reportMarkdown.value) return ''
  const rawHtml = marked.parse(reportMarkdown.value)
  return DOMPurify.sanitize(rawHtml, { ADD_ATTR: ['target', 'rel'] })
})

// ========== 方法 ==========

// 搜索案件
async function searchCases(query) {
  if (!query || query.trim() === '') {
    // 首次加载默认列表
    await loadCases('')
    return
  }
  searchingCases.value = true
  try {
    const res = await request.get('/ai/cases', {
      params: { keyword: query, limit: 30 },
    })
    caseOptions.value = res.data.items || []
  } catch (e) {
    console.error('搜索案件失败', e)
  } finally {
    searchingCases.value = false
  }
}

// 加载案件列表（默认）
async function loadCases(keyword) {
  searchingCases.value = true
  try {
    const params = { limit: 50 }
    if (keyword) params.keyword = keyword
    const res = await request.get('/ai/cases', { params })
    caseOptions.value = res.data.items || []
  } catch (e) {
    console.error('加载案件列表失败', e)
    ElMessage.error('加载案件列表失败')
  } finally {
    searchingCases.value = false
  }
}

// 选中案件
function onCaseSelected(caseId) {
  if (!caseId) {
    selectedCase.value = null
    return
  }
  const found = caseOptions.value.find((c) => c.case_id === caseId)
  selectedCase.value = found || null
}

// 文件变化
function onFileChange() {
  extraFiles.value = [...uploadRef.value.uploadFiles]
}

function onFileRemove() {
  extraFiles.value = [...uploadRef.value.uploadFiles]
}

// ========== SSE 事件处理 ==========

// 处理 SSE 事件
function handleSSEEvent(event) {
  switch (event.type) {
    case 'progress':
      loadingText.value = event.message
      // 根据 stage 更新步骤
      if (event.stage === 'aggregating') currentStep.value = 1
      else if (event.stage === 'ocr') currentStep.value = 2
      else if (event.stage === 'analyzing') currentStep.value = 3
      break

    case 'content':
      // 增量追加文本
      reportMarkdown.value += event.delta
      break

    case 'done':
      generatedAt.value = event.generated_at
      currentStep.value = 4
      generating.value = false
      // 保存 RAG 检索到的相关法条
      if (event.relevant_provisions && event.relevant_provisions.length > 0) {
        relevantProvisions.value = event.relevant_provisions
      }
      // 使用动态追问建议（若有）
      if (event.suggested_questions && event.suggested_questions.length > 0) {
        suggestedQuestions.value.splice(
          0,
          suggestedQuestions.value.length,
          ...event.suggested_questions,
        )
      }
      ElMessage.success('分析完成')
      break

    case 'error':
      generating.value = false
      currentStep.value = 0
      ElMessage.error(`分析失败：${event.message}`)
      break
  }
}

// 流式分析（SSE）
async function startStreamAnalysis(formData) {
  currentStep.value = 1
  reportMarkdown.value = ''
  loadingText.value = '正在连接 AI 分析服务…'

  const token = localStorage.getItem('token')
  try {
    const baseURL = request.defaults.baseURL || ''
    const response = await fetch(`${baseURL}/ai/analyze/stream`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      body: formData,
    })

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })

      // 按行解析 SSE 事件
      const lines = buffer.split('\n')
      buffer = lines.pop() || '' // 不完整的行留下次处理

      for (const line of lines) {
        const trimmed = line.trim()
        if (trimmed.startsWith('data: ')) {
          try {
            const event = JSON.parse(trimmed.slice(6))
            handleSSEEvent(event)
          } catch (e) {
            console.warn('SSE 解析失败:', trimmed.slice(0, 100), e)
          }
        }
      }
    }

    // 处理 buffer 中剩余的数据
    if (buffer.trim().startsWith('data: ')) {
      try {
        const event = JSON.parse(buffer.trim().slice(6))
        handleSSEEvent(event)
      } catch (e) {
        console.error(e)
      }
    }
  } catch (e) {
    console.error('SSE 请求失败:', e)
    // 降级到非流式
    ElMessage.info('流式连接失败，切换到非流式模式...')
    await startNonStreamAnalysis(formData)
  }
}

// 非流式分析（降级方案）
async function startNonStreamAnalysis(formData) {
  currentStep.value = 1
  loadingText.value = '正在聚合案件数据…'
  await new Promise((r) => setTimeout(r, 500))

  currentStep.value = 2
  loadingText.value = '正在 OCR 识别文件文本…'
  await new Promise((r) => setTimeout(r, 500))

  currentStep.value = 3
  loadingText.value = '正在调用 DeepSeek 进行分析（约 1-3 分钟）…'

  try {
    const res = await request.post('/ai/analyze', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 180000,
    })

    reportMarkdown.value = res.data.report_markdown
    generatedAt.value = res.data.generated_at
    currentStep.value = 4
    generating.value = false
    // 保存 RAG 检索到的相关法条
    if (res.data.relevant_provisions && res.data.relevant_provisions.length > 0) {
      relevantProvisions.value = res.data.relevant_provisions
    }
    // 使用动态追问建议（若有）
    if (res.data.suggested_questions && res.data.suggested_questions.length > 0) {
      suggestedQuestions.value.splice(
        0,
        suggestedQuestions.value.length,
        ...res.data.suggested_questions,
      )
    }
    ElMessage.success('分析完成')
  } catch (e) {
    console.error('非流式分析失败', e)
    const detail = e.response?.data?.detail || e.message || '请求失败'
    ElMessage.error(`分析失败：${detail}`)
    generating.value = false
    currentStep.value = 0
  }
}

// 生成报告（入口：优先流式，失败降级非流式）
async function generateReport() {
  if (!selectedCaseId.value) {
    ElMessage.warning('请先选择一个案件')
    return
  }
  if (!privacyConfirmed.value) {
    ElMessage.warning('请先确认隐私风险提示')
    return
  }

  generating.value = true
  currentStep.value = 1

  const formData = new FormData()
  formData.append('case_id', selectedCaseId.value)

  // 添加上传的文件
  const files = uploadRef.value?.uploadFiles || []
  for (const f of files) {
    if (f.raw) {
      formData.append('files', f.raw)
    }
  }

  if (useStreaming.value) {
    await startStreamAnalysis(formData)
  } else {
    await startNonStreamAnalysis(formData)
  }
}

// 下载 PDF（使用浏览器原生打印/另存为PDF机制，解决空白和文字不可复制问题）
function downloadPdf() {
  const caseInfo = selectedCase.value
  const caseNumber = caseInfo?.case_number || '报告'

  // 创建隐藏的 iframe
  const iframe = document.createElement('iframe')
  iframe.style.position = 'fixed'
  iframe.style.right = '-9999px'
  iframe.style.bottom = '-9999px'
  iframe.style.width = '100vw'
  iframe.style.height = '100vh'
  document.body.appendChild(iframe)

  // 注入 Markdown 渲染后的 HTML 以及针对 PDF 优化的 CSS
  iframe.srcdoc = `
    <!DOCTYPE html>
    <html lang="js">
    <head>
      <title>案件智能分析报告_${caseNumber}</title>
      <style>
        @page { margin: 20mm; }
        body {
          font-family: 'SimSun', '宋体', 'PingFang SC', sans-serif;
          font-size: 14pt;
          line-height: 1.8;
          color: #000;
        }
        h1 { text-align: center; font-size: 22pt; border-bottom: 2px solid #333; padding-bottom: 10px; margin-bottom: 20px; }
        h2 { font-size: 18pt; color: #165DFF; margin-top: 25px; page-break-after: avoid; }
        h3 { font-size: 16pt; margin-top: 20px; page-break-after: avoid; }
        p, li { margin: 10px 0; }
        a { color: #165DFF; text-decoration: none; word-break: break-all; }
        blockquote {
          border-left: 4px solid #ccc;
          background-color: #f9f9f9;
          padding: 10px 15px;
          margin: 15px 0;
          page-break-inside: avoid;
        }
        table {
          border-collapse: collapse;
          width: 100%;
          margin: 15px 0;
          page-break-inside: avoid;
        }
        th, td { border: 1px solid #666; padding: 10px; text-align: left; }
        th { background-color: #f2f2f2; font-weight: bold; }
        code, pre {
          background-color: #f5f5f5;
          padding: 5px;
          font-family: monospace;
          page-break-inside: avoid;
        }
        .meta-info { text-align: center; color: #666; font-size: 12pt; margin-bottom: 30px; }
        .disclaimer {
          margin-top: 40px;
          padding: 15px;
          border: 1px solid #ccc;
          background: #fafafa;
          font-size: 11pt;
          color: #666;
          page-break-inside: avoid;
        }
      </style>
    </head>
    <body>
      <h1>案件智能分析报告</h1>
      <div class="meta-info">
        案号：${caseNumber} | 案件类别：${caseInfo?.case_category || ''} | 生成时间：${generatedAt.value}
      </div>
      <div class="content">
        ${renderedHtml.value}
      </div>
      <div class="disclaimer">
        <strong>免责声明：</strong>本报告由 AI 自动生成，仅供律师参考，不构成正式法律意见。报告中涉及的法条引用、策略建议等，请结合专业判断和实际情况审慎使用。
      </div>
    </body>
    </html>
  `

  // 等待内容加载完成后触发打印
  iframe.onload = () => {
    try {
      iframe.contentWindow.focus()
      iframe.contentWindow.print()
    } catch (e) {
      console.error('打印/导出 PDF 失败:', e)
      ElMessage.error('导出 PDF 失败，请检查浏览器权限')
    } finally {
      // 清理 iframe
      setTimeout(() => {
        document.body.removeChild(iframe)
      }, 1000)
    }
  }
}

// 复制报告内容（优先 Clipboard API，失败降级为 execCommand）
async function copyReport() {
  const text = reportMarkdown.value
  if (!text) {
    ElMessage.warning('暂无报告内容可复制')
    return
  }

  // 方案一：现代 Clipboard API
  if (navigator.clipboard && window.isSecureContext) {
    try {
      await navigator.clipboard.writeText(text)
      copied.value = true
      ElMessage.success('已复制到剪贴板')
      setTimeout(() => {
        copied.value = false
      }, 2000)
      return
    } catch {
      // 降级到方案二
    }
  }

  // 方案二：传统 execCommand 降级（兼容非 HTTPS 或大文本）
  try {
    const textarea = document.createElement('textarea')
    textarea.value = text
    textarea.style.position = 'fixed'
    textarea.style.left = '-9999px'
    textarea.style.top = '-9999px'
    document.body.appendChild(textarea)
    textarea.focus()
    textarea.select()
    // @ts-ignore: 保留 execCommand 作为旧版浏览器或非 HTTPS 环境的降级方案
    const success = document.execCommand('copy')
    document.body.removeChild(textarea)
    if (success) {
      copied.value = true
      ElMessage.success('已复制到剪贴板')
      setTimeout(() => {
        copied.value = false
      }, 2000)
    } else {
      ElMessage.error('复制失败，请手动选择复制')
    }
  } catch {
    ElMessage.error('复制失败，请手动选择复制')
  }
}

// 导出 Word 文档
async function downloadDocx() {
  if (!reportMarkdown.value) {
    ElMessage.warning('暂无报告内容可导出')
    return
  }
  exportingDocx.value = true
  try {
    const formData = new FormData()
    formData.append('report_markdown', reportMarkdown.value)
    formData.append('case_number', selectedCase.value?.case_number || '未知案号')
    formData.append('case_category', selectedCase.value?.case_category || '')

    const res = await request.post('/ai/export/docx', formData, {
      responseType: 'blob',
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 30000,
    })

    // 创建 Blob 并触发下载
    const url = window.URL.createObjectURL(new Blob([res.data]))
    const link = document.createElement('a')
    link.href = url
    link.download = `案件分析报告_${selectedCase.value?.case_number || '未知'}.docx`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    ElMessage.success('Word 文档下载成功')
  } catch (e) {
    ElMessage.error('Word 导出失败：' + (e.response?.data?.detail || e.message))
  } finally {
    exportingDocx.value = false
  }
}

// ========== 追问对话方法 ==========

// 发送追问消息
async function sendMessage() {
  const text = chatInput.value.trim()
  if (!text || chatLoading.value) return

  // 当前历史（不含本次消息）
  const historyToSend = [...chatMessages.value]

  // 立即显示用户消息
  chatMessages.value.push({
    role: 'user',
    content: text,
    _time: new Date().toISOString(),
  })
  chatInput.value = ''
  scrollToBottom()

  chatLoading.value = true
  try {
    const formData = new FormData()
    formData.append('case_id', selectedCaseId.value)
    formData.append('report_markdown', reportMarkdown.value)
    formData.append('messages', JSON.stringify(historyToSend))
    formData.append('user_message', text)

    const res = await request.post('/ai/chat', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 120000,
    })

    // 用服务端返回的完整历史替换本地消息
    chatMessages.value = (res.data.messages || []).map((m) => ({
      ...m,
      _time: m._time || new Date().toISOString(),
    }))
  } catch (e) {
    console.error('追问请求失败', e)
    const errMsg = e.response?.data?.detail || e.message || '请求失败'
    chatMessages.value.push({
      role: 'assistant',
      content: `⚠️ 抱歉，追问请求失败：${errMsg}`,
      _time: new Date().toISOString(),
    })
  } finally {
    chatLoading.value = false
    await nextTick()
    scrollToBottom()
  }
}

// 点击建议问题快捷发送
function sendSuggestion(question) {
  chatInput.value = question
  sendMessage()
}

// 清空对话历史
function clearChat() {
  chatMessages.value = []
  chatInput.value = ''
}

// 渲染聊天消息中的 Markdown（精简版，不含大标题）
function renderChatMarkdown(text) {
  if (!text) return ''
  const rawHtml = marked.parse(text)
  return DOMPurify.sanitize(rawHtml)
}

// 渲染法律条文内容
function renderedProvisionContent(text) {
  if (!text) return ''
  const rawHtml = marked.parse(text)
  return DOMPurify.sanitize(rawHtml)
}

// 格式化聊天时间
function formatChatTime(isoStr) {
  if (!isoStr) return ''
  const d = new Date(isoStr)
  const pad = (n) => String(n).padStart(2, '0')
  return `${pad(d.getHours())}:${pad(d.getMinutes())}`
}

// 滚动到消息底部
function scrollToBottom() {
  const el = chatMessagesRef.value
  if (el) {
    el.scrollTop = el.scrollHeight
  }
}

// ========== 生命周期 ==========
onMounted(() => {
  loadCases('')
})
</script>

<style scoped>
.ai-analysis-page {
  max-width: 1100px;
  margin: 0 auto;
  padding: 20px;
}

.page-header {
  margin: 16px 0;
}

.page-header h2 {
  font-size: 24px;
  display: flex;
  align-items: center;
  gap: 8px;
  color: #303133;
}

.page-desc {
  color: #909399;
  font-size: 14px;
  margin-top: 6px;
}

/* 隐私警告 */
.privacy-alert {
  margin-bottom: 20px;
}

.privacy-warning-content ul {
  margin: 8px 0 8px 20px;
  line-height: 1.8;
}

.privacy-note {
  color: #e6a23c;
  font-weight: bold;
  margin: 8px 0;
}

.privacy-checkbox {
  margin-top: 10px;
}

/* 案件选择器下拉样式 */
.case-option-item {
  padding: 4px 0;
}

.case-option-main {
  display: flex;
  align-items: center;
  gap: 8px;
}

.case-number {
  font-weight: bold;
  color: #165dff;
}

.case-option-sub {
  font-size: 12px;
  color: #909399;
  margin-top: 2px;
  display: flex;
  gap: 12px;
}

.lawyer-name {
  color: #67c23a;
}

/* 选中案件预览 */
.selected-case-preview {
  :deep(.el-descriptions__body) {
    font-size: 13px;
  }
}

/* 上传区域 */
.upload-area {
  :deep(.el-upload-dragger) {
    width: 100%;
  }
}

/* 操作按钮 */
.action-bar {
  margin: 24px 0;
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

/* 报告展示区 */
.report-section {
  margin-top: 20px;
}

.report-card {
  :deep(.el-card__body) {
    padding: 24px;
  }
}

.report-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.report-meta {
  font-size: 12px;
  color: #909399;
}

/* Markdown 渲染样式 */
.markdown-body {
  line-height: 1.8;
  font-size: 15px;
  color: #303133;
}

.markdown-body :deep(h2) {
  font-size: 20px;
  color: #165dff;
  border-left: 4px solid #165dff;
  padding-left: 12px;
  margin: 24px 0 12px;
}

.markdown-body :deep(h3) {
  font-size: 17px;
  margin: 20px 0 10px;
  color: #303133;
}

.markdown-body :deep(h4) {
  font-size: 15px;
  font-weight: bold;
  margin: 16px 0 8px;
}

.markdown-body :deep(p) {
  margin: 8px 0;
}

.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  padding-left: 24px;
  margin: 8px 0;
}

.markdown-body :deep(li) {
  margin: 4px 0;
}

.markdown-body :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 12px 0;
}

.markdown-body :deep(th),
.markdown-body :deep(td) {
  border: 1px solid #dcdfe6;
  padding: 8px 12px;
  text-align: left;
}

.markdown-body :deep(th) {
  background: #f5f7fa;
  font-weight: bold;
}

.markdown-body :deep(blockquote) {
  border-left: 4px solid #e6a23c;
  background: #fdf6ec;
  padding: 10px 16px;
  margin: 12px 0;
  border-radius: 4px;
  color: #856404;
}

.markdown-body :deep(code) {
  background: #f5f5f5;
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 14px;
}

.markdown-body :deep(pre code) {
  display: block;
  padding: 12px;
  overflow-x: auto;
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 4px;
}

.markdown-body :deep(hr) {
  border: none;
  border-top: 1px solid #dcdfe6;
  margin: 20px 0;
}

.markdown-body :deep(img) {
  max-width: 100%;
  height: auto;
}

/* 免责声明 */
.report-disclaimer {
  margin-top: 20px;
}

/* 配置区域加载 */
.config-section {
  position: relative;
}

/* ==================== 追问对话区域 ==================== */
.chat-section {
  margin-top: 24px;
}

.chat-card {
  border: 1px solid #e4e7ed;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chat-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

/* 消息列表容器 */
.chat-messages {
  max-height: 480px;
  overflow-y: auto;
  padding: 16px 4px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  scroll-behavior: smooth;
}

.chat-messages::-webkit-scrollbar {
  width: 6px;
}

.chat-messages::-webkit-scrollbar-thumb {
  background: #dcdfe6;
  border-radius: 3px;
}

.chat-messages::-webkit-scrollbar-thumb:hover {
  background: #c0c4cc;
}

/* 空状态 */
.chat-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 32px 16px;
  text-align: center;
}

.chat-empty-title {
  font-size: 15px;
  color: #606266;
  margin: 12px 0 4px;
}

.chat-empty-desc {
  font-size: 13px;
  color: #909399;
  margin-bottom: 16px;
}

.chat-suggestions {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 8px;
  max-width: 500px;
}

.suggestion-tag {
  cursor: pointer;
  transition: all 0.2s;
  border: 1px dashed #b3d8ff;
  background: #ecf5ff;
  color: #409eff;
}

.suggestion-tag:hover {
  background: #409eff;
  color: #fff;
  border-color: #409eff;
}

/* 单条消息 */
.chat-message {
  display: flex;
  gap: 10px;
  max-width: 85%;
  animation: fadeInUp 0.3s ease;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.chat-message--ai {
  align-self: flex-start;
}

.chat-message--user {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.chat-avatar {
  flex-shrink: 0;
  padding-top: 2px;
}

.chat-bubble-wrapper {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.chat-bubble {
  padding: 12px 16px;
  border-radius: 12px;
  line-height: 1.7;
  font-size: 14px;
  word-break: break-word;
}

.bubble-ai {
  background: #f0f5ff;
  border: 1px solid #d6e4ff;
  border-top-left-radius: 4px;
  color: #303133;
}

.bubble-user {
  background: linear-gradient(135deg, #165dff, #3b7cff);
  color: #fff;
  border-top-right-radius: 4px;
}

.bubble-loading {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 14px 20px;
}

.loading-dot {
  font-size: 10px;
  animation: dotPulse 1.4s infinite ease-in-out;
}

.loading-dot:nth-child(1) {
  animation-delay: 0s;
}
.loading-dot:nth-child(2) {
  animation-delay: 0.2s;
}
.loading-dot:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes dotPulse {
  0%,
  80%,
  100% {
    opacity: 0.3;
    transform: scale(0.8);
  }
  40% {
    opacity: 1;
    transform: scale(1.2);
  }
}

/* 聊天消息中的 Markdown 样式 */
.bubble-content :deep(h2),
.bubble-content :deep(h3),
.bubble-content :deep(h4) {
  font-size: 15px;
  margin: 6px 0 4px;
  color: inherit;
}

.bubble-content :deep(p) {
  margin: 4px 0;
}

.bubble-content :deep(ul),
.bubble-content :deep(ol) {
  padding-left: 18px;
  margin: 4px 0;
}

.bubble-content :deep(li) {
  margin: 2px 0;
}

.bubble-content :deep(blockquote) {
  border-left: 3px solid #a0c4ff;
  padding: 4px 10px;
  margin: 6px 0;
  background: rgba(255, 255, 255, 0.5);
  border-radius: 4px;
}

.bubble-content :deep(code) {
  background: rgba(0, 0, 0, 0.06);
  padding: 1px 5px;
  border-radius: 3px;
  font-size: 13px;
}

.bubble-content :deep(pre code) {
  display: block;
  padding: 8px 12px;
  background: rgba(0, 0, 0, 0.04);
  border-radius: 4px;
  overflow-x: auto;
}

.bubble-content :deep(table) {
  font-size: 13px;
  border-collapse: collapse;
  width: 100%;
  margin: 6px 0;
}

.bubble-content :deep(th),
.bubble-content :deep(td) {
  border: 1px solid #dcdfe6;
  padding: 4px 8px;
  text-align: left;
}

.bubble-content :deep(th) {
  background: rgba(255, 255, 255, 0.6);
}

/* 用户气泡中的 Markdown 颜色适配 */
.bubble-user .bubble-content :deep(blockquote) {
  border-left-color: rgba(255, 255, 255, 0.4);
  background: rgba(255, 255, 255, 0.15);
  color: rgba(255, 255, 255, 0.9);
}

.bubble-user .bubble-content :deep(code) {
  background: rgba(255, 255, 255, 0.2);
  color: #fff;
}

.bubble-user .bubble-content :deep(a) {
  color: #ffd666;
}

.chat-time {
  font-size: 11px;
  color: #c0c4cc;
  padding: 0 4px;
}

.chat-message--user .chat-time {
  text-align: right;
}

/* 输入区域 */
.chat-input-area {
  border-top: 1px solid #ebeef5;
  padding-top: 12px;
  margin-top: 4px;
}

.chat-input-area :deep(.el-textarea__inner) {
  border-radius: 8px;
  font-size: 14px;
  line-height: 1.6;
}

.chat-input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
}

.chat-input-hint {
  font-size: 12px;
  color: #c0c4cc;
}

/* ==================== 相关法条面板 ==================== */
.provisions-section {
  margin-top: 24px;
}

.provisions-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.provisions-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.provisions-list {
  max-height: 500px;
  overflow-y: auto;
}

.provision-item {
  margin-bottom: 4px;
}

.provision-tags {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  flex-wrap: wrap;
}

.provision-chapter {
  font-size: 12px;
  color: #909399;
}

.provision-content {
  font-size: 14px;
  line-height: 1.9;
  color: #303133;
}

.provision-content :deep(blockquote) {
  border-left: 4px solid #67c23a;
  background: #f0f9eb;
  padding: 10px 16px;
  margin: 8px 0;
  border-radius: 4px;
}

/* ==================== 移动端适配 ==================== */
@media (max-width: 768px) {
  .ai-analysis-page {
    padding: 12px;
  }

  .page-header h2 {
    font-size: 18px;
  }

  .config-section .el-row {
    flex-direction: column;
  }
  .config-section .el-col-16,
  .config-section .el-col-8 {
    flex: 1;
    max-width: 100%;
  }
  .selected-case-preview {
    margin-top: 12px;
  }

  .action-bar {
    flex-direction: column;
  }
  .action-bar .el-button {
    width: 100%;
    justify-content: center;
  }

  .report-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .markdown-body {
    font-size: 14px;
  }
  .markdown-body :deep(h2) {
    font-size: 17px;
  }
  .markdown-body :deep(h3) {
    font-size: 15px;
  }

  .chat-messages {
    max-height: 320px;
  }
  .chat-message {
    max-width: 95%;
  }
  .chat-bubble {
    font-size: 13px;
    padding: 10px 12px;
  }
  .chat-input-area :deep(.el-textarea__inner) {
    font-size: 13px;
  }

  .upload-area :deep(.el-upload-dragger) {
    padding: 20px 12px;
  }
}

@media (max-width: 400px) {
  .ai-analysis-page {
    padding: 8px;
  }
  .page-header h2 {
    font-size: 16px;
  }
  .markdown-body {
    font-size: 13px;
  }
  .el-page-header {
    font-size: 13px;
  }
}
</style>
