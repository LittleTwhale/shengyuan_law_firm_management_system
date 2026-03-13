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
      <el-table-column prop="client_name" label="委托人" min-width="100" />
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
        :layout="isMobile ? 'prev, pager, next' : 'prev, pager, next, jumper, ->, total'"
        :current-page="page"
        :page-size="pageSize"
        :total="total"
        :pager-count="isMobile ? 5 : 7"
        @current-change="handlePageChange"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/utils/request'
import { useRouter } from 'vue-router'

const router = useRouter()

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
    // 动态生成 HTML，增加跳转链接
    // 注意：这里的字段名要对应后端 check_interest_conflict_for_case 返回的字典 key
    let conflictHtml = `<div style="max-height: 400px; overflow-y: auto;">
      <p style="color: #e6a23c; margin-bottom: 15px; font-size: 16px;">
        <i class="el-icon-warning"></i>
        案件 <strong>${caseNumber}</strong> 可能存在利益冲突，管理员操作需谨慎。
      </p>
      <div style="background: #fff5f5; padding: 15px; border-radius: 4px; border: 1px solid #fab6b6;">
        <h4 style="margin: 0 0 10px 0; color: #f56c6c;">冲突详情：</h4>
        <ul style="margin: 0; padding-left: 20px;">
          ${conflicts
            .map(
              (c) => `
            <li style="margin-bottom: 12px; line-height: 1.5;">
              <div style="font-weight: bold; color: #303133;">${c.conflict_type}</div>
              <div style="font-size: 13px; color: #606266;">
                冲突案件：
                <a href="/main/cases/${c.case_id}" target="_blank" style="color: #409eff; text-decoration: underline; font-weight: bold;">
                  ${c.case_number}
                </a>
                <span style="margin-left: 10px;">(主办: ${c.other_lawyer_name})</span>
              </div>
              <div style="font-size: 13px; color: #F56C6C;">
                说明：${c.message}
              </div>
            </li>
          `,
            )
            .join('')}
        </ul>
      </div>
      <p style="margin-top: 15px; font-size: 13px; color: #909399;">
        提示：点击业务号可新窗口打开详情。确认"强制通过"将忽略此冲突。
      </p>
    </div>`

    ElMessageBox.confirm(conflictHtml, '可能存在利益冲突', {
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
  try {
    // 第一次尝试请求 (force = false)
    await sendReviewRequest(row, status, false)

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
          await sendReviewRequest(row, status, true)
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

// 强制通过审核（忽略冲突）
const sendReviewRequest = async (row, status, force) => {
  await request.put(`/case_review/${row.case_id}/review`, null, {
    params: {
      review_status: status,
      force: force, // 传递 force 参数
    },
  })
}

// 批量审核
const batchReview = async (status) => {
  if (!selectedCases.value.length) return

  try {
    await ElMessageBox.confirm(
      `确定要将选中的 ${selectedCases.value.length} 个案件标记为「${status}」吗？`,
      '批量审核确认',
      { type: status === '已审核' ? 'success' : 'warning' },
    )

    await Promise.all(
      selectedCases.value.map((item) =>
        request.put(`/case_review/${item.case_id}/review`, null, {
          params: { review_status: status },
        }),
      ),
    )

    ElMessage.success(
      `已成功批量${status === '已审核' ? '通过' : '拒绝'} ${selectedCases.value.length} 个案件`,
    )
    selectedCases.value = []
    isAllSelected.value = false
    await fetchPendingCases()
  } catch (err) {
    if (err !== 'cancel') {
      console.error('批量审核失败:', err)
      ElMessage.error(err.response?.data?.detail || '批量审核失败')
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
