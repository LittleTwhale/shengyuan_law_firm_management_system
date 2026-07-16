<template>
  <div class="complaint-form-page">
    <!-- 页面标题 -->
    <el-page-header @back="$router.push('/main')" title="返回工作台" />
    <div class="page-header">
      <h2>
        <el-icon :size="28"><EditPen /></el-icon>
        起诉状要素提取
        <el-tag
          type="warning"
          effect="dark"
          size="small"
          style="vertical-align: middle; margin-left: 8px"
          >试运行</el-tag
        >
      </h2>
      <p class="page-desc">
        上传文件，AI 自动提取关键信息并填充至要素式模板，支持在线编辑和 PDF 导出
      </p>
    </div>

    <!-- ============ 隐私风险提醒 ============ -->
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
            <li>您上传的文件的 OCR 识别文本</li>
            <li>可能包含当事人姓名/名称、金额、日期等案件信息</li>
          </ul>
          <p class="privacy-note">
            请确保已获得客户授权或已做脱敏处理。提取完成后，数据不会被持久化保存。
          </p>
          <el-checkbox v-model="privacyConfirmed" class="privacy-checkbox">
            我已了解上述风险，确认继续
          </el-checkbox>
        </div>
      </template>
    </el-alert>

    <!-- ============ 步骤 1：文件上传 ============ -->
    <div class="upload-section" v-if="!extractDone">
      <el-card shadow="never">
        <template #header>
          <span><strong>① 上传起诉状文件</strong></span>
          <span class="card-tip">支持 PDF、Word (.docx/.doc)、图片 (.jpg/.png/.bmp 等)</span>
        </template>

        <el-upload
          ref="uploadRef"
          v-model:file-list="fileList"
          :auto-upload="false"
          :limit="5"
          :accept="'.pdf,.docx,.doc,.jpg,.jpeg,.png,.bmp,.tif,.webp'"
          :on-exceed="handleExceed"
          :on-change="handleFileChange"
          drag
          multiple
        >
          <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
          <div class="el-upload__text">将文件拖到此处，或 <em>点击上传</em></div>
          <template #tip>
            <div class="el-upload__tip">
              每个文件最大 30MB，一次最多上传 5 个文件。建议上传清晰的扫描件以获得最佳提取效果。
            </div>
          </template>
        </el-upload>
      </el-card>

      <!-- ============ 步骤 2：开始提取 ============ -->
      <el-card shadow="never" style="margin-top: 20px">
        <template #header>
          <span><strong>② 开始提取</strong></span>
        </template>

        <!-- 提取进度提示（按钮上方，点击提取后立即可见） -->
        <div v-if="extracting" class="extract-progress">
          <el-alert type="info" :closable="false" show-icon>
            <template #title>
              <span>{{ extractStatusText }}</span>
            </template>
          </el-alert>
          <el-progress
            :percentage="extractProgress"
            :stroke-width="8"
            :show-text="extractProgress > 0"
          />
        </div>

        <div class="action-area">
          <el-button
            type="primary"
            size="large"
            :disabled="!canExtract"
            :loading="extracting"
            @click="startExtraction"
          >
            <el-icon><MagicStick /></el-icon>
            {{ extracting ? 'AI 提取中...' : '开始提取' }}
          </el-button>
          <span class="action-hint" v-if="!canExtract && fileList.length === 0">
            请先上传文件
          </span>
          <span class="action-hint" v-else-if="!canExtract && !privacyConfirmed">
            请先勾选隐私确认
          </span>
        </div>
      </el-card>
    </div>

    <!-- ============ 步骤 3：预览与编辑 ============ -->
    <div class="result-section" v-if="extractDone">
      <el-card shadow="never" class="preview-card">
        <template #header>
          <div class="preview-header">
            <span><strong>③ 预览与编辑</strong></span>
            <div class="preview-actions">
              <el-button @click="resetAll" :disabled="generatingPdf">
                <el-icon><RefreshLeft /></el-icon>重新上传
              </el-button>
              <el-button type="primary" @click="exportPdf" :loading="generatingPdf">
                <el-icon><Download /></el-icon>导出 PDF
              </el-button>
              <el-button type="success" @click="exportHtml">
                <el-icon><Document /></el-icon>导出为HTML（可编辑）
              </el-button>
            </div>
          </div>
        </template>

        <el-alert type="success" :closable="false" show-icon style="margin-bottom: 16px">
          <template #title>
            AI 提取完成！请仔细核对以下所有字段。 您可以直接在表单中修改任何字段，修改后点击「导出
            PDF」。
          </template>
        </el-alert>

        <!-- iframe 预览区 — 使用 srcdoc 注入模板 + 数据 -->
        <div
          class="iframe-wrapper"
          v-loading="loadingPreview"
          element-loading-text="正在加载模板..."
        >
          <iframe
            ref="previewIframe"
            class="preview-iframe"
            :srcdoc="iframeSrcdoc"
            @load="onIframeLoad"
          ></iframe>
        </div>
      </el-card>
    </div>

    <!-- ============ 错误信息 ============ -->
    <el-card shadow="never" v-if="extractError" style="margin-top: 20px">
      <el-result icon="error" title="提取失败" :sub-title="extractError">
        <template #extra>
          <el-button type="primary" @click="resetAll">重新上传</el-button>
        </template>
      </el-result>
    </el-card>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Document, Download, EditPen, MagicStick, RefreshLeft, UploadFilled } from '@element-plus/icons-vue'
