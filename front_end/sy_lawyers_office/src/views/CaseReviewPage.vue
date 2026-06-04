<template>
  <div class="case-review-page">
    <!-- ========== 顶部统计卡片 ========== -->
    <div class="stats-row">
      <div class="stat-card stat-pending" @click="switchTab('待审核')">
        <div class="stat-num">{{ stats.pending }}</div>
        <div class="stat-label">待审核</div>
      </div>
      <div class="stat-card stat-approved" @click="switchTab('已审核')">
        <div class="stat-num">{{ stats.approved }}</div>
        <div class="stat-label">近7天已审核</div>
      </div>
      <div class="stat-card stat-rejected" @click="switchTab('已拒绝')">
        <div class="stat-num">{{ stats.rejected }}</div>
        <div class="stat-label">近7天已拒绝</div>
      </div>
    </div>

    <!-- ========== Tab 切换栏 ========== -->
    <div class="tab-bar">
      <div
        class="tab-item"
        :class="{ active: activeTab === '待审核' }"
        @click="switchTab('待审核')"
      >
        <el-badge :value="stats.pending" :hidden="stats.pending === 0" class="tab-badge">
          <span>待审核</span>
        </el-badge>
      </div>
      <div
        class="tab-item"
        :class="{ active: activeTab === '已审核' }"
        @click="switchTab('已审核')"
      >
        <el-badge :value="stats.approved" :hidden="stats.approved === 0" class="tab-badge">
          <span>已审核</span>
        </el-badge>
      </div>
      <div
        class="tab-item"
        :class="{ active: activeTab === '已拒绝' }"
        @click="switchTab('已拒绝')"
      >
        <el-badge :value="stats.rejected" :hidden="stats.rejected === 0" class="tab-badge">
          <span>已拒绝</span>
        </el-badge>
      </div>
    </div>

    <!-- ========== 待审核 Tab - 批量操作栏 ========== -->
    <div v-if="activeTab === '待审核'" class="bulk-bar">
      <div class="bulk-left">
        <el-checkbox
          v-model="isAllSelected"
          :indeterminate="isIndeterminate"
          @change="toggleSelectAll"
          :disabled="!casesList.length"
        >
          全选当前页
        </el-checkbox>
        <span class="selected-count" v-if="selectedCases.length">
          已选 {{ selectedCases.length }} 项
        </span>
      </div>
      <div class="bulk-right">
        <el-button
          type="success"
          size="small"
          :disabled="!selectedCases.length"
          @click="batchReview('已审核')"
          :icon="CircleCheck"
        >
          批量通过
        </el-button>
        <el-button
          type="danger"
          size="small"
          :disabled="!selectedCases.length"
          @click="batchReview('已拒绝')"
          :icon="CircleClose"
        >
          批量拒绝
        </el-button>
      </div>
    </div>

    <!-- ========== 已审核 / 已拒绝 Tab 提示条 ========== -->
    <div v-if="activeTab !== '待审核'" class="info-bar">
      <el-alert
        :title="`近 7 天内您审核通过的 ${activeTab} 业务`"
        type="info"
        :closable="false"
        show-icon
      />
    </div>

    <!-- ========== 桌面端表格视图 ========== -->
    <div class="table-wrapper" v-show="!isMobile">
      <el-table
        ref="caseTableRef"
        :data="casesList"
        style="width: 100%"
        border
        stripe
        v-loading="tableLoading"
        @selection-change="handleSelectionChange"
        :row-class-name="tableRowClassName"
        empty-text="暂无业务数据"
      >
        <!-- 多选框 - 仅待审核显示 -->
        <el-table-column v-if="activeTab === '待审核'" type="selection" width="48" fixed="left" />

        <!-- 业务号 -->
        <el-table-column label="业务号" min-width="150">
          <template #default="{ row }">
            <span class="link-text" @click="navigateToDetail(row.case_id)">{{
              row.case_number
            }}</span>
          </template>
        </el-table-column>

        <!-- 委托人 -->
        <el-table-column label="委托人" min-width="110">
          <template #default="{ row }">
            {{ getClientNames(row.parties) || '-' }}
          </template>
        </el-table-column>

        <!-- 业务类别 -->
        <el-table-column prop="case_category" label="业务类别" min-width="100" />

        <!-- 主办律师 -->
        <el-table-column prop="main_lawyer.real_name" label="主办律师" min-width="90" />

        <!-- 创建时间 -->
        <el-table-column label="创建时间" min-width="155" align="center">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>

        <!-- 审核时间 - 仅已审核/已拒绝 -->
        <el-table-column
          v-if="activeTab !== '待审核'"
          label="审核时间"
          min-width="155"
          align="center"
        >
          <template #default="{ row }">
            {{ formatDate(row.reviewed_at) }}
          </template>
        </el-table-column>

        <!-- 审核意见 - 仅已拒绝 -->
        <el-table-column v-if="activeTab === '已拒绝'" label="审核意见" min-width="160">
          <template #default="{ row }">
            <el-tooltip :content="row.review_comment || '无'" placement="top">
              <span class="comment-text">{{
                row.review_comment ? truncate(row.review_comment, 20) : '-'
              }}</span>
            </el-tooltip>
          </template>
        </el-table-column>

        <!-- 操作列 -->
        <el-table-column label="操作" min-width="160" fixed="right">
          <template #default="{ row }">
            <div class="action-buttons">
              <!-- 待审核：通过/拒绝 -->
              <template v-if="activeTab === '待审核'">
                <el-button type="success" size="small" plain @click="review(row, '已审核')"
                  >通过</el-button
                >
                <el-button type="danger" size="small" plain @click="review(row, '已拒绝')"
                  >拒绝</el-button
                >
              </template>
              <!-- 已审核/已拒绝：撤回审核 -->
              <template v-else>
                <el-button type="warning" size="small" plain @click="revertReview(row)">
                  <el-icon style="margin-right: 3px"><Refresh /></el-icon>撤回审核
                </el-button>
              </template>
              <!-- 查看详情 -->
              <el-button size="small" @click="navigateToDetail(row.case_id)">详情</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- ========== 移动端卡片视图 ========== -->
    <div class="card-list" v-show="isMobile" v-loading="tableLoading">
      <div v-if="!casesList.length" class="empty-state">
        <el-empty description="暂无业务数据" />
      </div>
      <div
        v-for="item in casesList"
        :key="item.case_id"
        class="case-card"
        :class="'card-' + activeTab"
      >
        <!-- 卡片头部 -->
        <div class="card-header" @click="navigateToDetail(item.case_id)">
          <span class="card-number">{{ item.case_number }}</span>
          <span class="card-status" :class="'status-' + activeTab">
            {{ activeTab }}
          </span>
        </div>

        <!-- 卡片主体 -->
        <div class="card-body">
          <div class="card-row">
            <span class="card-label">委托人</span>
            <span class="card-value">{{ getClientNames(item.parties) || '-' }}</span>
          </div>
          <div class="card-row">
            <span class="card-label">类别</span>
            <span class="card-value">{{ item.case_category }}</span>
          </div>
          <div class="card-row">
            <span class="card-label">主办律师</span>
            <span class="card-value">{{ item.main_lawyer?.real_name || '-' }}</span>
          </div>
          <div class="card-row">
            <span class="card-label">创建时间</span>
            <span class="card-value">{{ formatDate(item.created_at) }}</span>
          </div>
          <div v-if="activeTab !== '待审核'" class="card-row">
            <span class="card-label">审核时间</span>
            <span class="card-value">{{ formatDate(item.reviewed_at) }}</span>
          </div>
          <div v-if="activeTab === '已拒绝' && item.review_comment" class="card-row">
            <span class="card-label">审核意见</span>
            <span class="card-value comment">{{ item.review_comment }}</span>
          </div>
        </div>

        <!-- 卡片操作 -->
        <div class="card-actions">
          <template v-if="activeTab === '待审核'">
            <el-button type="success" size="small" @click="review(item, '已审核')">通过</el-button>
            <el-button type="danger" size="small" @click="review(item, '已拒绝')">拒绝</el-button>
          </template>
          <template v-else>
            <el-button type="warning" size="small" plain @click="revertReview(item)">
              <el-icon style="margin-right: 3px"><Refresh /></el-icon>撤回审核
            </el-button>
          </template>
          <el-button size="small" @click="navigateToDetail(item.case_id)">详情</el-button>
        </div>
      </div>
    </div>

    <!-- ========== 分页 ========== -->
    <div class="pagination-container">
      <el-pagination
        background
        :layout="isMobile ? 'prev, pager, next' : 'total, sizes, prev, pager, next, jumper'"
        :page-sizes="[10, 20, 50, 100]"
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :total="total"
        :pager-count="isMobile ? 5 : 7"
        @current-change="handlePageChange"
        @size-change="handleSizeChange"
      />
    </div>

    <!-- ========== 批量审核进度弹窗 ========== -->
    <el-dialog
      v-model="showBatchProgress"
      title="批量审核进度"
      width="400px"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      :show-close="false"
    >
      <div class="batch-progress-body">
        <el-progress
          type="dashboard"
          :percentage="batchTotal === 0 ? 0 : Math.round((batchProgress / batchTotal) * 100)"
          :status="batchProgress >= batchTotal ? 'success' : undefined"
        >
          <template #default>
            <span class="batch-progress-num">{{ batchProgress }} / {{ batchTotal }}</span>
          </template>
        </el-progress>
        <div class="batch-progress-stats">
          <span class="bp-success"
            ><el-icon><CircleCheck /></el-icon> 成功: {{ batchSuccessCount }}</span
          >
          <span class="bp-fail"
            ><el-icon><CircleClose /></el-icon> 跳过/失败: {{ batchFailCount }}</span
          >
        </div>
        <p v-if="batchProgress < batchTotal" class="batch-progress-hint">
          正在处理中，遇到冲突会弹窗提示，请勿刷新页面...
        </p>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { CircleCheck, CircleClose, Refresh } from '@element-plus/icons-vue'
