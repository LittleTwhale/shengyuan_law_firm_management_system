<template>
  <div class="case-review-page">
    <div class="header">
      <h2>业务审核</h2>
      <div class="bulk-actions">
        <el-button
          type="primary"
          size="small"
          @click="toggleSelectAll"
          :disabled="!casesList.length"
        >
          {{ isAllSelected ? '取消全选' : '全选当前页' }}
        </el-button>

        <el-button
          type="success"
          size="small"
          :disabled="!selectedCases.length"
          @click="batchReview('已审核')"
          >批量通过</el-button
        >

        <el-button
          type="danger"
          size="small"
          :disabled="!selectedCases.length"
          @click="batchReview('已拒绝')"
          >批量拒绝</el-button
        >
      </div>
    </div>

    <el-table
      ref="caseTableRef"
      :data="casesList"
      style="width: 100%"
      border
      v-loading="tableLoading"
      @selection-change="handleSelectionChange"
    >
      <el-table-column type="selection" width="55" fixed="left" />
      <el-table-column prop="case_id" label="案件ID" min-width="80" />
      <el-table-column prop="case_number" label="案件编号" min-width="150" />
      <el-table-column label="委托人" min-width="100">
        <template #default="{ row }">
          {{ getClientNames(row.parties) || '-' }}
        </template>
      </el-table-column>
      <el-table-column prop="case_category" label="案件类别" min-width="120" />
      <el-table-column prop="main_lawyer.real_name" label="主办律师" min-width="100" />
      <el-table-column
        prop="created_at"
        label="创建时间"
        align="center"
        min-width="160"
        :formatter="(row, column, cellValue) => formatDate(cellValue)"
      />

      <el-table-column label="案件详情" min-width="140">
        <template #default="scope">
          <div
            class="detail-cell"
            @click="navigateToDetail(scope.row.case_id)"
            title="点击查看详情"
          >
            点击查看完整信息
          </div>
        </template>
      </el-table-column>

      <el-table-column label="操作" min-width="140" fixed="right">
        <template #default="scope">
          <div class="action-buttons">
            <el-button type="success" size="small" @click="review(scope.row, '已审核')"
              >通过</el-button
            >
            <el-button type="danger" size="small" @click="review(scope.row, '已拒绝')"
              >拒绝</el-button
            >
          </div>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination-container">
      <el-pagination
        background
        :layout="isMobile ? 'prev, pager, next' : 'total, sizes, prev, pager, next, jumper'"
        :page-sizes="[10, 20, 50, 100, 500, 1000]"
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :total="total"
        :pager-count="isMobile ? 5 : 7"
        @current-change="handlePageChange"
        @size-change="handleSizeChange"
      />
    </div>

    <el-dialog
      v-model="showBatchProgress"
      title="批量审核进度"
      width="400px"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      :show-close="false"
    >
      <div style="text-align: center; padding: 20px 0">
        <el-progress
          type="dashboard"
          :percentage="batchTotal === 0 ? 0 : Math.round((batchProgress / batchTotal) * 100)"
        >
          <template #default>
            <span style="font-size: 20px; font-weight: bold"
              >{{ batchProgress }} / {{ batchTotal }}</span
            >
          </template>
        </el-progress>
        <div style="margin-top: 20px; font-size: 14px; color: #606266">
          <span style="color: #67c23a; margin-right: 15px">
            <i class="el-icon-check"></i> 成功: {{ batchSuccessCount }}
          </span>
          <span style="color: #f56c6c">
            <i class="el-icon-close"></i> 跳过/失败: {{ batchFailCount }}
          </span>
        </div>
        <p
          v-if="batchProgress < batchTotal"
          style="margin-top: 15px; color: #909399; font-size: 12px"
        >
          正在处理中，遇到冲突会弹窗提示，请勿刷新页面...
        </p>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/utils/request'
import { useRouter } from 'vue-router'

const router = useRouter()

// 辅助函数：从 parties 中提取委托人名称
const getClientNames = (parties) => {
  if (!parties || !parties.length) return ''
  return parties
    .filter(p => p.party_type && p.party_type.includes('委托'))
    .map(p => p.name)
    .join('、')
}

// 表格数据
const casesList = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const tableLoading = ref(false)
const caseTableRef = ref(null)

// 响应式屏幕判断
const screenWidth = ref(window.innerWidth)
const isMobile = computed(() => screenWidth.value < 768)