import request from '@/utils/request'

// ============ 状态 ============
const fileList = ref([])
const privacyConfirmed = ref(false)
const extracting = ref(false)
const extractDone = ref(false)
const extractError = ref('')
const extractProgress = ref(0)
const extractStatusText = ref('')
const generatingPdf = ref(false)
const loadingPreview = ref(false)

const previewIframe = ref(null)
const iframeSrcdoc = ref('')
const extractedFields = ref(null)

// ============ 计算属性 ============
const canExtract = computed(() => {
  return fileList.value.length > 0 && privacyConfirmed.value && !extracting.value
})

// ============ 方法 ============

/** 文件超出限制 */
function handleExceed() {
  ElMessage.warning('最多上传 5 个文件')
}

/** 文件列表变更 */
function handleFileChange(file, newFileList) {
  // 检查文件大小
  const maxSize = 30 * 1024 * 1024
  if (file.size > maxSize) {
    ElMessage.error(`文件 ${file.name} 超过 30MB 限制`)
    const idx = newFileList.findIndex((f) => f.uid === file.uid)
    if (idx > -1) newFileList.splice(idx, 1)
    return
  }
  fileList.value = newFileList
}

/** 模拟进度动画 */
function startProgressAnimation() {
  extractProgress.value = 0
  extractStatusText.value = '正在上传文件并执行 OCR 识别...'

  const steps = [
    { progress: 20, text: '正在上传文件并执行 OCR 识别...', delay: 500 },
    { progress: 50, text: 'OCR 识别完成，正在调用 AI 提取字段...', delay: 3000 },
    { progress: 80, text: 'AI 正在分析起诉状内容...', delay: 8000 },
    { progress: 95, text: '正在生成结构化数据...', delay: 12000 },
  ]

  steps.forEach((step) => {
    setTimeout(() => {
      if (!extracting.value) return
      extractProgress.value = step.progress
      extractStatusText.value = step.text
    }, step.delay)
  })
}