import request from '@/utils/request'
import { useRouter } from 'vue-router'

const router = useRouter()

// ---------- 辅助函数 ----------
const getClientNames = (parties) => {
  if (!parties || !parties.length) return ''
  return parties
    .filter((p) => p.party_type && p.party_type.includes('委托'))
    .map((p) => p.name)
    .join('、')
}

const truncate = (str, len) => {
  if (!str) return ''
  return str.length > len ? str.slice(0, len) + '…' : str
}

// ---------- 响应式 ----------
const screenWidth = ref(window.innerWidth)
const isMobile = computed(() => screenWidth.value < 768)

const handleResize = () => {
  screenWidth.value = window.innerWidth
}

// ---------- Tab 切换 ----------
const activeTab = ref('待审核')

const switchTab = (tab) => {
  activeTab.value = tab
  page.value = 1
  selectedCases.value = []
  isAllSelected.value = false
  isIndeterminate.value = false
  fetchCases()
}

// ---------- 统计 ----------
const stats = ref({ pending: 0, approved: 0, rejected: 0 })

const fetchStats = async () => {
  try {
    const [pendingRes, approvedRes, rejectedRes] = await Promise.all([
      request.get('/case_review/pending', { params: { limit: 1 } }),
      request.get('/case_review/pending', { params: { review_status: '已审核', limit: 1 } }),
      request.get('/case_review/pending', { params: { review_status: '已拒绝', limit: 1 } }),
    ])
    stats.value = {
      pending: pendingRes.data.total || 0,
      approved: approvedRes.data.total || 0,
      rejected: rejectedRes.data.total || 0,
    }
  } catch {
    // 静默失败
  }
}

