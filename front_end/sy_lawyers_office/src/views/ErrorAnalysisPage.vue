<template>
  <div class="error-analysis-page">
    <!-- 页面标题 -->
    <el-page-header @back="$router.push('/main')" title="返回工作台" />
    <div class="page-header">
      <h2>
        <el-icon :size="28"><WarningFilled /></el-icon>
        错误分析报告
      </h2>
      <p class="page-desc">服务端错误已由 DeepSeek 自动分析，查看错误原因和修复建议</p>
    </div>

    <!-- 状态提示 -->
    <el-alert title="自动诊断说明" type="info" :closable="true" show-icon class="info-alert">
      <template #default>
        <div class="info-content">
          <p>
            当您在使用过程中遇到错误提示时，系统会自动将错误信息发送至
            <strong>DeepSeek AI</strong> 进行分析诊断。
            分析完成后，您可以在此页面查看错误原因和解决方案建议。
          </p>
          <p class="info-note">分析结果仅供参考，请结合实际情况判断。</p>
        </div>
      </template>
    </el-alert>

    <!-- 状态筛选标签 -->
    <div class="filter-bar">
      <el-radio-group v-model="statusFilter" @change="handleStatusChange" size="small">
        <el-radio-button label="">全部</el-radio-button>
        <el-radio-button label="completed">
          <el-icon><CircleCheck /></el-icon> 已完成
        </el-radio-button>
        <el-radio-button label="pending">
          <el-icon><Clock /></el-icon> 排队中
        </el-radio-button>
        <el-radio-button label="processing">
          <el-icon><Loading /></el-icon> 分析中
        </el-radio-button>
        <el-radio-button label="failed">
          <el-icon><CloseBold /></el-icon> 失败
        </el-radio-button>
      </el-radio-group>

      <div class="filter-bar-right">
        <el-tag v-if="isAdmin" type="warning" size="small" effect="dark" class="admin-badge">
          <el-icon><View /></el-icon> 管理员 — 查看全部记录
        </el-tag>
        <el-button type="primary" :icon="Refresh" size="small" @click="fetchData" circle />
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="5" animated />
    </div>

    <!-- 空状态 -->
    <el-empty
      v-else-if="!loading && list.length === 0"
      :description="statusFilter ? '没有符合条件的分析记录' : '还没有错误分析记录'"
      :image-size="120"
    >
      <template #image>
        <el-icon :size="60" color="#c0c4cc"><CircleCheckFilled /></el-icon>
      </template>
    </el-empty>

    <!-- 列表视图：桌面端表格 / 移动端卡片 -->
    <template v-else>
      <!-- === 桌面端表格 === -->
      <div v-if="!isMobile" class="desktop-table">
        <el-table
          :data="list"
          stripe
          style="width: 100%"
          @row-click="openDetail"
          highlight-current-row
        >
          <el-table-column prop="id" label="ID" width="70" align="center" />

          <el-table-column label="状态" width="110" align="center">
            <template #default="{ row }">
              <el-tag
                :type="statusTagType(row.analysis_status)"
                :icon="statusIcon(row.analysis_status)"
                size="small"
                effect="dark"
              >
                {{ statusLabel(row.analysis_status) }}
              </el-tag>
            </template>
          </el-table-column>

          <el-table-column label="异常类型" min-width="150">
            <template #default="{ row }">
              <span class="error-type-badge">{{ row.error_type }}</span>
            </template>
          </el-table-column>

          <el-table-column label="错误消息" min-width="250">
            <template #default="{ row }">
              <span class="error-msg-text">{{ row.error_message }}</span>
            </template>
          </el-table-column>

          <!-- 触发用户（管理员可见） -->
          <el-table-column v-if="isAdmin" label="触发用户" width="120" align="center">
            <template #default="{ row }">
              <span class="user-name-text">{{ row.user_real_name || '匿名' }}</span>
            </template>
          </el-table-column>

          <el-table-column label="请求" width="180">
            <template #default="{ row }">
              <el-tag size="small" type="info" effect="plain">
                {{ row.request_method }}
              </el-tag>
              <span class="request-path">{{ row.request_path }}</span>
            </template>
          </el-table-column>

          <el-table-column label="时间" width="170">
            <template #default="{ row }">
              <span class="time-text">{{ formatTime(row.created_at) }}</span>
            </template>
          </el-table-column>

          <el-table-column label="操作" width="140" align="center">
            <template #default="{ row }">
              <el-button type="primary" link size="small" @click.stop="openDetail(row)">
                查看
              </el-button>
              <el-button type="danger" link size="small" @click.stop="confirmDelete(row)">
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- === 移动端卡片 === -->
      <div v-else class="mobile-cards">
        <div v-for="item in list" :key="item.id" class="error-card" @click="openDetail(item)">
          <div class="card-header">
            <el-tag :type="statusTagType(item.analysis_status)" size="small" effect="dark">
              {{ statusLabel(item.analysis_status) }}
            </el-tag>
            <div class="card-header-right">
              <span v-if="isAdmin" class="card-user">{{ item.user_real_name || '匿名' }}</span>
              <span class="card-time">{{ formatTime(item.created_at) }}</span>
            </div>
          </div>

          <div class="card-body">
            <div class="card-error-type">{{ item.error_type }}</div>
            <div class="card-error-msg">{{ item.error_message }}</div>
          </div>

          <div class="card-footer">
            <div class="card-footer-left">
              <el-tag size="small" type="info" effect="plain">
                {{ item.request_method }}
              </el-tag>
              <span class="card-path">{{ item.request_path }}</span>
            </div>
            <el-button type="danger" link size="small" @click.stop="confirmDelete(item)">
              删除
            </el-button>
          </div>
        </div>
      </div>

      <!-- 分页 -->
      <div class="pagination-bar">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="fetchData"
          @current-change="fetchData"
          background
          small
        />
      </div>
    </template>

    <!-- ============================================================ -->
    <!-- 详情对话框 -->
    <!-- ============================================================ -->
    <el-dialog
      v-model="detailVisible"
      :title="detailData ? `${detailData.error_type} 分析详情` : '加载中...'"
      width="800px"
      class="detail-dialog"
      :destroy-on-close="true"
      :close-on-click-modal="false"
      append-to-body
      @closed="onDetailClosed"
    >
      <template v-if="detailData">
        <!-- 基本信息区 -->
        <el-descriptions :column="isMobile ? 1 : 2" border size="small" class="detail-meta">
          <el-descriptions-item label="异常类型">
            <el-tag size="small" effect="dark">{{ detailData.error_type }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="分析状态">
            <el-tag :type="statusTagType(detailData.analysis_status)" size="small" effect="dark">
              {{ statusLabel(detailData.analysis_status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="请求方法">{{
            detailData.request_method
          }}</el-descriptions-item>
          <el-descriptions-item label="请求路径" class="path-cell">{{
            detailData.request_path
          }}</el-descriptions-item>
          <el-descriptions-item label="触发用户">{{
            detailData.user_real_name || detailData.user_accounts || '匿名用户'
          }}</el-descriptions-item>
          <el-descriptions-item label="错误时间">{{
            formatTime(detailData.created_at)
          }}</el-descriptions-item>
        </el-descriptions>

        <!-- 错误消息 -->
        <div class="detail-section">
          <h4 class="section-title">
            <el-icon><Warning /></el-icon> 错误消息
          </h4>
          <el-input
            type="textarea"
            :model-value="detailData.error_message"
            readonly
            :rows="3"
            class="detail-textarea"
          />
        </div>

        <!-- 异常堆栈 -->
        <div v-if="detailData.traceback_summary" class="detail-section">
          <h4 class="section-title">
            <el-icon><List /></el-icon> 异常堆栈
          </h4>
          <pre class="traceback-block">{{ detailData.traceback_summary }}</pre>
        </div>

        <!-- DeepSeek 分析结果 -->
        <div
          v-if="detailData.analysis_status === 'completed' && detailData.analysis_result"
          class="detail-section"
        >
          <h4 class="section-title analysis-title">
            <el-icon :size="20"><MagicStick /></el-icon>
            DeepSeek 分析建议
            <el-tag size="small" type="success" effect="light" style="margin-left: 8px">
              由 AI 生成
            </el-tag>
          </h4>
          <div
            class="analysis-result markdown-body"
            v-html="renderMarkdown(detailData.analysis_result)"
          />
        </div>

        <!-- 分析中 -->
        <div
          v-else-if="detailData.analysis_status === 'processing'"
          class="detail-section status-section"
        >
          <el-result
            icon="info"
            title="分析进行中"
            sub-title="DeepSeek 正在分析此错误，请稍后再查看"
          >
            <template #icon>
              <el-icon class="is-loading" :size="48"><Loading /></el-icon>
            </template>
          </el-result>
        </div>

        <!-- 排队中 -->
        <div
          v-else-if="detailData.analysis_status === 'pending'"
          class="detail-section status-section"
        >
          <el-result
            icon="warning"
            title="等待分析"
            sub-title="此错误已加入分析队列，请稍后查看结果"
          />
        </div>

        <!-- 分析失败 -->
        <div
          v-else-if="detailData.analysis_status === 'failed'"
          class="detail-section status-section"
        >
          <el-result icon="error" title="分析失败" sub-title="DeepSeek 分析未能完成">
            <template #extra>
              <p v-if="detailData.analysis_error" class="error-detail-text">
                原因: {{ detailData.analysis_error }}
              </p>
            </template>
          </el-result>
        </div>
      </template>

      <template #footer>
        <div style="flex: 1" />
        <el-button @click="detailVisible = false">关闭</el-button>
        <el-button
          v-if="detailData?.analysis_status === 'completed'"
          type="primary"
          @click="copyResult"
        >
          复制分析结果
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  WarningFilled,
  CircleCheck,
  Clock,
  Loading,
  CloseBold,
  Refresh,
  CircleCheckFilled,
  Warning,
  List,
  MagicStick,
  View,
} from '@element-plus/icons-vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import request from '@/utils/request'

// ── 响应式检测 ──
const isMobile = ref(window.innerWidth < 768)
const handleResize = () => {
  isMobile.value = window.innerWidth < 768
}
onMounted(() => window.addEventListener('resize', handleResize))
onBeforeUnmount(() => window.removeEventListener('resize', handleResize))

// ── 数据状态 ──
const list = ref([])
const total = ref(0)
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const statusFilter = ref('')

// ── 管理员标记 ──
const isAdmin = ref(localStorage.getItem('role') === 'admin' || localStorage.getItem('role') === 'owner')

// ── 详情对话框 ──
const detailVisible = ref(false)
const detailData = ref(null)
const detailLoading = ref(false)
const detailPollTimer = ref(null) // 自动轮询定时器

// ── 状态映射 ──
const statusMap = {
  pending: { label: '排队中', tag: 'info', icon: Clock },
  processing: { label: '分析中', tag: 'warning', icon: Loading },
  completed: { label: '已完成', tag: 'success', icon: CircleCheck },
  failed: { label: '失败', tag: 'danger', icon: CloseBold },
}

function statusLabel(status) {
  return statusMap[status]?.label || status
}
function statusTagType(status) {
  return statusMap[status]?.tag || 'info'
}
function statusIcon(status) {
  return statusMap[status]?.icon || null
}

// ── 格式化时间 ──
function formatTime(isoStr) {
  if (!isoStr) return '-'
  try {
    const d = new Date(isoStr)
    const pad = (n) => String(n).padStart(2, '0')
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
  } catch {
    return isoStr
  }
}

// ── Markdown 渲染 ──
function renderMarkdown(text) {
  if (!text) return ''
  try {
    const raw = marked.parse(text, { async: false })
    return DOMPurify.sanitize(raw)
  } catch {
    return text
  }
}

// ── 获取列表数据 ──
async function fetchData() {
  loading.value = true
  try {
    const params = {
      skip: (currentPage.value - 1) * pageSize.value,
      limit: pageSize.value,
    }
    if (statusFilter.value) {
      params.analysis_status = statusFilter.value
    }

    const res = await request.get('/error-analyses', { params })
    list.value = res.data.items || []
    total.value = res.data.total || 0
  } catch (err) {
    ElMessage.error('获取错误分析列表失败')
    console.error(err)
  } finally {
    loading.value = false
  }
}

// ── 状态筛选 ──
function handleStatusChange() {
  currentPage.value = 1
  fetchData()
}

// ── 自动轮询详情（status 为 pending/processing 时） ──
function startDetailPoll(analysisId) {
  // 清除旧定时器
  if (detailPollTimer.value) {
    clearTimeout(detailPollTimer.value)
    detailPollTimer.value = null
  }

  const poll = async () => {
    try {
      const res = await request.get(`/error-analyses/${analysisId}`)
      detailData.value = res.data

      // 如果仍在等待中，继续轮询（最多 2 分钟，每 5 秒一次）
      if (res.data.analysis_status === 'pending' || res.data.analysis_status === 'processing') {
        detailPollTimer.value = setTimeout(poll, 5000)
      }
    } catch {
      // 轮询失败则静默停止
      detailPollTimer.value = null
    }
  }

  detailPollTimer.value = setTimeout(poll, 5000)
}

// ── 打开详情 ──
async function openDetail(row) {
  // 清除旧轮询
  if (detailPollTimer.value) {
    clearTimeout(detailPollTimer.value)
    detailPollTimer.value = null
  }

  detailLoading.value = true
  detailVisible.value = true
  detailData.value = null

  try {
    const res = await request.get(`/error-analyses/${row.id}`)
    detailData.value = res.data

    // 如果状态是待处理/处理中，启动自动轮询
    if (res.data.analysis_status === 'pending' || res.data.analysis_status === 'processing') {
      startDetailPoll(row.id)
    }
  } catch (err) {
    console.error(err)
    ElMessage.error('获取详情失败')
    detailVisible.value = false
  } finally {
    detailLoading.value = false
  }
}

// ── 监听详情对话框关闭 — 清除轮询 ──
// 利用 Vue 的 watchEffect 或直接在模板的 @closed 事件处理
function onDetailClosed() {
  if (detailPollTimer.value) {
    clearTimeout(detailPollTimer.value)
    detailPollTimer.value = null
  }
}

// ── 复制分析结果（Clipboard API 优先，失败回退 execCommand） ──
async function copyResult() {
  const text = detailData.value?.analysis_result
  if (!text) return

  try {
    // 方案一：Clipboard API（需 HTTPS / localhost）
    await navigator.clipboard.writeText(text)
    ElMessage.success('已复制到剪贴板')
  } catch {
    // 方案二：textarea + execCommand 回退（兼容所有环境）
    try {
      const textarea = document.createElement('textarea')
      textarea.value = text
      textarea.style.position = 'fixed'
      textarea.style.opacity = '0'
      textarea.style.left = '-9999px'
      document.body.appendChild(textarea)
      textarea.select()
      document.execCommand('copy')
      document.body.removeChild(textarea)
      ElMessage.success('已复制到剪贴板')
    } catch {
      ElMessage.error('复制失败，请手动选中文本复制')
    }
  }
}

// ── 删除分析记录 ──
function confirmDelete(row) {
  if (!row || !row.id) return
  ElMessageBox.confirm(`确定删除此错误分析记录吗？删除后无法恢复。`, '删除确认', {
    confirmButtonText: '确认删除',
    cancelButtonText: '取消',
    type: 'warning',
    confirmButtonClass: 'el-button--danger',
  })
    .then(() => deleteAnalysis(row.id))
    .catch(() => {})
}

async function deleteAnalysis(id) {
  try {
    await request.delete(`/error-analyses/${id}`)
    ElMessage.success('删除成功')
    // 如果删除的是当前打开的详情，关闭弹窗
    if (detailData.value?.id === id) {
      detailVisible.value = false
    }
    // 刷新列表
    await fetchData()
  } catch (err) {
    const msg = err.response?.data?.detail || '删除失败'
    ElMessage.error(msg)
  }
}

// ── 组件卸载时清除定时器 ──
onBeforeUnmount(() => {
  if (detailPollTimer.value) {
    clearTimeout(detailPollTimer.value)
    detailPollTimer.value = null
  }
})

// ── 初始化 ──
onMounted(() => {
  fetchData()
})
</script>

<style scoped>
/* ── 页面布局 ── */
.error-analysis-page {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  margin: 16px 0 20px;
  padding: 20px 24px;
  background: linear-gradient(135deg, #f0f5ff 0%, #f7f9fc 100%);
  border-radius: 12px;
  border: 1px solid #e8edf4;
}
.page-header h2 {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 22px;
  color: #165dff;
}
.page-desc {
  margin-top: 6px;
  color: #86909c;
  font-size: 14px;
  padding-left: 38px;
}

/* ── 信息提示 ── */
.info-alert {
  margin-bottom: 20px;
  border-radius: 10px;
}
.info-alert :deep(.el-alert__content) {
  width: 100%;
}
.info-content p {
  margin: 4px 0;
  line-height: 1.7;
  font-size: 13px;
}
.info-note {
  color: #909399;
  font-size: 12px;
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed #e5e6eb;
}

/* ── 筛选栏 ── */
.filter-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 16px;
  padding: 14px 18px;
  background: #fff;
  border-radius: 10px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
  border: 1px solid #f0f1f3;
}

/* ── 筛选栏右侧（管理员标记 + 刷新按钮） ── */
.filter-bar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}
.admin-badge {
  font-size: 12px;
  white-space: nowrap;
}

/* ── 加载状态 ── */
.loading-container {
  padding: 40px 20px;
  background: #fff;
  border-radius: 8px;
}

/* ── 桌面端表格 ── */
.desktop-table {
  background: #fff;
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
  border: 1px solid #f0f1f3;
}
.desktop-table :deep(.el-table th) {
  background-color: #f7f8fa;
  color: #4e5969;
  font-weight: 600;
  font-size: 13px;
}
.desktop-table :deep(.el-table tr) {
  cursor: pointer;
  transition: background-color 0.15s;
}
.desktop-table :deep(.el-table tr:hover > td) {
  background-color: #f5f8ff;
}

.error-type-badge {
  display: inline-block;
  padding: 3px 12px;
  background: #ecf5ff;
  color: #165dff;
  border-radius: 4px;
  font-size: 13px;
  font-weight: 500;
  font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
}
.error-msg-text {
  color: #606266;
  font-size: 13px;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.request-path {
  margin-left: 6px;
  color: #909399;
  font-size: 12px;
}
.time-text {
  color: #909399;
  font-size: 12px;
}
/* 触发用户姓名（表格列） */
.user-name-text {
  color: #4e5969;
  font-size: 13px;
  font-weight: 500;
}

/* ── 移动端卡片 ── */
.mobile-cards {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.error-card {
  background: #fff;
  border-radius: 12px;
  padding: 16px 18px;
  box-shadow: 0 1px 6px rgba(0, 0, 0, 0.04);
  border: 1px solid #f0f1f3;
  cursor: pointer;
  transition:
    transform 0.15s,
    box-shadow 0.15s;
}
.error-card:hover {
  box-shadow: 0 2px 10px rgba(22, 93, 255, 0.08);
  border-color: #d6e4f0;
}
.error-card:active {
  transform: scale(0.985);
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}
.card-time {
  font-size: 12px;
  color: #909399;
}
.card-header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}
.card-user {
  font-size: 12px;
  color: #165dff;
  font-weight: 500;
  background: #ecf5ff;
  padding: 0 8px;
  border-radius: 4px;
  line-height: 22px;
}

.card-body {
  margin-bottom: 10px;
}
.card-error-type {
  font-weight: 600;
  font-size: 15px;
  color: #303133;
  margin-bottom: 4px;
  font-family: 'SF Mono', 'Fira Code', monospace;
}
.card-error-msg {
  font-size: 13px;
  color: #606266;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
}
.card-footer-left {
  display: flex;
  align-items: center;
  gap: 6px;
  overflow: hidden;
}
.card-path {
  font-size: 12px;
  color: #909399;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* ── 分页 ── */
.pagination-bar {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
  padding: 12px 0;
}

/* ── 详情对话框 ── */
.detail-dialog :deep(.el-dialog) {
  border-radius: 12px;
  overflow: hidden;
}
.detail-dialog :deep(.el-dialog__header) {
  padding: 18px 24px;
  border-bottom: 1px solid #f0f1f3;
}
.detail-dialog :deep(.el-dialog__body) {
  padding: 22px 24px;
  max-height: 65vh;
  overflow-y: auto;
}
.detail-dialog :deep(.el-dialog__footer) {
  padding: 14px 24px;
  border-top: 1px solid #f0f1f3;
}

.detail-meta {
  margin-bottom: 22px;
}
.detail-meta :deep(.el-descriptions__cell) {
  padding: 10px 14px;
}
.detail-meta .path-cell :deep(.el-descriptions__content) {
  word-break: break-all;
  font-size: 13px;
}

.detail-section {
  margin-bottom: 22px;
}
.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 600;
  color: #1d2129;
  margin-bottom: 12px;
  padding-bottom: 10px;
  border-bottom: 1px solid #ebeef5;
}
.analysis-title {
  color: #165dff;
}

.detail-textarea {
  font-size: 13px;
}
.detail-textarea :deep(textarea) {
  background: #f8f9fb;
  border-color: #e5e6eb;
}

.traceback-block {
  background: #f8f9fb;
  border: 1px solid #e5e6eb;
  border-radius: 8px;
  padding: 14px 18px;
  font-size: 12px;
  line-height: 1.7;
  font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
  color: #4e5969;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 400px;
  overflow-y: auto;
}

/* ── DeepSeek 分析结果 ── */
.analysis-result {
  background: linear-gradient(135deg, #f5f9ff 0%, #fafcff 100%);
  border: 1px solid #d6e4f0;
  border-radius: 10px;
  padding: 20px 24px;
  line-height: 1.9;
  font-size: 14px;
  color: #2b3a4a;
}
.analysis-result :deep(h1),
.analysis-result :deep(h2),
.analysis-result :deep(h3),
.analysis-result :deep(h4) {
  margin-top: 18px;
  margin-bottom: 10px;
  color: #165dff;
  font-weight: 600;
}
.analysis-result :deep(h1) {
  font-size: 19px;
}
.analysis-result :deep(h2) {
  font-size: 17px;
  border-bottom: 1px solid #e5edf5;
  padding-bottom: 6px;
}
.analysis-result :deep(h3) {
  font-size: 15px;
}
.analysis-result :deep(p) {
  margin: 10px 0;
}
.analysis-result :deep(ul),
.analysis-result :deep(ol) {
  padding-left: 22px;
  margin: 10px 0;
}
.analysis-result :deep(li) {
  margin: 6px 0;
}
.analysis-result :deep(li::marker) {
  color: #165dff;
}
.analysis-result :deep(code) {
  background: #e8f0fe;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 13px;
  font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
  color: #165dff;
}
.analysis-result :deep(pre) {
  background: #1e1e2e;
  border-radius: 8px;
  padding: 16px 18px;
  overflow-x: auto;
  margin: 14px 0;
}
.analysis-result :deep(pre code) {
  background: transparent;
  color: #cdd6f4;
  padding: 0;
  font-size: 13px;
}
.analysis-result :deep(blockquote) {
  border-left: 4px solid #165dff;
  background: #f0f5ff;
  padding: 10px 14px;
  margin: 14px 0;
  color: #4e5969;
  border-radius: 0 6px 6px 0;
  font-size: 13px;
}
.analysis-result :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 14px 0;
  font-size: 13px;
}
.analysis-result :deep(th),
.analysis-result :deep(td) {
  border: 1px solid #d9e1ec;
  padding: 10px 14px;
  text-align: left;
}
.analysis-result :deep(th) {
  background: #eaf2fa;
  font-weight: 600;
  color: #1d2129;
}
.analysis-result :deep(strong) {
  color: #1d2129;
  font-weight: 600;
}

/* ── 状态区（pending/processing/failed） ── */
.status-section {
  padding: 24px 0;
}
.error-detail-text {
  color: #909399;
  font-size: 13px;
  margin-top: 8px;
}

/* ── 分析中脉冲动画 ── */
.status-section .is-loading {
  animation: pulse-rotate 1.4s ease-in-out infinite;
  color: #165dff;
}
@keyframes pulse-rotate {
  0%,
  100% {
    opacity: 1;
    transform: rotate(0deg);
  }
  50% {
    opacity: 0.5;
    transform: rotate(180deg);
  }
}

/* ── 响应式适配 ── */
@media (max-width: 768px) {
  .error-analysis-page {
    padding: 12px;
  }
  .page-header {
    padding: 16px 18px;
    margin: 12px 0 16px;
  }
  .page-header h2 {
    font-size: 18px;
  }
  .page-desc {
    padding-left: 0;
    font-size: 13px;
  }
  .filter-bar {
    padding: 10px 14px;
  }
  .filter-bar :deep(.el-radio-group) {
    display: flex;
    flex-wrap: nowrap;
    overflow-x: auto;
    gap: 4px;
  }
  .filter-bar :deep(.el-radio-button__inner) {
    font-size: 12px;
    padding: 6px 10px;
    white-space: nowrap;
  }
  .detail-dialog :deep(.el-dialog) {
    width: 95% !important;
    margin: 10px auto;
    border-radius: 10px;
  }
  .detail-dialog :deep(.el-dialog__body) {
    padding: 16px;
    max-height: 60vh;
  }
  .traceback-block {
    max-height: 250px;
    font-size: 11px;
  }
  .analysis-result {
    padding: 14px 16px;
    font-size: 13px;
  }
  .pagination-bar :deep(.el-pagination) {
    flex-wrap: wrap;
    justify-content: center;
  }
}

/* ── 暗色代码块优化 ── */
.markdown-body {
  word-break: break-word;
}
</style>