const handleResize = () => {
  screenWidth.value = window.innerWidth
}

// 多选状态
const selectedCases = ref([])
const isAllSelected = ref(false)

// 批量审核进度相关状态
const showBatchProgress = ref(false)
const batchProgress = ref(0)
const batchTotal = ref(0)
const batchSuccessCount = ref(0)
const batchFailCount = ref(0)

// 监听勾选变化
const handleSelectionChange = (val) => {
  selectedCases.value = val
  isAllSelected.value = val.length === casesList.value.length && val.length > 0
}

// 切换全选/取消全选
const toggleSelectAll = () => {
  if (!caseTableRef.value) return
  if (isAllSelected.value) {
    caseTableRef.value.clearSelection()
  } else {
    casesList.value.forEach((row) => {
      caseTableRef.value.toggleRowSelection(row, true)
    })
  }
}

// 利益冲突确认对话框
const showConflictDialog = (conflicts, caseId, caseNumber) => {
  return new Promise((resolve) => {
    // 提取并映射 HTML
    const conflictItemsHtml = conflicts
      .map((c) => {
        const isFuzzy = c.match_level === 'fuzzy'
        const themeColor = isFuzzy ? '#E6A23C' : '#f56c6c'
        const tagText = isFuzzy ? '疑似匹配' : '匹配冲突'

        return `
        <li style="margin-bottom: 15px; line-height: 1.5; border-bottom: 1px dashed #ebeef5; padding-bottom: 10px;">
          <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
            <span style="font-weight: bold; color: #303133;">${c.conflict_type}</span>
            <span style="font-size: 12px; color: ${themeColor}; border: 1px solid ${themeColor}; padding: 1px 6px; border-radius: 3px; background-color: ${isFuzzy ? '#fdf6ec' : '#fef0f0'};">
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
        </li>
      `
      })
      .join('')

    let conflictHtml = `<div style="max-height: 400px; overflow-y: auto;">
      <p style="color: #e6a23c; margin-bottom: 15px; font-size: 15px;">
        <i class="el-icon-warning"></i>
        案件 <strong>${caseNumber}</strong> 存在潜在的利益冲突风险，请仔细核实。
      </p>
      <div style="background: #fafafa; padding: 15px; border-radius: 4px; border: 1px solid #ebeef5;">
        <ul style="margin: 0; padding-left: 15px;">
          ${conflictItemsHtml}
        </ul>
      </div>
      <p style="margin-top: 15px; font-size: 13px; color: #909399;">
        提示：点击业务号可新窗口打开详情。确认“强制通过”将忽略上述冲突。
      </p>
    </div>`

    ElMessageBox.confirm(conflictHtml, '存在利益冲突风险', {
      dangerouslyUseHTMLString: true,
      confirmButtonText: '强制通过',
      cancelButtonText: '取消审核',
      type: 'warning',
      customClass: 'conflict-dialog',
      closeOnClickModal: false,
    })
      .then(() => {
        resolve(true) // 用户选择强制通过
      })
      .catch(() => {
        resolve(false) // 用户取消
      })
  })
}

// 审核操作
const review = async (row, status) => {
  // 拒绝时弹出输入框，要求填写修改建议
  let reviewComment = ''
  if (status === '已拒绝') {
    try {
      const { value } = await ElMessageBox.prompt(
        `请输入对案件「${row.case_number}」的修改建议或拒绝原因：`,
        '填写审核意见',
        {
          confirmButtonText: '确认拒绝',
          cancelButtonText: '取消',
          inputType: 'textarea',
          inputPlaceholder: '请详细说明需要修改的内容...',
          inputValidator: (val) => {
            if (!val || !val.trim()) {
              return '请输入拒绝原因或修改建议'
            }
            return true
          },
        },
      )
      reviewComment = value.trim()
    } catch {
      // 用户取消输入，终止审核操作
      return
    }
  }

  try {
    // 第一次尝试请求 (force = false)
    await sendReviewRequest(row, status, false, reviewComment)

    ElMessage.success(`案件已${status === '已审核' ? '通过' : '拒绝'}`)
    await fetchPendingCases()
  } catch (err) {
    // 捕获 409 冲突
    if (err.response?.status === 409 && err.response?.data?.detail?.conflicts) {
      const conflictData = err.response.data.detail

      // 弹出对话框
      const userConfirmed = await showConflictDialog(
        conflictData.conflicts,
        row.case_id,
        row.case_number,
      )

      if (userConfirmed) {
        // 用户确认强制通过，再次请求 (force = true)
        try {
          await sendReviewRequest(row, status, true, reviewComment)
          ElMessage.warning(`已忽略冲突，强制通过案件 ${row.case_number}`)
          await fetchPendingCases()
        } catch (retryErr) {
          console.error('强制审核失败:', retryErr)
          ElMessage.error('强制操作失败: ' + (retryErr.response?.data?.detail || '未知错误'))
        }
      }
    } else {
      // 其他常规错误
      console.error('审核失败:', err)
      ElMessage.error(
        err.response?.data?.detail?.message || err.response?.data?.detail || '审核操作失败',
      )
    }
  }
}