// ---------- 表格数据 ----------
const casesList = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const tableLoading = ref(false)
const caseTableRef = ref(null)

const fetchCases = async () => {
  tableLoading.value = true
  try {
    const params = {
      skip: (page.value - 1) * pageSize.value,
      limit: pageSize.value,
    }
    // 非待审核 Tab 传 review_status
    if (activeTab.value !== '待审核') {
      params.review_status = activeTab.value
    }
    const res = await request.get('/case_review/pending', { params })
    casesList.value = res.data.items || []
    total.value = res.data.total || 0
  } catch (err) {
    console.error('获取业务列表失败:', err)
    ElMessage.error(err.response?.data?.detail || '获取业务列表失败')
    casesList.value = []
    total.value = 0
  } finally {
    tableLoading.value = false
  }
}

// ---------- 多选（仅待审核 Tab） ----------
const selectedCases = ref([])
const isAllSelected = ref(false)
const isIndeterminate = ref(false)

const handleSelectionChange = (val) => {
  selectedCases.value = val
  const totalCount = casesList.value.length
  if (val.length === 0) {
    isAllSelected.value = false
    isIndeterminate.value = false
  } else if (val.length === totalCount) {
    isAllSelected.value = true
    isIndeterminate.value = false
  } else {
    isAllSelected.value = false
    isIndeterminate.value = true
  }
}

