/**
 * 错误分析通知模块
 *
 * 当 axios 拦截器检测到 500 错误且响应中包含 analysis_id 时调用。
 * 负责轮询分析结果，完成后以弹窗形式展示给触发错误的用户。
 *
 * 使用原生 fetch 轮询，避免与 request.js（axios 实例）产生循环依赖。
 */
import { ElMessage, ElMessageBox } from 'element-plus'
import { marked } from 'marked'
import DOMPurify from 'dompurify'

/** API 基础地址，与 request.js 的 baseURL 保持一致 */
const BASE_URL = 'http://127.0.0.1:8002/api'

/** 轮询间隔（毫秒） */
const POLL_INTERVAL = 5000

/** 最大轮询次数（5s × 24 = 2 分钟） */
const MAX_RETRIES = 24

/**
 * 入口：处理包含 analysis_id 的 500 错误响应
 * @param {object} errorData  - 后端返回的 error.response.data
 * @param {string} serverMsg  - 后端返回的 detail 消息
 */
export function handleErrorAnalysis(errorData, serverMsg) {
  const analysisId = errorData.analysis_id

  // 去重命中：后端直接返回了已完成的分析结果，立即弹窗
  if (errorData.analysis_status === 'completed' && errorData.analysis_result) {
    showAnalysisDialog(errorData.analysis_result, errorData.error_type || '错误分析')
    return
  }

  // 新记录：提示用户，启动轮询
  ElMessage.info(serverMsg || '系统正在分析此错误，分析完成后将自动弹出结果')

  // 延迟首次轮询，给后端一点时间
  setTimeout(() => pollAnalysisResult(analysisId, MAX_RETRIES), POLL_INTERVAL)
}

/**
 * 轮询分析结果
 * @param {number} analysisId - 分析记录 ID
 * @param {number} retries    - 剩余重试次数
 */
async function pollAnalysisResult(analysisId, retries) {
  if (retries <= 0) {
    ElMessage.info('错误分析仍在进行中，可稍后在「错误分析报告」页面查看结果')
    return
  }

  try {
    const token = localStorage.getItem('token')
    const headers = token ? { Authorization: `Bearer ${token}` } : {}

    const res = await fetch(`${BASE_URL}/error-analyses/${analysisId}`, { headers })

    if (!res.ok) {
      // 请求失败，继续重试
      scheduleNext(analysisId, retries)
      return
    }

    const data = await res.json()

    if (data.analysis_status === 'completed') {
      showAnalysisDialog(data.analysis_result, data.error_type || '错误分析')
      return
    }

    if (data.analysis_status === 'failed') {
      ElMessage.warning('错误分析未能完成，请联系管理员')
      return
    }

    // 仍在 pending / processing，继续轮询
    scheduleNext(analysisId, retries)
  } catch {
    // 网络异常，静默重试
    scheduleNext(analysisId, retries)
  }
}

/** 调度下一次轮询 */
function scheduleNext(analysisId, retries) {
  setTimeout(() => pollAnalysisResult(analysisId, retries - 1), POLL_INTERVAL)
}

/**
 * 弹出分析结果对话框
 * @param {string} content   - Markdown 格式的分析结果
 * @param {string} errorType - 错误类型名称
 */
export function showAnalysisDialog(content, errorType) {
  const html = renderMarkdown(content)

  ElMessageBox.alert(html, `${errorType} — 分析建议`, {
    dangerouslyUseHTMLString: true,
    confirmButtonText: '我知道了',
    customClass: 'error-analysis-notify-dialog',
    showClose: true,
    center: true,
    roundButton: true,
  })
}

/** Markdown → 安全 HTML */
function renderMarkdown(text) {
  if (!text) return '<p>暂无分析结果</p>'
  try {
    const raw = marked.parse(text, { async: false })
    return DOMPurify.sanitize(raw)
  } catch {
    return text.replace(/</g, '&lt;').replace(/>/g, '&gt;')
  }
}