// 发送审核请求（支持传入审核意见）
const sendReviewRequest = async (row, status, force, reviewComment = '') => {
  const params = {
    review_status: status,
    force: force,
  }
  // 只有拒绝且有意见时才传 review_comment
  if (reviewComment) {
    params.review_comment = reviewComment
  }
  await request.put(`/case_review/${row.case_id}/review`, null, {
    params,
  })
}

// 批量审核（分片高并发+断点续传机制）
const batchReview = async (status) => {
  if (!selectedCases.value.length) return

  // 拒绝时弹出输入框，要求填写统一修改建议
  let batchComment = ''
  if (status === '已拒绝') {
    try {
      const { value } = await ElMessageBox.prompt(
        `请输入对选中的 ${selectedCases.value.length} 个案件的统一修改建议：`,
        '填写批量审核意见',
        {
          confirmButtonText: '确认批量拒绝',
          cancelButtonText: '取消',
          inputType: 'textarea',
          inputPlaceholder: '请说明需要修改的共性问题（可留空，留空则不附加意见）...',
        },
      )
      batchComment = (value || '').trim()
    } catch {
      // 用户取消输入，终止批量审核
      return
    }
  }

  try {
    await ElMessageBox.confirm(
      `确定要将选中的 ${selectedCases.value.length} 个案件标记为「${status}」吗？`,
      '批量审核确认',
      { type: status === '已审核' ? 'success' : 'warning' },
    )

    // 初始化进度条数据
    batchTotal.value = selectedCases.value.length
    batchProgress.value = 0
    batchSuccessCount.value = 0
    batchFailCount.value = 0
    showBatchProgress.value = true

    const CHUNK_SIZE = 50 // 设定每个批次发送 50 条给后端，兼顾进度条刷新频率和服务器压力

    // 核心拆分循环
    for (let i = 0; i < selectedCases.value.length; i += CHUNK_SIZE) {
      const chunk = selectedCases.value.slice(i, i + CHUNK_SIZE)
      const chunkIds = chunk.map((item) => item.case_id)

      try {
        // 请求新的批量接口，传入审核意见
        const res = await request.post('/case_review/batch_review', {
          case_ids: chunkIds,
          review_status: status,
          force_ids: [], // 首次跑批都不强制通过
          review_comment: batchComment || null, // 传入统一审核意见
        })

        const { success_cases, conflict_cases, error_cases } = res.data

        // 1. 无冲突的直接推进进度
        batchSuccessCount.value += success_cases.length
        batchFailCount.value += error_cases.length
        batchProgress.value += success_cases.length + error_cases.length

        // 2. 单独处理本批次被拦截的冲突案件
        if (conflict_cases && conflict_cases.length > 0) {
          for (const conflictItem of conflict_cases) {
            // 弹出对话框并等待用户选择
            const userConfirmed = await showConflictDialog(
              conflictItem.conflicts,
              conflictItem.case_id,
              conflictItem.case_number,
            )

            if (userConfirmed) {
              // 用户确认强制通过，发送单条强制请求补录 (force = true)
              try {
                // 传入对象包装 case_id，兼容原有的 sendReviewRequest 结构，同时传入统一意见
                await sendReviewRequest({ case_id: conflictItem.case_id }, status, true, batchComment)
                batchSuccessCount.value++
              } catch (retryErr) {
                console.error(`案件 ${conflictItem.case_number} 强制审核失败:`, retryErr)
                batchFailCount.value++
              }
            } else {
              // 用户取消审核当前案件，视为跳过
              batchFailCount.value++
            }
            // 无论当前冲突案件强制通过还是跳过，都推进进度条
            batchProgress.value++
          }
        }
      } catch (err) {
        // 如果整个网络请求崩了，这批次全部算失败，进度条继续走下一批
        console.error(`批次处理失败:`, err)
        batchFailCount.value += chunk.length
        batchProgress.value += chunk.length
      }
    }

    // 延时关闭进度条，让用户看到 100% 状态
    setTimeout(() => {
      showBatchProgress.value = false
      ElMessage({
        message: `批量操作结束！成功 ${batchSuccessCount.value} 笔，跳过/失败 ${batchFailCount.value} 笔。`,
        type: batchFailCount.value > 0 ? 'warning' : 'success',
        duration: 5000,
      })

      // 清空选择并刷新列表
      selectedCases.value = []
      isAllSelected.value = false
      if (caseTableRef.value) {
        caseTableRef.value.clearSelection()
      }
      fetchPendingCases()
    }, 800)
  } catch (err) {
    if (err !== 'cancel') {
      console.error('批量审核发生错误:', err)
      ElMessage.error('批量审核发生错误')
    }
  }
}