const toggleSelectAll = (checked) => {
  if (!caseTableRef.value) return
  if (checked) {
    casesList.value.forEach((row) => caseTableRef.value.toggleRowSelection(row, true))
  } else {
    caseTableRef.value.clearSelection()
  }
}

// ---------- 利益冲突对话框 ----------
const showConflictDialog = (conflicts, caseId, caseNumber) => {
  return new Promise((resolve) => {
    const conflictItemsHtml = conflicts
      .map((c) => {
        const isFuzzy = c.match_level === 'fuzzy'
        const themeColor = isFuzzy ? '#E6A23C' : '#f56c6c'
        const tagText = isFuzzy ? '疑似匹配' : '匹配冲突'

        return `
        <li style="margin-bottom: 15px; line-height: 1.6; border-bottom: 1px dashed #ebeef5; padding-bottom: 10px;">
          <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
            <span style="font-weight: bold; color: #303133;">${c.conflict_type}</span>
            <span style="font-size: 12px; color: ${themeColor}; border: 1px solid ${themeColor}; padding: 1px 6px; border-radius: 3px; background: ${isFuzzy ? '#fdf6ec' : '#fef0f0'};">
              ${tagText}
            </span>
          </div>
          <div style="font-size: 13px; color: #606266; margin-bottom: 4px;">
            关联业务：
            <a href="/main/cases/${c.case_id}" target="_blank" style="color: #409eff; text-decoration: underline; font-weight: bold;">
              ${c.case_number}
            </a>
            <span style="margin-left: 10px;">(主办: ${c.other_lawyer_name})</span>
          </div>
          <div style="font-size: 13px; color: ${themeColor};">
            说明：${c.message}
          </div>
        </li>`
      })
      .join('')

    const html = `<div style="max-height: 400px; overflow-y: auto;">
      <p style="color: #e6a23c; margin-bottom: 15px; font-size: 15px;">
        <i class="el-icon-warning"></i>
        业务 <strong>${caseNumber}</strong> 存在潜在的利益冲突风险，请仔细核实。
      </p>
      <div style="background: #fafafa; padding: 15px; border-radius: 4px; border: 1px solid #ebeef5;">
        <ul style="margin: 0; padding-left: 15px;">${conflictItemsHtml}</ul>
      </div>
      <p style="margin-top: 15px; font-size: 13px; color: #909399;">
        提示：点击业务号可新窗口打开详情。确认"强制通过"将忽略上述冲突。
      </p>
    </div>`

    ElMessageBox.confirm(html, '存在利益冲突风险', {
      dangerouslyUseHTMLString: true,
      confirmButtonText: '强制通过',
      cancelButtonText: '取消审核',
      type: 'warning',
      customClass: 'conflict-dialog',
      closeOnClickModal: false,
    })
      .then(() => resolve(true))
      .catch(() => resolve(false))
  })
}

// ---------- 单条审核 ----------
const sendReviewRequest = async (row, status, force, reviewComment = '') => {
  const params = { review_status: status, force }
  if (reviewComment) params.review_comment = reviewComment
  await request.put(`/case_review/${row.case_id}/review`, null, { params })
}