/** 开始提取 */
async function startExtraction() {
  if (!canExtract.value) return

  extracting.value = true
  extractError.value = ''
  startProgressAnimation()

  try {
    // 构建 FormData
    const formData = new FormData()
    for (const file of fileList.value) {
      formData.append('files', file.raw)
    }

    // 调用 API
    const res = await request.post('/complaint-form/extract', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 120000, // 2 分钟超时
    })

    if (res.data && res.data.success) {
      extractedFields.value = res.data.fields
      extractProgress.value = 100
      extractStatusText.value = '提取完成，正在加载模板...'

      // 加载模板并注入数据
      await loadTemplateWithData(res.data.fields)

      extractDone.value = true
      ElMessage.success(
        `提取完成！共处理 ${res.data.file_count} 个文件，OCR 文本 ${res.data.ocr_length} 字符`,
      )
    } else {
      throw new Error(res.data?.detail || '提取失败，返回数据格式异常')
    }
  } catch (error) {
    console.error('起诉状提取失败:', error)
    let errMsg = '提取失败，请稍后重试'
    if (error.response?.data?.detail) {
      errMsg = error.response.data.detail
    } else if (error.message) {
      errMsg = error.message
    }
    extractError.value = errMsg
    ElMessage.error(errMsg)
  } finally {
    extracting.value = false
  }
}

/** 加载模板 HTML 并注入提取数据 */
async function loadTemplateWithData(fields) {
  loadingPreview.value = true
  try {
    // cache: 'no-cache' 跳过浏览器缓存，每次验证最新模板
    const res = await fetch('/templates/formal_complaint_form.html', { cache: 'no-cache' })
    if (!res.ok) {
      throw new Error('模板请求失败: HTTP ' + res.status)
    }
    // 直接使用原始模板，不注入 script（通过 postMessage 传递数据）
    iframeSrcdoc.value = await res.text()
    // 保存数据，等 iframe 加载完成后通过 postMessage 发送
    extractedFields.value = fields
  } catch (error) {
    console.error('加载模板失败:', error)
    ElMessage.error('加载模板失败，请检查网络连接')
  }
}

/** iframe 加载完成后，直接操作 iframe window 填入数据 */
function onIframeLoad() {
  loadingPreview.value = false
  if (!extractedFields.value || !previewIframe.value) return

  const iframeWin = previewIframe.value.contentWindow
  if (!iframeWin) return

  // 直接设置数据并调用 fillForm（srcdoc iframe 同源，可直接访问）
  iframeWin.__COMPLAINT_DATA__ = extractedFields.value
  if (typeof iframeWin.fillForm === 'function') {
    iframeWin.fillForm(extractedFields.value)
  }
}

/** 导出 PDF — 直接在 iframe 内触发浏览器原生打印（完美渲染 @media print + 宋体） */
function exportPdf() {
  if (!previewIframe.value) {
    ElMessage.error('预览未加载，无法导出')
    return
  }

  const iframe = previewIframe.value
  const iframeWin = iframe.contentWindow
  const iframeDoc = iframe.contentDocument || iframeWin.document

  // 预设打印文件名（Chrome「另存为 PDF」会读取 document.title）
  iframeDoc.title = '要素式起诉状'

  // 确保 iframe 获得焦点，print() 只打印 iframe 内容
  iframeWin.focus()
  iframeWin.print()

  generatingPdf.value = false
}