// 加载待审核案件
const fetchPendingCases = async () => {
  tableLoading.value = true
  try {
    const res = await request.get(`/case_review/pending`, {
      params: {
        skip: (page.value - 1) * pageSize.value,
        limit: pageSize.value,
      },
    })
    casesList.value = res.data.items || []
    total.value = res.data.total || 0
  } catch (err) {
    console.error('获取待审核案件失败:', err)
    ElMessage.error(err.response?.data?.detail || '获取待审核案件失败')
    casesList.value = []
    total.value = 0
  } finally {
    tableLoading.value = false
  }
}

// 跳转到详情页
const navigateToDetail = (caseId) => {
  const routeData = router.resolve({
    path: `/main/cases/${caseId}`,
    query: {
      from: '/main/case_review',
    },
  })
  window.open(routeData.href, '_blank')
}

// 切换每页显示条数
const handleSizeChange = (size) => {
  pageSize.value = size
  page.value = 1 // 切换条数后回到第一页
  fetchPendingCases()
}

// 分页切换
const handlePageChange = (p) => {
  page.value = p
  fetchPendingCases()
}

// 日期格式化
const formatDate = (dateVal) => {
  if (!dateVal) return ''

  let timestamp
  if (typeof dateVal === 'number') {
    if (dateVal.toString().length === 10) {
      dateVal *= 1000
    }
    timestamp = dateVal
  } else if (typeof dateVal === 'string') {
    const formats = [dateVal.replace(' ', 'T'), dateVal.replace(' ', 'T') + 'Z', dateVal]

    for (const fmt of formats) {
      const tempDate = new Date(fmt)
      if (!isNaN(tempDate.getTime())) {
        timestamp = tempDate.getTime()
        break
      }
    }
  } else if (dateVal instanceof Date) {
    timestamp = dateVal.getTime()
  }

  if (timestamp === undefined || isNaN(timestamp)) {
    console.warn('无法解析的日期格式:', dateVal)
    return '无效日期'
  }

  const date = new Date(timestamp)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  })
}

// 页面加载时初始化
onMounted(() => {
  fetchPendingCases()
  window.addEventListener('resize', handleResize)
})

// 组件卸载时移除监听
onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.case-review-page {
  padding: 20px;
}

/* 头部响应式布局 */
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap; /* 允许折叠换行 */
  gap: 15px; /* 换行后的间距 */
}

.header h2 {
  margin: 0;
}

.bulk-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.detail-cell {
  color: #409eff;
  cursor: pointer;
  text-decoration: underline;
  white-space: nowrap; /* 保证文字不换行断裂 */
}

.action-buttons {
  display: flex;
  gap: 5px;
}

/* 分页容器响应式排版 */
.pagination-container {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}

/* 冲突对话框样式优化 */
:deep(.conflict-dialog) {
  width: 90% !important; /* 移动端占满屏幕宽度 */
  max-width: 600px !important; /* 桌面端最大宽度 */
}
:deep(.conflict-dialog .el-message-box__content) {
  max-height: 50vh; /* 使用视窗高度百分比，避免小屏幕超出 */
  overflow-y: auto;
}

/* 针对小屏幕(移动端)的进一步微调 */
@media screen and (max-width: 768px) {
  .case-review-page {
    padding: 10px; /* 移动端减小内边距节省空间 */
  }

  .pagination-container {
    justify-content: center; /* 移动端分页居中 */
  }
}
</style>