const review = async (row, status) => {
  let reviewComment = ''
  if (status === '已拒绝') {
    try {
      const { value } = await ElMessageBox.prompt(
        `请输入对业务「${row.case_number}」的修改建议或拒绝原因：`,
        '填写审核意见',
        {
          confirmButtonText: '确认拒绝',
          cancelButtonText: '取消',
          inputType: 'textarea',
          inputPlaceholder: '请详细说明需要修改的内容...',
          inputValidator: (val) => (!val || !val.trim() ? '请输入拒绝原因或修改建议' : true),
        },
      )
      reviewComment = value.trim()
    } catch {
      return
    }
  }

  try {
    await sendReviewRequest(row, status, false, reviewComment)
    ElMessage.success(`业务已${status === '已审核' ? '通过' : '拒绝'}`)
    fetchCases()
    fetchStats()
  } catch (err) {
    if (err.response?.status === 409 && err.response?.data?.detail?.conflicts) {
      const conflictData = err.response.data.detail
      const userConfirmed = await showConflictDialog(
        conflictData.conflicts,
        row.case_id,
        row.case_number,
      )
      if (userConfirmed) {
        try {
          await sendReviewRequest(row, status, true, reviewComment)
          ElMessage.warning(`已忽略冲突，强制通过业务 ${row.case_number}`)
          fetchCases()
          fetchStats()
        } catch (retryErr) {
          ElMessage.error('强制操作失败: ' + (retryErr.response?.data?.detail || '未知错误'))
        }
      }
    } else {
      ElMessage.error(
        err.response?.data?.detail?.message || err.response?.data?.detail || '审核操作失败',
      )
    }
  }
}