/** 导出为 HTML（可编辑）— 将 iframe 中用户修改的内容同步到 HTML 属性后下载 */
function exportHtml() {
  if (!previewIframe.value) {
    ElMessage.error('预览未加载，无法导出')
    return
  }

  const iframe = previewIframe.value
  const iframeDoc = iframe.contentDocument || iframe.contentWindow.document

  if (!iframeDoc) {
    ElMessage.error('无法获取预览内容')
    return
  }

  // ====== 将表单控件的实时值同步回 HTML 属性，确保用户编辑被保留 ======

  // 1) contenteditable span：文本内容已在 DOM 中，无需同步（原 input[type="text"] 已全部替换）

  // 2) 多行文本域：将 value 写回 textContent
  iframeDoc.querySelectorAll('textarea').forEach((el) => {
    el.textContent = el.value
  })

  // 3) 单选框和复选框：checked 状态写回 checked 属性
  iframeDoc.querySelectorAll('input[type="radio"], input[type="checkbox"]').forEach((el) => {
    if (el.checked) {
      el.setAttribute('checked', 'checked')
    } else {
      el.removeAttribute('checked')
    }
  })

  // 4) 下拉选择框（模板中暂未使用，但做兼容处理）
  iframeDoc.querySelectorAll('select').forEach((el) => {
    const selected = el.options[el.selectedIndex]
    if (selected) {
      el.setAttribute('value', selected.value)
      // 同步各 option 的 selected 属性
      Array.from(el.options).forEach((opt) => {
        if (opt.selected) {
          opt.setAttribute('selected', 'selected')
        } else {
          opt.removeAttribute('selected')
        }
      })
    }
  })

  // ====== 序列化完整 HTML ======
  const docType = iframeDoc.doctype
  let htmlContent = ''
  if (docType) {
    htmlContent = '<!DOCTYPE ' + docType.name + '>\n'
  }
  htmlContent += iframeDoc.documentElement.outerHTML

  // ====== 触发文件下载 ======
  const blob = new Blob([htmlContent], { type: 'text/html;charset=utf-8' })
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = '要素式起诉状.html'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.URL.revokeObjectURL(url)

  ElMessage.success('HTML 文件已下载，您可以使用 Word 或浏览器打开并编辑')
}

/** 重置所有状态 */
function resetAll() {
  fileList.value = []
  privacyConfirmed.value = false
  extracting.value = false
  extractDone.value = false
  extractError.value = ''
  extractProgress.value = 0
  extractStatusText.value = ''
  extractedFields.value = null
  iframeSrcdoc.value = ''
}

// ============ 响应式布局 ============
const isMobile = ref(false)
function checkMobile() {
  isMobile.value = window.innerWidth < 768
}
onMounted(() => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
})
onUnmounted(() => {
  window.removeEventListener('resize', checkMobile)
})
</script>

<style scoped>
.complaint-form-page {
  max-width: 1100px;
  margin: 0 auto;
}

.page-header {
  margin: 20px 0 16px;
}
.page-header h2 {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 24px;
  color: #303133;
  margin: 0;
}
.page-desc {
  color: #909399;
  font-size: 14px;
  margin-top: 8px;
}

/* 隐私提醒 */
.privacy-alert {
  margin-bottom: 20px;
}
.privacy-warning-content ul {
  margin: 8px 0;
  padding-left: 20px;
}
.privacy-warning-content li {
  line-height: 1.8;
}
.privacy-note {
  color: #909399;
  font-size: 13px;
}
.privacy-checkbox {
  margin-top: 8px;
}

/* 上传区域 */
.card-tip {
  font-size: 13px;
  color: #909399;
  margin-left: 12px;
}

/* 操作区域 */
.action-area {
  display: flex;
  align-items: center;
  gap: 16px;
}
.action-hint {
  color: #909399;
  font-size: 14px;
}

/* 提取进度 */
.extract-progress {
  margin-top: 20px;
}
.extract-progress .el-alert {
  margin-bottom: 12px;
}

/* 预览区域 */
.preview-card {
  margin-top: 0;
}
.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}
.preview-actions {
  display: flex;
  gap: 10px;
}

/* iframe 容器 */
.iframe-wrapper {
  width: 100%;
  min-height: 600px;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  overflow: hidden;
  background: #f5f5f5;
}
.preview-iframe {
  width: 100%;
  height: 75vh;
  border: none;
  background: #fff;
}

@media (max-width: 768px) {
  .complaint-form-page {
    padding: 0;
  }
  .page-header h2 {
    font-size: 18px;
  }
  .preview-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  .preview-actions {
    width: 100%;
    justify-content: flex-end;
  }
  .iframe-wrapper {
    min-height: 400px;
  }
  .preview-iframe {
    height: 60vh;
  }
}
</style>