// ---------- 撤回审核 ----------
const revertReview = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要将业务「${row.case_number}」的审核状态撤回为「待审核」吗？`,
      '撤回审核确认',
      {
        type: 'warning',
        confirmButtonText: '确认撤回',
        cancelButtonText: '取消',
        confirmButtonClass: 'el-button--warning',
      },
    )
    await sendReviewRequest(row, '待审核', true)
    ElMessage.success(`业务 ${row.case_number} 已撤回为待审核`)
    fetchCases()
    fetchStats()
  } catch (err) {
    if (err !== 'cancel') {
      ElMessage.error('撤回审核失败: ' + (err.response?.data?.detail || '未知错误'))
    }
  }
}

// ---------- 批量审核 ----------
const batchProgress = ref(0)
const batchTotal = ref(0)
const batchSuccessCount = ref(0)
const batchFailCount = ref(0)
const showBatchProgress = ref(false)

const batchReview = async (status) => {
  if (!selectedCases.value.length) return

  let batchComment = ''
  if (status === '已拒绝') {
    try {
      const { value } = await ElMessageBox.prompt(
        `请输入对选中的 ${selectedCases.value.length} 个业务的统一修改建议：`,
        '填写批量审核意见',
        {
          confirmButtonText: '确认批量拒绝',
          cancelButtonText: '取消',
          inputType: 'textarea',
          inputPlaceholder: '请说明需要修改的共性问题（可留空）...',
        },
      )
      batchComment = (value || '').trim()
    } catch {
      return
    }
  }

  try {
    await ElMessageBox.confirm(
      `确定要将选中的 ${selectedCases.value.length} 个业务标记为「${status}」吗？`,
      '批量审核确认',
      { type: status === '已审核' ? 'success' : 'warning' },
    )

    batchTotal.value = selectedCases.value.length
    batchProgress.value = 0
    batchSuccessCount.value = 0
    batchFailCount.value = 0
    showBatchProgress.value = true

    const CHUNK_SIZE = 50

    for (let i = 0; i < selectedCases.value.length; i += CHUNK_SIZE) {
      const chunk = selectedCases.value.slice(i, i + CHUNK_SIZE)
      const chunkIds = chunk.map((item) => item.case_id)

      try {
        const res = await request.post('/case_review/batch_review', {
          case_ids: chunkIds,
          review_status: status,
          force_ids: [],
          review_comment: batchComment || null,
        })

        const { success_cases, conflict_cases, error_cases } = res.data

        batchSuccessCount.value += success_cases.length
        batchFailCount.value += error_cases.length
        batchProgress.value += success_cases.length + error_cases.length

        if (conflict_cases && conflict_cases.length > 0) {
          for (const conflictItem of conflict_cases) {
            const userConfirmed = await showConflictDialog(
              conflictItem.conflicts,
              conflictItem.case_id,
              conflictItem.case_number,
            )
            if (userConfirmed) {
              try {
                await sendReviewRequest(
                  { case_id: conflictItem.case_id },
                  status,
                  true,
                  batchComment,
                )
                batchSuccessCount.value++
              } catch {
                batchFailCount.value++
              }
            } else {
              batchFailCount.value++
            }
            batchProgress.value++
          }
        }
      } catch {
        batchFailCount.value += chunk.length
        batchProgress.value += chunk.length
      }
    }

    setTimeout(() => {
      showBatchProgress.value = false
      ElMessage({
        message: `批量操作结束！成功 ${batchSuccessCount.value} 笔，跳过/失败 ${batchFailCount.value} 笔。`,
        type: batchFailCount.value > 0 ? 'warning' : 'success',
        duration: 5000,
      })
      selectedCases.value = []
      isAllSelected.value = false
      isIndeterminate.value = false
      if (caseTableRef.value) caseTableRef.value.clearSelection()
      fetchCases()
      fetchStats()
    }, 800)
  } catch (err) {
    if (err !== 'cancel') {
      ElMessage.error('批量审核发生错误')
    }
  }
}

// ---------- 导航 ----------
const navigateToDetail = (caseId) => {
  const routeData = router.resolve({
    path: `/main/cases/${caseId}`,
    query: { from: '/main/case_review' },
  })
  window.open(routeData.href, '_blank')
}

// ---------- 分页 ----------
const handleSizeChange = (size) => {
  pageSize.value = size
  page.value = 1
  fetchCases()
}

const handlePageChange = (p) => {
  page.value = p
  fetchCases()
}

// ---------- 表格行样式 ----------
const tableRowClassName = () => {
  if (activeTab.value === '已拒绝') return 'row-rejected'
  if (activeTab.value === '已审核') return 'row-approved'
  return ''
}

// ---------- 日期格式化 ----------
const formatDate = (dateVal) => {
  if (!dateVal) return ''
  let timestamp
  if (typeof dateVal === 'number') {
    timestamp = dateVal.toString().length === 10 ? dateVal * 1000 : dateVal
  } else if (typeof dateVal === 'string') {
    const d = new Date(dateVal.replace(' ', 'T'))
    if (!isNaN(d.getTime())) timestamp = d.getTime()
  } else if (dateVal instanceof Date) {
    timestamp = dateVal.getTime()
  }
  if (!timestamp || isNaN(timestamp)) return '无效日期'
  return new Date(timestamp).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  })
}

// ---------- 生命周期 ----------
onMounted(() => {
  fetchStats()
  fetchCases()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
/* ========== 整体布局 ========== */
.case-review-page {
  padding: 20px;
  max-width: 1600px;
  margin: 0 auto;
}

/* ========== 统计卡片行 ========== */
.stats-row {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.stat-card {
  flex: 1;
  min-width: 120px;
  padding: 18px 20px;
  border-radius: 10px;
  cursor: pointer;
  transition:
    transform 0.2s,
    box-shadow 0.2s;
  user-select: none;
  text-align: center;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.stat-pending {
  background: linear-gradient(135deg, #eef2ff, #e0e7ff);
  border: 1px solid #c7d2fe;
}
.stat-approved {
  background: linear-gradient(135deg, #ecfdf5, #d1fae5);
  border: 1px solid #a7f3d0;
}
.stat-rejected {
  background: linear-gradient(135deg, #fef2f2, #fde8e8);
  border: 1px solid #fecaca;
}

.stat-num {
  font-size: 32px;
  font-weight: 700;
  line-height: 1.2;
}

.stat-pending .stat-num {
  color: #4f46e5;
}
.stat-approved .stat-num {
  color: #059669;
}
.stat-rejected .stat-num {
  color: #dc2626;
}

.stat-label {
  font-size: 13px;
  color: #6b7280;
  margin-top: 4px;
}

/* ========== Tab 栏 ========== */
.tab-bar {
  display: flex;
  gap: 0;
  margin-bottom: 16px;
  border-bottom: 2px solid #e5e7eb;
}

.tab-item {
  padding: 10px 24px;
  font-size: 15px;
  cursor: pointer;
  color: #6b7280;
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
  transition:
    color 0.2s,
    border-color 0.2s;
  user-select: none;
  position: relative;
}

.tab-item:hover {
  color: #374151;
}

.tab-item.active {
  color: #4f46e5;
  border-bottom-color: #4f46e5;
  font-weight: 600;
}

.tab-badge :deep(.el-badge__content) {
  font-size: 11px;
  height: 18px;
  line-height: 18px;
  padding: 0 6px;
}

/* ========== 待审核 - 批量操作栏 ========== */
.bulk-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  margin-bottom: 16px;
  flex-wrap: wrap;
  gap: 10px;
}

.bulk-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.selected-count {
  font-size: 13px;
  color: #6b7280;
}

.bulk-right {
  display: flex;
  gap: 8px;
}

/* ========== 提示条 ========== */
.info-bar {
  margin-bottom: 16px;
}

/* ========== 表格 ========== */
.table-wrapper {
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #e5e7eb;
}

.link-text {
  color: #4f46e5;
  cursor: pointer;
  font-weight: 500;
}

.link-text:hover {
  text-decoration: underline;
}

.comment-text {
  color: #6b7280;
  font-size: 13px;
}

.action-buttons {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

/* 表格行颜色 */
:deep(.row-rejected) {
  background-color: #fef2f2;
}
:deep(.row-approved) {
  background-color: #f0fdf4;
}

/* ========== 移动端卡片 ========== */
.card-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.case-card {
  background: #fff;
  border-radius: 10px;
  border: 1px solid #e5e7eb;
  overflow: hidden;
  transition: box-shadow 0.2s;
}

.case-card:hover {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 14px;
  cursor: pointer;
  border-bottom: 1px solid #f3f4f6;
}

.card-number {
  font-weight: 600;
  font-size: 14px;
  color: #4f46e5;
}

.card-status {
  font-size: 12px;
  padding: 2px 10px;
  border-radius: 10px;
  font-weight: 500;
}

.status-待审核 {
  background: #eef2ff;
  color: #4f46e5;
  border: 1px solid #c7d2fe;
}
.status-已审核 {
  background: #ecfdf5;
  color: #059669;
  border: 1px solid #a7f3d0;
}
.status-已拒绝 {
  background: #fef2f2;
  color: #dc2626;
  border: 1px solid #fecaca;
}

.card-body {
  padding: 10px 14px;
}

.card-row {
  display: flex;
  padding: 4px 0;
  font-size: 13px;
}

.card-label {
  width: 64px;
  flex-shrink: 0;
  color: #9ca3af;
}

.card-value {
  color: #374151;
  flex: 1;
  word-break: break-all;
}

.card-value.comment {
  color: #dc2626;
  font-size: 12px;
}

.card-actions {
  display: flex;
  gap: 8px;
  padding: 10px 14px;
  border-top: 1px solid #f3f4f6;
  flex-wrap: wrap;
}

/* ========== 空状态 ========== */
.empty-state {
  padding: 40px 0;
}

/* ========== 分页 ========== */
.pagination-container {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}

/* ========== 批量进度弹窗 ========== */
.batch-progress-body {
  text-align: center;
  padding: 10px 0;
}

.batch-progress-num {
  font-size: 22px;
  font-weight: bold;
}

.batch-progress-stats {
  margin-top: 18px;
  display: flex;
  justify-content: center;
  gap: 24px;
  font-size: 14px;
}

.bp-success {
  color: #67c23a;
}
.bp-fail {
  color: #f56c6c;
}

.batch-progress-hint {
  margin-top: 14px;
  color: #909399;
  font-size: 13px;
}

/* ========== 冲突对话框 ========== */
:deep(.conflict-dialog) {
  width: 90% !important;
  max-width: 600px !important;
}
:deep(.conflict-dialog .el-message-box__content) {
  max-height: 55vh;
  overflow-y: auto;
}

/* ========== 移动端适配 ========== */
@media screen and (max-width: 768px) {
  .case-review-page {
    padding: 12px;
  }

  .stats-row {
    gap: 10px;
  }

  .stat-card {
    padding: 14px 12px;
    min-width: 80px;
  }

  .stat-num {
    font-size: 24px;
  }

  .tab-item {
    padding: 10px 14px;
    font-size: 14px;
  }

  .bulk-bar {
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
  }

  .bulk-right {
    justify-content: stretch;
  }

  .bulk-right .el-button {
    flex: 1;
  }

  .pagination-container {
    justify-content: center;
  }
}
</style>
